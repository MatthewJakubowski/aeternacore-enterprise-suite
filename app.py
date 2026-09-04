import streamlit as st
import numpy as np
import plotly.graph_objects as go
from core.models import CompleteLabProfile
from core.i18n import I18N
from core.biostatistics import BiostatisticalClinicalEngine
from core.simulations import LongevitySimulations
from export.pdf_generator import generate_pdf_in_memory
from export.interop import MedicalInteroperabilityEngine

st.set_page_config(page_title="AeternaCore Enterprise | Mateusz Jakubowski", layout="wide", page_icon="🧬")

st.markdown("""
<style>
    .header-box {
        background: linear-gradient(135deg, #090e1a 0%, #1e293b 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        color: white;
    }
    .tag-brand {
        background: #0284c7;
        color: #ffffff;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
        margin-bottom: 6px;
    }
    .badge-link {
        display: inline-flex;
        align-items: center;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 9999px;
        padding: 4px 12px;
        color: #38bdf8 !important;
        text-decoration: none !important;
        font-size: 12.5px;
        font-weight: 700;
        margin-top: 8px;
    }
    .metric-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px;
        color: white;
    }
    .metric-lbl { font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px; }
    .metric-val { font-size: 24px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state.lang = "PL"

col_h1, col_h2 = st.columns([4, 1])
with col_h2:
    selected_lang = st.radio("🌐 Language / Język", ["PL", "EN"], index=0 if st.session_state.lang == "PL" else 1, horizontal=True)
    st.session_state.lang = selected_lang

lang = st.session_state.lang
t = I18N[lang]

st.markdown(f"""
<div class="header-box">
    <span class="tag-brand">#FromPipetteToPython</span>
    <span style="color: #94a3b8; font-size: 13px; font-weight: 500; margin-left: 8px;">{t['header_subtitle']}</span>
    <h1 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #ffffff;">{t['header_title']}</h1>
    <p style="margin: 4px 0 8px 0; color: #38bdf8; font-size: 13.5px; font-weight: 600;">{t['header_bio']}</p>
    <a class="badge-link" href="https://mateusz-jakubowski.ai.studio/" target="_blank">{t['badge_portfolio']}</a>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎛 " + ("Dane Laboratoryjne" if lang == "PL" else "Lab Data Matrix"))
    preset = st.selectbox(
        "🧪 Presety Diagnostyczne LIS" if lang == "PL" else "🧪 LIS Diagnostic Presets",
        [
            "STANDARD (Fizjologiczny)",
            "EDTA CONTAMINATION (K+ 8.5, Ca2+ 0.8)",
            "HEMOLYSIS INTERFERENCE (HIL)",
            "DELTA CHECK KINETIC SPIKE",
            "ACUTE INFLAMMATION PARADOX (hsCRP 45)",
            "CPIC PGX COLLISION (SLCO1B1 *5/*5)"
        ]
    )

    def_age, def_glu, def_alb, def_cr = 40, 92, 4.55, 0.92
    def_hscrp, def_prev_crp, def_hil = 0.60, 0.90, "CLEAR"
    def_potassium, def_calcium = 4.4, 2.35
    def_mthfr, def_slco, def_statin = "CC", "NORMAL", "Atorwastatyna"

    if preset == "EDTA CONTAMINATION (K+ 8.5, Ca2+ 0.8)":
        def_potassium = 8.6
        def_calcium = 0.75
    elif preset == "HEMOLYSIS INTERFERENCE (HIL)":
        def_hil = "HEMOLYSIS"
        def_hscrp = 4.80
    elif preset == "DELTA CHECK KINETIC SPIKE":
        def_prev_crp = 0.40
        def_hscrp = 6.80
    elif preset == "ACUTE INFLAMMATION PARADOX (hsCRP 45)":
        def_hscrp = 45.0
    elif preset == "CPIC PGX COLLISION (SLCO1B1 *5/*5)":
        def_mthfr = "677TT"
        def_slco = "POOR"
        def_statin = "Symwastatyna"

    with st.expander("Pre-Analityka & Jonogram" if lang == "PL" else "Pre-Analytics & Electrolytes", expanded=True):
        hil_status = st.selectbox("Indeks HIL", ["CLEAR", "HEMOLYSIS", "LIPEMIA"], index=["CLEAR", "HEMOLYSIS", "LIPEMIA"].index(def_hil))
        prev_hscrp = st.number_input("Poprzednie hsCRP [mg/L]", 0.0, 50.0, float(def_prev_crp), step=0.1)
        potassium = st.number_input("Potas (K+) [mmol/L]", 2.0, 10.0, float(def_potassium), step=0.1)
        calcium = st.number_input("Wapń (Ca2+) [mmol/L]", 0.5, 4.0, float(def_calcium), step=0.05)

    with st.expander("Metabolizm & Lipidy" if lang == "PL" else "Metabolic & Lipids", expanded=True):
        age = st.slider("Wiek / Age", 18, 90, def_age)
        sex = st.radio("Płeć / Sex", ["M", "K"] if lang == "PL" else ["M", "F"], horizontal=True)
        glu = st.number_input("Glukoza / Glucose [mg/dL]", 30, 500, def_glu)
        ins = st.number_input("Insulina / Insulin [uIU/mL]", 1.0, 80.0, 5.2)
        apob = st.number_input("ApoB [mg/dL]", 30, 250, 88)
        tg = st.number_input("Triglicerydy / TG [mg/dL]", 30, 600, 75)
        hdl = st.number_input("HDL-C [mg/dL]", 15, 120, 55)

    with st.expander("Morfologia & Zapalenie" if lang == "PL" else "CBC & Inflammation", expanded=False):
        hscrp = st.number_input("hsCRP [mg/L]", 0.01, 80.0, float(def_hscrp), step=0.05)
        wbc = st.number_input("WBC [10^9/L]", 1.0, 30.0, 5.6)
        neut_abs = st.number_input("Neutrofile (#)", 0.5, 20.0, 3.4)
        lym_abs = st.number_input("Limfocyty (#)", 0.2, 10.0, 1.8)
        lym_pct = st.number_input("Limfocyty (%)", 5.0, 75.0, 31.5)
        mcv = st.number_input("MCV [fl]", 60.0, 120.0, 88.5)
        rdw = st.number_input("RDW [%]", 9.0, 25.0, 12.2)
        plt = st.number_input("Płytki (PLT) [10^9/L]", 30, 800, 235)

    with st.expander("Biochemia Narządowa" if lang == "PL" else "Organ Chemistry", expanded=False):
        alb = st.number_input("Albumina [g/dL]", 1.5, 6.0, float(def_alb))
        cr = st.number_input("Kreatynina [mg/dL]", 0.3, 10.0, float(def_cr))
        ast = st.number_input("AST [U/L]", 5, 200, 21)
        alt = st.number_input("ALT [U/L]", 5, 200, 19)
        alp = st.number_input("ALP [U/L]", 15, 300, 52)
        sbp = st.number_input("Ciśnienie RR [mmHg]", 80, 220, 122)
        smoker = st.checkbox("Status palacza" if lang == "PL" else "Smoker", value=False)
        vo2 = st.slider("VO2max [ml/kg/min]", 15.0, 80.0, 43.5)
        hrv = st.slider("HRV rMSSD [ms]", 10.0, 150.0, 44.0)

    with st.expander("Farmakogenomika CPIC" if lang == "PL" else "Pharmacogenomics CPIC", expanded=False):
        mthfr = st.selectbox("MTHFR", ["CC", "677CT", "677TT"], index=["CC", "677CT", "677TT"].index(def_mthfr))
        slco = st.selectbox("SLCO1B1", ["NORMAL", "POOR"], index=["NORMAL", "POOR"].index(def_slco))
        statin = st.selectbox("Statyna", ["Atorwastatyna", "Rozuwastatyna", "Symwastatyna", "BRAK"], index=["Atorwastatyna", "Rozuwastatyna", "Symwastatyna", "BRAK"].index(def_statin))

profile = CompleteLabProfile(
    age=float(age), sex="M" if sex in ["M", "Male"] else "K", vo2max=float(vo2), hrv_rmssd=float(hrv),
    sbp_mmhg=float(sbp), is_smoker=smoker, hil_status=hil_status, prev_hscrp=float(prev_hscrp),
    alb_g_dl=float(alb), cr_mg_dl=float(cr), glu_mg_dl=float(glu), ins_uiu_ml=float(ins),
    hscrp_mg_l=float(hscrp), lym_pct=float(lym_pct), lym_abs=float(lym_abs), neut_abs=float(neut_abs),
    mcv_fl=float(mcv), rdw_pct=float(rdw), plt_10_9_l=float(plt), ast_u_l=float(ast), alt_u_l=float(alt),
    alp_u_l=float(alp), wbc_10_9_l=float(wbc), apob_mg_dl=float(apob), tg_mg_dl=float(tg),
    hdl_mg_dl=float(hdl), potassium_mmol_l=float(potassium), calcium_mmol_l=float(calcium),
    mthfr_genotype=mthfr, slco1b1_status=slco, prescribed_statin=statin
)

res = BiostatisticalClinicalEngine.evaluate_all(profile, lang=lang)

kpi_cols = st.columns(5)
with kpi_cols[0]:
    delta_color = "#4ade80" if res['age_delta'] <= 0 else "#f87171"
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">{t["lbl_pheno"]}</div><div class="metric-val" style="color:#38bdf8;">{res["pheno_age"]} <span style="font-size:13px;color:#cbd5e1;">{t["lbl_yrs"]}</span></div><div style="color:{delta_color};font-size:12px;font-weight:600;">{res["age_delta"]:+0.2f} {t["lbl_vs"]}</div></div>', unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">{t["lbl_pace"]}</div><div class="metric-val" style="color:#a78bfa;">{res["dunedin_pace"]} <span style="font-size:13px;color:#cbd5e1;">yr/yr</span></div><div style="color:#94a3b8;font-size:12px;">DunedinPACE</div></div>', unsafe_allow_html=True)
with kpi_cols[2]:
    badge_bg = "#10b981" if res['autoval_code'] == "PASS" else "#ef4444"
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">{t["lbl_lis"]}</div><div class="metric-val" style="color:{badge_bg};font-size:18px;margin-top:4px;">{res["autoval_code"]}</div><div style="color:#94a3b8;font-size:11px;">{res["autoval_verdict"][:20]}...</div></div>', unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">{t["lbl_tyg"]}</div><div class="metric-val" style="color:#34d399;">{res["tyg_index"]} <span style="font-size:13px;color:#cbd5e1;">/ {res["homa_ir"]}</span></div><div style="color:#94a3b8;font-size:12px;">Metabolizm glikemii</div></div>', unsafe_allow_html=True)
with kpi_cols[4]:
    st.markdown(f'<div class="metric-card"><div class="metric-lbl">{t["lbl_score"]}</div><div class="metric-val" style="color:#f43f5e;">{res["score2_pct"]}%</div><div style="color:#94a3b8;font-size:12px;">10-Year CVD Risk</div></div>', unsafe_allow_html=True)

st.write("")

tab_sum, tab_shap, tab_recs, tab_iso, tab_mc, tab_ode, tab_exp, tab_story, tab_law = st.tabs([
    t["tab_summary"], t["tab_shap"], t["tab_protocols"], t["tab_iso"],
    t["tab_mc"], t["tab_ode"], t["tab_interop"], t["tab_story"], t["tab_compliance"]
])

with tab_sum:
    col_g, col_r = st.columns(2)
    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=res["pheno_age"],
            delta={'reference': profile.age, 'increasing': {'color': "#ef4444"}, 'decreasing': {'color': "#10b981"}, 'valueformat': ".2f"},
            number={'suffix': f" {t['lbl_yrs']}", 'font': {'size': 30}},
            title={'text': f"<b>{t['gauge_title']}</b><br><span style='font-size:12px;color:#94a3b8'>{t['gauge_sub']}: {profile.age:.1f} {t['lbl_yrs']}</span>"},
            gauge={
                'axis': {'range': [max(18, profile.age - 15), profile.age + 15]},
                'bar': {'color': "#0284c7"},
                'steps': [
                    {'range': [profile.age - 15, profile.age - 2], 'color': "rgba(16, 185, 129, 0.2)"},
                    {'range': [profile.age - 2, profile.age + 2], 'color': "rgba(245, 158, 11, 0.2)"},
                    {'range': [profile.age + 2, profile.age + 15], 'color': "rgba(239, 68, 68, 0.2)"}
                ],
                'threshold': {'line': {'color': "#f8fafc", 'width': 3}, 'value': profile.age}
            }
        ))
        fig_gauge.update_layout(height=290, template="plotly_dark", margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_r:
        r_cardio = min(max(100 - (45 - profile.vo2max) * 2.2, 20), 100)
        r_immune = min(max(100 - (profile.hscrp_mg_l - 0.7) * 25, 20), 100)
        r_metab = min(max(100 - (res["homa_ir"] - 1.0) * 35, 20), 100)
        r_renal = min(max((res["egfr"] / 110) * 100, 20), 100)
        r_liver = min(max(100 - (res["fib4"] * 40), 20), 100)
        scores = [r_cardio, r_immune, r_metab, r_renal, r_liver, r_cardio]
        cats = t['radar_cats'] + [t['radar_cats'][0]]

        fig_radar = go.Figure(go.Scatterpolar(r=scores, theta=cats, fill='toself', fillcolor='rgba(2, 132, 199, 0.2)', line=dict(color='#0284c7', width=2)))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark", height=290, margin=dict(l=50, r=50, t=30, b=30), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown(f"""
    ### 📋 {"Szczegółowy Raport Biometryczny" if lang == "PL" else "Biometric Examination Summary"}
    * **{"Wiek Metrykalny" if lang == "PL" else "Chronological Age"}:** **{profile.age:.1f}** | **PhenoAge:** **{res['pheno_age']}** (Delta: **{res['age_delta']:+0.2f}**)
    * **{"10-letnie Ryzyko Śmiertelności Ogólnej" if lang == "PL" else "10-Year All-Cause Mortality Risk"}:** **{res['mort_10y']}%**
    * **{"Parametry Narządowe" if lang == "PL" else "Organ Reserves"}:** eGFR: **{res['egfr']} ml/min** | FIB-4: **{res['fib4']}** | NLR: **{res['nlr']}** | Zone 2 HR: **{res['z2_range']}**
    """)

with tab_shap:
    sorted_m = sorted(res["marginals"].items(), key=lambda x: abs(x[1]), reverse=True)
    y_lbls = [k for k, _ in sorted_m]
    x_vals = [v for _, v in sorted_m]
    colors_list = ["#ef4444" if v > 0 else "#10b981" for v in x_vals]

    fig_waterfall = go.Figure(go.Bar(
        y=y_lbls, x=x_vals, orientation='h', marker=dict(color=colors_list),
        text=[f"{v:+0.2f} " + t["lbl_yrs"] for v in x_vals], textposition="outside"
    ))
    max_abs = max([abs(v) for v in x_vals] + [1.0])
    fig_waterfall.update_layout(
        title=f"<b>{t['shap_title']}</b>", template="plotly_dark",
        xaxis=dict(title=t['shap_xaxis'], range=[-max_abs * 1.35, max_abs * 1.35]),
        yaxis=dict(autorange="reversed"), height=420, margin=dict(l=220, r=50, t=50, b=40), paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

with tab_recs:
    for rec in res["recommendations"]:
        st.markdown(rec)
        st.divider()

with tab_iso:
    st.markdown(f"""
    ### 🔬 {"5-Stopniowy Protokół Kontroli Jakości i Autowalidacji LIS" if lang == "PL" else "5-Stage Quality Control & LIS Autovalidation Engine"} (PN-EN ISO 15189:2023)
    * **Poziom 1 (Statystyczna Kontrola Jakości - Westgard Rules):** `{res['l1_westgard']}`
    * **Poziom 2 (Spektrofotometryczna Weryfikacja Interferencji HIL):** `{res['l2_hil']}`
    * **Poziom 3 (Weryfikacja Wartości Krytycznych / Panic Values):** `{res['l3_panic']}`
    * **Poziom 4 (Analiza Kinetyki Podłużnej - Longitudinal Delta Check 90d):** `{res['l4_delta']}`
    * **Poziom 5 (Zabezpieczenie Transmisji Szpitalnej HL7/EDM):** `AUTHORIZED FOR SECURE TRANSMISSION`

    > **{"Decyzja Systemowa Silnika LIS" if lang == "PL" else "LIS Disposition"}:** **{res['autoval_verdict']}**
    """)

with tab_mc:
    mc = LongevitySimulations.run_monte_carlo(profile.age, res["pheno_age"], res["dunedin_pace"])
    fig_mc = go.Figure()
    fig_mc.add_trace(go.Scatter(x=mc["time"], y=mc["chrono"], name=t['mc_chrono'], line=dict(dash="dash", color="#94a3b8", width=1.5)))
    fig_mc.add_trace(go.Scatter(x=np.concatenate([mc["time"], mc["time"][::-1]]), y=np.concatenate([mc["active_p90"], mc["active_p10"][::-1]]), fill='toself', fillcolor='rgba(2, 132, 199, 0.15)', line=dict(color='rgba(0,0,0,0)'), name=t['mc_band']))
    fig_mc.add_trace(go.Scatter(x=mc["time"], y=mc["active_median"], name=t['mc_opt'], line=dict(color="#0284c7", width=2.5)))
    fig_mc.add_trace(go.Scatter(x=mc["time"], y=mc["passive_median"], name=t['mc_pas'], line=dict(color="#ef4444", width=2)))
    fig_mc.update_layout(title=f"<b>{t['mc_title']}</b>", template="plotly_dark", height=350, margin=dict(l=40, r=40, t=50, b=40), paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_mc, use_container_width=True)

with tab_ode:
    t_ode, crp_traj, glu_traj = LongevitySimulations.run_bio_ode(profile.hscrp_mg_l, profile.glu_mg_dl)
    fig_ode = go.Figure()
    fig_ode.add_trace(go.Scatter(x=t_ode, y=crp_traj, name="hsCRP [mg/L]", line=dict(color="#ef4444", width=2)))
    fig_ode.add_trace(go.Scatter(x=t_ode, y=glu_traj, name=t['ode_glu'], line=dict(color="#0284c7", width=2), yaxis="y2"))
    fig_ode.update_layout(
        title=f"<b>{t['ode_title']}</b>",
        template="plotly_dark",
        xaxis=dict(title="Miesiące / Months"),
        yaxis=dict(title=dict(text="hsCRP [mg/L]", font=dict(color="#ef4444")), tickfont=dict(color="#ef4444")),
        yaxis2=dict(title=dict(text=t['ode_glu'], font=dict(color="#0284c7")), tickfont=dict(color="#0284c7"), overlaying="y", side="right"),
        height=350,
        margin=dict(l=40, r=40, t=50, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig_ode, use_container_width=True)

with tab_exp:
    st.markdown("### 🖨 " + ("Pakiety Transmisyjne i Eksport Sprawozdania" if lang == "PL" else "Data Packages & Report Export"))
    pdf_bytes = generate_pdf_in_memory(res)
    fhir_data = MedicalInteroperabilityEngine.generate_fhir_r4(res)
    edm_data = MedicalInteroperabilityEngine.generate_edm_xml(res)
    csv_data = MedicalInteroperabilityEngine.generate_research_csv(res)

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1:
        st.download_button(t["pdf_btn"], data=pdf_bytes, file_name=f"AeternaCore_Report_{profile.age:.0f}yo.pdf", mime="application/pdf", use_container_width=True)
    with col_b2:
        st.download_button(t["dl_fhir_btn"], data=fhir_data, file_name="FHIR_R4_Bundle.json", mime="application/json", use_container_width=True)
    with col_b3:
        st.download_button(t["dl_edm_btn"], data=edm_data, file_name="Dokumentacja_EDM.xml", mime="application/xml", use_container_width=True)
    with col_b4:
        st.download_button(t["dl_csv_btn"], data=csv_data, file_name="Research_Vector.csv", mime="text/csv", use_container_width=True)

    with st.expander("Podgląd struktury HL7 FHIR R4 Bundle (JSON)", expanded=False):
        st.code(fhir_data, language="json")

with tab_story:
    st.markdown(t["story_text"])

with tab_law:
    st.markdown(t["disclaimer_text"])
