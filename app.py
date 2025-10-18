import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# --- User Credentials with Roles ---
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "admin": {"password": "admin", "role": "admin"}
}

# --- Sheet URLs ---
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"

# --- Google Sheet Setup ---
def get_sheets():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet1 = client.open_by_url(OBSERVATION_URL).sheet1
    sheet2 = client.open_by_url(PERMIT_URL).sheet1
    return sheet1, sheet2

# --- Login Page ---
def login():
    st.markdown("""
        <style>
        body {
            background-color: #e6f0fa;
        }
        .login-container {
            max-width: 400px;
            margin: 4rem auto;
            padding: 2rem;
            border-radius: 12px;
            background-color: white;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .login-title {
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 1.5rem;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        .stButton>button {
            background-color: #2c3e50;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
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
        user_data = USER_CREDENTIALS.get(username)
        if user_data and user_data["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user_data["role"]
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# --- Sidebar Navigation ---
def sidebar():
    st.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            background-color: rgb(245, 247, 250);
            padding: 20px;
        }
        .sidebar-title {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .css-1lcbmhc {padding-top: 0rem;}
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-title">🧭 Navigation</div>', unsafe_allow_html=True)
        menu_options = {
            "🏠 Home": "Home",
            "📝 Observation Form": "Observation Form",
            "🛠️ Permit Form": "Permit Form",
            "📊 Dashboard": "Dashboard",
            "🚪 Logout": "Logout"
        }
        choice = st.selectbox("Go to", list(menu_options.keys()))
        if st.button("🔄 Refresh"):
            st.rerun()

        return menu_options[choice]

# --- Observation Form ---
def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    well_numbers = ["2334", "2556", "1858", "2433", "2553", "2447"]

    submitted = False

    with st.form("obs_form"):
        form_date = st.date_input("Date")
        date_str = form_date.strftime("%Y-%m-%d")
        data = {
            "DATE": date_str,
            "WELL NO": st.selectbox("Well No", well_numbers),
            "AREA": st.text_input("Area"),
            "OBSERVER NAME": st.selectbox("Observer Name", [
                "AJISH JOSEPH", "ARFAN", "ARUN SOMAN", "JAMALI", "JOSEPH", "MD ILYAS",
                "MUNSIF KHAN", "MUHAMMAD ILYAS", "MUHAMMAD SOOMER", "M.UMAIR", "PRADEEP",
                "QAMAR", "SHIVA KANNAN", "SUDISH", "SURESH BABU", "VAISHAK", "VARGHEESE"
            ]),
            "OBSERVATION DETAILS": st.text_area("Observation Details"),
            "RECOMMENDED SOLUTION/ACTION TAKEN": st.text_area("Recommended Action"),
            "SUPERVISOR NAME": st.text_input("Supervisor Name"),
            "DISCIPLINE": st.selectbox("Discipline", [
                "EQUIPMENT", "CIVIL", "PIPING", "ADMINISTRATION", "E&I", "WPR", "QC", "STORES",
                "WORK PERMIT SYSTEM", "SCAFFOLDING", "VEHICHLE", "PAINTING"
            ]),
            "CATEGORY": st.selectbox("Category", [
                "Abrasive Blasting and Coating", "Chemical Handling and Hazardous material",
                "Civil, Concrete Work", "Compressed Gases", "Confined Space / Restricted area",
                "Crane and Lifting Devices", "Electrical Safety", "Environmental / Waste Management",
                "Fall Protection/Personal Fall Arrest System Use/Falling Hazard",
                "Fire prevention & Protection", "General Equipment (Air Compressors/Power Generator etc.)",
                "Hand/Power Tools and Electrical appliances", "Health, hygiene & welfare",
                "Heavy Equipment", "Hot work (Cutting/Welding/Brazing)", "Housekeeping & Material Management",
                "Personal Protective Equipment’s PPE Usage", "Radiation and NDT",
                "Scaffolds, Ladders and Elevated work platforms",
                "Security, Unsafe Behavior, and other project Requirements",
                "Trenching/Excavation/Shoring", "Vehicles / Traffic Control",
                "Work Permit, Risk Assessment, JSA & other procedures"
            ]),  # "Fire Extinguisher T.P Expiry" removed here
            "CLASSIFICATION": st.selectbox("Classification", ["POSITIVE", "UNSAFE CONDITION", "UNSAFE ACT"]),
            "STATUS": st.selectbox("Status", ["Open", "Closed"]),
        }

        submit = st.form_submit_button("Submit")
        if submit:
            # block submission if someone manually typed/selected the banned category for VEHICHLE
            if data.get("CATEGORY") == "Fire Extinguisher T.P Expiry" and data.get("DISCIPLINE") == "VEHICHLE":
                st.error("❌ Submissions with 'Fire Extinguisher T.P Expiry' for heavy vehicle are not allowed.")
            else:
                try:
                    sheet.append_row(list(data.values()))
                    st.success("✅ Observation submitted successfully!")
                    submitted = True
                except Exception as e:
                    st.error(f"❌ Error submitting data: {e}")

    if submitted:
        if st.button("➕ Enter New Observation Form"):
            st.rerun()

# --- Permit Form ---
def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")

    submitted = False

    with st.form("permit_form"):
        form_date = st.date_input("Date")
        date_str = form_date.strftime("%Y-%m-%d")
        data = {
            "DATE": date_str,
            "PERMIT TYPE": st.text_input("Permit Type"),
            "LOCATION": st.text_input("Location"),
            "DESCRIPTION": st.text_area("Description"),
            "RESPONSIBLE": st.text_input("Responsible Person"),
            "STATUS": st.selectbox("Status", ["Active", "Closed", "Pending"]),
        }

        submit = st.form_submit_button("Submit")
        if submit:
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Permit log submitted successfully!")
                submitted = True
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

    if submitted:
        if st.button("➕ Enter New Permit Log"):
            st.rerun()

# --- Dashboard View ---
def show_combined_dashboard(sheet1, sheet2):
    st.header("📊 Dashboard")
    dash_option = st.sidebar.radio("Choose Dashboard", ["📋 Observation Dashboard", "🛠️ Permit Dashboard"])

    if dash_option == "📋 Observation Dashboard":
        st.subheader("📋 Observation Dashboard")
        obs_data = sheet1.get_all_records()
        obs_df = pd.DataFrame(obs_data)
        # filter out existing rows that are Fire Extinguisher T.P Expiry for VEHICHLE
        if not obs_df.empty and "CATEGORY" in obs_df.columns and "DISCIPLINE" in obs_df.columns:
            obs_df = obs_df[~((obs_df["CATEGORY"] == "Fire Extinguisher T.P Expiry") & (obs_df["DISCIPLINE"] == "VEHICHLE"))]
        st.dataframe(obs_df)

    elif dash_option == "🛠️ Permit Dashboard":
        st.subheader("🛠️ Permit Dashboard")
        permit_data = sheet2.get_all_records()
        permit_df = pd.DataFrame(permit_data)
        st.dataframe(permit_df)

# --- Main App ---
def main():
    if "logged_in" not in st.session_state:
        login()
        return

    sheet1, sheet2 = get_sheets()
    choice = sidebar()

    if choice == "Home":
        st.title("🏠 Welcome to the Field Reporting App")
        st.write("Use the sidebar to navigate between forms and dashboard.")

    elif choice == "Observation Form":
        show_observation_form(sheet1)

    elif choice == "Permit Form":
        show_permit_form(sheet2)

    elif choice == "Dashboard":
        if st.session_state.get("role") == "admin":
            show_combined_dashboard(sheet1, sheet2)
        else:
            st.warning("🚫 Access Denied: Only admin users can view dashboard data.")

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()

# --- Run App ---
if __name__ == "__main__":
    main()

