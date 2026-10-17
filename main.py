import time
import cv2
import socket
import sys
from speechInput import record_until_silence, transcribe
from nlpEngine import process_visitor_input
from pepperController import (
    pepper_greet, pepper_say, pepper_checkin, pepper_reset,
    pepper_farewell, pepper_sleep, pepper_wake,
    pepper_listening, pepper_restore,
    pepper_hide_tablet, pepper_show_map, pepper_open_tablet
)
import os
from sharedState import CHECKIN_FLAG, CANCEL_FLAG

# quits program so pepper stops constantly asking stuff
QUIT_PHRASES = {"quit", "shutdown", "shut down", "exit", "close", "turn off", "stop"}

def shutdown_pepper():
    print("Shutdown command received. Restoring Pepper to default state...")
    pepper_say("Shutting down now. Goodbye!", colour="green")
    pepper_restore()
    print("Shutdown complete.")
    sys.exit(0)

#how long with no face before pepper goes to sleep
SLEEP_AFTER = 30
# maximum number of exchanges before ending conversation automatically
MAX_EXCHANGES = 5

#tracks when a face was last seen and whether pepper is sleeping
last_face_time = time.time()
is_sleeping = False

#data preprocessing. common stuff it mishears
def clean_transcript(text):
    replacements = {
        "empty": "MB",
        "em be": "MB",
        "m b": "MB",
        "emby": "MB",
        "main building": "MB",
        "work next study": "where can I study",
        "work, nice study": "where can I study",
        "work nice study": "where can I study",
        "work next to the": "where can I study",
    }
    lower = text.lower()
    for wrong, right in replacements.items():
        lower = lower.replace(wrong, right)
    return lower

#conversation loop
def run_conversation(flask_url):
    exchanges = 0
    consecutive_silence = 0

    while exchanges < MAX_EXCHANGES:
        #debugging
        print("Exchange {}/{}".format(exchanges + 1, MAX_EXCHANGES))

        #listen to visitor transcribes it. blue eyes stay on while recording
        pepper_listening()
        #prompt for person to start speaking and stop
        pepper_say("Listening", colour="blue")
        record_until_silence()
        pepper_say("Okay", colour="blue")
        transcript = clean_transcript(transcribe())

        #if visitor says nothing twice in a row assume they have left
        if not transcript.strip():
            consecutive_silence += 1
            print("No response detected ({}/2)".format(consecutive_silence))
            if consecutive_silence >= 2:
                print("Visitor appears to have left.")
                pepper_farewell(text="It was lovely talking to you! Bye bye!")
                return
            pepper_say("Sorry, I didn't catch that. Could you repeat that?", colour="green")
            continue

        consecutive_silence = 0
        print("Visitor said: {}".format(transcript))

        #check for verbal shutdown command before sending to GPT
        if any(phrase in transcript.lower() for phrase in QUIT_PHRASES):
            shutdown_pepper()

        #yellow eyes + hmm while GPT processes to make silence less and show progress
        pepper_say("Hmmmm...", colour="yellow")

        result = process_visitor_input(transcript)
        intent = result.get("intent", "unknown")
        reply = result.get("reply", "I am sorry, I did not understand that.")
        #debugging intent and reply
        print("Intent: {} | Reply: {}".format(intent, reply))

        #ends conversation if visitor says goodbye
        if intent == "goodbye":
            pepper_farewell(text=reply)
            print("Visitor said goodbye.")
            return

        #if visitor wants to check in, open tablet then wait for submission, cancel, or timeout
        elif intent == "checkin":
            for f in [CHECKIN_FLAG, CANCEL_FLAG]:
                if os.path.exists(f):
                    os.remove(f)
            pepper_checkin(text=reply, url=flask_url)
            deadline = time.time() + 45
            result = None
            while time.time() < deadline:
                if os.path.exists(CHECKIN_FLAG):
                    os.remove(CHECKIN_FLAG)
                    result = "submitted"
                    break
                if os.path.exists(CANCEL_FLAG):
                    os.remove(CANCEL_FLAG)
                    result = "cancelled"
                    break
                time.sleep(0.5)
            if result != "submitted":
                pepper_say("No problem! Is there anything else I can help you with?", colour="green")
                pepper_open_tablet(flask_url + "/welcome")
                exchanges += 1
                continue
            time.sleep(2)
            pepper_hide_tablet()
            pepper_say("Great, you're all checked in! Is there anything else I can help you with?", colour="green")
            exchanges += 1
            continue

        else:
            pepper_say(reply, colour="green")
            if intent == "navigation":
                pepper_show_map(flask_url + "/map")
                pepper_open_tablet(flask_url + "/welcome")

        exchanges += 1
        time.sleep(0.5)

    #automatically say goodbye if max exchanges reached to stop people hogging!
    pepper_farewell(text="It was lovely talking to you! Have a great day, bye bye!")

