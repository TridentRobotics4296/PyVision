import numpy as np
import cv2
import csv

class Processor:
    def __init__(self, width=240, height=180, debug=False):
        super().__init__()

        self.ipAddress = "10.102.0.134"
        self.socketAddress = "1234" 
        self.port = "8080"
        self.frameCounter = 5
        self.frame_rate = 2

        self.snapArray = []

        self.debug = debug

        self.width = width * (2 if debug else 1)
        self.imgWidth = width
        self.height = height

        with open('cameraSnapNum.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_counts = 0
            for row in csv_reader:
                self.snapArray.append(0)
                self.snapArray[line_counts] = int(row[1])
                line_counts += 1

        configArray = []

        with open('cameraCalibration.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                configArray.append(0)
                configArray[line_count] = int(row[1])
                line_count += 1

        self.hMin = configArray[0]
        self.hMax = configArray[1]
        self.sMin = configArray[2]
        self.sMax = configArray[3]
        self.vMin = configArray[4]
        self.vMax = configArray[5]

        self.count = self.snapArray[0]
        self.frameCounter = self.snapArray[1]

        self.m_goalX = int(width / 2)
        self.m_goalY = int(height / 2)
        self.m_deltaX = 5
        self.m_deltaY = 5

        self.m_currentX = 0
        self.m_currentY = 0

        

    def update_config(self, config):
        self.hMin = config['hmin']
        self.hMax = config['hmax']

        self.sMin = config['smin']
        self.sMax = config['smax']

        self.vMin = config['vmin']
        self.vMax = config['vmax']

    def get_config(self):
        theConfig = dict()
        theConfig['hmin'] = self.hMin
        theConfig['hmax'] = self.hMax
        theConfig['smin'] = self.sMin
        theConfig['smax'] = self.sMax
        theConfig['vmin'] = self.vMin
        theConfig['vmax'] = self.vMax
        

        return theConfig

    def return_ipAddress(self):
        return self.ipAddress

    def return_socketAddress(self):
        return self.socketAddress

    def process(self, frame):
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        tmpout = np.zeros((self.height, self.width, frame.shape[2]))
        # define range of blue color in HSV
        lower = np.array([self.hMin, self.sMin, self.vMin])
        upper = np.array([self.hMax, self.sMax, self.vMax])
        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower, upper)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        targetBottom = 0
        targetCenter = 0
        if len(contours) > 0:
            self.target = cv2.boundingRect(contours[0])
            c_width = self.target[2] # get width of the contour
            c_height = self.target[3] # get width of the contour
            biggestContourIndex = 0
            contourIndex = -1
            for c in contours:
                # Iterate through all the contours
                newRect = cv2.boundingRect(c)
                new_c_width = newRect[2]
                new_c_height = newRect[3]
                if new_c_width > c_width and new_c_height > c_height:
                    # find the contour with the biggest width (Probably the target)
                    self.target = newRect
                    biggestContourIndex = contourIndex
                    c_width = new_c_width
                    c_height = new_c_height
            self.targetBottom = self.target[1]
            self.targetLeft = self.target[0]
            self.targetCenter = self.target[0] + (self.target[2] / 2)
            crosshairColor = (255, 0, 0)
            #  Draw current target object center
            # m_currentX = self.target.x + (self.target.width / 2)
            # m_currentY = self.target.y + (self.target.height / 2)
            # ontarget = False
            # targetColor = cv2.Scalar(0, 0, 255)
            # if ((abs(m_currentX - m_goalX) <= m_deltaX) && (abs(m_currentY - m_goalY) <= m_deltaY))
            # {
            #    targetColor = Scalar(0, 255, 0);
            #    ontarget = true;
            # }
            # else if ((abs(m_currentX - m_goalX) <= (3 * m_deltaX)) && (abs(m_currentY - m_goalY) <= (3 * m_deltaY)))
            # {
            #    targetColor = Scalar(0, 100, 255);
            # }
            # line(imgbgr, Point(m_currentX, 0), Point(m_currentX, imgbgr.rows), targetColor, 2);
            # line(imgbgr, Point(0, m_currentY), Point(imgbgr.cols, m_currentY), targetColor, 2);
            # if (ontarget)
            # {
            #    circle(imgbgr, Point(m_currentX, m_currentY), 5, Scalar(0, 255, 0), 2);
            #    circle(imgbgr, Point(m_currentX, m_currentY), 15, Scalar(0, 255, 0), 2);
            #    circle(imgbgr, Point(m_currentX, m_currentY), 25, Scalar(0, 255, 0), 2);
            # }     
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            # tmpout[0:self.height, 0:self.width] = frame
            # Just Draw Blue for now
            cv2.rectangle(tmpout, (self.targetLeft, self.targetBottom), (self.targetLeft + c_width, c_height), (0, 255, 0), 2)
            # Draw the goal crosshairs
            cv2.line(tmpout, (self.m_goalX, 0), (self.m_goalX, self.height), crosshairColor, 2)
            cv2.line(tmpout, (0, self.m_goalY), (self.imgWidth, self.m_goalY), crosshairColor, 2)
            if self.debug:  
                tmpout[0:self.height, self.imgWidth:self.width] = mask
                cv2.rectangle(tmpout, (self.targetLeft + self.imgWidth, self.targetBottom), (self.targetLeft + c_width + self.imgWidth, c_height), (0, 255, 0), 2)
                cv2.line(tmpout, (self.m_goalX + self.imgWidth, 0), (self.m_goalX + self.imgWidth, self.height), crosshairColor, 2)
                cv2.line(tmpout, (self.imgWidth, self.m_goalY), (self.width, self.m_goalY), crosshairColor, 2)
        # outimg = np.hstack([frame, mask])

        with open('cameraSnapNum.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_counts = 0
            for row in csv_reader:
                self.snapArray.append(0)
                self.snapArray[line_counts] = int(row[1])
                line_counts += 1

        self.count = self.snapArray[0]
        self.counter = self.snapArray[1]
    
        if self.counter == 0:
            cv2.imwrite("cameraSnapshot" + str(self.count) + ".jpg", outimg)

        return mask

    def setFrameCounter(self, num):
        self.frameCounter = num

    def takeSnapshot(self):
        from cameraCalibration import Window

        self.frameCounter = 0
        self.setFrameCounter(self.frameCounter)
        print(str(self.frameCounter))

        self.count += 1
        print("cameraSnapshot" + str(self.count))

        v = open("cameraSnapNum.csv","w+")  
        v.write("cameraSnapNum," + str(self.count))
        v.write("\n" + "btnNum," + str(self.frameCounter))
        v.close() 
