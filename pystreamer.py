# import the necessary packages
from flask import Response
from flask import Flask
from flask import render_template

from Processor import Processor
import threading
import argparse
import datetime
#import imutils
import time
import cv2
import numpy as np

import json
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to
# warmup
#vs = VideoStream(usePiCamera=1).start()
vs = cv2.VideoCapture(0)
#vs.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320);
#vs.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240);



m_H_MIN = 80;
m_S_MIN = 45;
m_V_MIN = 0;

m_H_MAX = 120;
m_S_MAX = 255;
m_V_MAX = 255;

processor = Processor(debug=True)

#vs = VideoStream(src=0).start()
time.sleep(2.0)

@app.route("/")
def index():
        # return the rendered template
        return render_template("index.html")

def process_image(frameCount):
        # grab global references to the video stream, output frame, and
        # lock variables
        global vs, outputFrame, lock
        end_time = datetime.datetime.now()

        start_frame = datetime.datetime.now()

        # initialize the motion detector and the total number of frames
        # read thus far
        total = 0

        fps_window = np.zeros(15)
        # loop over frames from the video stream
        while True:
            # start_frame = datetime.datetime.now()
            
            # read the next frame from the video stream, resize it,
            # convert the frame to grayscale, and blur it
            rc, frame = vs.read()
#                frame = imutils.resize(frame, width=400)
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # gray = cv2.GaussianBlur(gray, (7, 7), 0)

            # # grab the current timestamp and draw it on the frame
            # timestamp = datetime.datetime.now()
            # cv2.putText(frame, timestamp.strftime(
            #         "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
            #         cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            outImg = processor.process(frame)
            total += 1
            
            end_time = datetime.datetime.now()

            duration = end_time - start_frame
            if duration.microseconds > 0:
                fps = 1000000 / duration.microseconds
            else:
                fps = 1

            fps_window[total % 15] = fps
            fps_avg = fps_window.mean()

            start_frame = datetime.datetime.now()
            
            cv2.rectangle(outImg, (0, outImg.shape[0]), (outImg.shape[1], outImg.shape[0] - 40), (0, 0, 0), -1)
            cv2.putText(outImg, "FPS: {}".format(int(fps_avg)), (10, outImg.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # acquire the lock, set the output frame, and release the
            # lock
            with lock:
                    outputFrame = outImg.copy()


def generate():
        # grab global references to the output frame and lock variables
        global outputFrame, lock

        # loop over frames from the output stream
        while True:
                # wait until the lock is acquired
                with lock:
                        # check if the output frame is available, otherwise skip
                        # the iteration of the loop
                        if outputFrame is None:
                                continue

                        # encode the frame in JPEG format
                        (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

                        # ensure the frame was successfully encoded
                        if not flag:
                                continue

                imgData = bytearray(encodedImage)
                # yield the output frame in the byte format
                yield(b'--frame\r\n' + b'Content-Type: image/jpeg\r\n' + bytes("Content-Length: {}".format(int(len(imgData))), 'utf8') + b'\r\n\r\n' +
                        imgData + b'\r\n')

@app.route("/video_feed")
def video_feed():
        # return the response generated along with the specific media
        # type (mime type)
        return Response(generate(),
                mimetype = "multipart/x-mixed-replace; boundary=frame")


def update_config():
        while True:
                #  Wait for next request from client
                message = socket.recv()
                print("Received request: %s" % message)

                #  Do some work
                config = json.loads(message)

                action = config['action']
                print('Action: ' + action)

                if action == "GET":
                        currentConfig = processor.get_config()
                        currentConfig['success'] = "true"
                        print(message)
                elif action == "PUT":
                        processor.update_config(config)
                        config['success'] = "true"
                        print(config)

                #  Send reply back to client
                message = json.dumps(currentConfig)
                socket.send(bytes(message, 'utf-8'))

# check to see if this is the main thread of execution
if __name__ == '__main__':
        # construct the argument parser and parse command line arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-i", "--ip", type=str, required=True,
                help="ip address of the device")
        ap.add_argument("-o", "--port", type=int, required=True,
                help="ephemeral port number of the server (1024 to 65535)")
        ap.add_argument("-f", "--frame-count", type=int, default=32,
                help="# of frames used to construct the background model")
        args = vars(ap.parse_args())

        # start a thread that will perform motion detection
        t = threading.Thread(target=process_image, args=(
                args["frame_count"],))
        t.daemon = True
        t.start()

        t = threading.Thread(target=update_config)
        t.daemon = True
        t.start()

        # start the flask app
        app.run(host=args["ip"], port=args["port"], debug=True,
                threaded=True, use_reloader=False)

# release the video stream pointer
vs.release()
