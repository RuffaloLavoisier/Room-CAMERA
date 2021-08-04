#use git 2021 1 8 servo app and web control
#go to folder and start python2
#ip alarm and send photo

import datetime
import os
import sys
import threading
import time

import cv2
import imutils
import numpy as np
import RPi.GPIO as GPIO
from flask import (Flask, Response, render_template, request, send_file,
                   send_from_directory)
from flask_basicauth import BasicAuth
from imutils.video.pivideostream import PiVideoStream
from numpy.core.numeric import _frombuffer

from camera import VideoCamera
from CheckDirectory import createFolder
from DeleteFile import delete_file

email_update_interval = 5  # sends an email only once in this time interval

# creates a camera object, flip vertically
video_camera = VideoCamera(flip=True)

object_classifier1 = cv2.CascadeClassifier(
    "models/facial_recognition_model.xml")  # an opencv classifier
object_classifier2 = cv2.CascadeClassifier(
    "models/fullbody_recognition_model.xml")  # an opencv classifier
object_classifier3 = cv2.CascadeClassifier(
    "models/upperbody_recognition_model.xml")  # an opencv classifier

# App Globals (do not edit)
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = '4321'
app.config['BASIC_AUTH_PASSWORD'] = '1234'
app.config['BASIC_AUTH_FORCE'] = False


# directory path
# /save/save_file/client_download_photo
Client_Download_Photo = "/save/save_file/client_download_photo"
# /save/save_file/client_download_video
Client_Download_Video = "/save/save_file/client_download_video"
# /save/save_file/save_all_video/
Save_All_Video = "/save/save_file/save_all_video/"
# /save/save_file/save_detect_video/
Save_Detect_Video = "/save/save_file/save_detect_video/"
# /save/save_file/save_detect_photo/photo
Save_Detect_P = "/save/save_file/save_detect_photo/photo"
# /save/save_file/save_detect_photo/obj_photo
Save_Detect_OP = "/save/save_file/save_detect_photo/obj_photo"


flask_log = ''
flask_ip_log = ""
lock = threading.Lock
thread_zoom_frame = None
GPIO.setwarnings(False)

servo_pin = 12
#led_pin =
freq = 50
GPIO.setmode(GPIO.BOARD)
GPIO.setup(servo_pin, GPIO.OUT)
#GPIO.setup(led_pin,GPIO.OUT)
pwm = GPIO.PWM(servo_pin, freq)
pwm.start(0)

#led state
led_state = 0

last_time = 0
video_time = 10
save_video_file = ''
basic_auth = BasicAuth(app)
last_epoch = 0

deadline = 3  # delete file deadline

scale = 1  # need zoom 20210208 sunghwan

count = 0
log_value = ''

set_fps = 25

# common path

consecFrames = 0
all_rec_save = 0
state_all_rec = 0
rec_state = 0
user_choice_rec_start = 0

#log type : text file,video(frame,obj) ,photo(frame,obj),print,web click
#click video REC
#auto check machine video REC
#we want save and send


def user_want_rec():  # Recording start when user clicked button
    global user_choice_rec_start, save_video_file, scale, set_fps, Client_Download_Video
    state_user_rec = 0 # rec state
    print("Start User REC Function !")
    while True:
        while user_choice_rec_start == 1:  # user clicked record button

            if state_user_rec == 0:  # if not rec
                #frame_read = video_camera.show_in_zoom(zoom(),False)
                frame_read = video_camera.zoom_frame(scale, False)

                timestamp = datetime.datetime.now()
                (h, w) = frame_read.shape[:2]
                save_video_file = timestamp.strftime("%Y%m%d-%H%M%S") # 파일 이름

                #check directory
                createFolder(Client_Download_Video)

                # save path
                p = "{}/{}.mp4".format(
                    Client_Download_Video  # 사용자 지정 영상 파일 저장 경로
                    , save_video_file # 현재시간을 파일 이름으로
                    )

                output_file = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(
                    'M', 'J', 'P', 'G'), set_fps+30, (w, h), True)

                state_user_rec = 1

            elif state_user_rec == 1:  # if start rec
                frame_read = video_camera.zoom_frame(scale, False)
                output_file.write(frame_read)
                if user_choice_rec_start == 0:  # after user clicked save button
                    break
        #print "not while"
        if state_user_rec == 1:
            output_file.release()
            state_user_rec = 0


