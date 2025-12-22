import json
import pandas as pd
from core.model import ProjectModel
from core.engine import FinancialResults
from io import BytesIO

def export_to_json(project: ProjectModel) -> str:
    """Exports model to JSON string."""
    try:
        return project.model_dump_json(indent=4)
    except AttributeError:
        # Fallback for Pydantic v1
        return project.json(indent=4)

def import_from_json(json_str: str) -> ProjectModel:
    """Imports model from JSON string."""
    try:
        return ProjectModel.model_validate_json(json_str)
    except AttributeError:
        # Fallback for Pydantic v1
        return ProjectModel.parse_raw(json_str)

from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def export_to_excel(project: ProjectModel, results: FinancialResults) -> bytes:
    """Exports model inputs and result tables to a styled Excel file."""
    buffer = BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # --- Sheet 1: Assumptions ---
        ws_assump = workbook.add_worksheet("Assumptions")
        # Formats
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#2c3e50'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#ecf0f1', 'border': 1})
        num_fmt = workbook.add_format({'num_format': '#,##0.00'})
        bold_fmt = workbook.add_format({'bold': True})
        
        ws_assump.write(0, 0, f"Feasibility Study: {project.name}", title_fmt)
        ws_assump.write(1, 0, f"Date: {project.created_at.strftime('%Y-%m-%d')}", bold_fmt)
        ws_assump.write(2, 0, f"Version: {project.version} | Mode: {project.calculation_mode.upper()}", bold_fmt)
        
        # General Params
        ws_assump.write(4, 0, "General Parameters", bold_fmt)
        ws_assump.write(5, 0, "Horizon (Years)", bold_fmt); ws_assump.write(5, 1, project.horizon_years)
        ws_assump.write(6, 0, "Currency", bold_fmt); ws_assump.write(6, 1, project.currency_base)
        ws_assump.write(7, 0, "Tax Rate", bold_fmt); ws_assump.write(7, 1, project.tax_config.corporate_tax_rate)
        ws_assump.write(8, 0, "Risk Free / Discount", bold_fmt); ws_assump.write(8, 1, project.discount_rate_unlevered)
        
        # Investment Summary
        ws_assump.write(10, 0, "Investment Summary", bold_fmt)
        total_capex = sum(c.amount for c in project.capex_items)
        ws_assump.write(11, 0, "Total CAPEX", bold_fmt); ws_assump.write(11, 1, total_capex, workbook.add_format({'num_format': '#,##0'}))
        
        # Products
        ws_assump.write(13, 0, "Revenue Drivers", bold_fmt)
        row = 14
        for p in project.products:
            ws_assump.write(row, 0, p.name)
            ws_assump.write(row, 1, f"Price: {p.unit_price} / Vol: {p.initial_volume}")
            row += 1
            
        ws_assump.set_column(0, 0, 30)
        ws_assump.set_column(1, 1, 40)

        # --- Sheet 2: Summary ---
        
        # Styling formats for xlsxwriter
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Helper to style a worksheet for xlsxwriter
        def style_sheet_xlsxwriter(sheet_name):
            ws = writer.sheets[sheet_name]
            
            # Simple approach: Set column width globally for first 30 columns
            # xlsxwriter worksheet objects don't expose data dimensions easily without tracking
            ws.set_column(0, 30, 20) # Set columns A through AE to width 20
            
            # Header format check?
            # Pandas writes header with bold by default.
            pass

        # 1. Summary Sheet (Transposed)
        summary_data = {
            "Internal ID": project.id,
            "Project Name": project.name,
            "Horizon": f"{project.horizon_years} Years",
            "Currency": project.currency_base,
            "Mode": project.calculation_mode,
            "NPV": results.kpi.get("npv", 0),
            "IRR": results.kpi.get("irr", 0),
            "ROI (%)": results.kpi.get("roi", 0),
            "Payback (Yrs)": results.kpi.get("payback", 0),
            "Ending Debt Balance": results.kpi.get("ending_debt_balance", 0),
            "Terminal Treatment": results.kpi.get("terminal_debt_treatment", ""),
            "Terminal Debt Payoff": results.kpi.get("terminal_debt_payoff", 0)
        }
        df_summary = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        style_sheet_xlsxwriter('Summary')
        
        # 2. Financial Statements
        results.income_statement.to_excel(writer, sheet_name='Income Statement')
        style_sheet_xlsxwriter('Income Statement')
        
        results.cash_flow_statement.to_excel(writer, sheet_name='Cash Flow')
        style_sheet_xlsxwriter('Cash Flow')
        
        # 3. CAPEX
        if project.capex_items:
            capex_df = pd.DataFrame([item.dict() for item in project.capex_items])
            capex_df.to_excel(writer, sheet_name='CAPEX Details', index=False)
            style_sheet_xlsxwriter('CAPEX Details')
            
        # 4. Loans
        if project.loans:
            loans_df = pd.DataFrame([item.dict() for item in project.loans])
            loans_df.to_excel(writer, sheet_name='Financing Details', index=False)
            style_sheet_xlsxwriter('Financing Details')
            
    return buffer.getvalue()
