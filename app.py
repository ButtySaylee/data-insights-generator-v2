import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from fpdf import FPDF
import gspread
#from googletrans import Translator
from oauth2client.service_account import ServiceAccountCredentials
import base64
import time
import os
import re
from datetime import datetime
from io import StringIO
import hashlib
import secrets


# Function to connect to Google Sheets
def connect_to_google_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = {
        "type": st.secrets["connections"]["gsheets"]["type"],
        "project_id": st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"],
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"]
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

# Function to hash passwords with a salt for better security
def hash_password(password, salt):
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

# Function to create a new user account in Google Sheet
def create_user_account(school_id, password, email):
    try:
        sheet = connect_to_google_sheet("Apnapan User Accounts")
        # Check if school_id already exists
        cell = sheet.find(school_id, in_column=1)
        if cell:
            return False, "School ID already exists."

        # If cell is None, the ID is not found, so we can proceed.
        # Generate a salt and hash the password
        salt = secrets.token_hex(16)
        hashed_password = hash_password(password, salt)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Append new user data including the salt. Ensure your GSheet has a 'Salt' column.
        sheet.append_row([school_id, hashed_password, salt, email, timestamp])
        return True, "Account created successfully!"
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

# Function to validate login credentials
def validate_login(school_id, password):
    """Validates user login using salted password hashes."""
    try:
        sheet = connect_to_google_sheet("Apnapan User Accounts")
        cell = sheet.find(school_id, in_column=1)
        if cell:
            user_data = sheet.row_values(cell.row)
            # Assuming columns are: School ID (1), Password (2), Salt (3)
            stored_hash = user_data[1]
            salt = user_data[2]

            # Hash the provided password with the stored salt and compare
            hashed_input_password = hash_password(password, salt)
            if hashed_input_password == stored_hash:
                return True, "Login successful!"
            else:
                return False, "Invalid password."
        else:
            return False, "School ID not found."

    except Exception as e:
        return False, f"Error validating login: {str(e)}"

# Function to validate user for password reset
def validate_reset_request(school_id, email):
    """Checks if the school_id and email match a record."""
    try:
        sheet = connect_to_google_sheet("Apnapan User Accounts")
        cell = sheet.find(school_id, in_column=1)
        if cell:
            user_data = sheet.row_values(cell.row)
            # Assuming columns: School ID (1), Password (2), Salt (3), Email (4)
            stored_email = user_data[3]
            if email.strip().lower() == stored_email.strip().lower():
                return True, "Verification successful. Please set your new password."
            else:
                return False, "The email address provided does not match our records for this School ID."
        else:
            return False, "School ID not found."
    except Exception as e:
        return False, f"An error occurred during verification: {str(e)}"

# Function to update user password in the sheet
def update_user_password(school_id, new_password):
    """Finds a user by school_id and updates their password."""
    try:
        sheet = connect_to_google_sheet("Apnapan User Accounts")
        cell = sheet.find(school_id, in_column=1)
        if cell:
            user_data = sheet.row_values(cell.row)
            # Assuming Salt is in column 3
            salt = user_data[2]
            new_hashed_password = hash_password(new_password, salt)
            sheet.update_cell(cell.row, 2, new_hashed_password)  # Update password in column 2
            return True, "Password has been updated successfully!"
        else:
            # This case should ideally not be hit if the flow is correct
            return False, "School ID not found. Could not update password."
    except Exception as e:
        return False, f"An error occurred while updating password: {str(e)}"

# Set page config for mobile-friendly design
st.set_page_config(layout="wide", page_title="Data Insights Generator")

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'login'
    
# Define the navigate_to function
def navigate_to(page):
    st.session_state['current_page'] = page
    
# Custom CSS for consistent theme and centering
st.markdown("""
    <style>
        .stApp {
            background-color: #d6ecf9;
            font-family: 'Segoe UI', sans-serif;
            color: black !important;
        }
        h1, h2, h3, h4 {
            color: #003366 !important;
        }
        .stTextInput > div > div > input {
            background-color: #ff6666 !important;
            color: white !important;
            border-radius: 20px !important;
            padding: 12px !important;
            border: none !important;
            font-size: 16px !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: white !important;
            opacity: 0.8 !important;
        }
        .forgot-link {
            color: #ff6666 !important;
            font-size: 14px;
            text-decoration: none;
        }
        .pulse-text {
            text-align: center;
            font-size: 18px;
            color: #ff6666;
            margin-top: 20px;
        }
        .bubble {
            background-color: #ff9999;
            color: #003366;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-left: 8px;
        }
        .stTextInput label {
            color: black !important;
        }

        button, .stDownloadButton button {{
            background-color: #ff6666 !important;
            color: white !important;
            border-radius: 8px;
        }}

        /* Ensure text inside all buttons is white */
        div[data-testid="stForm"] button p,
        div[data-testid="stButton"] > button p {
            color: white !important;
        }

        /* Hover effect for all buttons */
        div[data-testid="stForm"] button:hover,
        div[data-testid="stButton"] > button:hover {
            background-color: #333333 !important; /* Slightly lighter black on hover */
        }
    </style>
""", unsafe_allow_html=True)
    
# Login Page
if st.session_state['current_page'] == 'login':
    # Load and encode logo
    logo_base64 = ""
    logo_path = "images/project_apnapan_logo.png"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as img_file:
                logo_base64 = base64.b64encode(img_file.read()).decode()
            print(f"Logo loaded successfully: {logo_path}, length: {len(logo_base64)}")
        except Exception as e:
            print(f"Error loading logo: {e}")
    else:
        print(f"Logo file not found: {logo_path}")

    # Display title and logo
    st.markdown("<h1 style='text-align: center; color: white;'>Apnapan Pulse</h1>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-bottom: 30px;">
        <img src="data:image/png;base64,{logo_base64}" alt="Project Apnapan Logo" style="height: 100px;" />
    </div>
    """, unsafe_allow_html=True)

    # Login form container
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: black;'>Log in credentials</h3>", unsafe_allow_html=True)

    with st.form(key="login_form"):
    # Center the input fields using columns
        col1, col2, col3 = st.columns([1, 2, 1])  # Left padding, content, right padding
        with col2:  # Center the input fields
            school_id = st.text_input("School ID", placeholder="Enter your school ID", key="school_id")
            password = st.text_input("Password", placeholder="Enter your security pin", type="password", key="password")
            
            login_button = st.form_submit_button("Find your pulse!", use_container_width=True)

            # Use columns for the other two actions
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                create_account_button = st.form_submit_button("Create Account", use_container_width=True, help="Click to create a new account")
            with col_b2:
                forgot_password_button = st.form_submit_button("Forgot Password?", use_container_width=True, help="Click to reset your password")

            if forgot_password_button:
                navigate_to('forgot_password')
                    
        # Add custom CSS to reduce the size of the "Show Password" text
        st.markdown("""
        <style>
            label[for="password"] {
                font-size: 12px !important; /* Reduce font size */
                color: #666 !important; /* Optional: Change color */
            }
        </style>
        """, unsafe_allow_html=True)

        if login_button:
            success, message = validate_login(school_id, password)
            if success:
                st.success(message)
                navigate_to('landing')
                st.rerun()
            else:
                st.error(message)

        if create_account_button:
            navigate_to('create_account')
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
    
# Create Account Page
if st.session_state['current_page'] == 'create_account':
    st.title("Create Account")
    st.write("Fill in the details below to create a new account.")

    with st.form(key="create_account_form"):
        new_school_id = st.text_input("School ID", placeholder="Enter your school ID")
        new_password = st.text_input("Password", placeholder="Enter your password", type="password")
        confirm_password = st.text_input("Confirm Password", placeholder="Re-enter your password", type="password")
        email = st.text_input("Email", placeholder="Enter your email address")

        submitted = st.form_submit_button("Create Account")
        if submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            elif not new_school_id or not new_password or not email:
                st.error("All fields are required. Please fill in all the details.")
            else:
                success, message = create_user_account(new_school_id, new_password, email)
                if success:
                    st.success(message)
                    navigate_to('login')
                    st.rerun()
                else:
                    st.error(message)

    if st.button("Back to Login", key="back_to_login_from_create"):
        navigate_to('login')
        st.rerun()

    st.stop()

# Forgot Password Page
if st.session_state['current_page'] == 'forgot_password':
    st.title("Reset Your Password")

    # Initialize state for the multi-step form
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1
    if 'reset_school_id' not in st.session_state:
        st.session_state.reset_school_id = None

    # Step 1: Verify User
    if st.session_state.reset_step == 1:
        st.write("Enter your School ID and registered email to verify your account.")
        with st.form(key="verify_user_form"):
            school_id = st.text_input("School ID", placeholder="Enter your school ID")
            email = st.text_input("Registered Email", placeholder="Enter the email you signed up with")
            
            submitted = st.form_submit_button("Verify Account")
            if submitted:
                if not school_id or not email:
                    st.error("Please enter both your School ID and email address.")
                else:
                    success, message = validate_reset_request(school_id, email)
                    if success:
                        st.session_state.reset_school_id = school_id
                        st.session_state.reset_step = 2
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    # Step 2: Set New Password
    elif st.session_state.reset_step == 2:
        st.write(f"Account verified for School ID: **{st.session_state.reset_school_id}**")
        st.write("You can now set a new password.")
        with st.form(key="set_new_password_form"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            submitted = st.form_submit_button("Set New Password")
            if submitted:
                if not new_password or not confirm_password:
                    st.error("Please fill out both password fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match. Please try again.")
                else:
                    success, message = update_user_password(st.session_state.reset_school_id, new_password)
                    if success:
                        st.success(message)
                        st.info("You can now log in with your new password.")
                        # Reset state and prepare for navigation
                        del st.session_state.reset_step
                        del st.session_state.reset_school_id
                    else:
                        st.error(message)

    # Always show the back to login button, but handle state reset
    if st.button("Back to Login", key="back_to_login_from_forgot"):
        # Clean up state if user navigates away mid-process
        if 'reset_step' in st.session_state:
            del st.session_state.reset_step
        if 'reset_school_id' in st.session_state:
            del st.session_state.reset_school_id
        navigate_to('login')
        st.rerun()

    st.stop()

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'landing'

# Function to navigate to a specific page
def navigate_to(page):
    st.session_state['current_page'] = page

scale_base64 = ""
scale_path = "images/Likert_Scale.png"  # Make sure this matches your file name and location
if os.path.exists(scale_path):
    try:
        with open(scale_path, "rb") as img_file:
            scale_base64 = base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error loading Likert scale image: {e}")
else:
    print(f"Scale file not found: {scale_path}")


st.markdown("""
    <style>
    /* General fix for all checkbox labels */
    .stCheckbox div[data-testid="stMarkdownContainer"] > p {
        color: black !important;
        font-weight: 500;
    }
    /* Extra fallback for some Streamlit versions */
    .stCheckbox label {
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load and encode logo
logo_base64 = ""
logo_path = "images/project_apnapan_logo.png"  # Adjust this path to match your file location
if os.path.exists(logo_path):
    try:
        with open(logo_path, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode()
        print(f"Logo loaded successfully: {logo_path}, length: {len(logo_base64)}")
    except Exception as e:
        print(f"Error loading logo: {e}")
    else:
        print(f"Logo file not found: {logo_path}")

# Inject CSS for styling
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] label {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <style>
        .stApp {{
            background-color: #d6ecf9;
            font-family: 'Segoe UI', sans-serif;
            color: black !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            background-color: #def2e3;
            border-radius: 10px;
            padding: 1rem;
            color: black !important;
        }}
        h1, h2, h3, h4 {{
            color: #003366 !important;
        }}
        .stMetric label, .stMetric span {{
            color: #003366 !important;
        }}
        .stFileUploader {{
            border: 2px dashed #3366cc;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 10px;
            color: black;
        }}
        .custom-logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: -10px;
            margin-bottom: 20px;
        }}
        .custom-logo img {{
            height: 60px;
        }}
        .custom-logo span {{
            font-size: 26px;
            font-weight: bold;
            color: #003366;
        }}
        .block-container {{
            padding-top: 1.5rem;
        }}
        .stAlert p, .stAlert div, .stAlert {{
            color: black !important;
        }}
        .css-1cpxqw2, .css-ffhzg2 {{
            color: black !important;
        }}
        label, .stCheckbox > div, .stRadio > div, .stSelectbox > div,
        .stMultiSelect > div, .css-16idsys, .css-1r6slb0, .css-1n76uvr {{
            color: black !important;
        }}
    </style>
    <div class="custom-logo">
        <img src="data:image/png;base64,{logo_base64}" alt="Project Apnapan Logo" />
        <span>Project Apnapan</span>
    </div>
""", unsafe_allow_html=True)

# Sample dataset for preview (move this up!)
sample_data = pd.DataFrame({
    "StudentID": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "Gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
    "Grade": [10, 9, 11, 8, 12, 10, 9, 11, 10, 12],
    "Religion": ["Hindu", "Muslim", "Christian", "Sikh", "Hindu", "Buddhist", "Jain", "Islam", "Hindu", "Christian"],
    "Ethnicity_cleaned": ["Asian", "African", "Latin", "Asian", "African", "Latin", "Asian", "African", "Latin", "Asian"],
    "What_items_among_these_do_you_have_at_home": [
        "Car, Computer, Apna Ghar", "Laptop, Rent", "Apna Ghar", "Computer", "Car, Apna Ghar",
        "Rent", "Computer, Apna Ghar", "Laptop", "Car, Computer", "Apna Ghar"
    ],
    "Do_you_feel_safe_at_school": ["Agree", "Neutral", "Strongly Agree", "Disagree", "Agree", "Neutral", "Strongly Agree", "Disagree", "Agree", "Neutral"],
    "Do_you_feel_welcome_at_school": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Agree", "Neutral", "Strongly Agree", "Neutral", "Agree", "Disagree"],
    "Are_you_respected_by_peers": ["Neutral", "Agree", "Strongly Agree", "Neutral", "Agree", "Disagree", "Strongly Agree", "Neutral", "Agree", "Neutral"],
    "Do_teachers_notice_you": ["Disagree", "Neutral", "Agree", "Disagree", "Neutral", "Strongly Disagree", "Agree", "Disagree", "Neutral", "Disagree"],
    "Do_you_have_a_close_teacher": ["Agree", "Neutral", "Strongly Agree", "Disagree", "Agree", "Neutral", "Strongly Agree", "Disagree", "Agree", "Neutral"]
})


# Landing Page
if st.session_state['current_page'] == 'landing':
    st.title("Welcome to the Data Insights Generator!")
    st.write("Your journey to understanding students’ experiences begins here.")
    st.write("This easy-to-use tool is designed to help schools uncover meaningful insights about student belonging and well-being. Let’s get started!")
    
    st.markdown(
    """
    <div style="font-size:1.15rem;">
        <div style="margin-bottom: 10px;">
            <span style="font-size:1.25rem; font-weight:700; color:#003366;">Step-1:</span>
            <span style="font-weight:600;">Upload Your Data</span>
            <br>
            <span>
                Click on the
                <span style="color:#d7263d; font-weight:bold; background:#fff3cd; padding:2px 6px; border-radius:4px;">Browse File</span>
                button to upload your survey or student data.
            </span>
        </div>
        <div style="margin-bottom: 10px;">
            <span style="font-size:1.25rem; font-weight:700; color:#003366;">Step-2:</span>
            <span style="font-weight:600;"> 
                Explore the Insight Dashboard</span>
                <br>
                <span>Click on the </span><span style="color:#003366; font-weight:bold; background:#e6b0aa; padding:2px 6px; border-radius:4px;">Insight Dashboard</span>
                <span>to instantly view key trends, metrics, and patterns in your data.
            </span>
        </div>
        <div style="margin-bottom: 10px;">
            <span style="font-size:1.25rem; font-weight:700; color:#003366;">Step-3:</span>
            <span style="font-weight:600;">
                Discover Group-Level Insights</span>
                <br>
                <span>Head to the</span> <span style="color:#003366; font-weight:bold; background:#a3d8d3; padding:2px 6px; border-radius:4px;">Explore Belonging Across Groups</span>
                section to see how different student groups (based on gender, grade, religion, etc) experience belonging in your school.
            </span>
            </div>
            <div style="margin-bottom: 10px;">
                <span style="font-size:1.25rem; font-weight:700; color:#003366;">Step-4:</span>
                <span style="font-weight:600;">
                    Download a Custom Report</span>
                <br>
                    <span>Click the <span style="color:#003366; font-weight:bold; background:#fdf8b7; padding:2px 6px; border-radius:4px;">Generate Report</span>
                    button to download a personalized insights report you can share with your team.
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
        
    # Show sample data info directly under Step-4
    st.markdown("### Sample Data Preview")
    st.write("""To get the most out of this tool, your data should include:
    - **Demographic Columns**: e.g., StudentID, Gender, Grade, Religion, Ethnicity
    - **Socio-Economic Status Indicators**: e.g., What items do you have at home? (Car, Laptop, Apna Ghar, etc.)
    - **Survey Responses**: e.g., 'Strongly Agree', 'Agree', 'Neutral', 'Disagree', 'Strongly Disagree'
    """)
    st.write("This tool is designed with care to support schools in building more inclusive, welcoming, and responsive learning environments. We’re excited you’re here!")
    
    show_sample_onboard = st.toggle("Show Sample Data", value=False, key="toggle_sample_onboard")
    if show_sample_onboard:
        st.markdown("### Expected Data Structure")
        st.dataframe(sample_data.head())
    st.download_button(
        label="📥 Download Sample Data",
        data=sample_data.to_csv(index=False),
        file_name="sample_data.csv",
        mime="text/csv"
    )

    # Button to navigate to the main page
    if st.button("Start Exploring", key="start_exploring_button"):
        navigate_to('main') 
    st.stop()

# Questionnaire mapping
questionnaire_mapping = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5
}
# Add a "Back" button to navigate to the landing page
if st.button("Back to Landing Page", key="back_button"):
    navigate_to('landing')
    
# Main Page
if st.session_state['current_page'] == 'main':
    st.title("Data Insights Generator")
    st.write("Explore your data and generate insights.")

    # Existing main page content goes here
# Upload Data with Drag-and-Drop
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "txt"])


