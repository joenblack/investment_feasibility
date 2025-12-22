from datetime import datetime
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid

# --- Enums and Types ---
CurrencyType = Literal["TRY", "USD", "EUR"]
GranularityType = Literal["Year", "Month"]
DepreciationMethod = Literal["StraightLine", "Accelerated"]
LoanPaymentMethod = Literal["EqualPrincipal", "EqualPayment", "Bullet"]
ScenarioType = Literal["Base", "Best", "Worst", "Custom"]

# --- Sub-Models ---

class CAPEXItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Item"
    category: str = "Machinery" # Construction, Infrastructure, Software, etc.
    amount: float = 0.0
    currency: CurrencyType = "TRY"
    year: int = 1  # Investment year (relative to start)
    month: int = 1 # Investment month (if monthly granularity)
    vat_rate: float = 0.20
    is_imported: bool = False
    customs_duty_rate: float = 0.0

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Product A"
    unit_price: float = 100.0
    unit_cost: float = 60.0 # Variable cost per unit
    currency: CurrencyType = "TRY"
    initial_volume: float = 1000.0
    year_growth_rate: float = 0.05 # 5% growth
    price_escalation_rate: float = 0.0 # Inflation on price
    cost_escalation_rate: float = 0.0 # Inflation on cost
    
    # Production / Efficiency
    production_capacity_per_year: float = 10000.0 # Max theoretical
    oee_percent: float = 0.85 # Efficiency
    scrap_rate: float = 0.02 # Scrap % (Cost incurred, no revenue)
    
    # Commercial / Payment
    # Cash Flow Timing
    advance_payment_pct: float = 0.0 # 0.20 = 20% advance
    payment_terms_days: Optional[int] = None # If None, use Global DSO. If set, override.
    # Note: Global DSO is used in NWC. If we set this, engine should use it instead of global?
    # Or keep simple: Global NWC handles Receivables. This 'advance' allows negative NWC (pre-payment).

class ExpenseItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Rent"
    amount_per_year: float = 0.0
    currency: CurrencyType = "TRY"
    growth_rate: float = 0.0
    category: str = "General" # Personnel, Rent, Energy, etc.

class Personnel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "Manager"
    count: int = 1
    monthly_gross_salary: float = 0.0
    currency: CurrencyType = "TRY"
    yearly_raise_rate: float = 0.0
    sgk_tax_rate: float = 0.22 # Employer burden
    start_year: int = 1

class Loan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Bank Loan 1"
    amount: float = 0.0
    currency: CurrencyType = "TRY"
    interest_rate: float = 0.25 # Annual
    term_years: int = 5
    grace_period_years: int = 0
    payment_method: LoanPaymentMethod = "EqualPayment"
    start_year: int = 1

class Leasing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Leasing 1"
    asset_value: float = 0.0
    annual_interest_rate: float = 0.10
    term_years: int = 4
    down_payment: float = 0.0

class Grant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Incentive A"
    amount: float = 0.0
    is_capex_reduction: bool = True # If true, reduces depreciable base. If false, treated as income.
    year: int = 1

class TaxConfig(BaseModel):
    corporate_tax_rate: float = 0.25
    loss_carryforward_limit_years: int = 5
    machinery_useful_life: int = 10
    building_useful_life: int = 25
    depreciation_method: DepreciationMethod = "StraightLine"
    vat_exemption: bool = False

class WorkingCapitalConfig(BaseModel):
    dso: float = 60.0 # Days Sales Outstanding
    dio: float = 45.0 # Days Inventory Outstanding
    dpo: float = 30.0 # Days Payable Outstanding
    terminal_release: bool = True # Release NWC at end of project

DistributionType = Literal["Normal", "Triangular", "Uniform"]

class DistributionConfig(BaseModel):
    # "Normal", "Triangular", "Uniform", "Lognormal"
    dist_type: str = "Normal"
    
    # Normal / Lognormal
    mean_pct: float = 0.0 # Shift from base (e.g. 0.0 means centered on base)
    std_dev_pct: float = 0.10 # 10% standard deviation
    
    # Triangular
    min_pct: float = -0.10
    mode_pct: float = 0.0
    max_pct: float = 0.10
    
    model_config = ConfigDict(extra="ignore")

class RiskParams(BaseModel):
    monte_carlo_iterations: int = 1000
    random_seed: int = 42
    
    # Variable Distributions
    var_configs: Dict[str, DistributionConfig] = Field(default_factory=dict)
    
    # Correlation Matrix (Simple pairwise for key variables)
    # Stored as keys "Var1-Var2": correlation_coefficient
    correlation_base: Dict[str, float] = Field(default_factory=dict)
    
    def get_config(self, var_name: str) -> DistributionConfig:
        if var_name not in self.var_configs:
            self.var_configs[var_name] = DistributionConfig()
        return self.var_configs[var_name]
    
    def set_correlation(self, var1: str, var2: str, corr: float):
        # Sort to ensure consistent key
        key = "-".join(sorted([var1, var2]))
        self.correlation_base[key] = corr
        
    def get_correlation(self, var1: str, var2: str) -> float:
        if var1 == var2: return 1.0
        key = "-".join(sorted([var1, var2]))
        return self.correlation_base.get(key, 0.0)
    
    model_config = ConfigDict(extra="ignore")

TerminalValueMethod = Literal["None", "PerpetuityGrowth", "ExitMultiple"]

class TerminalValueConfig(BaseModel):
    method: TerminalValueMethod = "None"
    growth_rate: float = 0.02 # 2%
    exit_multiple: float = 7.0 # 7x EBITDA

# --- Main Model ---

class ProjectModel(BaseModel):
    # Metadata
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Feasibility Project"
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0" # Functional version (Business)
    schema_version: int = 1 # Data structure version (Technical)
    description: str = ""

    # Settings
    currency_base: CurrencyType = "TRY"
    # Exchange Rates (Base Year 1)
    # Map: "USD": 35.0, "EUR": 38.0
    exchange_rates: Dict[str, float] = Field(default_factory=lambda: {"USD": 35.0, "EUR": 38.0, "TRY": 1.0})
    
    granularity: GranularityType = "Year"
    horizon_years: int = 10
    start_year: int = 2024
    inflation_rate: float = 0.0

    # Modules
    capex_items: List[CAPEXItem] = []
    products: List[Product] = []
    fixed_expenses: List[ExpenseItem] = []
    personnel: List[Personnel] = []
    
    # Financials
    equity_contribution: float = 0.0 # Initial equity injection (if manually specified)
    loans: List[Loan] = []
    leasings: List[Leasing] = []
    grants: List[Grant] = []
    
    tax_config: TaxConfig = TaxConfig()
    nwc_config: WorkingCapitalConfig = WorkingCapitalConfig()
    risk_config: RiskParams = RiskParams()
    tv_config: TerminalValueConfig = TerminalValueConfig()

    # Calculation Settings
    discount_rate_unlevered: float = 0.20 # WACC
    discount_rate_levered: float = 0.25 # Cost of Equity
    calculation_mode: Literal["Unlevered", "Levered"] = "Unlevered"
    terminal_debt_treatment: Literal["payoff", "refinance"] = "payoff"

    @field_validator('horizon_years')
    @classmethod
    def validate_horizon(cls, v):
        if v < 3 or v > 30:
            raise ValueError('Horizon must be between 3 and 30 years')
        return v
    
    # The provided 'get_config' method was not syntactically correct and
    # its placement would overwrite the 'validate_horizon' method.
    # It has been omitted to maintain a syntactically correct file.
    # If this method is intended, please provide its correct context and definition.
    
    model_config = ConfigDict(validate_assignment=True)
