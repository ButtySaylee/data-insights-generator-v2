Apnapan Data Insights Platform

Empowering schools with data-driven insights to foster inclusive and supportive learning environments.
The Apnapan Data Insights Platform is a full-stack web application designed to help educators understand student experiences of belonging and well-being through advanced data analysis and visualization. Built with Streamlit, Python, Pandas, Plotly, and MongoDB, this tool processes student survey data, generates interactive dashboards, and produces actionable PDF reports, enabling schools to identify trends and promote inclusivity.
🌐 Live Demo - https://apnapanpulse.streamlit.app/
Try the app live at Apnapan Insights Platform.Note: Requires login credentials to access the full functionality. Contact the developer for guest access.
🌟 Features

Secure Authentication: User login, account creation, and password reset with salted password hashing, integrated with Google Sheets API for robust user management.
Data Processing: Dynamic questionnaire mapping, data cleaning, and socio-economic categorization using Pandas for accurate insights.
Interactive Dashboards: Visualize student belonging metrics (e.g., Safety, Respect, Welcome) across demographics like gender, grade, and ethnicity with Plotly.
File Management: Upload, store, and retrieve survey files securely using MongoDB Atlas, with history tracking for seamless user experience.
Automated Reporting: Generate professional PDF reports with FPDF, summarizing key metrics and insights for school administrators.
Responsive Design: Mobile-friendly interface with custom CSS for an intuitive and visually appealing user experience.
Feedback System: Collect user feedback via Google Sheets to continuously improve the platform.

🛠️ Tech Stack

Frontend: Streamlit, HTML, CSS
Backend: Python, MongoDB, Google Sheets API
Data Processing: Pandas, NumPy, scikit-learn (KMeans clustering)
Visualization: Plotly
PDF Generation: FPDF
Security: Hashlib, Secrets (salted password hashing)
Deployment: Streamlit Cloud

📊 How It Works

Upload Data: Schools upload survey data (CSV/Excel) containing demographic and questionnaire responses.
Data Cleaning: The platform processes data, maps Likert-scale responses to numeric values, and categorizes socio-economic status.
Insight Generation: Interactive dashboards display belonging metrics (e.g., Safety, Respect) by demographic groups.
Custom Reports: Generate downloadable PDF reports with key findings and actionable insights.
Secure Storage: Files are stored in MongoDB, with user-specific history for easy access.

🚀 Getting Started
Prerequisites

Python 3.8+
MongoDB Atlas account
Google Cloud Platform credentials for Google Sheets API
Required Python packages (see requirements.txt)

Installation

Clone the repository:
git clone https://github.com/ButtySaylee/data-insights-generator-v2.git
cd apnapan-insights-platform


Install dependencies:
pip install -r requirements.txt


Set up environment variables:Create a .streamlit/secrets.toml file with your MongoDB and Google Sheets credentials:
[mongo]
username = "your_mongo_username"
password = "your_mongo_password"
host = "your_mongo_host"
db_name = "your_db_name"
collection_name = "your_collection_name"

[connections.gsheets]
type = "service_account"
project_id = "your_project_id"
private_key_id = "your_private_key_id"
private_key = "your_private_key"
client_email = "your_client_email"
client_id = "your_client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your_client_x509_cert_url"


Run the application:
streamlit run app.py



📂 Project Structure
data-insights-generator-v2/
├── app.py                    # Main Streamlit application
├── images/                   # Logos and visual assets
│   ├── project_apnapan_logo.png
│   └── Likert_Scale.png
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml          # Sensitive credentials
└── README.md                 # Project documentation

🎯 Usage

Login/Create Account: Register with a School ID and email, or log in with existing credentials.
Upload Data: Use the file uploader to submit survey data (CSV/Excel).
Explore Insights: Navigate to the "Insight Dashboard" to view key metrics or "Explore Belonging Across Groups" for demographic breakdowns.
Generate Reports: Enter your school name and download a PDF report with tailored insights.
Provide Feedback: Share suggestions or issues via the feedback form.

📈 Sample Data
Download the sample dataset to test the platform. It includes:

Demographic columns (StudentID, Gender, Grade, Religion, Ethnicity)
Socio-economic indicators (e.g., possessions like Car, Laptop)
Survey responses (Likert scale: Strongly Disagree to Strongly Agree)

🤝 Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch: git checkout -b feature/your-feature.
Commit your changes: git commit -m 'Add your feature'.
Push to the branch: git push origin feature/your-feature.
Open a pull request.

Please ensure your code follows PEP 8 standards and includes relevant tests.
📬 Feedback
We value your input! Use the in-app feedback form or open an issue on GitHub to report bugs or suggest improvements.
📞 Contact
For support, reach out at:

Email: buttysaylee4@gmail.com
Phone: +91 9958781964

🌍 Impact
The Apnapan Data Insights Platform empowers schools to create inclusive environments by providing actionable insights into student well-being. By identifying trends in belonging and engagement, educators can foster supportive communities, making a meaningful difference in students' lives.

Built with 💙 by [Butty & Jahnavi] | Licensed under MIT License
