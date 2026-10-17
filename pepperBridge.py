import qi
import socket
import json
import sys
import time

from config import PEPPER_IP
PEPPER_PORT = 9559
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 6000

#this file is used for all the pepper stuff

#connects over network to pepper
def connect_to_pepper():
    print("Connecting to Pepper at {}...".format(PEPPER_IP))
    import os
    session = qi.Session()
    #pepper sends too many annoying message on terminal so use this to silence it
    devnull = open(os.devnull, 'w')
    old_stderr = sys.stderr
    sys.stderr = devnull
    session.connect("tcp://{}:{}".format(PEPPER_IP, PEPPER_PORT))
    sys.stderr = old_stderr
    devnull.close()
    print("Connected!")
    return session

#and gets its servies 
def get_services(session):
    services = {
        "tts": session.service("ALTextToSpeech"),
        "motion": session.service("ALMotion"),
        "tablet": session.service("ALTabletService"),
        "posture": session.service("ALRobotPosture"),
        "leds": session.service("ALLeds"),
    }
    #ALRALManagerModule starts slower than other services so retry until ready to stop it failing as much
    tablet_manager = None
    for _ in range(10):
        try:
            tablet_manager = session.service("ALRALManagerModule")
            break
        except Exception:
            time.sleep(3)
    services["tablet_manager"] = tablet_manager
    if tablet_manager is None:
        print("ALRALManagerModule: not available")
    else:
        print("ALRALManagerModule: connected")
    services["tts"].setLanguage("English")
    services["motion"].wakeUp()
    services["posture"].goToPosture("StandInit", 0.5)
    try:
        services["tablet"].resetTablet()
        print("Tablet initialised.")
    except Exception as e:
        print("Tablet init error: {}".format(e))
    return services

#physical gestures. name(which joint), angles(where to move in), times (how many seconds), True (wait until the movement finishes). Angles chose iteratively through trial and error of what looked like what.
def wave_hello(motion):
    print("Waving hello...")
    names  = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll"]
    angles = [-0.5, 0.3, -1.2, -0.5]
    times  = [1.0, 1.0, 1.0, 1.0]
    motion.angleInterpolation(names, angles, times, True)
    time.sleep(0.5)
    angles = [1.57, 0.09, -1.22, -0.51]
    motion.angleInterpolation(names, angles, times, True)

def wave_goodbye(motion):
    print("Waving goodbye...")
    names  = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll"]
    angles = [-0.3, 0.3, -1.2, -0.5]
    times  = [0.8, 0.8, 0.8, 0.8]
    motion.angleInterpolation(names, angles, times, True)
    for _ in range(3):
        angles = [-0.3, 0.5, -1.2, -0.8]
        motion.angleInterpolation(names, angles, [0.3, 0.3, 0.3, 0.3], True)
        angles = [-0.3, 0.1, -1.2, -0.3]
        motion.angleInterpolation(names, angles, [0.3, 0.3, 0.3, 0.3], True)
    angles = [1.4, 0.1, -1.2, -0.5]
    motion.angleInterpolation(names, angles, [1.0, 1.0, 1.0, 1.0], True)

def nod_head(motion):
    print("Nodding head...")
    names  = ["HeadPitch"]
    angles = [0.3]
    times  = [0.5]
    motion.angleInterpolation(names, angles, times, True)
    time.sleep(0.3)
    angles = [0.0]
    motion.angleInterpolation(names, angles, times, True)

def excited_routine(motion, leds):
    print("Excited routine...")
    leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.3)
    time.sleep(0.2)
    leds.fadeRGB("FaceLeds", 1.0, 1.0, 0.0, 0.3)
    time.sleep(0.2)
    leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.3)
    names  = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "HeadPitch", "HeadYaw"]
    angles = [-0.4, 0.3, -1.2, -0.5, -0.2, 0.0]
    times  = [0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
    motion.angleInterpolation(names, angles, times, True)
    time.sleep(0.3)
    rest_angles = [1.4, 0.1, -1.2, -0.5, 0.0, 0.0]
    motion.angleInterpolation(names, rest_angles, times, True)

def sleep_routine(motion, leds):
    print("Entering sleep routine...")
    #disable autonomous breathing/idle animations so they don't fight our sleep pose
    try:
        motion.setBreathEnabled("Body", False)
        motion.setBreathEnabled("Head", False)
    except Exception as e:
        print("setBreathEnabled error: {}".format(e))
    leds.fadeRGB("FaceLeds", 0.0, 0.0, 0.3, 2.0)
    names  = ["HeadPitch", "HeadYaw"]
    angles = [0.4, 0.0]
    times  = [3.0, 3.0]
    motion.angleInterpolation(names, angles, times, True)
    arm_names  = ["RShoulderPitch", "LShoulderPitch"]
    arm_angles = [1.6, 1.6]
    arm_times  = [3.0, 3.0]
    motion.angleInterpolation(arm_names, arm_angles, arm_times, True)
    print("Pepper is sleeping...")

def wake_up_routine(motion, leds, posture):
    print("Waking up...")
    leds.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.5)
    time.sleep(0.2)
    leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.3)
    time.sleep(0.2)
    leds.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.5)
    posture.goToPosture("StandInit", 0.6)
    names  = ["HeadPitch", "HeadYaw"]
    angles = [0.0, 0.0]
    times  = [0.8, 0.8]
    motion.angleInterpolation(names, angles, times, True)
    print("Pepper is awake!")

