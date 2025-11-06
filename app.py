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

# --- MASTER SITE LIST ---
ALL_SITES = [
    "1858", "1969", "1972", "2433", "2447", "2485", 
    "2534", "2549", "2553", "2556", "2566","2570","HRDH Laydown","2595"
]
# ------------------------

# -------------------- UTILITIES --------------------
def parse_date(s):
    """Safely parses a string into a date object, trying multiple formats."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    # Try parsing the new format first, then fall back to the old one for existing data
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).split(' ')[0], fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def badge_expiry(d, expiry_days=30): # <--- MODIFIED
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
        "PWAS Status", "Seat belt damaged", "Tyre Condition",
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
        date_format = "%d-%b-%Y"
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime(date_format)
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime(date_format)
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime(date_format)
        fe_tp_expiry = cols_dates[1].date_input("F.E TP expiry").strftime(date_format)
        tp_card_expiry = cols_dates[0].date_input("T.P Card expiry date").strftime(date_format)

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

#--------------------------------------------------------------- HSE OBSERVATION FORM-----------------------------------------------------------------------------------------------
def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    # Note: well_numbers list was removed and replaced with ALL_SITES from top of file
    
    OBSERVER_NAMES = [
        "Ajish", "Akhil Mohan", "Aqib", "Arfan", "Asim", "Ashraf Khan", "Bijo",
        "Felin", "Habeeb", "Ilyas", "Irfan", "Jamali", "Joseph Cruz", "Mohsin",
        "Pradeep", "Rajshekar", "Ricken", "Shiva Kannan", "Shiva Subramaniyam",
        "Sudheesh", "Vaishak", "Vargheese", "Wali Alam", "Zaheer"
    ]
    
    AREAS = [
        "Well Head", "Flow Line", "OHPL", "Tie In", 
        "Lay Down", "Cellar", "Remote Header"
    ]

    CATEGORIES = [
        "Fall Protection/Personal Fall Arrest System Use/Falling Hazard",
        "Trenching/Excavation/Shoring",
        "Scaffolds, Ladders and Elevated work platforms",
        "Crane and Lifting Devices",
        "Heavy Equipment",
        "Vehicles / Traffic Control",
        "Hand/Power Tools and Electrical appliances",
        "Electrical Safety",
        "Hot work (Cutting/Welding/Brazing)",
        "Fire prevention & Protection",
        "Abrasive Blasting and Coating",
        "Confined Space / Restricted area",
        "Civil, Concrete Work",
        "Compressed Gases",
        "General Equipment's (Air Compressors/Power Generator etc.)",
        "Work Permit, Risk Assessment, JSA & other procedures",
        "Chemical Handling and Hazardous material",
        "Environmental / Waste Management",
        "Health, hygiene & welfare",
        "Radiation and NDT",
        "Security, Unsafe Behavior, and other project Requirements"
    ]

    SUPERVISOR_TRADE_MAP = {
        "ANILKUMAR JANARDHANAN": "CONTROLLER-EQUIPMENT", "MANOJ THOMAS": "SUPERVISOR-SCAFFOLDING",
        "SIVA PRASAD PILLAI": "WELL IN CHARGE", "JAYAN RAJANAN": "FOREMAN-PIPING",
        "JAYAN PONNAN": "FOREMAN-PIPING", "MURUGAN VELAYUDHAN PERUMAL": "CONSTRUCTION-FOREMAN",
        "RAJEEVAN NAIR THANKAPPAN": "QA/QC INSPECTOR-CIVIL", "MOHAMMAD ALI SHAIKH": "FOREMAN-PAINTING (C.P)",
        "JEFFREY F. TABAMO": "CONSTRUCTION SUPERVISOR-E & I", "SHIVA PRASANTH": "SUPERVISOR-CIVIL",
        "ORLANDO GURGUD": "SUPERVISOR-PAINTING CREW", "BHASKARAN PILLAI BIMAL": "SUPERVISOR-PAINTING CREW",
        "MD MUBARAK MIAH": "QC INSPECTOR-PIPING", "MD MOSTACIMUR RAHMAN": "ELECTRICIAN",
        "SHAHID KHAN": "ELECTRICIAN", "AHMAL SUHAIB": "SUPERVISOR-PIPING",
        "MOHAMMED SALIM WAHIM": "SUPERVISOR-SAFETY", "SAHAJAHAN SHAIK": "CONSTRUCTION SUPERVISOR-CIVIL",
        "AHMED SABIT": "QC INSPECTOR-COATING", "BHUTULI KUMAR": "SCAFFOLDER",
        "BIBIN CHERIAN": "SUPERVISOR-CIVIL", "JOUHAR HUSSAIN": "QC INSPECTOR-INSTRUMENTATION",
        "KARTHIK KOTTUKKAL UDHAYAKUMAR": "QC INSPECTOR-WELDING", "MOHD ILYAS": "CONSTRUCTION SUPERVISOR-PIPING",
        "VIJENDER KUMAR BEHARI": "QC INSPECTOR-ELECTRICAL", "AZAGAR SHAHUL AHAN": "ELECTRICIAN",
        "SHAHIN": "SCAFFOLDER", "PREM KUMAR CHAUDHARY": "FOREMAN-E&I",
        "MD SABUJ MOLLAH": "SCAFFOLDER", "ROUF MD ABDUL RASHID": "QC INSPECTOR-INSTRUMENTATION",
        "SAJU SADANANDAN": "SUPERVISOR-CIVIL", "CHANDU RAMAMURTHI": "QC INSPECTOR-MECHANICAL",
        "KRISHNA BK": "SCAFFOLDER", "SASIDHARA KURUP": "FOREMAN-ELECTRICAL",
        "SELVIN SEBASTIAN": "CONSTRUCTION SUPERVISOR-E & I", "REPLY MENDOZA SILVESTRE": "QC INSPECTOR-PIPING",
        "SELVIN LEO SELVARAJ": "WELL IN CHARGE", "ANSELITO LABAL LURG": "QC INSPECTOR-COATING",
        "SWAMY NAGA VAMSI": "SCAFFOLDER", "BRIHASPATI ADAK": "FOREMAN-CIVIL",
        "JEROME GUEVARRA VILLAVER ROA": "QC INSPECTOR-ELECTRICAL (C.P)",
        "IBRAHIM IMAM DIMACALING": "QC INSPECTOR-CIVIL (BATCHING PLANT)", "VISHNU S": "CONSTRUCTION SUPERVISOR-CIVIL",
        "RABIN THAKUR BARAHI": "SCAFFOLDER", "MOHAMMAD AJMAL": "ELECTRICIAN",
        "MOHAMMAD ANAS ABDUL SALAM": "QC INSPECTOR-WELDING", "NOLI BADAYO DIVINO": "QC INSPECTOR-ELECTRICAL",
        "RAVI SINGH": "SUPERVISOR-CIVIL", "MOHAMMAD NAWAZ BARI": "QA/QC INSPECTOR-CIVIL",
        "JUBARAJ KONDAGORLA": "SCAFFOLDER", "ALLAN MENDOZA ALFELOR": "QC INSPECTOR-PIPING",
        "ANVAR MOHAMMED MANEEFA": "QC SUPERVISOR-CIVIL", "BALAKRISHNA": "FOREMAN-CIVIL",
        "SUNIL KUMAR SAHU": "FOREMAN-CIVIL", "GEORGE ELAVUMPARAMBIL JOSY": "QC INSPECTOR-ELECTRICAL",
        "MARCELING PODRIGUEZ SIANO": "QC INSPECTOR-TELECOM", "RAJESHWAR RAO NARAPAKA": "SUPERVISOR-SCAFFOLDING",
        "MUMTAZ ALAM": "FOREMAN-INSTRUMENTATION", "ASHIQUE AHMED YADAV": "FOREMAN-CIVIL",
        "QUAISAR ALI": "SUPERVISOR-ELECTRICAL", "ASHISH SINGH DHARAN": "FOREMAN-PIPING",
        "ZEESHAN YOUSUF": "SUPERVISOR-CIVIL", "PRADEEP PRASAD": "SCAFFOLDER",
        "SHIV MOHITO": "SCAFFOLDER (FIREWATCH)", "MOHAMMAD RAUSHAN": "SUPERVISOR-CIVIL",
        "AHMED ELTAYIB SIDEEG ALI": "SUPERVISOR-CIVIL", "SRIVENKATESWARARAO ATIKE": "SUPERVISOR-SAFETY",
        "AKRAM RAZZAK BIDI": "FOREMAN-SCAFFOLDING", "SURESH KUMAR": "WELL IN CHARGE",
        "SENTHIL NATH": "FOREMAN-CIVIL", "ANOOPKUMAR": "SUPERVISOR-ELECTRICAL",
        "VAIBHAV VINOD GIREJA": "SUPERVISOR-PIPING", "KHALID AHMED ABDULLAH BIN BATI": "ELECTRICIAN",
        "MOHAMMED MARDI NAHAR ALRELEI": "ELECTRICIAN", "IBRAHIM SOLDEV IBRAHIM SUWAYWAT": "ELECTRICIAN",
        "ABDULLAH SAAD BIN HASSAN ALHADHOUD": "SCAFFOLDER", "MOHAMMED ESSAM HUSSEIN ELSHAMI": "ELECTRICIAN",
        "Murtadha Hussein ALSaqer": "QC INSPECTOR-PIPING", "SURYA PRATAP": "CONSTRUCTION SUPERVISOR-PIPING",
        "WASEEM ABBAS KHADIM HUSSAIN": "QA/QC INSPECTOR-CIVIL", "LALIT KUMAR": "FOREMAN-INSTRUMENTATION",
        "JEROME HIGOY VALDEZ": "QC SUPERVISOR-E&I", "SREEDHARAN PARAMESHETHAN": "QC SUPERVISOR-PIPING",
        "RAJA ALAGAPPAN": "SUPERVISOR-PAINTING CREW", "UMASHANKER SAH": "QC INSPECTOR-WELDING",
        "AJITHKUMAR": "SUPERVISOR-PIPING","PAWAN":"SUPERVISOR-PIPING","AJMAL":"WELL IN CHARGE","SUMOD":"SURVEY","JITHIN JOHN":"SUPERVISOR-PIPING"
    }
    
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
            # --- MODIFIED LINE ---
            well_no = st.selectbox("Well No", ALL_SITES) # Uses the master ALL_SITES list
            supervisor_name = st.selectbox("Supervisor Name", supervisor_names)
            trade = SUPERVISOR_TRADE_MAP.get(supervisor_name, "")
            discipline = st.text_input("Discipline", value=trade, disabled=True)
            status = st.selectbox("Status", ["Open", "Closed"])
        
        obs_details = st.text_area("Observation Details")
        rec_action = st.text_area("Recommended Action")

        if st.form_submit_button("Submit"):
            data = [
                form_date.strftime("%d-%b-%Y"),
                well_no,
                area,
                observer_name,
                obs_details,
                rec_action,
                supervisor_name,
                discipline,
                category,
                classification,
                status
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    
    # Note: DRILL_SITES list was removed and replaced with ALL_SITES from top of file
    
    WORK_LOCATIONS = [
        "Well Head", "OHPL", "E&I Skid", "Burn Pit", "Cellar",
        "Flow Line", "Lay down", "CP area"
    ]
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
        "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC", "SHAHWAZ KHAN","PACIFICO LUBANG ICHON"
    ]

    with st.form("permit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_val = st.date_input("Date")
            # --- MODIFIED LINE ---
            drill_site = st.selectbox("Drill Site", ALL_SITES) # Uses the master ALL_SITES list
            work_location = st.selectbox("Work Location", WORK_LOCATIONS)
            permit_receiver = st.selectbox("Permit Receiver", PERMIT_RECEIVERS)

        with col2:
            permit_no = st.text_input("Permit No")
            permit_type = st.selectbox("Type of Permit", PERMIT_TYPES)
            permit_issuer = st.selectbox("Permit Issuer", PERMIT_ISSUERS)

        activity = st.text_area("Activity")

        if st.form_submit_button("Submit"):
            data = [
                date_val.strftime("%d-%b-%Y"), # Column A: DATE
                drill_site,                # Column B: DRILL SITE
                work_location,             # Column C: WORK LOCATION
                permit_no,                 # Column D: PERMIT NO
                permit_type,               # Column E: TYPE OF PERMIT
                activity,                  # Column F: ACTIVITY
                permit_receiver,           # Column G: PERMIT RECEIVER
                permit_issuer              # Column H: PERMIT ISSUER
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
        
        st.subheader("Vehicle & Driver Information")
        c1, c2 = st.columns(2)
        vehicle_type = c1.selectbox("Vehicle Type", VEHICLE_LIST)
        make = c2.text_input("Make")
        plate_no = c1.text_input("Plate No")
        asset_code = c2.text_input("Asset Code")
        owner = c1.text_input("Owner")
        qr_code = c2.text_input("Q.R code")
        driver_name = c1.text_input("Driver Name")
        iqama_no = c2.text_input("Iqama No")

        st.subheader("Expiry Dates")
        d1, d2 = st.columns(2)
        date_format = "%d-%b-%Y"
        mvpi_expiry = d1.date_input("MVPI Expiry date").strftime(date_format)
        insurance_expiry = d2.date_input("Insurance Expiry").strftime(date_format)
        licence_expiry = d1.date_input("Licence Expiry").strftime(date_format)
        # fire_ext_tp_expiry = d2.date_input("Fire Extinguisher T.P Expiry").strftime(date_format)

        st.subheader("Condition & Status")
        s1, s2 = st.columns(2)
        fa_box = s1.selectbox("F.A Box", ["Available", "Not Available", "Expired", "Inadequate Medicine"])
        pwas_status = s2.selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        seatbelt_damaged = s1.selectbox("Seat belt damaged", ["Yes", "No", "N/A"])
        tyre_condition = s2.selectbox("Tyre Condition", ["Good", "Worn Out", "Damaged", "Needs Replacement", "N/A"])
        suspension_systems = s1.selectbox("Suspension Systems", ["Good", "Faulty", "Needs Repair", "DamDamaged", "N/A"])
        
        remarks = st.text_area("Remarks")

        if st.form_submit_button("Submit"):
            data = [
                vehicle_type, make, plate_no, asset_code, owner, 
                mvpi_expiry, insurance_expiry,
                driver_name, iqama_no, licence_expiry,
                qr_code, fa_box, 
                pwas_status, seatbelt_damaged, tyre_condition,
                suspension_systems, remarks
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Heavy Vehicle submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- ADVANCED DASHBOARD (MODIFIED) --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])

    with tab_permit:
        st.subheader("Advanced Permit Log Analytics")
        try:
            df_permit = pd.DataFrame(permit_sheet.get_all_records())
            # Ensure column names are consistent and uppercase for easier access
            df_permit.columns = [str(col).strip().upper() for col in df_permit.columns]
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load permit data from Google Sheets: {e}")
            return

        if df_permit.empty:
            st.info("No permit data available to display.")
            return

        # --- Data Cleaning and Preparation ---
        if 'DATE' not in df_permit.columns:
            st.warning("The 'DATE' column is missing from the Permit Log sheet.")
            return

        df_permit['DATE'] = pd.to_datetime(df_permit['DATE'], errors='coerce')
        df_permit.dropna(subset=['DATE'], inplace=True)
        df_permit = df_permit.sort_values(by='DATE', ascending=False)

        # --- Interactive Filters ---
        st.markdown("#### Filter & Explore")
        with st.expander("Adjust Filters", expanded=True):
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                min_date = df_permit['DATE'].min().date()
                max_date = df_permit['DATE'].max().date()
                date_range = st.date_input(
                    "Select Date Range",
                    (min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="permit_date_range"
                )

            with col_filter2:
                # Check if columns exist before creating filters
                permit_types = df_permit['TYPE OF PERMIT'].unique() if 'TYPE OF PERMIT' in df_permit.columns else []
                selected_types = st.multiselect("Filter by Permit Type", options=permit_types, default=permit_types)

                issuers = df_permit['PERMIT ISSUER'].unique() if 'PERMIT ISSUER' in df_permit.columns else []
                selected_issuers = st.multiselect("Filter by Permit Issuer", options=issuers, default=issuers)

        # --- Apply Filters to DataFrame ---
        # Handle date range selection for filtering
        start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        # Create a boolean mask for each filter
        mask = (df_permit['DATE'] >= start_datetime) & (df_permit['DATE'] <= end_datetime)
        if selected_types and 'TYPE OF PERMIT' in df_permit.columns:
            mask &= df_permit['TYPE OF PERMIT'].isin(selected_types)
        if selected_issuers and 'PERMIT ISSUER' in df_permit.columns:
            mask &= df_permit['PERMIT ISSUER'].isin(selected_issuers)

        df_filtered = df_permit[mask]

        if df_filtered.empty:
            st.warning("No data matches the selected filters.")
            return

        # --- High-Level KPIs ---
        st.markdown("---")
        st.markdown("#### Key Metrics Overview")

        total_permits = len(df_filtered)
        hot_permits_count = 0
        if 'TYPE OF PERMIT' in df_filtered.columns:
            hot_permits_count = df_filtered[df_filtered['TYPE OF PERMIT'].str.contains("Hot", case=False)].shape[0]

        hot_permits_perc = (hot_permits_count / total_permits * 100) if total_permits > 0 else 0
        busiest_day = df_filtered['DATE'].dt.day_name().mode()[0] if not df_filtered.empty else "N/A"
        active_receivers = df_filtered['PERMIT RECEIVER'].nunique() if 'PERMIT RECEIVER' in df_filtered.columns else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Permits (in range)", f"{total_permits}")
        kpi2.metric("Hot Permits %", f"{hot_permits_perc:.1f}%")
        kpi3.metric("Busiest Day", busiest_day)
        kpi4.metric("Active Permit Receivers", f"{active_receivers}")
        st.markdown("---")

        # --- Visualizations ---
        st.markdown("#### Visual Insights")
        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
            if 'TYPE OF PERMIT' in df_filtered.columns:
                st.write("**Permit Type Distribution**")
                fig_type_pie = px.pie(
                    df_filtered, names='TYPE OF PERMIT', hole=0.4,
                )
                fig_type_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_type_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_type_pie, use_container_width=True)

            # -------------------- START: ADVANCED GRAPH (FINAL FIX) --------------------
            # Check if both columns needed for the stacked bar chart exist
            if 'DRILL SITE' in df_filtered.columns and 'TYPE OF PERMIT' in df_filtered.columns:
                st.write("**Permit Composition by Drill Site**")
                
                # Group by both drill site and permit type to get counts for stacking
                site_permit_counts = df_filtered.groupby(['DRILL SITE', 'TYPE OF PERMIT']).size().reset_index(name='count')
                
                # --- THIS IS THE NEW FIX ---
                # Convert DRILL SITE to a categorical type based on ALL_SITES
                # This ensures all sites are present on the axis, in the correct order.
                site_permit_counts['DRILL SITE'] = pd.Categorical(
                    site_permit_counts['DRILL SITE'],
                    categories=ALL_SITES,
                    ordered=True
                )
                # Drop any rows that might not be in our master ALL_SITES list
                site_permit_counts = site_permit_counts.dropna(subset=['DRILL SITE'])
                # ---------------------------

                fig_site_stacked = px.bar(
                    site_permit_counts, 
                    x='DRILL SITE', 
                    y='count', 
                    color='TYPE OF PERMIT',  # This creates the stack
                    title="Permit Type Breakdown per Site",
                    text_auto=True,
                    labels={
                        'count': 'Total Permits', 
                        'DRILL SITE': 'Drill Site', 
                        'TYPE OF PERMIT': 'Permit Type'
                    }
                )
                fig_site_stacked.update_layout(
                    barmode='stack', # Ensure bars are stacked
                    margin=dict(l=20, r=20, t=40, b=20) # Adjust top margin for title
                )
                st.plotly_chart(fig_site_stacked, use_container_width=True)
            
            # Fallback to the simple bar chart if 'TYPE OF PERMIT' column is missing
            elif 'DRILL SITE' in df_filtered.columns:
                st.write("**Total Permits by Drill Site**")
                site_counts = df_filtered['DRILL SITE'].value_counts().reset_index()

                # --- APPLY THE SAME FIX HERE ---
                # Convert to categorical to ensure all sites are shown in order
                site_counts['DRILL SITE'] = pd.Categorical(
                    site_counts['DRILL SITE'],
                    categories=ALL_SITES,
                    ordered=True
                )
                site_counts = site_counts.dropna(subset=['DRILL SITE'])
                # ---------------------------

                fig_site = px.bar(
                    site_counts, x='DRILL SITE', y='count', text_auto=True,
                    title="Total Permits per Drill Site",
                    labels={'count': 'Count', 'DRILL SITE': 'Drill Site'}
                )
                fig_site.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_site, use_container_width=True)
            # -------------------- END: ADVANCED GRAPH --------------------


        with col_viz2:
            if 'PERMIT ISSUER' in df_filtered.columns:
                st.write("**Permit Count by Issuer**")
                issuer_counts = df_filtered['PERMIT ISSUER'].value_counts().reset_index()
                fig_issuer_bar = px.bar(
                    issuer_counts,
                    x='PERMIT ISSUER',
                    y='count',
                    text_auto=True,
                    labels={'count': 'Number of Permits', 'PERMIT ISSUER': 'Issuer Name'}
                )
                fig_issuer_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_issuer_bar, use_container_width=True)

            if 'PERMIT RECEIVER' in df_filtered.columns:
                st.write("**Top 10 Permit Receivers**")
                receiver_counts = df_filtered['PERMIT RECEIVER'].value_counts().nlargest(10).reset_index()
                fig_receiver = px.bar(
                    receiver_counts, y='PERMIT RECEIVER', x='count', orientation='h', text_auto=True,
                    labels={'count': 'Count', 'PERMIT RECEIVER': 'Receiver Name'}
                )
                fig_receiver.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_receiver, use_container_width=True)
                
        # --- Time Series Analysis ---
        st.markdown("---")
        st.write("#### Permit Trend Over Time")
        permits_by_day = df_filtered.groupby(df_filtered['DATE'].dt.date).size().reset_index(name='count')
        fig_time = px.line(
            permits_by_day, x='DATE', y='count', markers=True,
            labels={'DATE': 'Date', 'count': 'Number of Permits'}
        )
        fig_time.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_time, use_container_width=True)

        # --- Full Data Table ---
        st.markdown("---")
        st.markdown("#### Detailed Permit Log (Filtered)")
        df_display_permit = df_filtered.copy()
        df_display_permit['DATE'] = df_display_permit['DATE'].dt.strftime('%d-%b-%Y')
        st.dataframe(df_display_permit, use_container_width=True)

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

        date_cols = ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]
        for col in date_cols:
                if col in df_equip.columns:
                        df_equip[col] = df_equip[col].apply(parse_date)

        today = date.today()
        thirty_days = today + timedelta(days=30) # <--- MODIFIED

        # -------------------- EXPIRY TRACKING TABLE --------------------
        st.subheader("🚨 Equipment Document Expiry Alerts")

        # Define columns to identify the equipment and columns to check for expiry
        id_cols = ["Equipment type", "Palte No.", "Owner", "Operator Name"]
        
        # Filter to only include columns that actually exist in the sheet
        existing_id_cols = [c for c in id_cols if c in df_equip.columns]
        existing_date_cols = [c for c in date_cols if c in df_equip.columns]

        if not existing_date_cols or not existing_id_cols:
            st.warning("Could not generate alerts. Key identifier or date columns are missing from the sheet.")
        else:
            # Melt the DataFrame to turn date columns into rows
            df_long = df_equip.melt(
                id_vars=existing_id_cols, 
                value_vars=existing_date_cols, 
                var_name="Document Type", 
                value_name="Expiry Date"
            )

            # Remove items where the date was never set
            df_long.dropna(subset=['Expiry Date'], inplace=True)

            # Filter for items that are expired or expiring within 30 days
            df_alerts = df_long[df_long['Expiry Date'] <= thirty_days].copy() # <--- MODIFIED

            if df_alerts.empty:
                st.success("✅ No documents are expired or expiring within 30 days.") # <--- MODIFIED
            else:
                # Add a status column for clarity
                df_alerts['Status'] = df_alerts['Expiry Date'].apply(
                    lambda d: "🚨 Expired" if d < today else "⚠️ Expiring Soon"
                )
                
                # Format date for display
                df_alerts['Expiry Date'] = df_alerts['Expiry Date'].apply(lambda d: d.strftime('%d-%b-%Y'))
                
                # Sort by Status (Expired first) then by date
                df_alerts = df_alerts.sort_values(by=["Status", "Expiry Date"])
                
                display_cols = [
                    "Equipment type", 
                    "Palte No.", 
                    "Document Type", 
                    "Expiry Date", 
                    "Status", 
                    "Operator Name", 
                    "Owner"
                ]
                
                # Filter display_cols to only include columns that actually exist in df_alerts
                final_cols = [col for col in display_cols if col in df_alerts.columns]
                
                st.dataframe(df_alerts[final_cols], use_container_width=True)
        # ---------------------------------- END OF TABLE ----------------------------------

        st.markdown("---")

        total_equipment = len(df_equip)
        expired_count = 0
        expiring_soon_count = 0

        for col in date_cols:
                if col in df_equip.columns:
                        # Use .loc to ensure we are checking the parsed date column
                        expired_count += df_equip.loc[df_equip[col] < today].shape[0]
                        expiring_soon_count += df_equip.loc[(df_equip[col] >= today) & (df_equip[col] <= thirty_days)].shape[0] # <--- MODIFIED

        kpi1_eq, kpi2_eq, kpi3_eq = st.columns(3)
        kpi1_eq.metric(label="Total Equipment", value=total_equipment)
        kpi2_eq.metric(label="Total Expired Items", value=expired_count, delta="Action Required", delta_color="inverse")
        kpi3_eq.metric(label="Expiring in 30 Days", value=expiring_soon_count, delta="Monitor Closely", delta_color="off") # <--- MODIFIED
        
        st.markdown("---")
        
        st.subheader("Visual Insights")
        c1_eq, c2_eq = st.columns(2)

        with c1_eq:
            if 'Equipment type' in df_equip.columns:
                fig_type_eq = px.bar(
                    df_equip['Equipment type'].value_counts().reset_index(),
                    x='Equipment type', y='count', title='Equipment Distribution by Type',
                    labels={'count': 'Number of Units', 'Equipment type': 'Type'},
                    text_auto=True 
                )
                fig_type_eq.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_type_eq, use_container_width=True)

        with c2_eq:
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
        
        st.subheader("Full Heavy Equipment Data")
        df_display_eq = df_equip.copy()
        for col in date_cols:
                if col in df_display_eq.columns:
                        df_display_eq[col] = df_display_eq[col].apply(badge_expiry, expiry_days=30) # <--- MODIFIED
        
        st.dataframe(df_display_eq, use_container_width=True)

    with tab_obs:
        st.subheader("Observation Analytics")
        st.info("Observation dashboard is under construction.")
        # Placeholder for observation analytics

    with tab_veh:
        st.subheader("Heavy Vehicle Analytics")
        st.info("Heavy Vehicle dashboard is under construction.")
        # Placeholder for heavy vehicle analytics

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


