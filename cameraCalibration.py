
# importing libraries 
import cv2 
import numpy as np 
import json
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *


import zmq

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://10.0.0.61:5555")


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.config = dict()
        self.config['hmin'] = 0
        self.config['hmax'] = 0
        self.config['smin'] = 0
        self.config['smax'] = 0
        self.config['vmin'] = 0
        self.config['vmax'] = 0

        vbox = QVBoxLayout()

        self.h_min_slider = QSlider(Qt.Horizontal)
        self.h_min_value_label = QLabel(str(self.config['hmin']))
        vbox.addWidget(self.configureSlider("H min", 0, 255, self.config['hmin'], 5, self.hMinChanged, self.h_min_slider, self.h_min_value_label))

        self.h_max_slider = QSlider(Qt.Horizontal)
        self.h_max_value_label = QLabel(str(self.config['hmax']))
        vbox.addWidget(self.configureSlider("H max", 0, 255, self.config['hmax'], 5, self.hMaxChanged, self.h_max_slider, self.h_max_value_label))

        self.s_min_slider = QSlider(Qt.Horizontal)
        self.s_min_value_label = QLabel(str(self.config['smin']))
        vbox.addWidget(self.configureSlider("S min", 0, 255, self.config['smin'], 5, self.sMinChanged, self.s_min_slider, self.s_min_value_label))

        self.s_max_slider = QSlider(Qt.Horizontal)
        self.s_max_value_label = QLabel(str(self.config['smax']))
        vbox.addWidget(self.configureSlider("S max", 0, 255, self.config['smax'], 5, self.sMaxChanged, self.s_max_slider, self.s_max_value_label))

        self.v_min_slider = QSlider(Qt.Horizontal)
        self.v_min_value_label = QLabel(str(self.config['vmin']))
        vbox.addWidget(self.configureSlider("V min", 0, 255, self.config['vmin'], 5, self.vMinChanged, self.v_min_slider, self.v_min_value_label))

        self.v_max_slider = QSlider(Qt.Horizontal)
        self.v_max_value_label = QLabel(str(self.config['vmax']))
        vbox.addWidget(self.configureSlider("V max", 0, 255, self.config['vmax'], 5, self.vMaxChanged, self.v_max_slider, self.v_max_value_label))


        self.setLayout(vbox)

        self.setWindowTitle("PyQt5 Sliders")
        self.resize(600, 300)

    def configureSlider(self, title, min, max, value, interval, signal, slider, value_label):
        groupBox = QGroupBox("Slider Example")

        title = QLabel(title)

        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.setSingleStep(1)

        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setValue(value)
        slider.setTickInterval(interval)
        slider.valueChanged.connect(signal)
        slider.sliderReleased.connect(self.sendConfig)

        vbox = QHBoxLayout()
        vbox.addWidget(title)
        vbox.addWidget(slider)
        vbox.addWidget(value_label)
        # vbox.addStretch(10)
        groupBox.setLayout(vbox)

        return groupBox

    def sendConfig(self):
        # Convert to JSON
        self.config['action'] = 'PUT'
        config_json = json.dumps(self.config)
        print(config_json)
        msgOut = config_json
        socket.send(bytes(msgOut, 'utf-8'))

        #  Get the reply.
        message = socket.recv()
        print("Received reply %s [ %s ]" % (msgOut, message))

    def setConfig(self, newConfig):
        self.config = newConfig

        # Update sliders
        self.h_min_slider.setValue(self.config['hmin'])
        self.h_max_slider.setValue(self.config['hmax'])
        self.s_min_slider.setValue(self.config['smin'])
        self.s_max_slider.setValue(self.config['smax'])
        self.v_min_slider.setValue(self.config['vmin'])
        self.v_max_slider.setValue(self.config['vmax'])

    def hMinChanged(self):
        self.updateSliderValue('hmin', self.h_min_slider, self.h_min_value_label)

    def hMaxChanged(self):
        self.updateSliderValue('hmax', self.h_max_slider, self.h_max_value_label)

    def sMinChanged(self):
        self.updateSliderValue('smin', self.s_min_slider, self.s_min_value_label)

    def sMaxChanged(self):
        self.updateSliderValue('smax', self.s_max_slider, self.s_max_value_label)

    def vMinChanged(self):
        self.updateSliderValue('vmin', self.v_min_slider, self.v_min_value_label)

    def vMaxChanged(self):
        self.updateSliderValue('vmax', self.v_max_slider, self.v_max_value_label)

    def updateSliderValue(self, key, slider, value_label):
        self.config[key] = slider.value()
        value_label.setText(str(self.config[key]))
        self.sendConfig()
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calibrate = Window()

    msg = dict()
    msg['action'] = "GET"
    retrieveConfigMsg = json.dumps(msg)

    socket.send(bytes(retrieveConfigMsg, 'utf-8'))
    
    configStr = socket.recv()
    currentConfig = json.loads(configStr)
    print(configStr)
    calibrate.setConfig(currentConfig)


    calibrate.show()

    # # Create a VideoCapture object and read from input file 
    # cap = cv2.VideoCapture("http://10.0.0.61:8080/video_feed") 
    
    # # Check if camera opened successfully 
    # if (cap.isOpened()== False):
    #     print("Error opening video  file")
    
    # # Read until video is completed 
    # while(cap.isOpened()): 
        
    #     # Capture frame-by-frame 
    #     ret, frame = cap.read() 
    #     if ret == True: 
        
    #         # Display the resulting frame 
    #         cv2.imshow('Frame', frame) 
        
    #         # Press Q on keyboard to  exit 
    #         if cv2.waitKey(25) & 0xFF == ord('q'): 
    #             break
        
    #     # Break the loop 
    #     else:  
    #         break
        
    # # When everything done, release  
    # # the video capture object
     
    # cap.release() 
    
    # # Closes all the frames 
    # cv2.destroyAllWindows() 

    sys.exit(app.exec_())