def listening_pose(motion, leds):
    print("Listening pose...")
    leds.fadeRGB("FaceLeds", 0.0, 0.0, 1.0, 0.5)
    leds.fadeRGB("EarLeds", 0.0, 0.0, 1.0, 0.5)
    names  = ["HeadPitch", "HeadYaw"]
    angles = [0.1, 0.2]
    times  = [0.8, 0.8]
    motion.angleInterpolation(names, angles, times, True)

#tries to open flask on the tablet
def show_url(services, url):
    try:
        if services["tablet_manager"]:
            services["tablet_manager"].webview()
        services["tablet"].showWebview(str(url))
    except Exception:
        try:
            services["tablet"].resetTablet()
            time.sleep(1)
            if services["tablet_manager"]:
                services["tablet_manager"].webview()
            services["tablet"].showWebview(str(url))
        except Exception as e:
            print("Tablet error: {}".format(e))

def speaking_pose(leds):
    print("Speaking pose...")
    leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.5)

#function to make changing eye colour easier
def set_eye_colour(leds, colour):
    if colour == "white":
        leds.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.5)
    elif colour == "green":
        leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.5)
    elif colour == "blue":
        leds.fadeRGB("FaceLeds", 0.0, 0.0, 1.0, 0.5)
    elif colour == "red":
        leds.fadeRGB("FaceLeds", 1.0, 0.0, 0.0, 0.5)
    elif colour == "yellow":
        leds.fadeRGB("FaceLeds", 1.0, 1.0, 0.0, 0.5)
#defining commands
def handle_command(command, services):
    action = command.get("action", "")
    print("Received action: {}".format(action))

    if action == "say":
        colour = command.get("colour")
        if colour:
            set_eye_colour(services["leds"], colour)
        text = command.get("text", "")
        print("Pepper says: {}".format(text))
        services["tts"].say(str(text))

    elif action == "greet":
        excited_routine(services["motion"], services["leds"])
        wave_hello(services["motion"])
        text = command.get("text", "Hello! Welcome to Aston University!")
        services["tts"].say(str(text))

    elif action == "checkin":
        text = command.get("text", "Please check in using the tablet.")
        speaking_pose(services["leds"])
        services["tts"].say(str(text))
        nod_head(services["motion"])
        url = command.get("url", "http://localhost:5000")
        try:
            services["tablet"].hideWebview()
            time.sleep(0.5)
        except Exception:
            pass
        #two tries to get it to show on tablet cause its finnicky
        show_url(services, url)
        time.sleep(1)
        show_url(services, url)

    elif action == "open_tablet":
        url = command.get("url", "http://localhost:5000")
        show_url(services, url)

    elif action == "farewell":
        text = command.get("text", "Bye bye! Have a great day!")
        speaking_pose(services["leds"])
        services["tts"].say(str(text))
        wave_goodbye(services["motion"])
        set_eye_colour(services["leds"], "white")

    elif action == "show_map":
        url = command.get("url", "http://localhost:5000/map")
        show_url(services, url)
        time.sleep(15)
        try:
            services["tablet"].hideWebview()
        except Exception as e:
            print("Tablet error: {}".format(e))

    elif action == "hide_tablet":
        try:
            services["tablet"].hideWebview()
        except Exception as e:
            print("Hide tablet error: {}".format(e))

    elif action == "sleep":
        sleep_routine(services["motion"], services["leds"])

    elif action == "wake":
        wake_up_routine(services["motion"], services["leds"], services["posture"])

    elif action == "listening":
        listening_pose(services["motion"], services["leds"])

    #used between visitors to reset pepper
    elif action == "reset":
        services["motion"].setStiffnesses("Body", 1.0)
        set_eye_colour(services["leds"], "white")
        services["posture"].goToPosture("StandInit", 0.5)
        print("Pepper reset to standby.")

    #if quitting restores pepper to normal state without code
    elif action == "restore":
        try:
            services["tablet"].hideWebview()
        except Exception:
            pass
        set_eye_colour(services["leds"], "white")
        services["posture"].goToPosture("StandInit", 0.5)
        try:
            services["motion"].setBreathEnabled("Body", True)
            services["motion"].setBreathEnabled("Head", True)
        except Exception:
            pass
        try:
            if services.get("autonomous_life"):
                services["autonomous_life"].setState("interactive")
        except Exception:
            pass
        print("Pepper restored to default state.")


def start_bridge(services):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #reuseaddr to allow it to use port if restarting
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((BRIDGE_HOST, BRIDGE_PORT))
    server.listen(5)
    print("Bridge listening on port {}...".format(BRIDGE_PORT))

    while True:
        try:
            conn, _ = server.accept()
            data = conn.recv(4096).decode("utf-8")
            if data:
                command = json.loads(data)
                handle_command(command, services)
                conn.send("OK".encode("utf-8"))
            conn.close()
        except Exception as e:
            print("Bridge error: {}".format(e))

if __name__ == "__main__":
    try:
        session = connect_to_pepper()
        services = get_services(session)
        set_eye_colour(services["leds"], "white")
        print("Pepper ready.")
        start_bridge(services)
    except Exception as e:
        print("Failed: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)