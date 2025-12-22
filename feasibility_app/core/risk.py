import numpy as np
import pandas as pd
from core.model import ProjectModel, DistributionConfig
from core.engine import calculate_financials
import copy
from typing import List, Dict

def run_sensitivity_variable(base_model: ProjectModel, variable: str, steps: np.ndarray) -> pd.DataFrame:
    """
    Varies a single variable by percentage steps (e.g. -10%, 0%, +10%)
    and records NPV/IRR.
    """
    results_list = []
    
    for step in steps:
        factor = step
        
        sim_model = copy.deepcopy(base_model)
        apply_factor_to_model(sim_model, variable, factor)
        
        res = calculate_financials(sim_model)
        results_list.append({
            "Change (Multiplier)": factor,
            "Change %": (factor - 1.0) * 100,
            "NPV": res.kpi["npv"],
            "IRR": res.kpi["irr"]
        })
        
    return pd.DataFrame(results_list)

def run_tornado_analysis(base_model: ProjectModel, variables: List[str] = None) -> pd.DataFrame:
    """
    Runs a Tornado analysis on key variables (auto-selected if None).
    Steps: -10% (0.9) and +10% (1.1).
    """
    if variables is None:
        variables = ["Price", "Volume", "CAPEX", "OPEX"]
        
    results = []
    base_res = calculate_financials(base_model)
    base_npv = base_res.kpi["npv"]
    
    for var in variables:
        # Downside (0.9)
        model_down = copy.deepcopy(base_model)
        apply_factor_to_model(model_down, var, 0.9)
        res_down = calculate_financials(model_down)
        npv_down = res_down.kpi["npv"]
        
        # Upside (1.1)
        model_up = copy.deepcopy(base_model)
        apply_factor_to_model(model_up, var, 1.1)
        res_up = calculate_financials(model_up)
        npv_up = res_up.kpi["npv"]
        
        results.append({
            "Variable": var,
            "Base NPV": base_npv,
            "Downside NPV (0.9x)": npv_down,
            "Upside NPV (1.1x)": npv_up,
            "Range": abs(npv_up - npv_down),
            "Swing Down": npv_down - base_npv,
            "Swing Up": npv_up - base_npv
        })
        
    df = pd.DataFrame(results)
    return df.sort_values(by="Range", ascending=True) # Sorted for Tornado Chart (Largest at top usually, Plotly does inverted)

def apply_factor_to_model(model: ProjectModel, variable: str, factor: float):
    # Common helper
    if variable == "Price":
        for p in model.products:
            p.unit_price *= factor
    elif variable == "Volume":
        for p in model.products:
            p.initial_volume *= factor
    elif variable == "CAPEX":
        for c in model.capex_items:
            c.amount *= factor
    elif variable == "OPEX":
        for e in model.fixed_expenses:
            e.amount_per_year *= factor
        for per in model.personnel:
            per.monthly_gross_salary *= factor

def get_inverse_cdf(val: float, config: DistributionConfig) -> float:
    """
    Inverse Transform Sampling helper.
    Maps a [0,1] uniform/normal value to the target distribution factor.
    Ideally we map Normal(0,1) -> Target.
    """
    # But for simplicity & Cholesky, we generate Correlated Standard Normals (Z scores).
    # Then we map Z -> Uniform -> Target Distribution?
    # Or map Z -> Target directly if Normal/LogNormal.
    pass

