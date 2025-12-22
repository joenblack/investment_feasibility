import numpy as np
import numpy_financial as npf

def calculate_loan_schedule(amount: float, annual_rate: float, term_years: int, method: str, start_year: int, horizon_years: int, grace_period_years: int = 0, payments_per_year: int = 1):
    """
    Generates loan schedule: Interest, Principal, Balance per period.
    Returns dictionary with arrays of length `horizon_years * payments_per_year`.
    """
    total_periods = horizon_years * payments_per_year
    term_periods = term_years * payments_per_year
    grace_periods = grace_period_years * payments_per_year
    
    # Check start period
    # start_year is 1-based.
    # If payments_per_year=1, start_idx = start_year - 1.
    # If payments_per_year=12, start_idx = (start_year - 1) * 12. (Assuming start at beginning of year)
    # TODO: Pass start_period instead or stick to year? Sticking to Year for simplicity (start of year).
    start_idx = (start_year - 1) * payments_per_year
    
    per_period_rate = annual_rate / payments_per_year
    
    interest_payment = np.zeros(total_periods)
    principal_payment = np.zeros(total_periods)
    ending_balance = np.zeros(total_periods)
    debt_drawdown = np.zeros(total_periods)
    
    if start_idx < total_periods:
        debt_drawdown[start_idx] = amount
    
    current_balance = amount
    
    # Iterate through periods
    for i in range(start_idx, min(start_idx + term_periods + grace_periods, total_periods)):
        # Calculate Interest
        interest = current_balance * per_period_rate
        interest_payment[i] = interest
        
        principal = 0.0
        
        # Check if we are in grace period
        periods_elapsed = i - start_idx
        if periods_elapsed < grace_periods:
            principal = 0.0
        else:
            remaining_periods = term_periods - (periods_elapsed - grace_periods)
            
            if method == "EqualPrincipal":
                principal = amount / term_periods
                
            elif method == "EqualPayment": # Annuity
                if per_period_rate == 0:
                     principal = current_balance / remaining_periods if remaining_periods > 0 else current_balance
                else:
                    pmt = npf.pmt(per_period_rate, remaining_periods, -current_balance)
                    principal = pmt - interest
                
            elif method == "Bullet":
                if i == (start_idx + term_periods + grace_periods - 1):
                    principal = current_balance
                else:
                    principal = 0.0
        
        # Guard
        if principal > current_balance:
            principal = current_balance
            
        principal_payment[i] = principal
        current_balance -= principal
        ending_balance[i] = current_balance
        
    # Fill remaining balances if loop ended early (e.g. loan finished but horizon continues)
    # Actually current_balance persists if not paid off? No, loop covers term.
    # If term ends before horizon, current_balance is 0.
    
    return {
        "drawdown": debt_drawdown,
        "interest": interest_payment,
        "principal": principal_payment,
        "balance": ending_balance
    }

def calculate_metrics(cash_flows: np.ndarray, discount_rate: float):
    """
    Calculates NPV, IRR, Payback Period.
    Expects cash_flows to include Year 0 (CF0) as the first element.
    CF0 should typically be negative for an investment.
    """
    
    # NPV
    # npf.npv assumes the first element is at t=0, second at t=1, etc.
    try:
        npv = npf.npv(discount_rate, cash_flows)
    except:
        npv = 0.0
    
    # IRR
    try:
        irr = npf.irr(cash_flows)
        if np.isnan(irr) or np.isinf(irr):
            irr = 0.0
    except:
        irr = 0.0
        
    # Payback Period
    cumulative_cf = np.cumsum(cash_flows)
    payback = 0.0
    
    # Identify if there is ANY negative cumulative position (Investment phase)
    # If strictly positive from start, payback is 0.
    if np.min(cumulative_cf) < 0:
        # Find the first period where cumulative crosses from negative to positive
        # We start check from the point it BECOMES negative? 
        # Usually it starts negative or becomes negative at Y1.
        across_zero = False
        for i in range(len(cumulative_cf)):
            if cumulative_cf[i] >= 0:
                # If we were previously negative, this is the crossover
                # But we need to check if we were EVER negative before this point?
                # Simplest check: if cumulative_cf[i-1] was negative.
                if i > 0 and cumulative_cf[i-1] < 0:
                    prev_cum = cumulative_cf[i-1]
                    curr_flow = cash_flows[i]
                    fraction = -prev_cum / curr_flow if curr_flow != 0 else 0
                    payback = (i - 1) + fraction
                    across_zero = True
                    break
            elif i > 0 and cumulative_cf[i] < 0 and cumulative_cf[i-1] >= 0:
                # DIPPED into negative (Delayed investment).
                # Effectively, we reset payback start? 
                # Standard Payback metric usually assumes T=0 investment. 
                # If Invest is at Y1, Payback includes Y1.
                pass
        
        if not across_zero:
            # Check if it ends positive?
            if cumulative_cf[-1] < 0:
                payback = float(len(cash_flows)) # Never pays back
            else:
                pass # Logic above should cover crossing
    
    # ROI (Simple Return on Investment)
    # ROI = (Total Net Cash Flow) / Total Investment
    # We define Total Investment as the sum of all Negative Cash Flows (Absolute) 
    # OR simpler: if CF0 is the main one.
    # To be robust for T=1 investments:
    # Sum of all initial consecutive negative flows? or Just sum of all negative flows?
    # Commercial standard usually: Total Equity Injection or Total Capex.
    # Here cash_flows is Net Flow.
    # Let's sum absolute value of all negative flows as 'Total Investment' estimate.
    
    negative_flows = cash_flows[cash_flows < 0]
    total_investment = np.sum(np.abs(negative_flows))
    
    roi = 0.0
    if total_investment > 0:
        net_profit = np.sum(cash_flows) # Sum of all flows (Neg + Pos) = Net Value generated
        # ROI = Net Profit / Inv
        roi = (net_profit / total_investment) * 100.0
    
    return {
        "npv": npv,
        "irr": irr,
        "payback": payback,
        "roi": roi
    }
