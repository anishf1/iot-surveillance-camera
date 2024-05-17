import io
import os

from picamera import PiCamera
import picamera
import logging
import socketserver
from threading import Condition
from http import server

from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO

#import anish2
#from anish2 import *
# *********************************************** GPIO setup *************************************************
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)

# *********************************************** Video finename and path *************************************************
filename_part1 = "surveillance"
file_ext = ".mp4"
now = datetime.now()
current_datetime = now.strftime("%d-%m-%Y_%H:%M:%S")
filename = filename_part1 + "_" + current_datetime + file_ext
filepath = "/home/pi/python_code/capture/"


def capture_video():
     camera.start_preview()
     camera.start_recording('/home/pi/python_code/capture/newvideo.h264')
     camera.wait_recording(10)
     camera.stop_recording()
     camera.stop_preview()


# *************************************************** Initiate pi Camera **************************************************************************
 camera = PiCamera()

# *************************************************** Main code for method call ********************************************************************
 while True:
     i = GPIO.input(11)
     if i == 1:
         print("Motion Detected")
         capture_video()
         sleep(2)
         res = os.system(
             "MP4Box -add /home/pi/python_code/capture/newvideo.h264 /home/pi/python_code/capture/newvideo.mp4")
         os.system("mv /home/pi/python_code/capture/newvideo.mp4 " + filepath + filename)
         sleep(2)

PAGE = """\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

timer=0

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    while True:
        i = GPIO.input(11)
        if i == 1:
            print("Motion Detected")
            timer=timer+1
            print("Amount of times motion has been detected:", timer)
             capture_video()
             sleep(2)
            output = StreamingOutput()
            # Uncomment the next line to change your Pi's Camera rotation (in degrees)
            # camera.rotation = 90
            camera.start_recording(output, format='mjpeg')
            try:
                address = ('', 8000)
                server = StreamingServer(address, StreamingHandler)
                server.serve_forever()
            finally:
                camera.stop_recording()

