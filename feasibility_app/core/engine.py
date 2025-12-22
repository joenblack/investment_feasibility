from typing import Dict, Any
import numpy as np
import pandas as pd
from core.model import ProjectModel, CurrencyType
from core import depreciation, finance, nwc

class FinancialResults:
    def __init__(self):
        self.years: list = []
        self.income_statement: pd.DataFrame = pd.DataFrame()
        self.cash_flow_statement: pd.DataFrame = pd.DataFrame()
        self.balance_sheet: pd.DataFrame = pd.DataFrame()
        self.kpi: Dict[str, float] = {}
        # Intermediate arrays for charts
        self.revenue_arr: np.ndarray = np.array([])
        self.ebitda_arr: np.ndarray = np.array([])
        self.ebitda_arr: np.ndarray = np.array([])
        self.free_cash_flow: np.ndarray = np.array([])
        self.dscr_arr: np.ndarray = np.array([])

def calculate_financials(model: ProjectModel) -> FinancialResults:
    horizon = model.horizon_years
    pp_year = 12 if model.granularity == "Month" else 1
    total_periods = horizon * pp_year
    
    # Years labels for Monthly would be dates or 1..12?
    # For reporting (Annual), we just stick to 1..Horizon.
    # The output 'years' list will be Annual for simplicity in chart x-axis unless monthly.
    years = list(range(1, horizon + 1)) 
    
    # Helper for FX
    def get_fx_multiplier(source_curr: str) -> float:
        if source_curr == model.currency_base:
            return 1.0
        # Simple Logic: Project Base / Source Rate ?
        # No, rates are usually X/TRY or X/Base?
        # Model stores: USD=35, EUR=38, TRY=1.
        # If Base is TRY. Source is USD. We have 100 USD.
        # Value = 100 * 35 = 3500 TRY.
        # Multiplier = Rate of Source / Rate of Base
        source_rate = model.exchange_rates.get(source_curr, 1.0)
        base_rate = model.exchange_rates.get(model.currency_base, 1.0)
        return source_rate / base_rate

    # 1. Revenue & OPEX
    revenue = np.zeros(total_periods)
    cogs = np.zeros(total_periods)
    total_receivables = np.zeros(total_periods)
    
    for prod in model.products:
        fx = get_fx_multiplier(prod.currency)
        
        # Initial annual figures (Converted to Base)
        annual_vol = prod.initial_volume
        unit_price = prod.unit_price * fx
        unit_cost = prod.unit_cost * fx
        
        # Per period figures
        period_demand_vol = annual_vol / pp_year
        period_capacity = prod.production_capacity_per_year / pp_year
        
        # Effective period growth rates
        vol_growth_p = (1 + prod.year_growth_rate) ** (1.0 / pp_year) - 1
        price_growth_p = (1 + prod.price_escalation_rate) ** (1.0 / pp_year) - 1
        cost_growth_p = (1 + prod.cost_escalation_rate) ** (1.0 / pp_year) - 1
        
        for i in range(total_periods):
            # 1. Determine Production Volume (Constrained)
            gross_needed = period_demand_vol / (1 - prod.scrap_rate) if prod.scrap_rate < 1 else period_demand_vol
            max_gross_prod = period_capacity * prod.oee_percent
            actual_gross_prod = min(gross_needed, max_gross_prod)
            actual_sales_vol = actual_gross_prod * (1 - prod.scrap_rate)
            
            # 2. Financials
            prod_rev = actual_sales_vol * unit_price
            revenue[i] += prod_rev
            cogs[i] += actual_gross_prod * unit_cost
            
            # 3. Receivables Calculation
            # Balance = Daily Sales * Terms
            # Here: Period Revenue / DaysInPeriod * Terms?
            # Or simplified: Revenue * (Terms / 365)?
            # If using Granularity=Year, terms/365 is correct.
            # If Month, terms/30?
            # Logic: Balance is roughly Sales * (Days / 365) regardless of granularity if Sales IS ANNUALIZED.
            # But here 'prod_rev' is PERIOD revenue.
            # If Period = Year, Rev * Terms/365.
            # If Period = Month, Rev * Terms/30?
            days_in_period = 365.0 / pp_year
            
            # Receivable Balance contribution
            # Only on the portion NOT advanced.
            credit_portion = 1.0 - prod.advance_payment_pct
            
            # Use Product terms if set, otherwise Global DSO
            terms = prod.payment_terms_days if prod.payment_terms_days is not None else model.nwc_config.dso
            
            prod_receivable = prod_rev * credit_portion * (terms / days_in_period)
            total_receivables[i] += prod_receivable
            
            # Growth
            period_demand_vol *= (1 + vol_growth_p)
            unit_price *= (1 + price_growth_p)
            unit_cost *= (1 + cost_growth_p)
            
            # Growth
            period_demand_vol *= (1 + vol_growth_p)
            unit_price *= (1 + price_growth_p)
            unit_cost *= (1 + cost_growth_p)
            
    gross_profit = revenue - cogs
    
    # --- SCALABLE PERSONNEL PRE-CALCULATION ---
    # We need aggregated actual sales volume per period to determine scaling factor.
    # Re-looping products to sum up actual volumes for Ratio.
    # Note: Ideally we could have summed this inside the loop above.
    # Let's do a quick pass or optimized way. For now, separate pass for clarity is fine or we can reconstruct.
    # Actually, we didn't store per-period volume for all products in an array.
    # Let's refactor the Revenue loop slightly to store 'total_sales_vol_by_period'
    
    # RE-RUN for Volume Index (Fast enough)
    total_sales_vol_by_period = np.zeros(total_periods)
    total_initial_vol = sum(p.initial_volume for p in model.products)
    
    if total_initial_vol > 0:
        for prod in model.products:
            # Re-simulate volume logic (identical to above)
            p_dem = prod.initial_volume / pp_year
            vol_g = (1 + prod.year_growth_rate) ** (1.0 / pp_year) - 1
            p_cap = prod.production_capacity_per_year / pp_year
            
            for i in range(total_periods):
                gross = p_dem / (1 - prod.scrap_rate) if prod.scrap_rate < 1 else p_dem
                max_g = p_cap * prod.oee_percent
                act_g = min(gross, max_g)
                act_sales = act_g * (1 - prod.scrap_rate)
                total_sales_vol_by_period[i] += act_sales
                p_dem *= (1 + vol_g)
        
        # Calculate Ratio
        # Initial Period Volume (Theoretical) = Total_Initial / pp_year
        base_period_vol = total_initial_vol / pp_year
        volume_scale_ratio = total_sales_vol_by_period / base_period_vol
    else:
        volume_scale_ratio = np.ones(total_periods)

    opex = np.zeros(total_periods)
    # Fixed Expenses
    for exp in model.fixed_expenses:
        fx = get_fx_multiplier(exp.currency) # Now assumed to exist or fail
        
        annual_amount = exp.amount_per_year * fx
        period_amount = annual_amount / pp_year
        rate_p = (1 + exp.growth_rate) ** (1.0 / pp_year) - 1
        
        for i in range(total_periods):
            opex[i] += period_amount
            period_amount *= (1 + rate_p)
            
    # Personnel
    for pers in model.personnel:
        fx = get_fx_multiplier(pers.currency)
        
        # Base Cost per person (Annual)
        base_annual_cost_per_person = (pers.monthly_gross_salary * fx) * 12 * (1 + pers.sgk_tax_rate)
        # Period cost per person
        period_cost_per_person = base_annual_cost_per_person / pp_year
        
        rate_p = (1 + pers.yearly_raise_rate) ** (1.0 / pp_year) - 1
        
        # Start period
        start_idx = (pers.start_year - 1) * pp_year
        
        for i in range(total_periods):
            if i >= start_idx:
                # Determine Headcount
                count = pers.count
                if pers.is_scalable:
                    count = pers.count * volume_scale_ratio[i]
                
                total_cost = count * period_cost_per_person
                opex[i] += total_cost
                
                # Apply Raise to Unit Cost
                period_cost_per_person *= (1 + rate_p)
                
    ebitda = gross_profit - opex
    
    # 2. CAPEX & Depreciation
    total_capex_flow = np.zeros(total_periods)
    dep_base_items = []
    
    for item in model.capex_items:
        fx = get_fx_multiplier(item.currency)
        
        # Determine period index
        if pp_year == 12:
            m = item.month if 1 <= item.month <= 12 else 1
            idx = (item.year - 1) * pp_year + (m - 1)
        else:
            idx = item.year - 1
            
        if 0 <= idx < total_periods:
            base_amount = item.amount * fx # Convert Base
            
            # Customs
            customs_cost = 0.0
            if item.is_imported:
                customs_cost = base_amount * item.customs_duty_rate
            
            # VAT
            vat_cost = 0.0
            if not model.tax_config.vat_exemption:
                vat_base = base_amount + customs_cost
                vat_cost = vat_base * item.vat_rate
            
            total_outflow = base_amount + customs_cost + vat_cost
            total_capex_flow[idx] += total_outflow
            
            # Depreciation Base
            dep_item = item.copy()
            dep_item.amount = base_amount + customs_cost # Already converted
            dep_base_items.append(dep_item)
            
    # 3. Grants
    grant_income_taxable = np.zeros(total_periods)
    grant_cash_inflow = np.zeros(total_periods)
    
    for grant in model.grants:
        # Grant currency usually local? Let's assume Base for now as 'Grant' model didn't get currency field update
        # If explicitly needed, we should add it. For now assume base.
        idx = (grant.year - 1) * pp_year
        if 0 <= idx < total_periods:
            grant_cash_inflow[idx] += grant.amount
            if not grant.is_capex_reduction:
                grant_income_taxable[idx] += grant.amount
                
    # Calculate Depreciation (Initial)
    dep_amort = depreciation.aggregate_depreciation(
        dep_base_items, 
        horizon, 
        model.tax_config.machinery_useful_life, 
        model.tax_config.building_useful_life,
        payments_per_year=pp_year
    )
    
    # Adjust Depreciation for Grants (Simplified: assume Grant matches currency logic or is mostly local)
    total_capex_reduction_grants = sum(g.amount for g in model.grants if g.is_capex_reduction)
    if total_capex_reduction_grants > 0:
        avg_life_periods = ((model.tax_config.machinery_useful_life + model.tax_config.building_useful_life) / 2) * pp_year
        period_dep_reduction = total_capex_reduction_grants / avg_life_periods
        dep_amort = np.maximum(0, dep_amort - period_dep_reduction)

    # 4. Finance (Loans)
    interest_expense = np.zeros(total_periods)
    principal_payment = np.zeros(total_periods)
    debt_drawdown = np.zeros(total_periods)
    
    for loan in model.loans:
        fx = get_fx_multiplier(loan.currency)
        
        # Calculate schedule in ORIGINAL currency, then convert flows? 
        # Or convert principal to Base and calc schedule? 
        # Better to calc in Original (for accurate interest on balance) then convert flows.
        
        schedule = finance.calculate_loan_schedule(
            loan.amount, 
            loan.interest_rate, 
            loan.term_years, 
            loan.payment_method, 
            loan.start_year, 
            horizon,
            loan.grace_period_years,
            payments_per_year=pp_year
        )
        
        # Add to totals (converted)
        interest_expense += schedule["interest"] * fx
        principal_payment += schedule["principal"] * fx
        debt_drawdown += schedule["drawdown"] * fx
        
    # Leasing
    leasing_interest = np.zeros(total_periods)
    leasing_principal = np.zeros(total_periods)
    leasing_downpayment = np.zeros(total_periods)
    
    for lease in model.leasings:
        # Lease asset usually follows item currency, but lease logic was simple.
        # Let's assume base for simplicity unless 'Leasing' model gets currency.
        # If it has amounts, we should probably assume Base or add currency.
        
        lease_life_periods = model.tax_config.machinery_useful_life * pp_year
        period_dep = lease.asset_value / lease_life_periods
        
        for i in range(min(total_periods, lease_life_periods)):
            dep_amort[i] += period_dep
            
        if lease.down_payment > 0:
            leasing_downpayment[0] += lease.down_payment
            
        financed_amt = lease.asset_value - lease.down_payment
        schedule = finance.calculate_loan_schedule(
            financed_amt,
            lease.annual_interest_rate,
            lease.term_years,
            "EqualPayment",
            1,
            horizon,
            0,
            payments_per_year=pp_year
        )
        leasing_interest += schedule["interest"]
        leasing_principal += schedule["principal"]
        
    total_interest = interest_expense + leasing_interest
    
    # ... Rest of logic (EBIT, Tax, NWC, CashFlow) uses these aggregated Base Currency arrays ...
    # NWC check: Revenue/COGS/OPEX are already in Base. So NWC calc is correct in Base.
    
    ebit = ebitda - dep_amort
    ebt = ebit - total_interest + grant_income_taxable
    
    # 5. Tax
    tax_payment = np.zeros(total_periods)
    accumulated_loss = 0.0
    for i in range(total_periods):
        ebt_curr = ebt[i]
        if ebt_curr < 0:
            tax_payment[i] = 0.0
            accumulated_loss += abs(ebt_curr)
        else:
            loss_usage = min(ebt_curr, accumulated_loss)
            taxable_base = ebt_curr - loss_usage
            tax_payment[i] = taxable_base * model.tax_config.corporate_tax_rate
            accumulated_loss -= loss_usage
            
    net_income = ebt - tax_payment
    
    # 6. NWC
    nwc_res = nwc.calculate_nwc(
        revenue, cogs, opex, 
        model.nwc_config.dso, model.nwc_config.dio, model.nwc_config.dpo,
        periods_per_year=pp_year,
        receivables_override=total_receivables
    )
    delta_nwc = nwc_res["delta_nwc"]
    
    # 7. Terminal Debt (Ending Balance needs FX conversion if displayed in Base)
    # We need to sum up balances of all loans converted.
    ending_debt = 0.0
    total_debt_balance_arr = np.zeros(total_periods)
    
    for loan in model.loans:
        fx = get_fx_multiplier(loan.currency)
        schedule = finance.calculate_loan_schedule(
            loan.amount, loan.interest_rate, loan.term_years, loan.payment_method, loan.start_year, horizon, loan.grace_period_years, payments_per_year=pp_year
        )
        total_debt_balance_arr += schedule["balance"] * fx
        
    ending_debt = total_debt_balance_arr[-1]
    terminal_payoff_amount = 0.0
    
    if ending_debt > 1.0:
        if model.terminal_debt_treatment == "payoff" and model.calculation_mode == "Levered":
            terminal_payoff_amount = ending_debt
            principal_payment[-1] += terminal_payoff_amount
            ending_debt = 0.0
            
    # 8. Cash Flows
    fcfe = (net_income + dep_amort - delta_nwc - total_capex_flow - leasing_downpayment + debt_drawdown - principal_payment - leasing_principal + grant_cash_inflow)
    nopat = (ebitda - dep_amort + grant_income_taxable) * (1 - model.tax_config.corporate_tax_rate)
    fcff = (nopat + dep_amort - delta_nwc - total_capex_flow - leasing_downpayment + grant_cash_inflow)
    
    if model.nwc_config.terminal_release:
        term_balance = nwc_res["nwc_balance"][-1] if len(nwc_res["nwc_balance"]) > 0 else 0
        fcfe[-1] += term_balance
        fcff[-1] += term_balance
        
    # ... Aggregation and Metrics reuse existing logic ...
    # We just need to define 'aggr_sum' etc again or assume they follow.
    # The snippet replacement will cut off the bottom part, so I need to include it or be careful.
    # The 'ReplacementContent' must be complete for the function or section.
    # I replaced basically the whole 'calculate_financials' body logic up to Metrics.
    # Let's verify what I'm replacing.
    
    # I am targeting lines 31-278 (Revenue loop to Cash Flow construction start).
    # I need to ensure the bottom part of calculate_financials (aggregation, metrics) is preserved or re-written.
    # I will rewrite the whole function to be safe and clean.
    
    # ... (Aggregation Code) ...
    def aggr_sum(arr):
        if pp_year == 1: return arr
        return arr.reshape(-1, pp_year).sum(axis=1)

    rev_a = aggr_sum(revenue)
    cogs_a = aggr_sum(cogs)
    opex_a = aggr_sum(opex)
    ebitda_a = aggr_sum(ebitda)
    dep_a = aggr_sum(dep_amort)
    grant_inc_a = aggr_sum(grant_income_taxable)
    interest_a = aggr_sum(total_interest)
    ebt_a = aggr_sum(ebt)
    tax_a = aggr_sum(tax_payment)
    ni_a = aggr_sum(net_income)
    nwc_delta_a = aggr_sum(delta_nwc)
    capex_a = aggr_sum(total_capex_flow)
    lease_down_a = aggr_sum(leasing_downpayment)
    draw_a = aggr_sum(debt_drawdown)
    princ_a = aggr_sum(principal_payment)
    lease_princ_a = aggr_sum(leasing_principal)
    grant_cash_a = aggr_sum(grant_cash_inflow)
    fcfe_a = aggr_sum(fcfe)
    fcff_a = aggr_sum(fcff)
    
    if model.calculation_mode == "Unlevered":
        target_stream = fcff_a
        initial_invest = 0.0
        discount_rate = model.discount_rate_unlevered
    else:
        target_stream = fcfe_a
        initial_invest = model.equity_contribution
        discount_rate = model.discount_rate_levered
        
    full_cash_flows = np.insert(target_stream, 0, -initial_invest)
    metrics = finance.calculate_metrics(full_cash_flows, discount_rate)
    
    cfads = ebitda_a - tax_a - nwc_delta_a - capex_a + grant_cash_a
    debt_service = princ_a + lease_princ_a + interest_a
    
    dscr_arr = np.zeros(len(years))
    valid_dscr_values = []
    
    for i in range(len(years)):
        if debt_service[i] > 0.01:
            val = cfads[i] / debt_service[i]
            dscr_arr[i] = val
            valid_dscr_values.append(val)
        else:
            dscr_arr[i] = 0.0
            
    metrics["dscr_min"] = min(valid_dscr_values) if valid_dscr_values else 0.0
    metrics["dscr_avg"] = np.mean(valid_dscr_values) if valid_dscr_values else 0.0
    
    metrics["ending_debt_balance"] = ending_debt
    metrics["terminal_debt_treatment"] = model.terminal_debt_treatment
    metrics["terminal_debt_payoff"] = terminal_payoff_amount
    
    # TV
    tv_value = 0.0
    tv_pv = 0.0
    if model.tv_config.method == "PerpetuityGrowth":
        last_fcf = target_stream[-1]
        g = model.tv_config.growth_rate
        r = discount_rate
        if r > g:
            tv_value = last_fcf * (1 + g) / (r - g)
    elif model.tv_config.method == "ExitMultiple":
        last_ebitda = ebitda_a[-1]
        ev_val = last_ebitda * model.tv_config.exit_multiple
        if model.calculation_mode == "Levered":
            tv_value = ev_val - ending_debt
        else:
            tv_value = ev_val
            
    if tv_value != 0:
        pv_factor = 1.0 / ((1 + discount_rate) ** horizon)
        tv_pv = tv_value * pv_factor
        
    metrics["tv_value"] = tv_value
    metrics["tv_pv"] = tv_pv
    metrics["tv_method"] = model.tv_config.method
    metrics["npv"] += tv_pv
    
    if tv_value != 0:
        kpi_flows = full_cash_flows.copy()
        kpi_flows[-1] += tv_value
        metrics["irr_tv"] = finance.calculate_metrics(kpi_flows, 0.0)["irr"]
        
    results = FinancialResults()
    results.years = years
    results.income_statement = pd.DataFrame({
        "Revenue": rev_a,
        "COGS": -cogs_a,
        "Gross Profit": rev_a - cogs_a,
        "OPEX": -opex_a,
        "EBITDA": ebitda_a,
        "Depreciation": -dep_a,
        "Grant Income": grant_inc_a,
        "EBIT": ebitda_a - dep_a + grant_inc_a,
        "Interest": -interest_a,
        "EBT": ebt_a,
        "Tax": -tax_a,
        "Net Income": ni_a
    }, index=years)
    
    results.cash_flow_statement = pd.DataFrame({
        "Net Income": ni_a,
        "Depreciation": dep_a,
        "Delta NWC": -nwc_delta_a,
        "CAPEX (w/ VAT)": -capex_a,
        "Lease Downpayment": -lease_down_a,
        "Debt Drawdown": draw_a,
        "Principal Repayment": -princ_a,
        "Lease Repayment": -lease_princ_a,
        "Grants (Cash)": grant_cash_a,
        "FCFE": fcfe_a,
        "FCFF": fcff_a
    }, index=years)
    
    results.kpi = metrics
    results.revenue_arr = rev_a
    results.ebitda_arr = ebitda_a
    results.free_cash_flow = target_stream
    results.dscr_arr = dscr_arr
    
    return results

    return calculate_financials(baseline)

