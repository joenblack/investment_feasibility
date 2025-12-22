import streamlit as st

from ui.components import ensure_state, sidebar_nav, save_button, t, require_active_project, bootstrap
from core.model import Product, ExpenseItem, Personnel

bootstrap(require_project=True)
sidebar_nav()

st.title(t("rev_opex_title"))
tab1, tab2, tab3 = st.tabs([t("tab_products"), t("tab_fixed_exp"), t("tab_personnel")])

with tab1:
    st.subheader(t("tab_products"))
    
    # Convert Products to DataFrame-friendly format for editing
    # We want to edit all fields: Name, Vol, Price, Cost, Currency, Growth, Esc, Capacity, OEE, Scrap, AdvPay, Terms
    
    products = st.session_state.project.products
    
    # Prepare data for editor
    # We use a list of dicts.
    # Note: data_editor with Pydantic models directly might work if we dump to dict?
    # But we need column config.
    
    import pandas as pd
    
    # Include ID in the data so we can update existing items
    # SCALING: Convert 0.05 -> 5.0 for user friendly editing
    from core.quality import check_product_status
    
    # Include ID in the data so we can update existing items
    # SCALING: Convert 0.05 -> 5.0 for user friendly editing
    data = []
    
    # 3.1 & 3.4: status computation
    for p in products:
        d = p.model_dump()
        
        # Quality Check
        status_code, status_reason = check_product_status(p)
        d['status_display'] = status_code # We will display this
        d['status_reason'] = status_reason # Maybe show as tooltip if possible, or just knowing it.
        
        # Scale rates
        d['year_growth_rate'] = d.get('year_growth_rate', 0) * 100
        d['price_escalation_rate'] = d.get('price_escalation_rate', 0) * 100
        d['cost_escalation_rate'] = d.get('cost_escalation_rate', 0) * 100
        d['oee_percent'] = d.get('oee_percent', 0) * 100
        d['scrap_rate'] = d.get('scrap_rate', 0) * 100
        d['advance_payment_pct'] = d.get('advance_payment_pct', 0) * 100
        data.append(d)

    if not data:
        # Default empty frame needs columns, including status
        df = pd.DataFrame(columns=[
            "id", "status_display", "name", "initial_volume", "year_growth_rate", "unit_price", "unit_cost", "currency", 
            "price_escalation_rate", "cost_escalation_rate", 
            "production_capacity_per_year", "oee_percent", "scrap_rate",
            "advance_payment_pct", "payment_terms_days", "status_reason"
        ])
    else:
        df = pd.DataFrame(data)
        
    # 3.2 Required Fields Hint
    st.info("💡 **A Product is Included only if:** Capacity > 0, OEE% > 0, Volume > 0, Price > 0, Scrap < 100%. Check the **Status** column.")

    # Column Config
    cc = {
        "status_display": st.column_config.TextColumn("Status", disabled=True, width="medium", help="✅ Included / ⛔ Excluded"),
        "status_reason": st.column_config.TextColumn("Issue", disabled=True, width="large"),
        "name": st.column_config.TextColumn(t("col_prod_name"), required=True),
        "initial_volume": st.column_config.NumberColumn(t("col_vol"), format="%.0f", min_value=0),
        "year_growth_rate": st.column_config.NumberColumn(f"{t('col_vol_growth')} (%)", format="%.2f"),
        "unit_price": st.column_config.NumberColumn(t("col_price"), format="%.2f", min_value=0),
        "unit_cost": st.column_config.NumberColumn(t("col_cost"), format="%.2f", min_value=0),
        "currency": st.column_config.SelectboxColumn(t("col_curr"), options=["TRY", "USD", "EUR"], width="small", required=True),
        "price_escalation_rate": st.column_config.NumberColumn(f"{t('col_price_esc')} (%)", format="%.2f"),
        "cost_escalation_rate": st.column_config.NumberColumn(f"{t('col_cost_esc')} (%)", format="%.2f"),
        "production_capacity_per_year": st.column_config.NumberColumn(t("col_capacity"), format="%.0f"),
        "oee_percent": st.column_config.NumberColumn(f"{t('col_oee')} (%)", format="%.2f", min_value=0.0, max_value=100.0),
        "scrap_rate": st.column_config.NumberColumn(f"{t('col_scrap')} (%)", format="%.2f", min_value=0.0, max_value=50.0),
        "advance_payment_pct": st.column_config.NumberColumn(f"{t('col_adv_pay')} (%)", format="%.2f", min_value=0.0, max_value=100.0),
        "payment_terms_days": st.column_config.NumberColumn(t("col_terms"), min_value=0, max_value=365)
    }
    
    edited_df = st.data_editor(
        df,
        key="prod_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config=cc,
        column_order=[
            "status_display", "status_reason", "name", "initial_volume", "unit_price", "unit_cost", "currency", 
            "year_growth_rate", "price_escalation_rate", "cost_escalation_rate",
            "production_capacity_per_year", "oee_percent", "scrap_rate",
            "advance_payment_pct", "payment_terms_days"
        ]
    )
    
    # Auto-Save Logic
    # ... (Logic continues) ...
    
    # Helper to convert DF row to clean dict
    def row_to_clean_dict(row):
        p_data = row.to_dict()
        clean_data = {}
        
        # 1. ID Handling
        row_id = p_data.get("id")
        if row_id is not None and not pd.isna(row_id) and str(row_id).strip() != "":
            clean_data["id"] = str(row_id)
        
        # 2. Field Sanitization
        for k, v in p_data.items():
            if k == "id": continue 
            
            if isinstance(v, list) and len(v) > 0: v = v[0]
            elif isinstance(v, list) and len(v) == 0: v = None
            
            if pd.isna(v) or v is None:
                if k == "name": clean_data[k] = "New Product"
                elif k == "currency": clean_data[k] = "TRY"
                elif k == "payment_terms_days": clean_data[k] = 0
                else: clean_data[k] = 0.0
            else:
                # SCALING BACK: Convert 5.0 -> 0.05
                if k in ['year_growth_rate', 'price_escalation_rate', 'cost_escalation_rate', 'oee_percent', 'scrap_rate', 'advance_payment_pct']:
                    clean_data[k] = float(v) / 100.0
                else:
                    clean_data[k] = v
        return clean_data

    # Check for changes
    # We reconstruct the list from edited_df
    candidate_products = []
    errors = []
    
    for index, row in edited_df.iterrows():
        try:
            clean_data = row_to_clean_dict(row)
            # Validate with Pydantic (using Model from core to ensure class match)
            # We store as dict in session state to avoid mismatch, but validation is useful.
            # actually we can just store the dict if validation passes.
            # But we want to ensure it IS valid.
            # Ensure we store Objects, not dicts
            prod = Product(**clean_data) 
            candidate_products.append(prod)
        except Exception as e:
            errors.append(f"Row {index+1}: {str(e)}")

    if errors:
        for err in errors:
            st.error(err)
    else:
        # Check equality to avoid redundant updates/reruns
        # Converting candidates to list of dicts for comparison
        candidate_dumps = [p.model_dump() for p in candidate_products]
        current_products_dump = [p.model_dump() for p in st.session_state.project.products]
        
        if candidate_dumps != current_products_dump:
            st.session_state.project.products = candidate_products
            
            # Persist to DB
            from core.db import save_project
            import time
            user = st.session_state.get('user', {'username': 'autosave'})
            save_project(st.session_state.project, user=user['username'])
            
            # Toast Throttling (3 seconds)
            now = time.time()
            last_toast = st.session_state.get('last_save_toast_ts', 0)
            
            if now - last_toast > 3.0:
                 st.toast(f"{t('save_products')} (Auto-DB) OK! ({len(candidate_products)})", icon="💾")
                 st.session_state['last_save_toast_ts'] = now
            
            # We do NOT rerun here to avoid interrupting the user while typing. 
            # The state is updated. On next interaction, it persists.



