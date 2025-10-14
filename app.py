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

HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"

# -------------------- UTILITIES --------------------
def parse_date(s):
    """Safely parses a string into a date object."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    try:
        return datetime.strptime(str(s).split(' ')[0], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def badge_expiry(d, expiry_days=10):
    """Creates a visual badge for expiry dates."""
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    if d < today:
        return f"🚨 Expired ({d.strftime('%Y-%m-%d')})"
    elif d <= today + timedelta(days=expiry_days):
        return f"⚠️ Expires Soon ({d.strftime('%Y-%m-%d')})"
    else:
        return f"✅ Valid ({d.strftime('%Y-%m-%d')})"

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600) # Cache for 10 minutes
def get_sheets():
    """Connects to Google Sheets and returns worksheet objects."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
    wb = client.open_by_url(EQUIPMENT_URL)

    def get_or_create(ws_title, headers=None):
        try:
            ws = wb.worksheet(ws_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = wb.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws
    
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

    heavy_equip_sheet = get_or_create(HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)

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
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime("%Y-%m-%d")
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime("%Y-%m-%d")
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime("%Y-%m-%d")
        fe_tp_expiry = cols_dates[1].date_input("F.E TP expiry").strftime("%Y-%m-%d")
        tp_card_expiry = cols_dates[0].date_input("T.P Card expiry date").strftime("%Y-%m-%d")

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
        form_date = st.date_input("Date")
        data = {
            "DATE": form_date.strftime("%Y-%m-%d"),
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
                sheet.append_row(list(data.values()))
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    
    # Lists for dropdowns
    DRILL_SITES = ["2485", "2566", "2534", "1969", "2549", "1972"]
    PERMIT_TYPES = ["Hot", "Cold", "CSE", "EOLB"]
    PERMIT_ISSUERS = ["VISHNU MOHAN", "UNNIMON SRINIVASAN"]
    PERMIT_RECEIVERS = [
        "MD MEHEDI HASAN NAHID", "JEFFREY VERBO YOSORES", "RAMESH KOTHAPALLY BHUMAIAH",
        "ALAA ALI ALI ALQURAISHI", "VALDIMIR FERNANDO", "PRINCE BRANDON LEE RAJU",
        "JEES RAJ RAJAN ALPHONSA", "BRAYAN DINESH", "EZBORN NGUNYI MBATIA",
        "AHILAN THANKARAJ", "MOHAMMAD FIROZ ALAM", "PRAVEEN SAHANI",
        "KANNAN GANESAN", "ARUN MANAYATHU ANANDH", "ANANDHU SASIDHARAN",
        "NINO URSAL CANON", "REJIL RAVI", "SIVA PRAVEEN SUGUMARAN",
        "AKHIL ASHOKAN", "OMAR MAHUSAY DATANGEL", "MAHAMMAD SINAN",
        "IRSHAD ALI MD QUYOOM", "RAISHKHA IQBALKHA PATHAN", "ABHILASH AMBAREEKSHAN",
        "SHIVKUMAR MANIKAPPA MANIKAPPA", "VAMSHIKRISHNA POLASA", "NIVIN PRASAD",
        "DHAVOUTH SULAIMAN JEILANI", "WINDY BLANCASABELLA", "MAHTAB ALAM",
        "BERIN ROHIN JOSEPH BENZIGER", "NEMWEL GWAKO", "RITHIC SAI",
        "SHAIK KHADEER", "SIMON GACHAU MUCHIRI", "JARUZELSKI MELENDES PESINO",
        "HAIDAR NASSER MOHAMMED ALKHALAF", "JEYARAJA JAYAPAL",
        "HASHEM ABDULMAJEED ALBAHRANI", "PRATHEEP RADHAKRISHNAN",
        "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC", "SHAHWAZ KHAN"
    ]

    with st.form("permit_form", clear_on_submit=True):
        # --- NEW TWO-COLUMN LAYOUT ---
        col1, col2 = st.columns(2)
        
        with col1:
            date_val = st.date_input("Date")
            permit_no = st.text_input("Permit No")
            permit_receiver = st.selectbox("Permit Receiver", PERMIT_RECEIVERS)

        with col2:
            drill_site = st.selectbox("Drill Site", DRILL_SITES)
            permit_type = st.selectbox("Type of Permit", PERMIT_TYPES)
            permit_issuer = st.selectbox("Permit Issuer", PERMIT_ISSUERS)

        activity = st.text_area("Activity")
        # -----------------------------

        if st.form_submit_button("Submit"):
            # The order must match your Google Sheet columns
            data = [
                date_val.strftime("%Y-%m-%d"),
                drill_site,
                permit_no,
                permit_type,
                activity,
                permit_receiver,
                permit_issuer
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Permit submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")
    VEHICLE_LIST = ["Bus", "Dump Truck", "Low Bed", "Trailer", "Water Tanker", "Mini Bus", "Flat Truck"]
    with st.form("vehicle_form", clear_on_submit=True):
        vehicle_type = st.selectbox("Vehicle Type", VEHICLE_LIST)
        make = st.text_input("Make")
        plate_no = st.text_input("Plate No")
        asset_code = st.text_input("Asset Code")
        owner = st.text_input("Owner")
        mvpi_expiry = st.date_input("MVPI Expiry date").strftime("%Y-%m-%d")
        insurance_expiry = st.date_input("Insurance Expiry").strftime("%Y-%m-%d")
        driver_name = st.text_input("Driver Name")
        iqama_no = st.text_input("Iqama No")
        licence_expiry = st.date_input("Licence Expiry").strftime("%Y-%m-%d")
        qr_code = st.text_input("Q.R code")
        fa_box = st.selectbox("F.A Box", ["Available", "Not Available", "Expired", "Inadequate Medicine"])
        fire_ext_tp_expiry = st.date_input("Fire Extinguisher T.P Expiry").strftime("%Y-%m-%d")
        pwas_status = st.selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        seatbelt_damaged = st.selectbox("Seat belt damaged", ["Yes", "No", "N/A"])
        tyre_condition = st.selectbox("Tyre Condition", ["Good", "Worn Out", "Damaged", "Needs Replacement", "N/A"])
        suspension_systems = st.selectbox("Suspension Systems", ["Good", "Faulty", "Needs Repair", "Damaged", "N/A"])
        remarks = st.text_input("Remarks")

        data = {
            "Vehicle Type": vehicle_type, "Make": make, "Plate No": plate_no, "Asset Code": asset_code,
            "Owner": owner, "MVPI Expiry date": mvpi_expiry, "Insurance Expiry": insurance_expiry,
            "Driver Name": driver_name, "Iqama No": iqama_no, "Licence Expiry": licence_expiry,
            "Q.R code": qr_code, "F.A Box": fa_box, "Fire Extinguisher T.P Expiry": fire_ext_tp_expiry,
            "PWAS Status": pwas_status, "Seat belt damaged": seatbelt_damaged, "Tyre Condition": tyre_condition,
            "Suspension Systems": suspension_systems, "Remarks": remarks
        }
        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Heavy Vehicle submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- ADVANCED DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])

    with tab_eqp:
        st.subheader("Heavy Equipment Analytics")
        try:
            df_equip = pd.DataFrame(heavy_equip_sheet.get_all_records())
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load data from Google Sheets: {e}")
            return

        if df_equip.empty:
            st.info("No Heavy Equipment data available to display.")
            return

        # --- Data Processing ---
        date_cols = ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]
        for col in date_cols:
             if col in df_equip.columns:
                 df_equip[col] = df_equip[col].apply(parse_date)

        today = date.today()
        ten_days = today + timedelta(days=10)

        # --- T.P Card Specific Expiry Alert ---
        st.subheader("🚨 T.P Card Expiry Alerts")
        tp_card_col = "T.P Card expiry date"
        tp_required_cols = ["Equipment type", "Palte No.", "Owner", tp_card_col]

        if all(col in df_equip.columns for col in tp_required_cols):
            tp_alert_df = df_equip.loc[df_equip[tp_card_col] <= ten_days, tp_required_cols].copy()

            if tp_alert_df.empty:
                st.success("✅ No T.P cards are expired or expiring within 10 days.")
            else:
                tp_alert_df["Status"] = tp_alert_df[tp_card_col].apply(
                    lambda d: "Expired" if d < today else "Expiring Soon"
                )
                st.dataframe(tp_alert_df, use_container_width=True)
        else:
            st.warning("Could not generate T.P Card alerts. One or more required columns are missing from the sheet: 'Equipment type', 'Palte No.', 'Owner', 'T.P Card expiry date'.")
        
        st.markdown("---")

        # --- KPIs ---
        total_equipment = len(df_equip)
        expired_count = 0
        expiring_soon_count = 0

        for col in date_cols:
             if col in df_equip.columns:
                 expired_count += df_equip[df_equip[col] < today].shape[0]
                 expiring_soon_count += df_equip[(df_equip[col] >= today) & (df_equip[col] <= ten_days)].shape[0]

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="Total Equipment", value=total_equipment)
        kpi2.metric(label="Total Expired Items", value=expired_count, delta="Action Required", delta_color="inverse")
        kpi3.metric(label="Expiring in 10 Days", value=expiring_soon_count, delta="Monitor Closely", delta_color="off")

        st.markdown("---")

        # --- General Expiry Alerts Section (All Documents) ---
        st.subheader("🔍 All Document Expiry Alerts")
        expired_dfs = []
        for col in date_cols:
            if col in df_equip.columns:
                required_cols = ["Equipment type", "Palte No.", "Owner", col]
                
                if all(c in df_equip.columns for c in required_cols):
                    expired_df = df_equip.loc[df_equip[col] <= ten_days, required_cols].copy()
                    expired_df.rename(columns={col: "Expiry Date"}, inplace=True)
                    expired_df["Document Type"] = col.replace(" date", "").replace(" expiry", "")
                    expired_dfs.append(expired_df)

        if not expired_dfs:
             st.success("✅ No equipment documents are expired or expiring within 10 days.")
        else:
            alert_df = pd.concat(expired_dfs, ignore_index=True).sort_values(by="Expiry Date")
            if alert_df.empty:
                st.success("✅ No equipment documents are expired or expiring within 10 days.")
            else:
                alert_df["Status"] = alert_df["Expiry Date"].apply(lambda d: "Expired" if d < today else "Expiring Soon")
                st.dataframe(alert_df, use_container_width=True)

        st.markdown("---")

        # --- Visualizations ---
        st.subheader("Visual Insights")
        c1, c2 = st.columns(2)

        with c1:
            if 'Equipment type' in df_equip.columns:
                fig_type = px.bar(
                    df_equip['Equipment type'].value_counts().reset_index(),
                    x='Equipment type', y='count', title='Equipment Distribution by Type',
                    labels={'count': 'Number of Units', 'Equipment type': 'Type'},
                    text_auto=True 
                )
                fig_type.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_type, use_container_width=True)

        with c2:
            if 'PWAS status' in df_equip.columns:
                fig_pwas = px.pie(
                    df_equip, names='PWAS status', title='PWAS Status Overview',
                    hole=0.3
                )
                st.plotly_chart(fig_pwas, use_container_width=True)
            
        if 'Owner' in df_equip.columns:
            fig_owner = px.bar(
                df_equip['Owner'].value_counts().nlargest(10).reset_index(),
                x='Owner', y='count', title='Top 10 Equipment Owners',
                labels={'count': 'Number of Units', 'Owner': 'Owner Name'},
                text_auto=True
            )
            st.plotly_chart(fig_owner, use_container_width=True)
        
        st.markdown("---")
        
        # --- Full Data View ---
        st.subheader("Full Heavy Equipment Data")
        df_display = df_equip.copy()
        for col in date_cols:
             if col in df_display.columns:
                 df_display[col] = df_display[col].apply(badge_expiry, expiry_days=10)
        
        st.dataframe(df_display, use_container_width=True)

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