def run_monte_carlo(base_model: ProjectModel, iterations: int = 1000) -> pd.DataFrame:
    """
    Runs Monte Carlo simulation with CORRELATED variables.
    """
    np.random.seed(base_model.risk_config.random_seed)
    
    # 1. Identify Variables involved
    vars_interest = ["Volume", "Price", "CAPEX", "OPEX"]
    n_vars = len(vars_interest)
    
    # 2. Build Covariance/Correlation Matrix
    corr_matrix = np.eye(n_vars)
    for i, v1 in enumerate(vars_interest):
        for j, v2 in enumerate(vars_interest):
            if i != j:
                c = base_model.risk_config.get_correlation(v1, v2)
                corr_matrix[i, j] = c
                
    # 3. Generate Correlated Standard Normals (Z-scores)
    # Shape: (iterations, n_vars)
    # Using multivariate_normal
    mean_vec = np.zeros(n_vars)
    
    try:
        # Check positive semi-definite, else fallback to independent
        z_scores = np.random.multivariate_normal(mean_vec, corr_matrix, iterations)
    except np.linalg.LinAlgError:
        print("Warning: Correlation matrix not PSD. Falling back to independent.")
        z_scores = np.random.normal(0, 1, size=(iterations, n_vars))
        
    results_list = []
    
    # Pre-fetch configs
    configs = {v: base_model.risk_config.get_config(v) for v in vars_interest}
    
    # 4. Transform Z-scores to Actual Multipliers
    # We'll batch process for speed instead of loop per iteration if possible?
    # Actually, calculate_financials is the bottleneck, so loop is fine.
    
    # Pre-calculate factors array (Iterations x Vars)
    factors_arr = np.zeros((iterations, n_vars))
    
    from scipy.stats import norm, triang, lognorm, uniform
    
    for i_var, var_name in enumerate(vars_interest):
        conf = configs[var_name]
        z_col = z_scores[:, i_var] # Standard Normals
        
        # Transform Z -> Target
        # Base multiplier is 1.0. The Distribution defines deviation from 1.0 (via percent params)
        # e.g. Mean=0.0 means 0% shift -> 1.0.
        
        if conf.dist_type == "Normal":
            # Target: Normal(mean_pct, std_dev_pct)
            # Factor = 1.0 + (mean_pct + Z * std_dev_pct)
            factors_arr[:, i_var] = 1.0 + (conf.mean_pct + z_col * conf.std_dev_pct)
            
        elif conf.dist_type == "Lognormal":
            # Lognormal is tricky. Usually defined by Mu, Sigma of underlying normal.
            # If user inputs Mean Pct and Std Dev Pct of the RESULTING variables?
            # Simplified: Mean=1.0+mean_pct, Sigma approx. 
            # Classic Lognormal: exp(mu + sigma*Z).
            # We want median to be 1.0? Or mean?
            # Let's assume user inputs 'std_dev_pct' as 'volatility'.
            # Factor = 1.0 + mean_pct * exp(sigma * Z - 0.5*sigma^2)?
            # Let's stick to simple LogNormal derived from Normal approximation
            # If Z is normal, exp(Z*sigma) is lognormal.
            sigma = conf.std_dev_pct
            factors_arr[:, i_var] = (1.0 + conf.mean_pct) * np.exp(z_col * sigma - 0.5 * sigma**2)
            
        elif conf.dist_type == "Uniform":
            # Map Z (Normal) -> U[0,1] -> Uniform[Min, Max]
            u_vals = norm.cdf(z_col)
            range_span = conf.max_pct - conf.min_pct
            factors_arr[:, i_var] = 1.0 + (conf.min_pct + u_vals * range_span)
            
        elif conf.dist_type == "Triangular":
            # Map Z (Normal) -> U[0,1] -> Triangular
            u_vals = norm.cdf(z_col)
            # scipy.stats.triang takes c (shape), loc, scale
            # c = (mode - min) / (max - min)
            # loc = min
            # scale = max - min
            denom = (conf.max_pct - conf.min_pct)
            if denom == 0: denom = 1e-9
            c = (conf.mode_pct - conf.min_pct) / denom
            
            # Using ppf (inverse cdf)
            tri_vals = triang.ppf(u_vals, c, loc=conf.min_pct, scale=denom)
            factors_arr[:, i_var] = 1.0 + tri_vals
            
    # 5. Run Simulation Loop
    for i in range(iterations):
        sim_model = copy.deepcopy(base_model)
        
        row_factors = {}
        
        for idx, var_name in enumerate(vars_interest):
            f = factors_arr[i, idx]
            row_factors[var_name] = f
            apply_factor_to_model(sim_model, var_name, f)
            
        res = calculate_financials(sim_model)
        
        row = {
            "Iteration": i,
            "NPV": res.kpi.get("npv", 0),
            "IRR": res.kpi.get("irr", 0),
        }
        # Add factors
        for k, v in row_factors.items():
            row[f"{k}_Factor"] = v
            
        results_list.append(row)
        
    return pd.DataFrame(results_list)

