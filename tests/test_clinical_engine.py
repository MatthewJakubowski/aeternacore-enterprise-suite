import pytest
from dataclasses import replace
from core.models import CompleteLabProfile
from core.biostatistics import BiostatisticalClinicalEngine

@pytest.fixture
def standard_profile():
    return CompleteLabProfile(
        age=40.0, sex="M", vo2max=43.5, hrv_rmssd=44.0, sbp_mmhg=122.0, is_smoker=False,
        hil_status="CLEAR", prev_hscrp=0.90, alb_g_dl=4.55, cr_mg_dl=0.92, glu_mg_dl=92.0,
        ins_uiu_ml=5.2, hscrp_mg_l=0.60, lym_pct=31.5, lym_abs=1.8, neut_abs=3.4,
        mcv_fl=88.5, rdw_pct=12.2, plt_10_9_l=235.0, ast_u_l=21.0, alt_u_l=19.0,
        alp_u_l=52.0, wbc_10_9_l=5.6, apob_mg_dl=88.0, tg_mg_dl=75.0, hdl_mg_dl=55.0,
        potassium_mmol_l=4.4, calcium_mmol_l=2.35, mthfr_genotype="CC", slco1b1_status="NORMAL",
        prescribed_statin="Atorwastatyna"
    )

def test_standard_profile_autovalidation_pass(standard_profile):
    """Weryfikacja czy profil fizjologiczny przechodzi autowalizację (AUTOPASS)."""
    res = BiostatisticalClinicalEngine.evaluate_all(standard_profile, lang="PL")
    assert res["autoval_code"] == "PASS"
    assert "AUTOPASS" in res["autoval_verdict"] or "AVR" in res["autoval_verdict"]

def test_edta_contamination_rejection(standard_profile):
    """Weryfikacja blokady zanieczyszczenia probówki EDTA z wykorzystaniem replace dla immutable dataclass."""
    edta_profile = replace(standard_profile, potassium_mmol_l=8.6, calcium_mmol_l=0.75)
    res = BiostatisticalClinicalEngine.evaluate_all(edta_profile, lang="PL")
    assert res["autoval_code"] in ["CRITICAL_REJECT", "REJECT"]

def test_phenoage_calculation_bounds(standard_profile):
    """Weryfikacja czy estymacja PhenoAge daje biologicznie wiarygodny wynik."""
    res = BiostatisticalClinicalEngine.evaluate_all(standard_profile, lang="PL")
    assert 15.0 < res["pheno_age"] < 100.0
    assert "age_delta" in res