def check_for_obj_save_photo():
	global scale, Save_Detect_OP, Save_Detect_P
	while True:
		frame, found_obj = video_camera.zoom_object(scale, object_classifier1, False)
		if found_obj:  # detect time

            now = datetime.datetime.now().strftime("%m%d_%H%M%S")
			
            createFolder(Save_Detect_OP)
            #save detect frame
              #if check obj save but just frame
			file_save_name = Save_Detect_OP + str(now) + '_obj_frame' + '.png'
			test_img = frame #get obj
			cv2.imwrite(file_save_name,test_img) #save file
            delete_file(Save_Detect_OP,deadline)

            createFolder(Save_Detect_P)
            #save normal frame
			file_save_name = Save_Detect_P + str(now) + '_get_frame' + '.png'
			test_img = video_camera.zoom_frame(scale,False) #get frame
			cv2.imwrite(file_save_name,test_img)
			delete_file(Save_Detect_P,deadline)

# if detect 5 sec rec mode
def check_for_objects(): #version : detect mode/normal mode 
	global last_epoch, found_obj,consecFrames,sale,set_fps,Save_Detect_Video
	state=0
	while True:
		frame, found_obj = video_camera.zoom_object(scale,object_classifier1,False) # face
		if found_obj: # if detect once start ! 
			frame_read = frame # frame read
			timestamp = datetime.datetime.now()
			(h,w) = frame_read.shape[:2]
            createFolder(Save_Detect_Video)
			DetectVideoFile = "{}/{}.mp4".format(
                Save_Detect_Video # 겍체 탐지하였을 때 자동 저장 디렉토리
                ,timestamp.strftime("%Y%m%d-%H%M%S"))
			output_file = cv2.VideoWriter(DetectVideoFile,cv2.VideoWriter_fourcc('M','J','P','G'), 10,(w,h), True)
			print("save start")

			prev = time.time()
			while time.time() - prev < 12:
				frame, nothing = video_camera.zoom_object(scale,object_classifier1,False)
				output_file.write(frame)
			output_file.release()
			print ("detect release !")
			delete_file(Save_Detect_Video,deadline) # 파일 용량 관리 오래된 로그 파일 삭제 

#		except:
#			print("Error : ", sys.exc_info()[0])



@app.route('/')
@basic_auth.required
def index():
	global user_choice_rec_start,rec_state,flask_ip_log,scale
	#flask_log = str(flask.request.remote.addr)+'\n'
	
	log_msg()
	#session.clear()
	rec_state = ''
	return render_template(
        'sample.html'
        ,user_choice_rec_start=user_choice_rec_start
        ,rec_state=rec_state
        ,scale=scale
    )

def log_msg(): # draw ip address
	global flask_ip_log 
	time = datetime.datetime.now().strftime(" - %Y %m %d %a %p %I:%M:%S")
	#flask_log = flask_log + str(request.environ.get('HTTP_X_REAL_IP',request.remote_addr))+time+'\n'
	ip = str(request.environ.get('HTTP_X_REAL_IP',request.remote_addr))
	number = str(ip).split(".")
	for i in range(4):
		ip_number = len(number[i])
		if i == 3:
			end_point = time + "\n"
		else:
			end_point = "."
		flask_ip_log = flask_ip_log + str(number[i])+\
			((3 - int(ip_number)) * " ")+end_point

def gen(camera):
    global scale
    while True:
        # 카메라로부터 프레임을 읽는다 
        frame, found_obj = camera.zoom_object(scale,object_classifier1,False) # input zoom frame

        if found_obj:
            frame_R = frame # detect frame
        else:
            frame_R = camera.zoom_frame(scale,False) # just frame

        timelog = datetime.datetime.now()
        cv2.putText(frame_R, timelog.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame_R.shape[0] - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', frame_R)
        frame_R=jpeg.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_R + b'\r\n\r\n')

@app.route('/video_feed_bsh_4477')
def video_feed():
    return Response(gen(video_camera),mimetype='multipart/x-mixed-replace; boundary=frame')

def log(): # debug log print
	global flask_log,flask_ip_log
	prev =0
	while True:
		now = time.time()
		if now-prev >= 2:
			prev = now
			a+=1
			b+=1
			os.system("clear")
			print ("-------------------------------------------------------------------")
			print (flask_log)
			print (flask_ip_log)

