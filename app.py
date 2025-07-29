import streamlit as st
from google.oauth2 import service_account
import gspread
from datetime import datetime

# Set page config
st.set_page_config(page_title="Web Form", layout="centered")

# Authenticate using Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

client = gspread.authorize(creds)
sheet = client.open("HSE OBS").sheet1  # Replace with your sheet name

# Streamlit UI
st.title("📋 Feedback Form")

with st.form("entry_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Your Feedback")
    submit = st.form_submit_button("Submit")

    if submit:
        if name and email and message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, name, email, message])
            st.success("✅ Your feedback was submitted successfully!")
        else:
            st.warning("Please fill out all fields.")
