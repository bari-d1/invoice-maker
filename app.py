from flask import Flask, redirect, session, url_for, request, jsonify, render_template, send_file
import os
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth.exceptions
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from invoice_script import main,get_list_of_calendars,get_events,check_completed,check_cancelled,check_durartion,lessons_per_student,checkin_per_student,list_of_checkin,get_students,get_student_events,create_invoice
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a securely generated secret key

# Replace this with the path to your OAuth 2.0 credentials
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
# /login route to start the OAuth flow
# Initialize Flask app and set the secret key for sessions
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# /login route to start the OAuth flow
@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('auth', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    # Save the state in the session for later validation
    session['state'] = state
    return redirect(authorization_url)
    
# /auth route to handle the OAuth callback
@app.route('/auth')
def auth():
    # Check if the state is in the session
    state = session.get('state')
    if not state:
        return redirect(url_for('login'))  # if no state, redirect to login again
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('auth', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    # Save credentials in the session
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # Redirect to another page after OAuth success
    return redirect(url_for('calendar'))


@app.route('/calendar')
def calendar():
    # Retrieve the credentials stored in the session
    creds_info = session.get('credentials')
    # If credentials are missing or expired, redirect to login
    if not creds_info:
        return redirect(url_for('login'))
    
    creds = Credentials.from_authorized_user_info(creds_info)

    # Check if the credentials are valid
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh the credentials if expired
        session['credentials'] = credentials_to_dict(creds)  # Save the refreshed credentials in session
    
    if not creds.valid:
        return redirect(url_for('login'))  # If credentials are still invalid, redirect to login

    # Build the Google Calendar service
    service = build('calendar', 'v3', credentials=creds)

    # Get the list of calendars
    calendar_list = service.calendarList().list().execute()

    # Render the template and pass the calendar list
    return render_template('select_calendar.html', calendars=calendar_list['items'])

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if the user is logged in and has valid credentials
    creds_info = session.get('credentials')
    if not creds_info:
        return redirect(url_for('login'))
    
    creds = Credentials.from_authorized_user_info(creds_info)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh the credentials if expired
        session['credentials'] = credentials_to_dict(creds)  # Store refreshed credentials in session
    
    if not creds.valid:
        return redirect(url_for('login'))  # Redirect to login if credentials are invalid
    # Handle the POST request when the user selects a calendar
    if request.method == 'POST':
        # Get the selected calendar ID from the form data
        selected_calendar_id = request.form.get('calendar_id')
        session['selected_calendar_id'] = selected_calendar_id
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendars().get(calendarId=session['selected_calendar_id']).execute()
        print(calendar)
        calendar_summary = calendar.get('summary', 'No name available')
        session['calendar_summary'] = calendar_summary
        print(calendar_summary)

        # Store the selected calendar ID in the session

        # Optionally, you can now fetch events from the selected calendar
        # (this can be done in a separate function or route)
        
        # For now, just redirect to the next page (e.g., view events for the selected calendar)
        return redirect(url_for('profile'))
    
    return render_template('generate.html', summary=session.get('calendar_summary', 'No calendar selected'))

@app.route('/select_student', methods=['GET', 'POST'])
def select_student():
    # Retrieve the credentials stored in the session
    creds_info = session.get('credentials')
    
    # If credentials are missing or expired, redirect to login
    if not creds_info:
        return redirect(url_for('login'))
    
    creds = Credentials.from_authorized_user_info(creds_info)

    # Check if the credentials are valid
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh the credentials if expired
        session['credentials'] = credentials_to_dict(creds)  # Save the refreshed credentials in session
    
    if not creds.valid:
        return redirect(url_for('login'))  # If credentials are still invalid, redirect to login

    if request.method == 'POST':
        selected_month = request.form.get('month')  # Get the month
        selected_year = request.form.get('year')  # Get the year
        session['selected_month'] = selected_month
        session['selected_year'] = selected_year
        print(session['selected_month'])
        print(session['selected_year'])
    students = get_students(get_events(creds,session['selected_year'], session['selected_month'], session["selected_calendar_id"]))
    return render_template('select_student.html', students=students)

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    # Collect necessary data from the form or session
    # get_students = get_students()
    creds_info = session.get('credentials')
    
    # If credentials are missing or expired, redirect to login
    if not creds_info:
        return redirect(url_for('login'))
    
    creds = Credentials.from_authorized_user_info(creds_info)

    # Check if the credentials are valid
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh the credentials if expired
        session['credentials'] = credentials_to_dict(creds)  # Save the refreshed credentials in session
    
    if not creds.valid:
        return redirect(url_for('login'))  # If credentials are still invalid, redirect to login
    selected_student = request.form.get('student')
    if not selected_student:
        return "No student selected", 400
    session['student'] = selected_student  
    calendar_id = session.get('selected_calendar_id')  # Example of getting calendar_id (you can adjust this)
    year = session.get('selected_year')  # Adjust based on what you need for your invoice
    month = session.get('selected_month')

    output_dir = os.path.join(os.getcwd(), 'output')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
    invoice_filename = f"invoice_{selected_student}_{year}_{month}.txt"
    invoice_file_path = os.path.join(output_dir, invoice_filename)
    with open(invoice_file_path, "w") as file:  # Open the file in append mode to add more invoices
            file.write("")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir) 
    # Run the invoice generation script and save it to a temporary file
    # Assuming 'generate_invoice' returns a path to the generated file
    if selected_student.lower() == "all":
        grand_total = 0
        students = get_students(get_events(creds,session['selected_year'], session['selected_month'], session["selected_calendar_id"]))
        for student in students:
            invoice_file_path, total = create_invoice(student, year, month, invoice_file_path, creds, calendar_id)
            grand_total += total
        with open(invoice_file_path, "a") as file:  # Open the file in append mode to add more invoices
            file.write("Total: £" + str(grand_total))
    else:      
        invoice_file_path, total = create_invoice(selected_student, year, month, invoice_file_path, creds, calendar_id)
    
    # Check if the file exists and then send it as a downloadable file
    return send_file(invoice_file_path, as_attachment=True, download_name=invoice_filename, mimetype='text/plain')

@app.route('/')
def index():
    return redirect(url_for('login'))  # If credentials are still invalid, redirect to login
if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development; remove in production
    # main()
    app.run(debug=True)
