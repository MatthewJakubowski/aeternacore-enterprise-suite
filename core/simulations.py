import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Tuple

class LongevitySimulations:
    @staticmethod
    def run_bio_ode(initial_crp: float, initial_glu: float, months: int = 24) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        basal_glu = 85.0
        k1 = 0.12
        k2 = 0.08
        alpha = 0.005
        beta = 0.15

        def system(t, y):
            crp, glu = y
            dcrp_dt = -k1 * crp + alpha * max(0.0, glu - basal_glu)
            dglu_dt = -k2 * (glu - basal_glu) + beta * max(0.0, crp - 0.5)
            return [dcrp_dt, dglu_dt]

        t_span = (0, months)
        t_eval = np.linspace(0, months, 100)
        sol = solve_ivp(system, t_span, [initial_crp, initial_glu], t_eval=t_eval, method='RK45')
        return sol.t, sol.y[0], sol.y[1]

    @staticmethod
    def run_monte_carlo(current_age: float, pheno_age: float, pace: float, years: int = 30, runs: int = 400) -> Dict[str, np.ndarray]:
        np.random.seed(42)
        time_steps = np.arange(0, years + 1)
        dt = 1.0

        sigma_passive = 0.45
        drift_passive = pace * 1.05
        traj_passive = np.zeros((runs, len(time_steps)))
        traj_passive[:, 0] = pheno_age

        sigma_active = 0.30
        drift_active = 0.82
        traj_active = np.zeros((runs, len(time_steps)))
        traj_active[:, 0] = pheno_age

        for t in range(1, len(time_steps)):
            traj_passive[:, t] = traj_passive[:, t-1] + drift_passive * dt + np.random.normal(0, sigma_passive, runs)
            traj_active[:, t] = traj_active[:, t-1] + drift_active * dt + np.random.normal(0, sigma_active, runs)

        return {
            "time": current_age + time_steps,
            "chrono": current_age + time_steps,
            "passive_median": np.median(traj_passive, axis=0),
            "active_median": np.median(traj_active, axis=0),
            "active_p10": np.percentile(traj_active, 10, axis=0),
            "active_p90": np.percentile(traj_active, 90, axis=0),
        }
