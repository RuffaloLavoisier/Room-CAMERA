import cv2
from imutils.video import VideoStream
#from imutils.video import VideoStream
import imutils
import time
import numpy as np

class VideoCamera(object):
    def __init__(self, flip = False):
        self.vs = VideoStream(src=0).start()
        #self.vs = PiVideoStream().start()
        self.flip = flip
        time.sleep(2.0)

    def __del__(self):
        self.vs.stop()

    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(np.flip(frame, 0),1)
        return frame

    def get_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        #  frame = imutils.resize(frame, width=600)
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def zoom_frame(self,scale,state):
        # zoom하는 실제 함수
        frame = self.flip_if_needed(self.vs.read())
        height, width = frame.shape[:2]
        #   중심값 계산
        center_x = int(width / 2)
        center_y = int(height / 2)
        radius_x, radius_y = int(width / 2), int(height / 2)

        # 실제 zoom 코드
        radius_x, radius_y = int(scale * radius_x), int(scale * radius_y)
        # size 계산
        min_x, max_x = center_x - radius_x, center_x + radius_x
        min_y, max_y = center_y - radius_y, center_y + radius_y
        # size에 맞춰 이미지를 자른다
        cropped = frame[min_y:max_y, min_x:max_x]
        # 원래 사이즈로 늘려서 리턴
        frame =  cv2.resize(cropped, (width, height))
        if state == 0: # rec,save...
            return frame
        else : # stream
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()

    def zoom_object(self,scale,classifier,state):
        # zoom하는 실제 함수
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy()
        height, width = frame.shape[:2]
        #   중심값 계산
        center_x = int(width / 2)
        center_y = int(height / 2)
        radius_x, radius_y = int(width / 2), int(height /2)
        # 실제 zoom 코드
        radius_x, radius_y = int(scale * radius_x), int(scale * radius_y)
        # size 계산
        min_x, max_x = center_x - radius_x, center_x +  radius_x
        min_y, max_y = center_y - radius_y, center_y +  radius_y
        # size에 맞춰 이미지를 자른다
        cropped = frame[min_y:max_y, min_x:max_x]
        # 원래 사이즈로 늘려서 리턴
        frame =  cv2.resize(cropped, (width, height))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(objects) > 0:
            found_objects = True
        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if state == 0: # rec,save..
            return (frame,found_objects)
        else : # stream mode
            ret, jpeg = cv2.imencode('.jpg', frame)
            return (jpeg.tobytes(), found_objects)

    def read_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        # frame = imutils.resize(frame, width=600)
        return frame

    def get_object(self, classifier):
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy() 
        #frame = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True

        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return (jpeg.tobytes(), found_objects)

    def Detect_in_zoom(self, classifier,zoom_img,state): # model,frame,stream
        found_objects = False
        frame = zoom_img.copy()
        # frame = self.flip_if_needed(self.vs.read()).co$
        # frame = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True
         # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if state == 0: # rec,save..
            return (frame,found_objects)
        else : # stream mode
            ret, jpeg = cv2.imencode('.jpg', frame)
            return (jpeg.tobytes(), found_objects)

    def read_object(self, classifier):
         found_objects = False
         frame = self.flip_if_needed(self.vs.read()).copy() 

        #  frame = imutils.resize(frame, width=600)

         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

         objects = classifier.detectMultiScale(
             gray,
             scaleFactor=1.1,
             minNeighbors=5,
             minSize=(30, 30),
             flags=cv2.CASCADE_SCALE_IMAGE
         )
         if len(objects) > 0:
             found_objects = True
      # Draw a rectangle around the objects
         for (x, y, w, h) in objects:
             cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
         return (frame,found_objects)
    
    def read_object_mix(self, face_classifier, upper_classifier, body_classifier):
        found_objects = False
        frame = self.flip_if_needed(self.vs.read()).copy()

        #  frame = imutils.resize(frame, width=600)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        face = face_classifier.detectMultiScale(  # 감지되는 영역을 찾음
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        upper = upper_classifier.detectMultiScale(  # 감지되는 영역을 찾음
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        body = body_classifier.detectMultiScale(  # 감지되는 영역을 찾음
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
            )

        if len(face) + len(upper) + len(body) > 0:  # 값이 있다면
            found_objects = True

         # Draw a rectangle around the objects
        for (x, y, w, h) in face:  # 표시
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        for (x, y, w, h) in upper:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        for (x, y, w, h) in body:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return (frame, found_objects)