def calculate_baseline(project: ProjectModel) -> FinancialResults:
    """
    Calculates financials for the 'Baseline' scenario (Existing Business).
    Logic: 
    1. Removes all Investment Cash Flows (CAPEX, Financing, Grants).
    2. Removes all Operating Items marked as 'is_incremental' (New Products, New OPEX, New Staff).
    
    This creates a true 'Before Investment' vs 'After Investment' EBITDA analysis.
    """
    # Create deep copy to avoid mutating original
    baseline = project.model_copy(deep=True)
    
    # 1. Reset Investment-related lists (Cash Flow Impact)
    baseline.capex_items = []
    baseline.loans = []
    baseline.leasings = []
    baseline.grants = []
    baseline.equity_contribution = 0.0
    
    # 2. Filter Operating Items (EBITDA Impact)
    # Only keep items that are NOT incremental (i.e. Base Business)
    kept_products = []
    for p in baseline.products:
        if not p.is_incremental:
            # Revert to Baseline Efficiency/Cost if defined
            if p.oee_percent_baseline is not None:
                p.oee_percent = p.oee_percent_baseline
            if p.scrap_rate_baseline is not None:
                p.scrap_rate = p.scrap_rate_baseline
            if p.unit_cost_baseline is not None:
                p.unit_cost = p.unit_cost_baseline
            kept_products.append(p)
            
    baseline.products = kept_products
    baseline.fixed_expenses = [e for e in baseline.fixed_expenses if not e.is_incremental]
    baseline.personnel = [p for p in baseline.personnel if not p.is_incremental]
    
    return calculate_financials(baseline)