#it sleeping?
def check_sleep_state():
    global is_sleeping, last_face_time
    if not is_sleeping and (time.time() - last_face_time) > SLEEP_AFTER:
        print("No visitor for {} seconds. Going to sleep...".format(SLEEP_AFTER))
        pepper_sleep()
        is_sleeping = True

#is there a visitor?
def on_visitor_detected(flask_url):
    global is_sleeping, last_face_time
    last_face_time = time.time()

    if is_sleeping:
        print("Waking up!")
        pepper_wake()
        is_sleeping = False
        time.sleep(1)
        pepper_open_tablet(flask_url + "/welcome")

    print("Visitor detected! Starting interaction...")
    pepper_open_tablet(flask_url + "/welcome")
    #greets visitor and gives info on how to speak to it
    pepper_greet("Hello! Welcome to Aston University. I am Pepper the robot receptionist. When I say Listening, speak your question, and I will say Okay when I am done. How can I help you today?")

    run_conversation(flask_url)

    print("Interaction complete. Waiting for next visitor...")
    pepper_reset()
    pepper_open_tablet(flask_url + "/welcome")

#face detection loop
def start_face_detection(flask_url):
    global last_face_time
    print("Starting face detection... press Q to quit.")
    cam = cv2.VideoCapture(0)
    cascade = cv2.CascadeClassifier(
        #face detection model in OpenCV
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    #tracks whether a visitor is currently present to stop it repeatedly triggering
    visitor_present = False

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Camera error.")
            break

        #changes grey for easier detection , puts a green box around faces
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(grey, scaleFactor=1.1, minNeighbors=5)

        if len(faces) > 0:
            last_face_time = time.time()
            #just triggers once per visit. dont need the camera after
            if not visitor_present:
                visitor_present = True
                on_visitor_detected(flask_url)
        else:
            visitor_present = False
            check_sleep_state()

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Visitor Detected", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Pepper Receptionist - Face Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    #quits
    cam.release()
    cv2.destroyAllWindows()

#waits for bridge to be ready or else pepper may be delayed in working and not do greeting and stuff
def wait_for_bridge(timeout=120):
    print("Waiting for Pepper bridge to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("localhost", 6000))
            s.close()
            print("Bridge is ready!")
            return True
        except Exception:
            time.sleep(1)
    print("Bridge did not respond within {}s, continuing anyway.".format(timeout))
    return False

#waits for the tablet to be ready or else it doesnt load correctly
def wait_for_flask(timeout=30):
    print("Waiting for Flask to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("localhost", 5000))
            s.close()
            print("Flask is ready!")
            return True
        except Exception:
            time.sleep(1)
    print("Flask did not respond within {}s, continuing anyway.".format(timeout))
    return False

if __name__ == "__main__":
    #tablet routes through proxy to communicate cause idk why its not connected to Pepper?!?!
    flask_url = "http://198.18.0.1:5000"
    print("Starting up...")
    wait_for_bridge()
    wait_for_flask()
    pepper_open_tablet(flask_url + "/welcome")
    start_face_detection(flask_url)