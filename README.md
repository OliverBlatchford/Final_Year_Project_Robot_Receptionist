# Final Year Project Robot Receptionist

An intelligent receptionist system built on the Pepper humanoid robot platform. It combines facial detection, speech recognition, smart conversational AI (GPT-4o), and an interactive tablet screen to greet visitors, answer questions, display building maps, and handle visitor check-ins.

> **Note:** Running this project live requires a physical Pepper robot. If you don't have access to the hardware, you can read the complete project report in `RobotReceptionistOliverBlatchfordFYP.pdf` to see full execution logs, system flowcharts, and testing results.

---

# What This Project Does
- **Visitor Detection:** Uses a live camera feed (OpenCV) to detect when a visitor walks up and automatically triggers a welcome routine.
- **Voice Interactions:** Listens to visitors, transcribes speech to text (OpenAI Whisper), and uses GPT-4o to understand intent and speak back appropriate answers.
- **Directions & Building Info:** Displays floorplan maps and custom building information on the robot's tablet screen when visitors ask for directions or FAQ details.
- **Digital Visitor Check-In:** Opens an on-screen form for guests to fill in on the tablet and automatically sends an email notification to the staff member they are meeting.
- **Smart Connection Bridge:** Connects Pepper's older system language (Python 2.7) with modern AI tools (Python 3.10+) using a background TCP socket connection.

---

# Testing & Usability Results
We tested the robot with real participants in a university lab setting:
- **Response Clarity:** Rated **4.8 / 5.0** for clear and easy-to-understand communication.
- **Information Trust:** Rated **4.6 / 5.0** for reliable and helpful answers.
- **Response Accuracy:** Rated **4.4 / 5.0** across all building questions and check-in tasks.
- **User Preference:** **80%** of participants preferred using the robot receptionist over waiting in line for a human staff member.
- **Data Privacy:** Fully GDPR compliant; voice audio and camera feeds are processed locally on the laptop so no personal biometric data leaves the device.

---

# Setup & How to Run

# 1. Set Up Your Environment File (`.env`)
Create a file named `.env` in the main project folder and add your key details:
''
OPENAI_API_KEY=
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
NOTIFY_EMAIL=
''
# 2. Connect the Robot
Press the chest button on Pepper to hear its current IP address.  
Open config.py and update the IP address to match Pepper.   
Turn on your laptop's mobile hotspot and verify Pepper connects. If it fails to connect, turn Pepper off and on again.   

# 3. Launch the Application
Double-click start.bat to run all processes automatically.   
When the startup terminal opens, enter nao as the password to activate the tablet interface.   

# Tech Stack
Languages: Python 3.10+, Python 2.7, HTML/CSS
AI & Vision Tools: OpenAI GPT-4o, OpenAI Whisper, OpenCV
Frameworks & Networking: Flask, NAOqi SDK, TCP Sockets   
Hardware: SoftBank / Aldebaran Pepper Robot
