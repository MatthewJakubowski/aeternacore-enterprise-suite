from dataclasses import dataclass

@dataclass(frozen=True)
class CompleteLabProfile:
    age: float
    sex: str
    vo2max: float
    hrv_rmssd: float
    sbp_mmhg: float
    is_smoker: bool
    hil_status: str
    prev_hscrp: float
    alb_g_dl: float
    cr_mg_dl: float
    glu_mg_dl: float
    ins_uiu_ml: float
    hscrp_mg_l: float
    lym_pct: float
    lym_abs: float
    neut_abs: float
    mcv_fl: float
    rdw_pct: float
    plt_10_9_l: float
    ast_u_l: float
    alt_u_l: float
    alp_u_l: float
    wbc_10_9_l: float
    apob_mg_dl: float
    tg_mg_dl: float
    hdl_mg_dl: float
    potassium_mmol_l: float
    calcium_mmol_l: float
    mthfr_genotype: str
    slco1b1_status: str
    prescribed_statin: str