with tab2:
    st.subheader(t("tab_fixed_exp"))
    with st.expander(t("add_expense")):
        c1, c2, c3 = st.columns(3)
        e_name = c1.text_input(t("expense_name"))
        e_cat = c2.text_input(t("category"), "General")
        e_amount = c3.number_input(t("annual_amount"), 0.0)
        e_growth = st.number_input(t("growth_rate"), 0.0)
        
        if st.button(t("add_expense")):
            exp = ExpenseItem(name=e_name, category=e_cat, amount_per_year=e_amount, growth_rate=e_growth/100.0)
            st.session_state.project.fixed_expenses.append(exp)
            st.rerun()
            
    for i, e in enumerate(st.session_state.project.fixed_expenses):
        st.write(f"{e.name} ({e.amount_per_year}/yr)")
        if st.button(t("remove") + f" {e.name}", key=f"del_e_{i}"):
            st.session_state.project.fixed_expenses.pop(i)
            st.rerun()

with tab3:
    st.subheader(t("tab_personnel"))
    with st.expander(t("add_role")):
        c1, c2 = st.columns(2)
        role = c1.text_input(t("role"))
        count = c2.number_input(t("count"), 1, 1000, 1)
        
        c3, c4 = st.columns(2)
        salary = c3.number_input(t("monthly_salary"), 0.0)
        sgk = c4.number_input(t("employer_tax"), value=22.5) # Example
        
        c5, c6 = st.columns(2)
        start_y = c5.number_input(t("start_year"), 1, st.session_state.project.horizon_years, 1)
        raise_r = c6.number_input(t("annual_raise"), 0.0)
        
        if st.button(t("add_personnel")):
            pers = Personnel(
                role=role, count=count, monthly_gross_salary=salary,
                sgk_tax_rate=sgk/100.0, start_year=start_y, yearly_raise_rate=raise_r/100.0
            )
            st.session_state.project.personnel.append(pers)
            st.rerun()

    for i, p in enumerate(st.session_state.project.personnel):
        st.write(f"{p.count}x {p.role} | {p.monthly_gross_salary}/m")
        if st.button(t("remove") + f" {p.role}", key=f"del_pers_{i}"):
            st.session_state.project.personnel.pop(i)
            st.rerun()

st.markdown("---")
save_button()
