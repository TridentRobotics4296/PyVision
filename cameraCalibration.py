# importing libraries 
import cv2 
import csv
import numpy as np
import json
import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from Processor import Processor

btnPress = False

import zmq

context = zmq.Context()

fileName = "cameraCalibration.csv"
configArray = []

processor = Processor(debug=True)

ipAddress = processor.return_ipAddress()
socketAddress = processor.return_socketAddress()

#  Socket to talk to server

print("Connecting to hello world server…")
print(ipAddress)
socket = context.socket(zmq.REQ)
socket.connect("tcp://" + ipAddress + ":" + socketAddress)

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
        self.config['exp'] = 0
        self.config['bri'] = 0
        self.config['sat'] = 0
        self.config['con'] = 0
        self.config['tog'] = 0
        
        vbox = QVBoxLayout()

        self.snapArray = []

        with open('cameraSnapNum.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_counts = 0
            for row in csv_reader:
                self.snapArray.append(0)
                self.snapArray[line_counts] = int(row[1])
                line_counts += 1

        self.count = self.snapArray[0]
        self.counter = self.snapArray[1]

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

        self.exp_slider = QSlider(Qt.Horizontal)
        self.exp_value_label = QLabel(str(self.config['exp']))
        vbox.addWidget(self.configureSlider("Exposure", 0, 100, self.config['exp'], 5, self.expChanged, self.exp_slider, self.exp_value_label))

        self.bri_slider = QSlider(Qt.Horizontal)
        self.bri_value_label = QLabel(str(self.config['bri']))
        vbox.addWidget(self.configureSlider("Brightness", 0, 255, self.config['bri'], 5, self.briChanged, self.bri_slider, self.bri_value_label))

        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_value_label = QLabel(str(self.config['sat']))
        vbox.addWidget(self.configureSlider("Saturation", 0 , 255, self.config['sat'], 5, self.satChanged, self.sat_slider, self.sat_value_label))

        self.con_slider = QSlider(Qt.Horizontal)
        self.con_value_label = QLabel(str(self.config['con']))
        vbox.addWidget(self.configureSlider("Contrast", 0 , 255, self.config['con'], 5, self.conChanged, self.con_slider, self.con_value_label))
        
        self.tog_slider = QSlider(Qt.Horizontal)
        self.tog_value_label = QLabel(str(self.config['tog']))
        vbox.addWidget(self.configureSlider("Mask Toggle", 0, 2, self.config['tog'], 5, self.togChanged, self.tog_slider, self.tog_value_label))


        v = open("cameraSnapNum.csv","w+")
        
        v.write("cameraSnapNum," + str(self.count))
        v.write("\n" + "btnNum," + str(self.counter))
        v.close()

        self.setLayout(vbox)

        self.setWindowTitle("Camera Calibration Menu")
        self.resize(600, 300)

    def configureSlider(self, title, min, max, value, interval, signal, slider, value_label):
        groupBox = QGroupBox("Camera Configuration")
        self.button = QPushButton('Take Snapshot', self)

        self.button.clicked.connect(self.on_click)
        self.counter = 1

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
        vbox.addWidget(self.button)
        groupBox.setLayout(vbox)
        
        return groupBox

    def sendConfig(self):
        # Convert to JSON
        self.config['action'] = 'PUT'
        config_json = json.dumps(self.config)
        #print(config_json)
        msgOut = config_json
        socket.send(bytes(msgOut, 'utf-8'))

        #  Get the reply.
        message = socket.recv()

        #print("Received reply %s [ %s ]" % (msgOut, message))

    def setConfig(self, newConfig):
        self.config = newConfig

        # Update sliders
        self.sat_slider.setValue(self.config['sat'])
        self.exp_slider.setValue(self.config['exp'])
        self.h_min_slider.setValue(self.config['hmin'])
        self.h_max_slider.setValue(self.config['hmax'])
        self.s_min_slider.setValue(self.config['smin'])
        self.s_max_slider.setValue(self.config['smax'])
        self.v_min_slider.setValue(self.config['vmin'])
        self.v_max_slider.setValue(self.config['vmax'])
        self.bri_slider.setValue(self.config['bri'])
        self.con_slider.setValue(self.config['con'])
        self.tog_slider.setValue(self.config['tog'])

    def returnBtnPress(self):
        return btnPress

    def hMinChanged(self):
        self.updateSliderValue('hmin', self.h_min_slider, self.h_min_value_label)

    def expChanged(self):
        self.updateSliderValue('exp', self.exp_slider, self.exp_value_label)
        os.system("v4l2-ctl --set-ctrl=exposure_absolute=" + str(self.config['exp']))
        print("v4l2-ctl --set-ctrl=exposure_absolute=," + str(self.config['exp']))
   
    def satChanged(self):
        self.updateSliderValue('sat', self.sat_slider, self.sat_value_label)
        os.system("v4l2-ctl --set-ctrl=saturation=" + str(self.config['sat']))
        print("v4l2-ctl --set-ctrl=saturation=," + str(self.config['sat']))
             
   
    def briChanged(self):
        self.updateSliderValue('bri', self.bri_slider, self.bri_value_label)
        os.system("v4l2-ctl --set-ctrl=brightness=" + str(self.config['bri']))
        print("v4l2-ctl --set-ctrl=brightness=," + str(self.config['bri']))
        
    def conChanged(self):
        self.updateSliderValue('con', self.con_slider, self.con_value_label)
        os.system("v4l2-ctl --set-ctrl=contrast=" + str(self.config['con']))
        print("v4l2-ctl --set-ctrl=contrast=," + str(self.config['con']))

    def hMaxChanged(self):
        self.updateSliderValue('hmax', self.h_max_slider, self.h_max_value_label)

    def togChanged(self):
        self.updateSliderValue('tog', self.tog_slider, self.tog_value_label)


    def sMinChanged(self):
        self.updateSliderValue('smin', self.s_min_slider, self.s_min_value_label)

    def sMaxChanged(self):
        self.updateSliderValue('smax', self.s_max_slider, self.s_max_value_label)

    def vMinChanged(self):
        self.updateSliderValue('vmin', self.v_min_slider, self.v_min_value_label)

    def vMaxChanged(self):
        self.updateSliderValue('vmax', self.v_max_slider, self.v_max_value_label)

    def writeFile(self):
        f = open(fileName,"w+")
        f.write("hmin," + str(self.config['hmin']))
        f.write("\n" + "hmax," + str(self.config['hmax']))
        f.write("\n" + "smin," + str(self.config['smin']))
        f.write("\n" + "smax," + str(self.config['smax']))
        f.write("\n" +  "vmin," + str(self.config['vmin']))
        f.write("\n" +  "vmax," + str(self.config['vmax']))
        f.write("\n" +  "exp," + str(self.config['exp']))
        f.write("\n" +  "bri," + str(self.config['bri']))
        f.write("\n" +  "sat," + str(self.config['sat']))
        f.write("\n" +  "con," + str(self.config['con']))
        f.write("\n" +  "tog," + str(self.config['tog']))

        f.close()

    def updateSliderValue(self, key, slider, value_label):
        self.config[key] = slider.value()
        value_label.setText(str(self.config[key]))
        self.sendConfig()
        
        self.button.move(100,500)
        # self.button.pressed.connect(self.on_click)
        #self.button.clicked.connect(self.on_click)
        self.writeFile()


    def runCalibration(self):
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


        # Create a VideoCapture object and read from input file 
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

    @pyqtSlot()
    def on_click(self):

        with open('cameraSnapNum.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_counts = 0
            for row in csv_reader:
                self.snapArray.append(0)
                self.snapArray[line_counts] = int(row[1])
                line_counts += 1

        self.count = self.snapArray[0]
        self.counter = self.snapArray[1]

        self.counter = 0
        
        v = open("cameraSnapNum.csv","w+")
        
        v.write("cameraSnapNum," + str(self.count))
        v.write("\n" + "btnNum," + str(self.counter))
        v.close()


        if self.counter == 0:
            print('PyQt5 button click')
            processor.takeSnapshot()
        
        self.counter = 1

        with open('cameraSnapNum.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_counts = 0
            for row in csv_reader:
                self.snapArray.append(0)
                self.snapArray[line_counts] = int(row[1])
                line_counts += 1

        self.count = self.snapArray[0]
        self.counter = self.snapArray[1]
        
        f = open("cameraSnapNum.csv","w+")
        
        f.write("cameraSnapNum," + str(self.count))
        f.write("\n" + "btnNum," + str(1))
        f.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calibrate = Window()
    calibrate.runCalibration()
