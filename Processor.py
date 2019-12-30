import numpy as np
import cv2



class Processor:
    def __init__(self, width=640, height=480, debug=False):
        super().__init__()

        self.debug = debug

        self.width = width * (2 if debug else 1)
        self.imgWidth = width
        self.height = height

        self.hMin = 80
        self.sMin = 45
        self.vMin = 0

        self.hMax = 120
        self.sMax = 255
        self.vMax = 255


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

    def process(self, frame):

        # Convert BGR to HSV
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
            tmpout[0:self.height, 0:self.imgWidth] = frame
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

        # outimg = np.hstack([frame, tmpout])

        return tmpout
