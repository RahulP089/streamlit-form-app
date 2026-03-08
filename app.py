import streamlit as st # for web
import pandas as pd # For JSON file
import gspread # Link spread sheet
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
import plotly.express as px # fore pie
import base64 # Added for image encoding
import os # Added for file path checking

# -------------------- USER LOGIN --------------------
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"
WPR_MASTER_URL = "https://docs.google.com/spreadsheets/d/17uH7qXczlZWU1_8UbogYIKzl7Xlb517brGI4G5YTLOY/edit"

HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"
WPR_MASTER_TAB = "WPR Master"

# --- MASTER SITE LIST ---
ALL_SITES = [
    "1858", "1969", "1972", "2433", "2447", "2485",
    "2534", "2549", "2553", "2516", "2556", "2575", "2566","2570","HRDH Laydown","2595"
]

# -------------------- UTILITIES --------------------
def get_img_as_base64(file):
    """Reads an image file and returns it as a base64 encoded string."""
    if not os.path.exists(file):
        return None
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def parse_date(s):
    """Safely parses a string into a date object, trying multiple formats."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).split(' ')[0], fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def badge_expiry(d, expiry_days=30):
    """Creates a visual badge for expiry dates."""
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%d-%b-%Y')
    if d < today:
        return f"🚨 Expired ({date_str})"
    elif d <= today + timedelta(days=expiry_days):
        return f"⚠️ Expires Soon ({date_str})"
    else:
        return f"✅ Valid ({date_str})"

def ensure_headers_match(worksheet, expected_headers):
    """Checks and overwrites the header row of a worksheet if it doesn't match the expected list."""
    try:
        current_header = worksheet.row_values(1)
        if current_header != expected_headers:
            worksheet.update('A1', [expected_headers])
            if len(current_header) > len(expected_headers):
                 worksheet.batch_clear([f'{chr(ord("A") + len(expected_headers))}1:Z1'])
            st.toast(f"✅ Headers updated in '{worksheet.title}'.", icon="🚨")
            st.cache_resource.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Failed to verify/fix headers in {worksheet.title}: {e}")

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600)
def get_sheets():
    """Connects to Google Sheets and returns worksheet objects."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
    wb_equip = client.open_by_url(EQUIPMENT_URL)
    wb_wpr = client.open_by_url(WPR_MASTER_URL)

    def get_or_create(wb, ws_title, headers=None):
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
        "T.P Card expiry date", "Q.R code", "PWAS status", "FA box Status", "Documents"
    ]

    heavy_vehicle_headers = [
        "Vehicle Type", "Make", "Plate No", "Asset Code", "Owner", "MVPI Expiry date", "Insurance Expiry",
        "Driver Name", "Iqama No", "Licence Expiry", "Q.R code", "F.A Box",
        "PWAS Status", "Seat belt damaged", "Tyre Condition", "Suspension Systems", "Remarks"
    ]

    wpr_master_headers = [
        "NAME", "DESIGNATION", "EMP #", "IQAMA NUMBER", "PERMIT TYPES", "AWPR ID EXPIRY DATE",
        "SAOO EXPIRY DATE", "SAOO valid days", "South Delegation Expiry Date", "South Delegation valid days",
        "Central Expiry Date", "Central Valid Days", "MDRK", "MDRK Valid Days", "Uniyzal Expiry date",
        "Uniyzal Deligation valid days", "POD ORIENTATION", "IQAMA VALID DAYS", "IQAMA", "Document"
    ]

    heavy_equip_sheet = get_or_create(wb_equip, HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(wb_equip, HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)
    wpr_sheet = get_or_create(wb_wpr, WPR_MASTER_TAB, headers=wpr_master_headers)

    ensure_headers_match(heavy_equip_sheet, heavy_equip_headers)
    ensure_headers_match(heavy_vehicle_sheet, heavy_vehicle_headers)
    ensure_headers_match(wpr_sheet, wpr_master_headers)

    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet, wpr_sheet

# -------------------- LOGIN PAGE --------------------
def login():
    IMG_PATH = "login_bg.jpg" 
    img_base64 = get_img_as_base64(IMG_PATH)
    
    background_css = ""
    if img_base64:
        file_extension = os.path.splitext(IMG_PATH)[1].lower()
        mime_type = "jpeg" if file_extension in [".jpg", ".jpeg"] else file_extension[1:]
        background_css = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/{mime_type};base64,{img_base64}");
            background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"] > .main {{ background-color: transparent !important; }}
        </style>
        """

    st.markdown(f"""
    {background_css}
    <style>
    .login-container {{
        background-color: transparent; max-width: 300px; margin: 4rem auto; 
        padding: 2rem; border-radius: 12px; text-align: center;
    }}
    .login-title {{
        font-size: 32px; font-weight: 700; color: white; 
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); margin-bottom: 1.5rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🛡️ Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        user = USER_CREDENTIALS.get(username)
        if user and user["password"] == password:
            st.session_state.update(logged_in=True, username=username, role=user["role"])
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
def sidebar():
    with st.sidebar:
        st.title("🧭 Navigation")
        menu_options = [
            "🏠 Home", "📝 Observation Form", "🛠️ Permit Form",
            "🏗️ Equipments", "🪪 WPR Master", "📊 Dashboard", "🚪 Logout"
        ]
        menu = st.selectbox("Go to", menu_options, key="main_menu")
        if menu == "🏗️ Equipments":
            return st.selectbox("Select Equipment", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"], key="equip_sub")
        return menu

# -------------------- FORMS --------------------
def show_equipment_form(sheet):
    st.header("🚜 Heavy Equipment Entry Form")
    EQUIPMENT_LIST = ["Excavator", "Backhoe Loader", "Wheel Loader", "Bulldozer", "Motor Grader", "Compactor / Roller", "Crane", "Forklift", "Boom Truck", "Side Boom", "Hydraulic Drill Unit", "Telehandler", "Skid Loader"]
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
        date_format = "%d-%b-%Y"
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime(date_format)
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime(date_format)
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime(date_format)
        tp_card_expiry = cols_dates[1].date_input("T.P Card expiry date").strftime(date_format)
        st.subheader("T.P Card & Status")
        cols_status = st.columns(2)
        tp_card_type = cols_status[0].selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_number = cols_status[1].text_input("T.P Card Number")
        pwas_status = cols_status[0].selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        fa_box_status = cols_status[1].text_input("FA box Status")
        qr_code = cols_status[0].text_input("Q.R code")
        documents = cols_status[1].text_input("Documents")
        if st.form_submit_button("Submit"):
            data = [equipment_type, make, plate_no, asset_code, owner, tp_insp_date, tp_expiry, insurance_expiry, operator_name, iqama_no, tp_card_type, tp_card_number, tp_card_expiry, qr_code, pwas_status, fa_box_status, documents]
            try:
                sheet.append_row(data)
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    OBSERVER_NAMES = ["AJISH", "AKHIL MOHAN", "AQIB", "ARFAN", "ASIM", "ASHRAF KHAN", "BIJO", "FELIN", "HABEEB", "ILYAS", "IRFAN", "JAMALI", "JOSEPH CRUZ", "MOHSIN", "PRADEEP", "RAJSHEKAR", "RICKEN", "SHIVA KANNAN", "SHIVA SUBRAMANIYAM", "SUDISH", "VAISHAK", "VARGHEESE", "WALI ALAM", "ZAHEER"]
    AREAS = ["Well Head", "Flow Line", "OHPL", "Tie In", "Lay Down", "Cellar", "Remote Header"]
    CATEGORIES = ["Fall Protection/PFAS", "Trenching/Excavation", "Scaffolds/Ladders", "Crane/Lifting", "Heavy Equipment", "Vehicles/Traffic", "Tools/Electrical", "Hot work", "Fire prevention", "Environmental", "PPE", "House Keeping"]
    SUPERVISOR_TRADE_MAP = {"RAJA KUMAR": "CONTROLLER-EQUIPMENT", "SREEDHARAN VISWANATHAN": "SUPERVISOR-PIPING", "MANOJ THOMAS": "WELL IN CHARGE", "ANIL KUMAR JANARDHANAN": "WELL IN CHARGE", "SIVA PRASAD PILLAI": "FOREMAN-PIPING", "JAYAN RAJAJAN": "FOREMAN-PIPING", "MURUGAN VANNIYAPERUMAL": "COORDINATOR-NDE", "ANU MOHAN MOHANAN PILLAI": "FIELD ADMINISTRATOR", "BHARAT CHANDRABARAL": "ASSISTANT-STORE", "SUMOD PRABHAKARA": "LAND SURVEYOR", "DHARMA RAJU UPPADA": "FOREMAN-HYDRO TEST", "JEFFREY F. TABAMO": "CONSTRUCTION SUPERVISOR-E & I", "ORLANDO GURGUD": "SUPERVISOR-PAINTING CREW", "RICHARD REYES RIVERAL": "SUPERVISOR-PAINTING CREW", "AJIMAL SULFIKAR": "SUPERVISOR-PIPING", "ARVIND KUMAR": "SUPERVISOR-CIVIL", "MAQSUD ALAM": "CONSTRUCTION SUPERVISOR-PIPING", "SIFAT MEHDI": "FOREMAN-INSTRUMENTATION", "SAJU SADANANDAN": "SUPERVISOR-CIVIL", "SASIDHARA KURUP": "FOREMAN-ELECTRICAL", "ALVIN CHARLY": "CONSTRUCTION SUPERVISOR-E & I", "PAWAN KUMAR YADAV": "FOREMAN-CIVIL", "BRIHASPATI ADAK": "FOREMAN-CIVIL", "JITHIN JOHN": "CONSTRUCTION SUPERVISOR-CIVIL", "RAVI SINGH": "SUPERVISOR-CIVIL", "ANILKUMAR SAHADEVAN": "SUPERVISOR-CIVIL", "BALA KRISHNA": "FOREMAN-CIVIL", "SUNIL KUMARSAHU": "FOREMAN-CIVIL", "RAJESHWAR YASOJI NARAYANA": "SUPERVISOR-SCAFFOLDING", "ASHWANI KUMAR YADAV": "FOREMAN-CIVIL", "QUAISAR ALI": "SUPERVISOR-ELECTRICAL", "ABHISHEK REGHUVARAN": "SUPERVISOR-PIPING", "ZEESHAN YOUSUF": "SUPERVISOR-CIVIL", "MOHAMMAD RAUSHAN": "SUPERVISOR-CIVIL", "AHAMED RIYAZ ASHRAE ALI": "SUPERVISOR-CIVIL", "ASLAM KHAN ALBAN": "FOREMAN-SCAFFOLDING", "SURESH KUMAR": "WELL IN CHARGE", "ANOOPKUMAR": "SUPERVISOR-ELECTRICAL", "VAISHNAV VINOD SREEJA": "SUPERVISOR-PIPING", "MOHAMMED MUHANNA AL WOSAIFER": "ENGINEER-MECHANICAL", "HISHAM IBRAHIM AL FARHAN": "ADMIN ASSISTANT", "HASSAN FAYAA MOHAMMED MASHNI": "ELECTRICAL ENGINEER", "ABDALLAH MOHAMMED ALMOTAWA": "ENGINEER-MECHANICAL", "RAJA ALAGAPPAN": "SUPERVISOR-PAINTING CREW", "SURESHKUMAR": "CONSTRUCTION SUPERVISOR-PIPING","GOPAN": "SUPERVISOR-CIVIL","BHARATH":"STORE KEEPER","HAROON":"STORE KEEPER","BIVIN":"FOREMAN-PIPING"}
    
    supervisor_names = [""] + sorted(list(SUPERVISOR_TRADE_MAP.keys()))
    with st.form("obs_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            form_date = st.date_input("Date")
            area = st.selectbox("Area", AREAS)
            observer_name = st.selectbox("Observer Name", OBSERVER_NAMES)
            classification = st.selectbox("Classification", ["POSITIVE", "UNSAFE CONDITION", "UNSAFE ACT"])
            category = st.selectbox("Category", CATEGORIES)
        with col2:
            well_no = st.selectbox("Well No", ALL_SITES)
            supervisor_name = st.selectbox("Supervisor Name", supervisor_names)
            trade = SUPERVISOR_TRADE_MAP.get(supervisor_name, "")
            st.text_input("Discipline", value=trade, disabled=True)
            status = st.selectbox("Status", ["OPEN", "CLOSE"])
        obs_details = st.text_area("Observation Details")
        rec_action = st.text_area("Recommended Action")
        if st.form_submit_button("Submit"):
            data = [form_date.strftime("%d-%b-%Y"), well_no, area, observer_name, obs_details, rec_action, supervisor_name, trade, category, classification, status]
            sheet.append_row(data)
            st.success("✅ Observation submitted!")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    WORK_LOCATIONS = ["Well Head", "OHPL", "OPTF", "E&I Skid", "Burn Pit", "Cellar", "Flow Line", "Lay down", "CP area","BD-Line"]
    PERMIT_TYPES = ["Hot", "Cold", "CSE", "EOLB"]
    PERMIT_RECEIVERS = ["MD MEHEDI HASAN NAHID","ALWIN", "JEFFREY VERBO YOSORES", "RAMESH KOTHAPALLY BHUMAIAH", "ALAA ALI ALI ALQURAISHI", "VALDIMIR FERNANDO", "PRINCE BRANDON LEE RAJU", "JEES RAJ RAJAN ALPHONSA", "BRAYAN DINESH", "EZBORN NGUNYI MBATIA", "AHILAN THANKARAJ", "MOHAMMAD FIROZ ALAM", "PRAVEEN SAHANI", "KANNAN GANESAN", "ARUN MANAYATHU ANANDH", "ANANDHU SASIDHARAN", "NINO URSAL CANON", "REJIL RAVI", "SIVA PRAVEEN SUGUMARAN", "AKHIL ASHOKAN", "OMAR MAHUSAY DATANGEL", "MAHAMMAD SINAN", "IRSHAD ALI MD QUYOOM", "RAISHKHA IQBALKHA PATHAN", "ABHILASH AMBAREEKSHAN", "SHIVKUMAR MANIKAPPA MANIKAPPA", "VAMSHIKRISHNA POLASA", "NIVIN PRASAD", "DHAVOUTH SULAIMAN JEILANI", "WINDY BLANCASABELLA", "MAHTAB ALAM", "BERIN ROHIN JOSEPH BENZIGER", "NEMWEL GWAKO", "RITHIC SAI", "SHAIK KHADEER", "SIMON GACHAU MUCHIRI", "DIFLIN", "JARUZELSKI MELENDES PESINO", "HAIDAR NASSER MOHAMMED ALKHALAF", "JEYARAJA JAYAPAL", "HASHEM ABDULMAJEED ALBAHRANI", "PRATHEEP RADHAKRISHNAN", "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC", "SHAHWAZ KHAN","PACIFICO LUBANG ICHON","ELMER","REMY E PORRAS"]
    PERMIT_ACTIVITIES = ["Mechanical Excavation", "Manual Excavation", "Welding/Cutting", "Holiday test", "Pole erection", "Painting", "Cable pulling", "Nitrogen purging", "Hydro test", "Radiography test"]
    with st.form("permit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("Date")
            drill_site = st.selectbox("Drill Site", ALL_SITES)
            work_location = st.selectbox("Work Location", WORK_LOCATIONS)
            permit_receiver = st.selectbox("Permit Receiver", PERMIT_RECEIVERS)
        with col2:
            permit_no = st.text_input("Permit No")
            permit_type = st.radio("Type", PERMIT_TYPES, horizontal=True)
            permit_issuer = st.radio("Issuer", ["UNNIMON SRINIVASAN","VISHNU MOHAN"], horizontal=True)
        activity = st.selectbox("Activity", PERMIT_ACTIVITIES)
        if st.form_submit_button("Submit"):
            data = [date_val.strftime("%d-%b-%Y"), drill_site, work_location, permit_no, permit_type, activity, permit_receiver, permit_issuer]
            sheet.append_row(data)
            st.success("✅ Permit Logged!")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")
    VEHICLE_LIST = ["Bus", "Dump Truck", "Low Bed", "Trailer", "Water Tanker", "Mini Bus", "Flat Truck"]
    with st.form("vehicle_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        vehicle_type = c1.selectbox("Vehicle Type", VEHICLE_LIST)
        make = c2.text_input("Make")
        plate_no = c1.text_input("Plate No")
        asset_code = c2.text_input("Asset Code")
        owner = c1.text_input("Owner")
        qr_code = c2.text_input("Q.R code")
        driver_name = c1.text_input("Driver Name")
        iqama_no = c2.text_input("Iqama No")
        d1, d2 = st.columns(2)
        mvpi_expiry = d1.date_input("MVPI Expiry").strftime("%d-%b-%Y")
        ins_expiry = d2.date_input("Insurance Expiry").strftime("%d-%b-%Y")
        lic_expiry = d1.date_input("Licence Expiry").strftime("%d-%b-%Y")
        fa_box = st.selectbox("F.A Box", ["Available", "Not Available", "Expired"])
        pwas = st.selectbox("PWAS Status", ["Working", "Not Working", "N/A"])
        remarks = st.text_area("Remarks")
        if st.form_submit_button("Submit"):
            data = [vehicle_type, make, plate_no, asset_code, owner, mvpi_expiry, ins_expiry, driver_name, iqama_no, lic_expiry, qr_code, fa_box, pwas, "N/A", "N/A", "N/A", remarks]
            sheet.append_row(data)
            st.success("✅ Vehicle Logged!")

# -------------------- NEW WPR MASTER FORM --------------------
def show_wpr_master_form(sheet):
    st.header("🪪 WPR Master Certification Form")
    with st.form("wpr_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("NAME")
        designation = c2.text_input("DESIGNATION")
        emp_no = c3.text_input("EMP #")
        iqama_no = c1.text_input("IQAMA NUMBER")
        permit_types = c2.text_input("PERMIT TYPES (e.g., Hot, Cold)")
        
        st.subheader("Certification Expiry Dates")
        d1, d2, d3 = st.columns(3)
        awpr_expiry = d1.date_input("AWPR ID EXPIRY DATE")
        saoo_expiry = d2.date_input("SAOO EXPIRY DATE")
        south_expiry = d3.date_input("South Delegation Expiry Date")
        central_expiry = d1.date_input("Central Expiry Date")
        mdrk_expiry = d2.date_input("MDRK Expiry Date")
        uniyzal_expiry = d3.date_input("Uniyzal Expiry Date")
        iqama_valid_date = d1.date_input("IQAMA VALID DATE")
        
        pod_orientation = c2.text_input("POD ORIENTATION")
        document_ref = c3.text_input("Document/IQAMA Link")

        if st.form_submit_button("Submit WPR Data"):
            today = date.today()
            # Calculate Valid Days for each
            saoo_days = (saoo_expiry - today).days
            south_days = (south_expiry - today).days
            central_days = (central_expiry - today).days
            mdrk_days = (mdrk_expiry - today).days
            uniyzal_days = (uniyzal_expiry - today).days
            iqama_days = (iqama_valid_date - today).days

            data = [
                name, designation, emp_no, iqama_no, permit_types,
                awpr_expiry.strftime("%d-%b-%Y"), saoo_expiry.strftime("%d-%b-%Y"), saoo_days,
                south_expiry.strftime("%d-%b-%Y"), south_days, central_expiry.strftime("%d-%b-%Y"),
                central_days, mdrk_expiry.strftime("%d-%b-%Y"), mdrk_days,
                uniyzal_expiry.strftime("%d-%b-%Y"), uniyzal_days, pod_orientation,
                iqama_days, iqama_valid_date.strftime("%d-%b-%Y"), document_ref
            ]
            try:
                sheet.append_row(data)
                st.success("✅ WPR Master Data Saved!")
            except Exception as e:
                st.error(f"Error: {e}")

# -------------------- DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet, wpr_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh, tab_wpr = st.tabs(["📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle", "🪪 WPR Master"])

    today = date.today()
    thirty_days = today + timedelta(days=30)

    # (Observation Dashboard Logic - Full)
    with tab_obs:
        st.subheader("Advanced Observation Analytics")
        df_obs = pd.DataFrame(obs_sheet.get_all_records())
        if not df_obs.empty:
            df_obs.columns = [str(col).strip().upper() for col in df_obs.columns]
            df_obs['DATE'] = pd.to_datetime(df_obs['DATE'], errors='coerce')
            st.metric("Total Observations", len(df_obs))
            fig_obs = px.pie(df_obs, names='CLASSIFICATION', title='Classification Distribution')
            st.plotly_chart(fig_obs, use_container_width=True)
            st.dataframe(df_obs, use_container_width=True)

    # (Permit Dashboard Logic - Full)
    with tab_permit:
        st.subheader("Permit Analytics")
        df_permit = pd.DataFrame(permit_sheet.get_all_records())
        if not df_permit.empty:
            df_permit.columns = [str(col).strip().upper() for col in df_permit.columns]
            st.metric("Total Permits Issued", len(df_permit))
            fig_p = px.bar(df_permit, x='DRILL SITE', color='TYPE OF PERMIT', title='Permits by Site')
            st.plotly_chart(fig_p, use_container_width=True)

    # (Equipment Dashboard Logic - Full)
    with tab_eqp:
        st.subheader("Equipment Tracking")
        df_equip = pd.DataFrame(heavy_equip_sheet.get_all_records())
        if not df_equip.empty:
            df_equip.columns = [str(col).strip().upper() for col in df_equip.columns]
            # Expiry badge application
            for col in ["T.P EXPIRY DATE", "INSURANCE EXPIRY DATE"]:
                if col in df_equip.columns:
                    df_equip[col] = df_equip[col].apply(lambda x: badge_expiry(parse_date(x)))
            st.dataframe(df_equip, use_container_width=True)

    # (Vehicle Dashboard Logic - Full)
    with tab_veh:
        st.subheader("Vehicle Tracking")
        df_veh = pd.DataFrame(heavy_vehicle_sheet.get_all_records())
        if not df_veh.empty:
            df_veh.columns = [str(col).strip().upper() for col in df_veh.columns]
            st.dataframe(df_veh, use_container_width=True)

    # (WPR Master Dashboard Logic - NEW)
    with tab_wpr:
        st.subheader("WPR Qualification Tracker")
        try:
            df_wpr = pd.DataFrame(wpr_sheet.get_all_records())
            if not df_wpr.empty:
                df_wpr.columns = [str(col).strip().upper() for col in df_wpr.columns]
                # Filter for candidates needing renewal soon (SAOO valid days < 30)
                if 'SAOO VALID DAYS' in df_wpr.columns:
                    df_wpr['SAOO VALID DAYS'] = pd.to_numeric(df_wpr['SAOO VALID DAYS'], errors='coerce')
                    renewals = df_wpr[df_wpr['SAOO VALID DAYS'] <= 30]
                    if not renewals.empty:
                        st.warning(f"🚨 {len(renewals)} WPR Personnel have SAOO expiries within 30 days!")
                        st.dataframe(renewals[['NAME', 'SAOO EXPIRY DATE', 'SAOO VALID DAYS']], hide_index=True)
                
                st.write("#### Full WPR Database")
                st.dataframe(df_wpr, use_container_width=True, hide_index=True)
            else:
                st.info("No WPR data available.")
        except Exception as e:
            st.error(f"Dashboard Error: {e}")

# -------------------- MAIN APP --------------------
def main():
    st.set_page_config(page_title="Onsite Reporting System", layout="wide")
    if "logged_in" not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        return

    try:
        obs, permit, equip, veh, wpr = get_sheets()
    except Exception as e:
        st.error(f"Google Sheets Connection Failed: {e}")
        return

    choice = sidebar()

    if choice == "🏠 Home":
        st.title("📋 Onsite Reporting System")
        st.write(f"Welcome, **{st.session_state.username}**!")
        st.info("System is active. Use the sidebar to navigate.")

    elif choice == "📝 Observation Form":
        show_observation_form(obs)

    elif choice == "🛠️ Permit Form":
        show_permit_form(permit)

    elif choice == "🪪 WPR Master":
        show_wpr_master_form(wpr)

    elif choice == "🚜 Heavy Equipment":
        show_equipment_form(equip)

    elif choice == "🚚 Heavy Vehicle":
        show_heavy_vehicle_form(veh)

    elif choice == "📊 Dashboard":
        if st.session_state.role == "admin":
            show_combined_dashboard(obs, permit, equip, veh, wpr)
        else:
            st.warning("🚫 Access Denied: Admin only.")

    elif choice == "🚪 Logout":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
