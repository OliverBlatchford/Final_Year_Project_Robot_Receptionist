import socket
import json

BRIDGE_HOST = "localhost"
BRIDGE_PORT = 6000

#sends command to bridge and returns true if it worked or false if not
def send_command(action, **kwargs):
    command = {"action": action}
    command.update(kwargs)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((BRIDGE_HOST, BRIDGE_PORT))
        s.send(json.dumps(command).encode("utf-8"))
        response = s.recv(1024).decode("utf-8")
        s.close()
        return response == "OK"
    except Exception as e:
        print("Could not reach Pepper bridge: {}".format(e))
        return False

#simplifies function calls
def pepper_say(text, colour=None):
    if colour:
        return send_command("say", text=text, colour=colour)
    return send_command("say", text=text)

def pepper_greet(text=None):
    if text:
        return send_command("greet", text=text)
    return send_command("greet")

def pepper_checkin(text=None, url="http://localhost:5000"):
    if text:
        return send_command("checkin", text=text, url=url)
    return send_command("checkin", url=url)

def pepper_open_tablet(url="http://localhost:5000"):
    return send_command("open_tablet", url=url)

def pepper_farewell(text=None):
    if text:
        return send_command("farewell", text=text)
    return send_command("farewell")

def pepper_sleep():
    return send_command("sleep")

def pepper_wake():
    return send_command("wake")

def pepper_listening():
    return send_command("listening")

def pepper_show_map(url="http://localhost:5000/map"):
    return send_command("show_map", url=url)

def pepper_hide_tablet():
    return send_command("hide_tablet")

def pepper_reset():
    return send_command("reset")

def pepper_restore():
    return send_command("restore")