@app.route('/', methods = ["POST"])
def control():
	global log_value,all_rec_save,user_choice_rec_start,save_video_file,scale,Client_Download_Photo,Client_Download_Video

	#if float(request.form['data']) <2:
	#	print ("zoom function activate")
	#	print ("ad"+str(request.form['data']))
	#	#print ("az"+str(request.form['zoom']))
	#	scale = float(request.form['data'])
	#	print ("scale :" + str(scale))
	#	return render_template('sample.html',log_value=log_value,user_choice_rec_start=user_choice_rec_start,scale=scale)

	#screenshot
	if request.form['data'] == 'screenshot':
		a = request.form['data']
		print (a)
		timestamp = datetime.datetime.now()
		test_img,f = video_camera.zoom_object(scale,object_classifier1,False) #save photo
		createFolder(Client_Download_Photo) # check directory
        FileName = timestamp.strftime("%Y%m%d-%H%M%S")+str(".png")
        pathFile = "{}/{}".format(
                Client_Download_Photo # 사용자 지정에 의한 스크린샷 저장 
                ,FileName
                )
		cv2.imwrite(pathFile,test_img) #SAVEPHOTO#
		delete_file(Client_Download_Photo,deadline)# 오래된 로그 파일 삭제 
		log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
		log_value += log_time+' - Screenshot success\n'
		return send_file(pathFile,mimetype='image/gif',attachment_filename=FileName,as_attachment=True) #save in client pc
	#log button
	if request.form['data'] == 'log_btn':
		print ("log btn")
		return render_template('sample.html',log_value=log_value)
	#save entire record
	if request.form['data'] == 'end':
		print ("record stop")
		all_rec_save = 1
		return render_template('sample.html',log_value=log_value,
			user_choice_rec_start=user_choice_rec_start)
	#user record start
	if request.form['data'] == 'record':
		print ("user record start")
		timestamp = datetime.datetime.now()
		log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
		log_value += log_time+' - User record start\n'+'The file name is '+save_video_file+'.mp4\n'
		user_choice_rec_start = 1
		return render_template('sample.html',user_choice_rec_start=user_choice_rec_start,
			log_value=log_value,rec_state="Recording Now")
	#user record stop
	if request.form['data'] == 'stop':
		user_choice_rec_start = 0
		timestamp = datetime.datetime.now()
		log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
		log_value += log_time+' - Stop user record\n'+'The file name is '+save_video_file+'.mp4\n'
		return render_template('sample.html',user_choice_rec_start=user_choice_rec_start,
			log_value=log_value,rec_state="Recording End")
	#user save record
	if request.form['data'] == 'save':
		print ("user save record")
		print (save_video_file)
		save_video = save_video_file + '.mp4'
		print (save_video)
		timestamp = datetime.datetime.now()
		log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
		log_value += log_time+' -  User video saved\n'
		#return (render_template('sample.html',log_value=log_value,user_choice_rec_start=user_choice_rec_start) ,
		#return send_from_directory('/home/pi/save_file/client_download_video/','20201228-223441.mp4',as_attachment=True)
		#return render_template('sample.html',log_value=log_value,user_choice_rec_start=user_choice_rec_start),
		return send_from_directory(
            Client_Download_Video # 웹으로 사용자에게 영상 파일 전송 
            ,str(save_video),as_attachment=True)

	print ("zoom function activate")
#	print ("ad"+str(request.form['data']))
	#print ("az"+str(request.form['zoom']))
	scale = float(request.form['data']) # 0.1-1.0
	print ("scale :" + str(scale))
	return render_template(
                                    'sample.html'
                                    ,user_choice_rec_start=user_choice_rec_start
                                    ,scale=scale
                                )

if __name__ == '__main__':
    
    # 오브젝트 감지할 때 영상 저장
    t1 = threading.Thread(target=check_for_objects, args=())    #오브젝트를 탐지했을 때
    # 오브젝트를 감지 했을 때 사진 저장
    t2 = threading.Thread(target=check_for_obj_save_photo, args=()) #목표 사진을 저장하기
    t3 = threading.Thread(target=user_want_rec, args=()) # 사용자에 의한 저장 
    t4 = threading.Thread(target=log, args=()) #로그 그리기

    t4.daemon = True
    t3.daemon = True
    t2.daemon = True
    t1.daemon = True

    t4.start()
    t3.start()
    t2.start()
    t1.start()
    
    app.run(host='0.0.0.0',port=8080, debug=False)
    #init delete
   # delete_file('/home/pi/save_file/save_all_video',deadline) #all save 
   # delete_file('/home/pi/save_file/save_detect_video',deadline) #detect video
   # delete_file('/home/pi/save_file/save_detect_photo/obj_photo',deadline) #detect obj_p
   # delete_file('/home/pi/save_file/save_detect_photo/photo',deadline) #detect just_p
   # delete_file('/home/pi/save_file/client_download_photo',deadline) #client down photo
   # delete_file('/home/pi/save_file/client_download_video',deadline) #client down videonbh