if uploaded_file is not None:
    # Determine file type and read accordingly
    file_type = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_type in ["csv", "txt"]:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            df = pd.read_csv(stringio)
        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV, TXT, XLS, or XLSX file.")
            st.stop()

        # Automatically remove timestamp-like columns
        timestamp_keywords = ['timestamp', 'date', 'time', 'created', 'submitted', 'record', 'entry', 'logged']
        timestamp_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in timestamp_keywords)]
        if timestamp_cols:
            df = df.drop(columns=timestamp_cols)
            st.write(f"Removed timestamp columns: {', '.join(timestamp_cols)}")

        # Display file details
        #st.write(f"File uploaded: {uploaded_file.name}")
        st.write(f"File size: {uploaded_file.size} bytes")
        num_columns = df.shape[1]  # shape returns (rows, columns), we want the second element (columns)
        st.write(f"Number of columns: {num_columns}")

        st.write("### Data Preview")
        col1, col2 = st.columns([8, 2])
        with col1:
            show_preview = st.toggle("Show Table", value=True, key="toggle_preview")
        if show_preview:
            st.dataframe(df.head())

        # Optional: Empty cleaning options expander (simplified as per request)
        with st.expander("Data Cleaning Options"):
            pass  # Removed duplicate rows and missing values options

        if 'df_cleaned' not in st.session_state:
            st.session_state['df_cleaned'] = df.copy()  # Initialize

    except Exception as e:
        st.error(f"Error processing file: {str(e)}. Please upload a valid CSV, TXT, XLS, or XLSX file.")
        st.stop()
    
    # Detect questionnaire columns dynamically
    questionnaire_cols = [col for col in df.columns if any(str(val).strip().title() in questionnaire_mapping for val in df[col].dropna())]

    #st.write("### Suggested Actions:")
    fill_method = True # st.selectbox("Handle missing values", ["None", "Mean", "Median", "Drop"])
    convert_questionnaire = True #st.checkbox("Convert Questionnaire Responses to Numeric", value=True)
    
    #if st.button("Apply Suggested Cleaning"):
    df_cleaned = df.copy()

    # #attempt to translate the column names, unable to get hands on a hinglish set 

    # # Initialize the Translator
    # translator = Translator()

    # # Create a function to translate column names
    # def translate_columns(columns):
    #     translated_column = []
    #     for text in columns:
    #       try:
    #         # Translate each column name from Hinglish/ to English
    #         translated = translator.translate(col, src='hi', dest='en').text
    #         translated_column.append(translated.text)
    #       except Exception as e:
    #         print(f"Error translating text '{text}': {e}")
    #         translated_column.append(text) 
    #     return translated_column

    # # Apply translation to all columns or specific columns
    # for col in df.columns:
    #   df_cleaned[col] = translate_columns(df[col])

    # print("\nTranslated DataFrame:")
    # print(df_cleaned)
        
    if convert_questionnaire and questionnaire_cols:
        for col in questionnaire_cols:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.title()
            df_cleaned[col] = df_cleaned[col].map(questionnaire_mapping).fillna(df_cleaned[col])
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    else:
        st.info("No questionnaire columns found to convert.")

    ethnicity_column = next((col for col in df_cleaned.columns if "ethnicity" in col.lower()), None)
    if ethnicity_column:
        df_cleaned["ethnicity_cleaned"] = df_cleaned[ethnicity_column].replace({
            v: "General" if "general" in str(v).lower() else
            "SC" if "sc" in str(v).lower() else
            "OBC" if "other" in str(v).lower() else
            "Don't Know" if "do" in str(v).lower() else
            "ST" if "st" in str(v).lower() else v
            for v in df_cleaned[ethnicity_column]
        })

    # if fill_method != "None":
    #     if st.button(f"Approve {fill_method} for missing values?"):
    #         if fill_method == "Mean" or fill_method == "Median":
    #             numeric_cols = df_cleaned.select_dtypes(include=['float64', 'int64']).columns
    #             if numeric_cols.empty:
    #                 st.warning("No numeric columns available for mean/median imputation.")
    #             else:
    #                 if fill_method == "Mean":
    #                     df_cleaned[numeric_cols] = df_cleaned[numeric_cols].fillna(df_cleaned[numeric_cols].mean())
    #                 elif fill_method == "Median":
    #                     df_cleaned[numeric_cols] = df_cleaned[numeric_cols].fillna(df_cleaned[numeric_cols].median())
    #         elif fill_method == "Drop":
    #             df_cleaned = df_cleaned.dropna()
    st.session_state['df_cleaned'] = df_cleaned
    # st.write("### Data Preview (After Cleaning)")
    # col1, col2 = st.columns([8, 2])
    # with col1:
    #     show_cleaned = st.toggle("Show Cleaned Data", value=True, key="toggle_cleaned")
    # if show_cleaned:
    #     st.dataframe(df_cleaned.head())    
    #st.write(f"Number of question columns used for Insights: {len(questionnaire_cols)}")

    # Insight Delivery
    df_cleaned = st.session_state.get('df_cleaned', df)

    belonging_questions = {
        "Safety": ["safe", "surakshit"],
        "Respect": ["respected", "izzat", "as much respect"],        
        "Welcome": ["being welcomed", "welcome", "swagat"],
        "Relationships with Teachers": ["one teacher", "share your problem", "care about your feelings", "close to your teachers"],
        "Participation": ["opportunities", "participate", "school activities", "take part"],        
        "Acknowledgement": ["notice", "noticed", "listen to you", "dekhein", "acknowledge", "recognized", "valued", "heard", "seen", "like you"]
    }

    #  Match each category to actual question columns
    matched_questions = {
        cat: [col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in keywords)]
        for cat, keywords in belonging_questions.items()
    }

    kaash_col = [col for col in df_cleaned.columns if "kaash" in col.lower()]
    df_cleaned["KaashScore"] = df_cleaned[kaash_col].apply(pd.to_numeric, errors="coerce").mean(axis=1) if kaash_col else 0

    # Belonging score with error handling
    belonging_cols = [col for sublist in matched_questions.values() for col in sublist]
    if belonging_cols:
        df_cleaned["BelongingRaw"] = df_cleaned[belonging_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        df_cleaned["BelongingCount"] = df_cleaned[belonging_cols].apply(pd.to_numeric, errors="coerce").notna().sum(axis=1)
        df_cleaned["BelongingScore"] = df_cleaned.apply(
            lambda row: (row["BelongingRaw"] - row["KaashScore"]) / row["BelongingCount"] if row["BelongingCount"] > 0 else 0,
            axis=1
        )
    else:
        df_cleaned["BelongingRaw"] = 0
        df_cleaned["BelongingCount"] = 0
        df_cleaned["BelongingScore"] = 0

    category_averages = {
        cat: df_cleaned[cols].apply(pd.to_numeric, errors='coerce').mean().mean() if cols else 0
        for cat, cols in matched_questions.items()
    }

    overall_belonging_score = df_cleaned["BelongingScore"].mean() if belonging_cols else None
    #st.write(overall_belonging_score)
    if category_averages:
        highest_area = max(category_averages, key=category_averages.get)
        # Filter out scores <= 0.00 for lowest score
        valid_categories = {k: v for k, v in category_averages.items() if v > 0.00}
        lowest_area = min(valid_categories, key=valid_categories.get) if valid_categories else None

    group_columns = {
        "Gender": ["gender", "What gender do you use"],
        "Grade": ["grade", "Which grade are you in"],
        "Income Status": ["Income Category"],
        "Health Condition": ["disability", "health condition"],
        "Ethnicity": ["ethnicity_cleaned"],
        "Religion": ["religion"]
    }

    with st.expander("Click here for Insight Dashboard!"):
        st.header("Insight Dashboard")
        st.write("### Key Metrics (Scale of 5)")
        show_dashboard = st.toggle("Show Metrics Board", value=True, key="toggle_dashboard")
        if show_dashboard:
            # Ensure df_cleaned is available
            df_cleaned = st.session_state.get('df_cleaned', pd.DataFrame())
            
            # Initialize variables with default values
            overall_belonging_score = None
            category_averages = {}
            highest_area = None
            lowest_area = None
            
            belonging_questions = {
            "Safety": ["safe", "surakshit"],
            "Respect": ["respected","respect", "izzat", "as much respect"],        
            "Welcome": ["being welcomed", "welcome", "swagat"],
            "Relationships with Teachers": ["one teacher", "share your problem", "care about your feelings", "close to your teachers", "close teacher"],
            "Participation": ["opportunities", "participate", "school activities", "take part"],        
            "Acknowledgement": ["notice", "noticed", "listen to you", "dekhein", "acknowledge", "recognized", "valued", "heard", "seen", "like you"]
            }
            

            # Recalculate matched_questions and related metrics if data is available
            if df_cleaned.empty:
                st.warning("No cleaned data available. Please upload and process a file first.")
            else:
                matched_questions = {
                    cat: [col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in keywords)]
                    for cat, keywords in belonging_questions.items()
                }
                # Add toggle for matched questions table
                show_matched_questions = st.toggle("Show Questions matched to Constructs", value=False, key="toggle_matched_questions")
                if show_matched_questions:
                    st.write("### Matched Questions")
                    # Convert matched_questions to DataFrame with newlines instead of commas
                    matched_questions_df = pd.DataFrame.from_dict(matched_questions, orient="index").T.fillna("")
                    matched_questions_df = matched_questions_df.apply(lambda x: "\n".join(x) if x.dtype == "object" and any(isinstance(val, list) for val in x) else x)
                    st.dataframe(matched_questions_df)

                belonging_cols = [col for sublist in matched_questions.values() for col in sublist]
                
                if belonging_cols:
                    df_cleaned["BelongingRaw"] = df_cleaned[belonging_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                    df_cleaned["BelongingCount"] = df_cleaned[belonging_cols].apply(pd.to_numeric, errors="coerce").notna().sum(axis=1)
                    df_cleaned["BelongingScore"] = df_cleaned.apply(
                        lambda row: (row["BelongingRaw"] / row["BelongingCount"]) if row["BelongingCount"] > 0 else 0,
                        axis=1
                    )
                    overall_belonging_score = df_cleaned["BelongingScore"].mean()
                    
                    category_averages = {
                        cat: df_cleaned[cols].apply(pd.to_numeric, errors='coerce').mean().mean() if cols else 0
                        for cat, cols in matched_questions.items()
                    }
                    highest_area = max(category_averages, key=category_averages.get)
                    # Filter out scores <= 0.00 for lowest score
                    valid_categories = {k: v for k, v in category_averages.items() if v > 0.00}
                    lowest_area = min(valid_categories, key=valid_categories.get) if valid_categories else None
                else:
                    st.info("No survey columns matched the keyword categories to calculate scores.")


            # Show Likert scale image above the three score cards
            if scale_base64:
                st.markdown(
                f'''
                <div style="display: flex; justify-content: center; align-items: center;">
                    <img src="data:image/png;base64,{scale_base64}" alt="Likert Scale" style="width:70%; max-width:600px; min-width:300px; height:150px; margin-bottom:18px;"/>
                </div>
                ''',
                unsafe_allow_html=True
            )
            # Three-column horizontal layout
            col1, col2, col3 = st.columns(3)

            if overall_belonging_score is not None and category_averages:
                with col1:
                    st.markdown(f"""
                        <div style="background-color:#e6b0aa; border: 4px solid #ff9999; border-radius:10px; padding:1rem; text-align:center;
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <h4> &#9734; Overall Belonging Score</h4>
                            <h4 style="margin:0;">{overall_belonging_score:.2f}</h4>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div style="background-color:#99ccff; border: 4px solid #A7C7E7; border-radius:10px; padding:0.5rem; text-align:center;
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <h4 style="font-size: 1.5rem; margin: 0;"> Highest Score: {highest_area} </h4>
                            <h2 style="font-size: 1.5rem; margin: 0;">{category_averages[highest_area]:.2f}</h2>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    if lowest_area is not None:
                        st.markdown(f"""
                            <div style="background-color:#FAC898; border: 4px solid #ffcc00; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                                <h4 style="font-size: 1.5rem; margin: 0;">Lowest Score: {lowest_area}</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">{category_averages[lowest_area]:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div style="background-color:#FAC898; border: 4px solid #ffcc00; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                                <h4 style="font-size: 1.5rem; margin: 0;">Lowest Score</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">N/A</h2>
                            </div>
                        """, unsafe_allow_html=True)
            st.markdown("<hr style='border: 1px dashed black; border-radius: 5px;'>", unsafe_allow_html=True)
            st.subheader("Category-wise Averages")
            # Two-column layout
            left_col, right_col = st.columns([1, 1])
            

            # Right column: Safety, Respect, and Welcome
            with left_col:
                if category_averages:
                    if "Safety" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#DFC5FE; border-radius:10px; padding:1rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                                <h4 style="font-size: 1rem; margin: 0;">Safety</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;"">{category_averages['Safety']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    if "Respect" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#fdf8b7; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center; margin-top: 1rem;">
                                <h4 style="font-size: 1rem; margin: 0;">Respect</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">{category_averages['Respect']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    if "Welcome" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#a3d8d3; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center; margin-top: 1rem;">
                                <h4 style="font-size: 1rem; margin: 0;">Welcome</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">{category_averages['Welcome']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
            with right_col:
                if category_averages:
                    if "Participation" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#DFC5FE; border-radius:10px; padding:1rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center;">
                                <h4 style="font-size: 1rem; margin: 0;">Participation</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;"">{category_averages['Participation']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    if "Acknowledgement" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#fdf8b7; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center; margin-top: 1rem;">
                                <h4 style="font-size: 1rem; margin: 0;">Acknowledgement</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">{category_averages['Acknowledgement']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)
                    if "Relationships with Teachers" in category_averages:
                        st.markdown(f"""
                            <div style="background-color:#a3d8d3; border-radius:10px; padding:0.5rem; text-align:center;
                                        box-shadow: 0 2px 5px rgba(0,0,0,0.1); color:black; width: 100%; height: 120px; display: flex; flex-direction: column; justify-content: center; margin-top: 1rem;">
                                <h4 style="font-size: 1rem; margin: 0;">Relationships with Teachers</h4>
                                <h2 style="font-size: 1.5rem; margin: 0;">{category_averages['Relationships with Teachers']:.2f}</h2>
                            </div>
                        """, unsafe_allow_html=True)

            # if category_averages:
            #     col1, col2 = st.columns([8, 2])
            #     with col1:
            #         show_averages = st.toggle("Show Table", value=False, key="toggle_averages")
            #     if show_averages:
            #         st.dataframe(pd.DataFrame.from_dict(category_averages, orient="index", columns=["Average Score"]).round(2))

            if not df_cleaned.empty:
                summary = df_cleaned.describe()
                col1, col2 = st.columns([8, 2])
                with col1:
                    show_summary = st.toggle("Show Summary Table", value=False, key="toggle_summary")
                if show_summary:
                    st.dataframe(summary)

        # Explore and Customize
    with st.expander("Click here to explore Belonging Across Groups!"):
        st.subheader("Compare How Different Student Groups Experience Belonging")
        show_explore = st.toggle("Show Charts", value=True, key="toggle_explore")
        if show_explore and not df_cleaned.empty:
            def categorize_income(possessions: str) -> str:
                if pd.isna(possessions):
                    return "Unknown"
                items = possessions.lower()
                has_car = "car" in items
                has_computer = "computer" in items or "laptop" in items
                has_home = "apna ghar" in items
                is_rented = "rent" in items
                if has_car and has_home:
                    return "High"
                if has_computer or (has_home and not has_car):
                    return "Mid"
                return "Low"

            possessions_col = next((col for col in df_cleaned.columns if "what items among these do you have at home".lower() in col.lower()), None)
            if possessions_col:
                df_cleaned["Income Category"] = df_cleaned[possessions_col].apply(categorize_income)

            st.subheader(" Demographic Overview")
            demographic_cols = {
                "Gender": ["gender", "What gender do you use"],
                "Grade": ["grade", "Which grade are you in"],
                "Religion": ["religion"],
                "Ethnicity": ["ethnicity_cleaned"]
            }

            demographic_data = {}
            for label, keywords in demographic_cols.items():
                matched_col = next((col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in keywords)), None)
                if matched_col:
                    demographic_data[label] = matched_col

            if demographic_data:
                items = list(demographic_data.items())

                for row_i in range(0, len(items), 2):
                    row = st.columns(2)

                    for col_i in range(2):
                        idx = row_i + col_i
                        if idx >= len(items):
                            break

                        label, col_name = items[idx]
                        col = row[col_i]

                        value_counts = df_cleaned[col_name].value_counts(dropna=False).rename_axis(label).reset_index(name='Count')
                        fig = px.pie(
                            value_counts,
                            names=label,
                            values='Count',
                            title=f"{label} Distribution",
                            hole=0.3
                        )

                        num_categories = len(value_counts)
                        if num_categories > 3 or any(len(str(cat)) > 8 for cat in value_counts[label]):
                            fig.update_traces(
                                textposition='outside',
                                textinfo='percent',
                                textfont=dict(size=15),
                                marker=dict(line=dict(color='#000000', width=1))
                            )
                        else:
                            fig.update_traces(
                                textposition='auto',
                                textinfo='percent',
                                textfont=dict(size=15)
                            )

                        fig.update_layout(
                            uniformtext_minsize=7,
                            margin=dict(t=45, b=45, l=45, r=45),
                            height=400,
                            width=400,
                            showlegend=True
                        )

                        config = {
                            'displayModeBar': True,
                            'modeBarButtonsToAdd': ['zoom2d', 'autoScale2d', 'resetScale2d', 'toImage'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': f'{label}_distribution',
                                'height': 500,
                                'width': 700
                            }
                        }

                        col.plotly_chart(fig, use_container_width=True, config=config)


            st.write("### Food for Thought")
            st.write(
                """
                Take a moment to observe the differences in the following charts.  
                - Do certain groups consistently score higher or lower? Why do you think that happens? 
                - What kind of experiences or challenges could be influencing their responses?  
                - Are there social, cultural, or school-related factors that might be shaping these patterns?

                """
            ) 
            st.write("")



            selected_area = st.selectbox("Which belonging aspect do you want to explore?", list(belonging_questions.keys()))
            if selected_area and not df_cleaned.empty:
                area_keywords = belonging_questions[selected_area]
                matched_cols = [col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in area_keywords)]
                if not matched_cols:
                    st.warning("No matching questions found for this aspect.")
                else:
                    target_col= matched_cols[0]
                    st.markdown(f"**Showing results for:** {', '.join(matched_cols)}")
                    
                    


                    col1, col2 = st.columns(2)
                    col_slots = [col1, col2]
                    chart_index = 0

                    group_columns = {
                        "Gender": ["gender", "What gender do you use"],
                        "Grade": ["grade", "Which grade are you in"],
                        "Income Status": ["Income Category"],
                        "Health Condition": ["disability", "health condition"],
                        "Ethnicity": ["ethnicity_cleaned"],
                        "Religion": ["religion"]
                    }
                    
                    # Gave a white box that looked unclean in most charts 
                    # st.markdown(   
                    #     """
                    #     <style>
                    #     .modebar {
                    #         display: block !important;
                    #         background-color: white !important;
                    #         border: 1px solid #ddd !important;
                    #         border-radius: 4px !important;
                    #         padding: 2px !important;
                    #     }
                    #     .modebar-group {
                    #         display: flex !important;
                    #         align-items: center !important;
                    #     }
                    #     .modebar-btn {
                    #         background-color: transparent !important;
                    #         border: none !important;
                    #         padding: 2px 6px !important;
                    #         color: #333333 !important;
                    #     }
                    #     .modebar-btn:hover {
                    #         background-color: #f0f0f0 !important;
                    #     }
                    #     </style>
                    #     """,
                    #     unsafe_allow_html=True
                    # )

                    st.markdown(
                        """
                        <style>
                        .modebar {
                            background-color: transparent !important;
                            border: none !important;
                            box-shadow: none !important;
                        }
                        .modebar-btn > svg { 
                            stroke: white !important;
                            fill: white !important;
                            opacity: 1 !important 
                        }
                        .modebar-btn:hover {
                            background-color: rgba(255, 255, 255, 0.2) !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )


                    for label, keywords in group_columns.items():
                        matched_group_col = next((col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in keywords)), None)
                        if matched_group_col:
                            if "ethnicity" in matched_group_col.lower() and "ethnicity_cleaned" in df_cleaned.columns:
                                plot_df = df_cleaned[["ethnicity_cleaned", target_col]].dropna()
                                plot_df.rename(columns={"ethnicity_cleaned": matched_group_col}, inplace=True)
                            else:
                                plot_df = df_cleaned[[matched_group_col, target_col]].dropna()
                            if target_col in plot_df.columns:
                                plot_df[target_col] = pd.to_numeric(plot_df[target_col], errors="coerce")
                            else:
                                st.warning(f"Column '{target_col}' not found in the data.")
                            group_avg = plot_df.groupby(matched_group_col)[target_col].agg(['mean', 'count']).reset_index()
                            group_avg.columns = [matched_group_col, 'AvgScore', 'Count']
                            with col_slots[chart_index % 2]:
                                fig = px.bar(
                                    group_avg,
                                    x=matched_group_col,
                                    y="AvgScore",
                                    text="Count",
                                    title=f"{selected_area} by {label}",
                                    labels={matched_group_col: label, "AvgScore": "Avg Score"},
                                    height=400,
                                    color=matched_group_col,
                                    color_discrete_sequence=px.colors.qualitative.Set3
                                )
                                fig.update_traces(
                                    texttemplate='N=%{text}',
                                    textposition='inside',
                                    insidetextanchor='middle',
                                    hovertemplate="%{x}<br>Avg Score: %{y:.2f}<br>Students: %{text}<extra></extra>"
                                )
                                for i, row in group_avg.iterrows():
                                    fig.add_annotation(
                                        x=row[matched_group_col],
                                        y=row["AvgScore"],
                                        text=f"Avg={row['AvgScore']:.2f}",
                                        showarrow=False,
                                        yshift=10,
                                        font=dict(color='white'),
                                        bgcolor='rgba(0,0,0,0.5)'
                                    )
                                max_y = group_avg["AvgScore"].max()
                                fig.update_layout(
                                    margin=dict(t=50),
                                    yaxis=dict(range=[0, max_y + 0.5])
                                )
                                config = {
                                    'displayModeBar': True,
                                    'modeBarButtonsToRemove': [
                                    'pan2d', 'select2d', 'lasso2d', 'zoom2d', 'autoScale2d', 'hoverClosestCartesian',
                                    'hoverCompareCartesian', 'toggleSpikelines', 'zoomInGeo', 'zoomOutGeo',
                                    'resetGeo', 'hoverClosestGeo', 'sendDataToCloud', 'toggleHover', 'drawline',
                                    'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'
                                    ],
                                    'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage', 'toggleFullscreen'],
                                    #'modeBarButtonsToAdd': ['zoom2d', 'autoScale2d', 'resetScale2d', 'toImage'],
                                    'toImageButtonOptions': {
                                        'format': 'png',
                                        'filename': 'Bar_chart_screenshot',
                                        'height': 500,
                                        'width': 700
                                    },
                                    'displaylogo': False
                                }
                                st.plotly_chart(fig, use_container_width=True, config=config)
                            chart_index += 1
                        else:
                            st.info(f"No data found for {label}.")

                # 🎯 Breakdown by Group (Percentage)
            st.markdown("### Breakdown by Group (Percentage)")
            show_breakdown = st.toggle("Show Chart", value=True, key="toggle_breakdown")
            if show_breakdown:
                breakdown_col = next((col for col in df_cleaned.columns if any(k.lower() in col.lower() for k in group_columns["Gender"])), None)
                if breakdown_col and target_col:
                    breakdown_df = df_cleaned[[breakdown_col, target_col]].dropna()
                    breakdown_df[target_col] = pd.to_numeric(breakdown_df[target_col], errors="coerce")
                    if not breakdown_df.empty:
                        def label_bucket(val):
                            if pd.isna(val):
                                return "Unknown"
                            if val <= 2:
                                return "Disagree"
                            elif val == 3:
                                return "Neutral"
                            elif val >= 4:
                                return "Agree"
                            return "Unknown"
                        breakdown_df["ResponseLevel"] = breakdown_df[target_col].apply(label_bucket)
                        percent_df = breakdown_df.groupby([breakdown_col, "ResponseLevel"]).size().reset_index(name='Count')
                        total_counts = percent_df.groupby(breakdown_col)['Count'].transform('sum')
                        percent_df['Percent'] = (percent_df['Count'] / total_counts * 100).round(1)
                        response_order = ["Agree", "Neutral", "Disagree", "Unknown"]
                        percent_df["ResponseLevel"] = pd.Categorical(percent_df["ResponseLevel"], categories=response_order, ordered=True)
                        fig = px.bar(
                            percent_df,
                            x=breakdown_col,
                            y="Percent",
                            color="ResponseLevel",
                            text=percent_df["Percent"].astype(str) + '%',
                            barmode="stack",
                            title=f"Percentage Breakdown of Responses to '{selected_area}' by Gender",
                            color_discrete_map={
                                "Agree": "#4CAF50",
                                "Neutral": "#FFC107",
                                "Disagree": "#F44336",
                                "Unknown": "#9E9E9E"
                            },
                            height=450
                        )
                        fig.update_layout(
                            yaxis_title="Percentage (%)",
                            xaxis_title=breakdown_col,
                            bargap=0.5,
                            legend_title="Response Level",
                            uniformtext_minsize=8,
                            uniformtext_mode='hide'
                        )
                        fig.update_traces(
                            textposition="inside",
                            insidetextanchor="middle",
                            cliponaxis=False
                        )
                        config = {
                            'displayModeBar': True,
                            'modeBarButtonsToRemove': [
                                'pan2d', 'select2d', 'lasso2d', 'zoom2d', 'autoScale2d', 'hoverClosestCartesian',
                                'hoverCompareCartesian', 'toggleSpikelines', 'zoomInGeo', 'zoomOutGeo',
                                'resetGeo', 'hoverClosestGeo', 'sendDataToCloud', 'toggleHover', 'drawline',
                                'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'
                            ],
                            'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage', 'toggleFullscreen'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'bar_chart_screenshot',
                                'height': 500,
                                'width': 700,
                                'scale': 2
                            },
                                        'displaylogo': False
                        }


                        st.plotly_chart(fig, use_container_width=True, config=config)

            # Take Action
            school_name = st.text_input("Enter your School Name", value="ABC High School", key="school_input")
            generate_pdf = st.button("Generate Report", key="generate_report_button")

            logo_path = "images/project_apnapan_logo.png"
            logo_exists = os.path.exists(logo_path)

            class ProStyledPDF(FPDF):
                def header(self):
                    if logo_exists:
                        self.image(logo_path, x=10, y=10, w=20)
                    self.set_font("Arial", "B", 18)
                    self.set_text_color(0, 51, 102)  # Navy Blue
                    self.cell(0, 10, school_name, ln=True, align="C")
                    self.set_font("Arial", "", 13)
                    self.cell(0, 10, "Data Insights Snapshot", ln=True, align="C")
                    self.ln(8)

                def footer(self):
                    self.set_y(-20)
                    self.set_font("Arial", "I", 10)
                    self.set_text_color(100)
                    self.cell(0, 10, "Generated using the Project Apnapan Data Insights Tool", 0, 1, "C")
                    self.cell(0, 10, datetime.today().strftime("%B %d, %Y"), 0, 0, "C")

                def metric_card(self, label, value, color_rgb):
                    self.set_fill_color(*color_rgb)
                    self.set_text_color(255, 255, 255)
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 12, f"{label}: {value:.2f}", ln=1, align="C", fill=True)
                    self.ln(2)

                def intro_section(self):
                    self.set_font("Arial", "", 12)
                    self.set_text_color(0)
                    self.multi_cell(0, 8, f"This report presents a snapshot of how students experience Belonging, "
                                        f"Safety, Respect, and Welcome at {school_name}. The results are based on "
                                        f"student-reported data collected from the survey file.")
                    self.ln(8)

            if generate_pdf and school_name.strip():
                if overall_belonging_score is None or not category_averages:
                    st.error("Cannot generate PDF: No valid data available. Please upload a file and process it.")
                else:
                    pdf = ProStyledPDF()
                    pdf.add_page()
                    pdf.intro_section()
                    pdf.metric_card("Overall Belonging Score", overall_belonging_score or 0, (0, 102, 204))  # Blue
                    pdf.metric_card("Safety", category_averages.get("Safety", 0), (0, 153, 0))               # Green
                    pdf.metric_card("Respect", category_averages.get("Respect", 0), (255, 153, 51))          # Orange
                    pdf.metric_card("Welcomed", category_averages.get("Welcome", 0), (204, 0, 102))          # Pink
                    clean_name = re.sub(r'[^\w\s-]', '', school_name).strip().replace(' ', '_')
                    safe_filename = f"{clean_name}_insights_report.pdf"
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="Downloading Report",
                        data=pdf_output,
                        file_name=safe_filename,
                        mime="application/pdf"
                    )

        # Feedback Loop
        def send_feedback_to_google_sheet(feedback_text):
            try:
                sheet = connect_to_google_sheet("Apnapan Data Insights Generator Tool Feedbacks")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([timestamp, feedback_text])
                print(f"Feedback submitted: {timestamp}, {feedback_text}")
                return True
            except Exception as e:
                print(f"Error: {e}")
                st.error(f"Failed to send feedback: {e}")
                return False

        # Feedback Section
    with st.expander("Feedback"):
        feedback = st.text_area("Flag any issues or suggestions")
        if st.button("Submit Feedback"):
            if feedback:
                if send_feedback_to_google_sheet(feedback):
                    st.success("Thank you! Your feedback has been recorded.")
                else:
                    st.error("Failed to submit feedback. Please try again later.")
            else:
                st.warning("Please enter some feedback before submitting.")

    with st.expander("Need Help?"):
        st.write("Contact us at: Phone: +91 1234567890")
