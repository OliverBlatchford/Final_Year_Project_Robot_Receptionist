from flask import Flask, render_template, request, jsonify, send_from_directory
import smtplib, datetime, os, threading
from email.mime.text import MIMEText
from sharedState import CHECKIN_FLAG, CANCEL_FLAG
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
visitor_log = []

# if project were real world would use the emails from staff directory. however issues with university quarantine so just sends to my email
STAFF_DIRECTORY = {
    'Ulysses Bernardet': 'u.bernardet@aston.ac.uk',
    'Oliver Blatchford': '230163795@aston.ac.uk',
    'Testing': 'Ollie@blatchford.org',
}

# get email stuff from env
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL')

#formats and sends a check in email to the staff being visited
def send_checkin_email(visitor):
    subject = 'New Check-In: {}'.format(visitor['name'])
    body = (
        '{} is here to meet {} for {}.\n\n'
        'Time: {}\n'
        'Student/Staff ID: {}\n'
    ).format(visitor['name'], visitor['visiting'], visitor['purpose'], visitor['time'], visitor['student_id'])
    
    #puts stuff for email
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = NOTIFY_EMAIL
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            #encrypt then log into my email and sends it
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())
        print('Check-in notification sent to {}'.format(NOTIFY_EMAIL))
    except Exception as e:
        print('Failed to send email: {}'.format(e))

#welcome screen
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

#checks that flask is still running and keeps it active
@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'})

#the root. welcome page should be this but added later
@app.route('/')
def index():
    return render_template('checkIn.html', staff=list(STAFF_DIRECTORY.keys()))

#when check in submitted it readds the data record it to the log. sened email in the background. checks in
@app.route('/checkin', methods=['POST'])
def checkin():
    data = request.json
    visitor = {
        'name': data['name'],
        'student_id': data.get('student_id', 'N/A'),
        'visiting': data['staff'],
        'purpose': data.get('purpose', ''),
        'time': datetime.datetime.now().strftime('%H:%M %d/%m/%Y')
    }
    visitor_log.append(visitor)
    threading.Thread(target=send_checkin_email, args=(visitor,), daemon=True).start()
    open(CHECKIN_FLAG, 'w').close()
    return jsonify({'status': 'success', 'message': 'Checked in! Notifying {}...'.format(visitor['visiting'])})

#cancels the form
@app.route('/cancel', methods=['POST'])
def cancel():
    open(CANCEL_FLAG, 'w').close()
    return jsonify({'status': 'cancelled'})

#put map on tablet
@app.route('/map')
def map_page():
    return render_template('map.html')

#stupid robot cant get image from laptop so have to do it this way
@app.route('/mapimage')
def map_image():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base_dir, 'mainBuildingMap.png')

#log page showing visitors
@app.route('/log')
def log_page():
    return render_template('log.html', visitors=visitor_log)

#dont just listen on local host
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
