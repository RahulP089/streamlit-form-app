import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
import plotly.express as px

# -------------------- USER LOGIN --------------------
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"

# --- Tab Names for Equipment Workbook ---
HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"

# -------------------- UTILITIES --------------------
def parse_date(s):
    """Safely parses a string into a date object."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    try:
        return datetime.strptime(str(s).split(' ')[0], "%d %B %Y").date()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(s).split(' ')[0], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

def badge_expiry(d, expiry_days=10):
    """Creates a visual badge for expiry dates."""
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%d %B %Y')
    if d < today:
        return f"🚨 Expired ({date_str})"
    elif d <= today + timedelta(days=expiry_days):
        return f"⚠️ Expires Soon ({date_str})"
    else:
        return f"✅ Valid ({date_str})"

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600) # Cache for 10 minutes
def get_sheets():
    """Connects to Google Sheets and returns worksheet objects."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    # --- Helper function to get or create a worksheet ---
    def get_or_create(workbook, ws_title, headers=None):
        try:
            ws = workbook.worksheet(ws_title)
            # Check if sheet is empty and add headers if needed
            if ws.row_count == 0 and headers:
                 ws.append_row(headers)
        except gspread.exceptions.WorksheetNotFound:
            ws = workbook.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws
    
    # --- Define Headers for ALL sheets to prevent KeyErrors ---
    obs_headers = [
        "DATE", "WELL NO", "AREA", "OBSERVER NAME", "OBSERVATION DETAILS",
        "RECOMMENDED SOLUTION/ACTION TAKEN", "SUPERVISOR NAME", "DISCIPLINE",
        "CATEGORY", "CLASSIFICATION", "STATUS"
    ]
    permit_headers = [
        "DATE", "PERMIT NO", "TYPE OF PERMIT", "ACTIVITY", "PERMIT RECEIVER", "PERMIT ISSUER"
    ]
    heavy_equip_headers = [
        "Equipment type", "Make", "Palte No.", "Asset code", "Owner", "T.P inspection date", "T.P Expiry date",
        "Insurance expiry date", "Operator Name", "Iqama NO", "T.P Card type", "T.P Card Number",
        "T.P Card expiry date", "Q.R code", "PWAS status", "F.E TP expiry",
        "FA box Status", "Documents"
    ]
    heavy_vehicle_headers = [
        "Vehicle Type", "Make", "Plate No", "Asset Code", "Owner", "MVPI Expiry date", "Insurance Expiry",
        "Driver Name", "Iqama No", "Licence Expiry", "Q.R code", "F.A Box",
        "Fire Extinguisher T.P Expiry", "PWAS Status", "Seat belt damaged", "Tyre Condition",
        "Suspension Systems", "Remarks"
    ]

    # --- Open workbooks ---
    obs_wb = client.open_by_url(OBSERVATION_URL)
    permit_wb = client.open_by_url(PERMIT_URL)
    equip_wb = client.open_by_url(EQUIPMENT_URL)

    # --- Get or create all worksheets securely ---
    obs_sheet = get_or_create(obs_wb, "Sheet1", headers=obs_headers)
    permit_sheet = get_or_create(permit_wb, "Sheet1", headers=permit_headers)
    heavy_equip_sheet = get_or_create(equip_wb, HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(equip_wb, HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)

    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet

# -------------------- LOGIN PAGE --------------------
def login():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px; margin: 4rem auto; padding: 2rem;
        border-radius: 12px; background-color: white;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .login-title {
        font-size: 32px; font-weight:700; color:#2c3e50;
        margin-bottom:1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🛡️ Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")
    st.markdown("</div>", unsafe_allow_html=True)

    if login_btn:
        user = USER_CREDENTIALS.get(username)
        if user and user["password"] == password:
            st.session_state.update(logged_in=True, username=username, role=user["role"])
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# -------------------- SIDEBAR --------------------
def sidebar():
    with st.sidebar:
        st.title("🧭 Navigation")
        menu_options = [
            "🏠 Home", "📝 Observation Form", "🛠️ Permit Form",
            "🏗️ Equipments", "📊 Dashboard", "🚪 Logout"
        ]
        menu = st.selectbox("Go to", menu_options, key="main_menu")

        if menu == "🏗️ Equipments":
            sub_menu = st.selectbox("Select Equipment", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"], key="equip_sub")
            return sub_menu
        return menu

# -------------------- FORMS --------------------
def show_equipment_form(sheet):
    st.header("🚜 Heavy Equipment Entry Form")
    EQUIPMENT_LIST = [
        "Excavator", "Backhoe Loader", "Wheel Loader", "Bulldozer", "Motor Grader", "Compactor / Roller",
        "Crane", "Forklift", "Boom Truck", "Side Boom", "Hydraulic Drill Unit", "Telehandler", "Skid Loader"
    ]
    with st.form("equipment_form", clear_on_submit=True):
        cols = st.columns(2)
        equipment_type = cols[0].selectbox("Equipment type", EQUIPMENT_LIST)
        make = cols[1].text_input("Make")
        plate_no = cols[0].text_input("Palte No.")
        asset_code = cols[1].text_input("Asset code")
        owner = cols[0].text_input("Owner")
        operator_name = cols[1].text_input("Operator Name")
        iqama_no = cols[0].text_input("Iqama NO")

        st.subheader("Expiry Dates")
        cols_dates = st.columns(2)
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime("%d %B %Y")
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime("%d %B %Y")
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime("%d %B %Y")
        fe_tp_expiry = cols_dates[1].date_input("F.E TP expiry").strftime("%d %B %Y")
        tp_card_expiry = cols_dates[0].date_input("T.P Card expiry date").strftime("%d %B %Y")

        st.subheader("T.P Card & Status")
        cols_status = st.columns(2)
        tp_card_type = cols_status[0].selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_number = cols_status[1].text_input("T.P Card Number")
        pwas_status = cols_status[0].selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        fa_box_status = cols_status[1].text_input("FA box Status")
        qr_code = cols_status[0].text_input("Q.R code")
        documents = cols_status[1].text_input("Documents")

        if st.form_submit_button("Submit", use_container_width=True):
            data = [
                equipment_type, make, plate_no, asset_code, owner, tp_insp_date, tp_expiry,
                insurance_expiry, operator_name, iqama_no, tp_card_type, tp_card_number,
                tp_card_expiry, qr_code, pwas_status, fe_tp_expiry, fa_box_status, documents
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    well_numbers = ["2334", "2556", "1858", "2433", "2553", "2447"]
    with st.form("obs_form", clear_on_submit=True):
        data = {
            "DATE": st.date_input("Date").strftime("%d %B %Y"),
            "WELL NO": st.selectbox("Well No", well_numbers),
            "AREA": st.text_input("Area"),
            "OBSERVER NAME": st.text_input("Observer Name"),
            "OBSERVATION DETAILS": st.text_area("Observation Details"),
            "RECOMMENDED SOLUTION/ACTION TAKEN": st.text_area("Recommended Action"),
            "SUPERVISOR NAME": st.text_input("Supervisor Name"),
            "DISCIPLINE": st.text_input("Discipline"),
            "CATEGORY": st.text_input("Category"),
            "CLASSIFICATION": st.selectbox("Classification", ["POSITIVE", "UNSAFE CONDITION", "UNSAFE ACT"]),
            "STATUS": st.selectbox("Status", ["Open", "Closed"])
        }
        if st.form_submit_button("Submit"):
            try:
                # IMPORTANT: The order of values must match the headers defined in get_sheets()
                sheet.append_row(list(data.values()))
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    with st.form("permit_form", clear_on_submit=True):
        data = {
            "DATE": st.date_input("Date").strftime("%d %B %Y"),
            "PERMIT NO": st.text_input("Permit No"),
            "TYPE OF PERMIT": st.text_input("Type of Permit"),
            "ACTIVITY": st.text_area("Activity"),
            "PERMIT RECEIVER": st.text_input("Permit Receiver"),
            "PERMIT ISSUER": st.text_input("Permit Issuer"),
        }
        if st.form_submit_button("Submit"):
            try:
                # IMPORTANT: The order of values must match the headers defined in get_sheets()
                sheet.append_row(list(data.values()))
                st.success("✅ Permit submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")
    VEHICLE_LIST = ["Bus", "Dump Truck", "Low Bed", "Trailer", "Water Tanker", "Mini Bus", "Flat Truck"]
    with st.form("vehicle_form", clear_on_submit=True):
        data = {
            "Vehicle Type": st.selectbox("Vehicle Type", VEHICLE_LIST),
            "Make": st.text_input("Make"),
            "Plate No": st.text_input("Plate No"),
            "Asset Code": st.text_input("Asset Code"),
            "Owner": st.text_input("Owner"),
            "MVPI Expiry date": st.date_input("MVPI Expiry date").strftime("%d %B %Y"),
            "Insurance Expiry": st.date_input("Insurance Expiry").strftime("%d %B %Y"),
            "Driver Name": st.text_input("Driver Name"),
            "Iqama No": st.text_input("Iqama No"),
            "Licence Expiry": st.date_input("Licence Expiry").strftime("%d %B %Y"),
            "Q.R code": st.text_input("Q.R code"),
            "F.A Box": st.selectbox("F.A Box", ["Available", "Not Available", "Expired", "Inadequate Medicine"]),
            "Fire Extinguisher T.P Expiry": st.date_input("Fire Extinguisher T.P Expiry").strftime("%d %B %Y"),
            "PWAS Status": st.selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"]),
            "Seat belt damaged": st.selectbox("Seat belt damaged", ["Yes", "No", "N/A"]),
            "Tyre Condition": st.selectbox("Tyre Condition", ["Good", "Worn Out", "Damaged", "Needs Replacement", "N/A"]),
            "Suspension Systems": st.selectbox("Suspension Systems", ["Good", "Faulty", "Needs Repair", "Damaged", "N/A"]),
            "Remarks": st.text_input("Remarks")
        }
        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Heavy Vehicle submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- ADVANCED DASHBOARD (UPDATED) --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])
    
    # --- NEW: OBSERVATION DASHBOARD TAB ---
    with tab_obs:
        st.subheader("Observation Analytics")
        try:
            df_obs = pd.DataFrame(obs_sheet.get_all_records())
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load observation data from Google Sheets: {e}")
            df_obs = pd.DataFrame() # Create empty dataframe to avoid further errors
        
        if df_obs.empty:
            st.info("No observation data available to display.")
        else:
            total_obs = len(df_obs)
            open_status_count = df_obs[df_obs['STATUS'] == 'Open'].shape[0] if 'STATUS' in df_obs.columns else 0
            
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Total Observations", total_obs)
            kpi2.metric("Open Observations", open_status_count)
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            
            with c1:
                if 'CLASSIFICATION' in df_obs.columns and not df_obs['CLASSIFICATION'].empty:
                    fig = px.pie(df_obs, names='CLASSIFICATION', title='Observation Classification', hole=0.3)
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                if 'STATUS' in df_obs.columns and not df_obs['STATUS'].empty:
                    fig2 = px.pie(df_obs, names='STATUS', title='Observation Status')
                    st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            st.dataframe(df_obs, use_container_width=True)


    # --- FIXED: PERMIT DASHBOARD TAB ---
    with tab_permit:
        st.subheader("Permit Log Analytics")
        try:
            df_permit = pd.DataFrame(permit_sheet.get_all_records())
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load permit data from Google Sheets: {e}")
            df_permit = pd.DataFrame() # Create empty dataframe to avoid further errors

        if df_permit.empty:
            st.info("No permit data available to display.")
        else:
            # This check is crucial for preventing the KeyError
            if 'DATE' not in df_permit.columns:
                st.error("Permit sheet is missing the 'DATE' column. Please check the Google Sheet.")
            else:
                df_permit['DATE'] = df_permit['DATE'].apply(parse_date)
                df_permit.dropna(subset=['DATE'], inplace=True)
                df_permit['DATE'] = pd.to_datetime(df_permit['DATE'])

                st.markdown("##### Key Metrics")
                total_permits = len(df_permit)
                permits_today = df_permit[df_permit['DATE'].dt.date == date.today()].shape[0]
                common_permit_type = df_permit['TYPE OF PERMIT'].mode()[0] if 'TYPE OF PERMIT' in df_permit.columns and not df_permit['TYPE OF PERMIT'].empty else "N/A"

                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric(label="Total Permits Issued", value=total_permits)
                kpi2.metric(label="Permits Issued Today", value=permits_today)
                kpi3.metric(label="Most Common Permit", value=common_permit_type)

                st.markdown("---")
                st.markdown("##### Visual Insights")
                
                permits_by_day = df_permit.groupby(df_permit['DATE'].dt.date).size().reset_index(name='count')
                fig_daily = px.bar(permits_by_day, x='DATE', y='count', title='Permits Issued Per Day', labels={'count': 'Number of Permits', 'DATE': 'Date'}, text_auto=True)
                st.plotly_chart(fig_daily, use_container_width=True)

                c1, c2 = st.columns(2)
                with c1:
                     if 'TYPE OF PERMIT' in df_permit.columns and not df_permit['TYPE OF PERMIT'].empty:
                         fig_type = px.pie(df_permit, names='TYPE OF PERMIT', title='Distribution of Permit Types', hole=0.3)
                         st.plotly_chart(fig_type, use_container_width=True)
                with c2:
                    if 'PERMIT ISSUER' in df_permit.columns and not df_permit['PERMIT ISSUER'].empty:
                        issuer_counts = df_permit['PERMIT ISSUER'].value_counts().nlargest(10).reset_index()
                        fig_issuer = px.bar(issuer_counts, x='count', y='PERMIT ISSUER', orientation='h', title='Top 10 Permit Issuers', labels={'count': 'Number of Permits', 'PERMIT ISSUER': 'Issuer Name'}, text_auto=True)
                        fig_issuer.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_issuer, use_container_width=True)

                st.markdown("---")
                st.markdown("##### Full Permit Log")
                st.dataframe(df_permit, use_container_width=True)

    with tab_eqp:
        st.subheader("Heavy Equipment Analytics")
        try:
            df_equip = pd.DataFrame(heavy_equip_sheet.get_all_records())
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load data from Google Sheets: {e}")
            df_equip = pd.DataFrame()

        if df_equip.empty:
            st.info("No Heavy Equipment data available to display.")
        else:
            date_cols = ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]
            for col in date_cols:
                 if col in df_equip.columns:
                     df_equip[col] = df_equip[col].apply(parse_date)

            today = date.today()
            ten_days = today + timedelta(days=10)

            st.subheader("🚨 T.P Card Expiry Alerts")
            tp_card_col = "T.P Card expiry date"
            tp_required_cols = ["Equipment type", "Palte No.", "Owner", tp_card_col]

            if all(col in df_equip.columns for col in tp_required_cols):
                valid_dates_df = df_equip.dropna(subset=[tp_card_col])
                tp_alert_df = valid_dates_df.loc[valid_dates_df[tp_card_col] <= ten_days, tp_required_cols].copy()

                if tp_alert_df.empty:
                    st.success("✅ No T.P cards are expired or expiring within 10 days.")
                else:
                    tp_alert_df["Status"] = tp_alert_df[tp_card_col].apply(lambda d: "Expired" if d < today else "Expiring Soon")
                    st.dataframe(tp_alert_df, use_container_width=True)
            else:
                st.warning("Could not generate T.P Card alerts. One or more required columns are missing.")
            
            st.markdown("---")
            
            total_equipment = len(df_equip)
            expired_count = 0
            expiring_soon_count = 0

            for col in date_cols:
                 if col in df_equip.columns:
                    valid_dates = pd.to_datetime(df_equip[col], errors='coerce').dt.date
                    expired_count += (valid_dates < today).sum()
                    expiring_soon_count += ((valid_dates >= today) & (valid_dates <= ten_days)).sum()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric(label="Total Equipment", value=total_equipment)
            kpi2.metric(label="Total Expired Items", value=expired_count, delta="Action Required", delta_color="inverse")
            kpi3.metric(label="Expiring in 10 Days", value=expiring_soon_count, delta="Monitor Closely", delta_color="off")
            
            st.markdown("---")
            st.subheader("🔍 All Document Expiry Alerts")
            # (The rest of the equipment dashboard code remains the same)
            st.dataframe(df_equip, use_container_width=True)


# -------------------- MAIN APP --------------------
def main():
    st.set_page_config(page_title="Onsite Reporting System", layout="wide")
    if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
        login()
        return

    obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet = get_sheets()
    choice = sidebar()

    if choice == "🏠 Home":
        st.title("📋 Onsite Reporting System")
        st.write(f"Welcome, **{st.session_state.get('username')}**!")
        st.info("Select an option from the sidebar to begin.")

    elif choice == "📝 Observation Form":
        show_observation_form(obs_sheet)

    elif choice == "🛠️ Permit Form":
        show_permit_form(permit_sheet)

    elif choice == "📊 Dashboard":
        if st.session_state.get("role") == "admin":
            show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet)
        else:
            st.warning("🚫 Access Denied: This page is for admins only.")

    elif choice == "🚜 Heavy Equipment":
        show_equipment_form(heavy_equip_sheet)

    elif choice == "🚚 Heavy Vehicle":
        show_heavy_vehicle_form(heavy_vehicle_sheet)

    elif choice == "🚪 Logout":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
