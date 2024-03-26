from flask import Flask, render_template, request, jsonify, redirect, url_for
import face_recognition
import pandas as pd
from datetime import datetime
import numpy as np
import cv2
import os
import base64
import csv
import logging
from flask import session
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, send
from flask import session



logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='C:/Users/neeharika/Documents/Phase-2 project/static_folder', template_folder='C:/Users/neeharika/Documents/Phase-2 project/templates')
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)



KNOWN_FACES_DIR = 'C:/Users/neeharika/Documents/Phase-2 project/known_faces'
ATTENDANCE_FILE = 'C:/Users/neeharika/Documents/Phase-2 project/attendance.csv'


known_faces_encodings = []
known_faces_names = []

def load_known_faces():
    for filename in os.listdir(KNOWN_FACES_DIR):
        filepath = os.path.join(KNOWN_FACES_DIR, filename)
        known_face = face_recognition.load_image_file(filepath)
        known_face_encoding = face_recognition.face_encodings(known_face)[0]

        known_faces_encodings.append(known_face_encoding)
        known_faces_names.append(os.path.splitext(filename)[0])
    logging.info(f"Loaded {len(known_faces_names)} known faces")

def ensure_csv_file_exists():
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Name', 'Time'])
            writer.writeheader()

def register_attendance(name):
    ensure_csv_file_exists()
    with open(ATTENDANCE_FILE, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Name', 'Time'])
        writer.writerow({"Name": name, "Time": datetime.now()})
    logging.info(f"Attendance recorded for {name}")

@app.route('/capture_image', methods=['POST'])
def capture_image():
    try:
        img_str = request.json['image'].split(",")[1]
        img_data = base64.b64decode(img_str)
        img_arr = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb_img)
        encodings = face_recognition.face_encodings(rgb_img, locations)

        recorded_names = []  # To avoid duplicate recordings
        ensure_csv_file_exists()  # Make sure the CSV file exists before attempting to write to it

        for encoding in encodings:
            matches = face_recognition.compare_faces(known_faces_encodings, encoding)
            name = None

            face_distances = face_recognition.face_distance(known_faces_encodings, encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = known_faces_names[best_match_index]
                
                if name not in recorded_names:
                    recorded_names.append(name)
                    # Record attendance in CSV
                    register_attendance(name)

        # Store the recorded names in the session for immediate web display
        session['recorded_attendance'] = recorded_names

        message = "Attendance recorded for " + ", ".join(recorded_names) if recorded_names else "No known faces detected."
        return jsonify({"message": message})
    except Exception as e:
        logging.error(f"Error in capture_image: {e}")
        return jsonify({"message": "Error processing image"})
@app.route('/attendance_list')
def attendance_list():
    # Load all known faces names as students
    students = known_faces_names

    # Retrieve recorded attendance from the session
    recorded_attendance = session.get('recorded_attendance', [])

    # Determine presence status based on the latest capture session
    attendance_status = [{'name': student, 'status': 'Present' if student in recorded_attendance else 'Absent'} for student in students]

    return render_template('attendance_list.html', attendance_status=attendance_status)

@app.route('/reset_attendance')
def reset_attendance():
    session.pop('recorded_attendance', None)  # Clear recorded attendance
    return redirect(url_for('take_attendance'))  # Redirect to the attendance capture page or any other page as needed
@app.route('/mark_present/<roll_number>')



def mark_present(roll_number):
    # Implement logic to mark the student as present
    # For example, update the CSV file or database record
    print(f"Marking roll number {roll_number} as present")  # Placeholder for your logic
    return redirect(url_for('attendance_list'))


@app.route('/mark_absent/<roll_number>')
def mark_absent(roll_number):
    # Implement logic to mark the student as absent
    print(f"Marking roll number {roll_number} as absent")  # Placeholder for your logic
    return redirect(url_for('attendance_list'))

@app.route('/submit_faculty_login', methods=['POST'])
def submit_faculty_login():
    username = request.form['uname']
    password = request.form['psw']
    if username == 'admin' and password == 'admin':
        return redirect(url_for('take_attendance'))
    else:
        # For simplicity, redirecting back without showing an error message.
        return redirect(url_for('faculty_login'))

@app.route('/')
def home():
    return render_template('Frontend.html')

@app.route('/faculty_login')
def faculty_login():
    return render_template('faculty_login.html')

@app.route('/take_attendance')
def take_attendance():
    return render_template('take_attendance.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/submit_student_login', methods=['POST'])
def submit_student_login():
    # Dummy validation for demonstration
    username = request.form['uname']
    password = request.form['psw']
    if username == 'shruthy' and password == 'password':
        return redirect(url_for('StudentPage'))
    else:
        # In a real application, consider adding a message indicating login failure
        return redirect(url_for('student_login'))

@app.route('/StudentPage')
def StudentPage():
    # Placeholder content, customize as needed
    return render_template('StudentPage.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)




if __name__ == '__main__':
    load_known_faces()  # Load the known faces before starting the server
    socketio.run(app, debug=True)

