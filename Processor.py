import numpy as np
import cv2
import csv

import zmq

context = zmq.Context()
visionSocket = context.socket(zmq.PUB)
# visionSocket.bind("tcp://*:" + "2323")

class Processor:
    def __init__(self, width=640, height=480, debug=False):
        super().__init__()

        self.ipAddress = "10.102.0.52"
        self.socketAddress = "5557" 
        self.port = "8080"  
        self.frameCounter = 5
        self.frame_rate = 30

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
    
        inimg = frame

        # Start measuring image processing time (NOTE: does not account for input conversion time):

        hsv = cv2.cvtColor(inimg, cv2.COLOR_BGR2HSV)
        lower_range = np.array([self.hMin, self.sMin, self.vMin])
        upper_range = np.array([self.hMax, self.sMax, self.vMax])
        mask = cv2.inRange(hsv, lower_range, upper_range)
        # stack = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
        outimg = mask
        # outimg = cv2.Laplacian(inimg, -1, ksize=5, scale=0.25, delta=127)
        cv2.bitwise_and(inimg, inimg, mask=mask)
        # Write a title:
        # cv2.putText(outimg, "JeVois Python Sandbox", (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255))

        # Write frames/s info from our timer into the edge map (NOTE: does not account for output conversion time):
        outheight = outimg.shape[0]
        outwidth = outimg.shape[1]

        edge = cv2.Canny(mask, 100, 100)
        blur = cv2.GaussianBlur(mask, (5, 5), 0)

        furthestLeft = [0, 0]
        furthestRight = [0, 0]
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #cv2.drawContours(inimg, contours, -1, (255, 255, 255), 2)

        # epsilon = 0.1*cv2.arcLength(contours,True)
        # approx = cv2.approxPolyDP(contours,epsilon,True)

        # extLeft = tuple(contours[contours[:, :, 0].argmin()][0])
        # extRight = tuple(c[c[:, :, 0].argmax()][0])
        # extTop = tuple(c[c[:, :, 1].argmin()][0])
        for c in contours:
            if cv2.contourArea(c) > 5:
                extLeft = tuple(c[c[:, :, 0].argmin()][0])
                extRight = tuple(c[c[:, :, 0].argmax()][0])
                extTop = tuple(c[c[:, :, 1].argmin()][0])
                extBot = tuple(c[c[:, :, 1].argmax()][0])
                middle = int(((extRight[0] - extLeft[0]) / 2) + extLeft[0])

                # visionSocket.send(bytes(str(middle), 'utf-8'))

                # jevois.sendSerial("left {} middle {} right {}".format(extLeft[0], middle, extRight[0]))
                pixelD = extRight[0] - extLeft[0]
                #v4l2-ctl --set-ctrl=

                cv2.circle(mask, (extLeft), 1, (100, 100, 255), 5)
                cv2.circle(mask, (extRight), 1, (100, 100, 255), 5)
                cv2.line(mask, (middle, -750), (middle, 750), (0, 0, 255), 2)
                cv2.line(mask, (extLeft), (extLeft[0] + pixelD, extRight[1]), (255, 100, 255), 2)

                # cv2.circle(inimg, (extTop), 1,(100, 100, 255), 5)
                # cv2.circle(inimg, (extBot), 1,(100, 100, 255), 5)
                distance = 432.2 * 2.718281828459045 ** (-0.0156 * pixelD) + 35.75

        tmpout = cv2.bitwise_and(inimg, inimg, mask=mask)

        # Convert our OpenCv output image to video output format and send to host over USB:
        # bgrimg = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
        # newImg = np.vstack((mask, inimg))

        return mask

        # hsv = cv2.cvtColor(inimg, cv2.COLOR_BGR2HSV)
        # lower_range = np.array([self.hMin, self.sMin, self.vMin])
        # upper_range = np.array([self.hMax, self.sMax, self.vMax])
        # mask = cv2.inRange(hsv, lower_range, upper_range)
        # # stack = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
        # outimg = mask
        # # outimg = cv2.Laplacian(inimg, -1, ksize=5, scale=0.25, delta=127)
        # cv2.bitwise_and(inimg, inimg, mask=mask)
        # # Write a title:
        # # cv2.putText(outimg, "JeVois Python Sandbox", (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255))
        # # Write frames/s info from our timer into the edge map (NOTE: does not account for output conversion time):
        # outheight = outimg.shape[0]
        # outwidth = outimg.shape[1]
        # edge = cv2.Canny(mask, 100, 100)
        # blur = cv2.GaussianBlur(mask, (5, 5), 0)
        # furthestLeft = [0, 0]
        # furthestRight = [0, 0]
        # contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # #cv2.drawContours(inimg, contours, -1, (255, 255, 255), 2)
        # # epsilon = 0.1*cv2.arcLength(contours,True)
        # # approx = cv2.approxPolyDP(contours,epsilon,True)
        # # extLeft = tuple(contours[contours[:, :, 0].argmin()][0])
        # # extRight = tuple(c[c[:, :, 0].argmax()][0])
        # # extTop = tuple(c[c[:, :, 1].argmin()][0])
        # # warpImg

        # for c in contours:
        #     rect = cv2.minAreaRect(c)
        #     verticies = cv2.boxPoints(rect)
        #     verticies = np.int0(verticies)
        #     br = verticies[0]
        #     bl = verticies[1]
        #     tr = verticies[2]
        #     tl = verticies[3]

        # #cv2.circle(inimg, (extBot), 1,(100, 100, 255), 5)
        #     warpImg = self.transform(mask, verticies)
        #     extLeft = tuple(c[c[:, :, 0].argmin()][0])
        #     extRight = tuple(c[c[:, :, 0].argmax()][0])
        #     extTop = tuple(c[c[:, :, 1].argmin()][0])
        #     extBot = tuple(c[c[:, :, 1].argmax()][0])
        #     middle = int(((extRight[0] - extLeft[0]) / 2) + extLeft[0])
        # # jevois.sendSerial("left {} middle {} right {}".format(extLeft[0], middle, extRight[0]))
        # # pixelD = extRight[0] - extLeft[0]
        # #v4l2-ctl --set-ctrl=
        # # cv2.circle(inimg, (extLeft), 1, (100, 100, 255), 5)
        # # cv2.circle(inimg, (extRight), 1, (100, 100, 255), 5)
        # # cv2.line(inimg, (middle, -750), (middle, 750), (0, 0, 255), 2)
        # # cv2.line(inimg, (extLeft), (extLeft[0] + pixelD, extRight[1]), (255, 100, 255), 2)
        # # cv2.circle(inimg, (extTop), 1,(100, 100, 255), 5)
        # # cv2.circle(inimg, (extBot), 1,(100, 100, 255), 5)
        # # distance = 432.2 * 2.718281828459045 ** (-0.0156 * pixelD) + 35.75
        # tmpout = cv2.bitwise_and(inimg, inimg, mask=mask)
        # # Convert our OpenCv output image to video output format and send to host over USB:
        # # bgrimg = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
        # # newImg = np.vstack((mask, inimg))
        # # Convert BGR to HSV
        # return frame

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

    def transform(self, image, pts):
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped

    def order_points(self, pts):
    	# initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype = "float32")
    
        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis = 1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
    
        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
    
        # return the ordered coordinates
        return rect
