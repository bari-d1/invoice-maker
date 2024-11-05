import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
from dateutil.parser import isoparse
from itertools import zip_longest

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
total = 0
creds = None
students = {
   "oliver" : ["Oliver Firth", "Foundation"],
   "fergus" : ["Fergus", "Foundation"],
   "alfie" : ["Alfie Stockton", "Foundation"], 
   "dylan" : ["Dylan Cunningham", "Excel"], 
   "saif" : ["Saif Ulhaq", "Excel"], 
   "jovan" : ["Jovan Douglas", "Foundation"], 
   "abdullah" : ["Abdullah Balogun", "Foundation"], 
   "olly" : ["Olly Bradley", "Foundation"], 
   "ethan" : ["Ethan Goldsbro", "Foundation"], 
   "yousef" : ["Yousef Shimal", "Foundation"]
}

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """

  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    global creds
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

def get_list_of_calenders():
    pass

def get_events(year, month):
    global creds
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        # now = datetime.now(timezone.utc).isoformat()
        year = year
        month = month

        # Set timeMin to the first day of the month at 00:00 UTC
        timeMin = datetime(year, month, 1, tzinfo=timezone.utc).isoformat()

        # Set timeMax to the first day of the next month at 00:00 UTC
        # This will exclude any events starting at midnight on the first of the following month
        if month == 12:
            timeMax = datetime(year + 1, 1, 1, tzinfo=timezone.utc).isoformat()
        else:
            timeMax = datetime(year, month + 1, 1, tzinfo=timezone.utc).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="c_1e119ea08cf4a6a222de44003e8883b3b7dd3aeac41f9a161ecd1328b1a32790@group.calendar.google.com",
                timeMin=timeMin,
                timeMax=timeMax,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events
    except HttpError as error:
        print(f"An error occurred: {error}")

def check_completed(events):
    color_ids = {
        "1": "Lavender",
        "2": "Sage",
        "3": "Grape",
        "4": "Flamingo",
        "5": "Banana",
        "6": "Tangerine",
        "7": "Peacock",
        "8": "Graphite",
        "9": "Blueberry",
        "10": "Basil",
        "11": "Tomato",
    }

    completed = []
    for event in events:
        if event.get("colorId") == "2" or event.get("colorId") == "10":
            completed.append(event)

    return completed

def check_cancelled(events):
    cancelled = []
    for event in events:
        if event.get("colorId") == "11" or event.get("colorId") == "6":
            cancelled.append(event)
    return cancelled

def check_durartion(event): #returns duration of an event in minutes
    start_time = isoparse(event['start'].get('dateTime') or event['start'].get('date'))
    end_time = isoparse(event['end'].get('dateTime') or event['end'].get('date'))
    
    # Calculate the duration in minutes
    duration = end_time - start_time
    duration_in_minutes = int(duration.total_seconds() // 60)
    
    return duration_in_minutes

def lessons_per_student(student, events): #different to check in session
    lessons = 0
    for event in events:
        summary = event.get("summary")
        name = summary.split('-')[0].strip()
        if name.lower() == student.strip().lower() and (check_durartion(event) == 60 or check_durartion(event) == 75):
            lessons += 1
        elif name.lower() == student.strip().lower() and (check_durartion(event) == 120 or check_durartion(event) == 135):
            lessons += 2
    return int(lessons)

def checkin_per_student(student, events):
    checkin = 0
    for event in events:
        summary = event.get("summary")
        name = summary.split('-')[0].strip()
        if name.lower() == student.strip().lower() and check_durartion(event) == 15:
            checkin += 1
        elif name.lower() == student.strip().lower() and check_durartion(event) == 75:
           checkin +=1
        elif name.lower() == student.strip().lower() and check_durartion(event) == 135:
           checkin +=1

    return int(checkin)

def list_of_checkin(student, events):
    checkin_events = []
    for event in events:
        summary = event.get("summary")
        name = summary.split('-')[0].strip()
        if name.lower() == student.strip().lower() and check_durartion(event) == 15:
            checkin_events.append(event)
        elif name.lower() == student.strip().lower() and check_durartion(event) == 75:
            checkin_events.append(event)
        elif name.lower() == student.strip().lower() and check_durartion(event) == 135:
            checkin_events.append(event)

    return checkin_events

def get_students(events):
    students = []
    for event in events:
        summary = event.get("summary")
        name = summary.split('-')[0].strip()
        if name not in students:
            students.append(name)
    return students

def get_student_events(student, events):
    student_events = []
    for event in events:
        summary = event.get("summary")
        name = summary.split('-')[0].strip()
        if name.lower() == student.lower().strip():
            student_events.append(event)
    return student_events
   

def create_invoice(student, year, month, file):
    # Student Name
    # Service x(no of lessons taught) = service rate * no of lessons taught
    # if foundation student:
    # S = date of lesson
    # if excel student:
    # S = date of lesson , C = date of checkin
    invoice = ""
    try:
        name = students[student.lower()][0]
    except KeyError:
        return "Student not found"
    service = students[student.lower()][1]
    no_of_lessons = lessons_per_student(student, check_completed(get_student_events(student, get_events(year, month))))
    student_events = get_student_events(student, get_events(year, month))
    global total

    if service.lower().strip() == "foundation":
        lesson_dates = ""
        amount = no_of_lessons * 15
        
        total += amount
        for event in check_completed(student_events):
            start_time = isoparse(event['start'].get('dateTime') or event['start'].get('date'))
            formatted_date = start_time.strftime('%d/%m/%y')
            lesson_dates += f"S = {formatted_date}\n"
        invoice = f"""{name}\n{service} Service x{no_of_lessons} = £{amount}\n{lesson_dates}"""
        
    elif service.lower().strip() == "excel":
        lesson_dates = ""
        amount = no_of_lessons * 22.50
        total += amount
        checkin_events = list_of_checkin(student, check_completed(get_student_events(student, get_events(year, month))))
        for s_event, c_event in zip_longest(check_completed(student_events), checkin_events, fillvalue=None):
            # Format the date for the S event, if it exists
            if s_event is not None:
                s_start_time = isoparse(s_event['start'].get('dateTime') or s_event['start'].get('date'))
                s_formatted_date = s_start_time.strftime('%d/%m/%y')
            else:
                s_formatted_date = "(banked)"  # Placeholder if there's no corresponding S event
            
            # Format the date for the C event, if it exists
            if c_event is not None:
                c_start_time = isoparse(c_event['start'].get('dateTime') or c_event['start'].get('date'))
                c_formatted_date = c_start_time.strftime('%d/%m/%y')
            elif c_event is None and no_of_lessons > 4:
                c_formatted_date = "(no checkin)"  # Placeholder if there's no corresponding C event
            else:
                c_formatted_date = "(banked)" 
            
            # Append the formatted dates in the specified format
            lesson_dates += f"S = {s_formatted_date}, C = {c_formatted_date}\n"
        invoice = f"""{name}\n{service} Service x{no_of_lessons} = £{amount}\n{lesson_dates}"""
    
    # Write invoice to the file
    file.write(invoice + "\n")

if __name__ == "__main__":
    main()
    events = get_events(2024, 10)
    completed = check_completed(events)
    my_students = get_students(events)
    
    # Open a file for writing invoices
    with open("invoices.txt", "w") as file:
        for student in my_students:
            create_invoice(student, 2024, 10, file)
    
        # Write the total at the bottom
        file.write(f"Total = £{total}\n")

    print(f"Invoices have been written to 'invoices.txt'. Total = £{total}")
