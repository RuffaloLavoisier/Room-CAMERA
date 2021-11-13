#use git 2021 1 8 servo app and web control
#go to folder and start python2
#ip alarm and send photo 
import cv2
import sys
#from mail import sendEmail
from flask import Flask, render_template_string, Response, request,send_from_directory, send_file #, session
import RPi.GPIO as GPIO
from camera import VideoCamera
from flask_basicauth import BasicAuth
from imutils.video.pivideostream import PiVideoStream
import imutils
import numpy as np
import time
import datetime
import threading
import os
from DeleteFile import delete_file 
#from gpiozero import LEDBoard

email_update_interval = 5 # sends an email only once in this time interval
video_camera = VideoCamera(flip=False) # creates a camera object, flip vertically
# True is camera line upper
# False is cameara line bottom

object_classifier1 = cv2.CascadeClassifier("models/facial_recognition_model.xml") # an opencv classifier
object_classifier2 = cv2.CascadeClassifier("models/fullbody_recognition_model.xml") # an opencv classifier
object_classifier3 = cv2.CascadeClassifier("models/upperbody_recognition_model.xml") # an opencv classifier

# directory path
# /save/save_file/client_download_photo
Client_Download_Photo = "save/save_file/client_download_photo"
# /save/save_file/client_download_video
Client_Download_Video = "save/save_file/client_download_video"
# /save/save_file/save_all_video/
Save_All_Video = "save/save_file/save_all_video/"
# /save/save_file/save_detect_video/
Save_Detect_Video = "save/save_file/save_detect_video"
# /save/save_file/save_detect_photo/photo
Save_Detect_P = "save/save_file/save_detect_photo/photo/"
# /save/save_file/save_detect_photo/obj_photo
Save_Detect_OP = "save/save_file/save_detect_photo/obj_photo/"




# App Globals (do not edit)
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = '4321'
app.config['BASIC_AUTH_PASSWORD'] = '1234'
app.config['BASIC_AUTH_FORCE'] = False

flask_log = ''
flask_ip_log = ""
lock = threading.Lock
thread_zoom_frame = None
file_name=0
GPIO.setwarnings(False)

servo_pin = 12
#led_pin = 
freq = 50
GPIO.setmode(GPIO.BOARD)
GPIO.setup(servo_pin,GPIO.OUT)
#GPIO.setup(led_pin,GPIO.OUT)
pwm = GPIO.PWM(servo_pin, freq)
pwm.start(0)

#led state
led_state=0

last_time=0
video_time=10
save_video_file=''
basic_auth = BasicAuth(app)
last_epoch = 0

deadline = 3 #delete file deadline

scale = 1 # need zoom 20210208 sunghwan

count =0
log_value = ''

set_fps = 25

# common path
# path='/home/pi/drone_opencv_ardupilot/save/save_file/save_all_video/'

consecFrames = 0
all_rec_save=0
state_all_rec=0
rec_state=0
user_choice_rec_start=0

#log type : text file,video(frame,obj) ,photo(frame,obj),print,web click
#click video REC
#auto check machine video REC
#we want save and send


# fix part
def user_want_rec(): #Recording start when user clicked button
    global user_choice_rec_start,save_video_file,scale,set_fps
    state_user_rec = 0
    print ("user_rec_func")
    while True:
        while user_choice_rec_start == 1 : #user clicked record button
 #           print "in while"
            if state_user_rec == 0 : #if not rec
                #frame_read = video_camera.show_in_zoom(zoom(),False)
                frame_read = video_camera.zoom_frame(scale,False)

                timestamp = datetime.datetime.now()
                (h,w) = frame_read.shape[:2]
                save_video_file = timestamp.strftime("%Y%m%d-%H%M%S")
                print (save_video_file)
                p = "{}/{}.mp4".format(Client_Download_Video, save_video_file) # save path
                print (p)
                output_file = cv2.VideoWriter(p,cv2.VideoWriter_fourcc('M','J','P','G'), set_fps+30,(w,h), True)
   #             print("user save start")
                state_user_rec = 1
            elif state_user_rec == 1: #if start rec
                #frame_read = video_camera.show_in_zoom(zoom(),False)
                frame_read = video_camera.zoom_frame(scale,False)

                output_file.write(frame_read)
                if user_choice_rec_start == 0: #after user clicked save button
                    break
#        print "not while"
        if state_user_rec == 1:
            output_file.release()
            state_user_rec = 0

# if detect save photo
def check_for_obj_save_photo():
    global scale
    while True:
        frame, found_obj = video_camera.zoom_object(scale,object_classifier1,object_classifier2,object_classifier3,False)
        if found_obj: # detect time
            now = datetime.datetime.now().strftime("%m%d_%H%M%S")
            
            #save detect frame
            #if check obj save but just frame
            path = Save_Detect_OP
            file_save_name = path + str(now) + '_obj_frame' + '.png'
            test_img = frame #get obj
            cv2.imwrite(file_save_name,test_img) #save file
            print (file_save_name)
            delete_file(path,deadline)

            #save normal frame
            path = Save_Detect_P #if check obj save but just frame
            file_save_name = path + str(now) + '_get_frame' + '.png'
            test_img = video_camera.zoom_frame(scale,False) #get frame
            cv2.imwrite(file_save_name,test_img)
            print (file_save_name)
            delete_file(path,deadline)




# if detect 5 sec rec mode
def check_for_objects(): #version : detect mode/normal mode 
	global last_epoch, found_obj,consecFrames,sale,set_fps
	state=0
	while True:
		frame, found_obj = video_camera.zoom_object(scale,object_classifier1,object_classifier2,object_classifier3,False)
		if found_obj: # if detect once start ! 
			frame_read = frame
			timestamp = datetime.datetime.now()
			(h,w) = frame_read.shape[:2]
			p = "{}/{}.mp4".format(Save_Detect_Video,timestamp.strftime("%Y%m%d-%H%M%S"))
			output_file = cv2.VideoWriter(p,cv2.VideoWriter_fourcc('M','J','P','G'), 10,(w,h), True)
			print("save start")

			prev = time.time()
			while time.time() - prev < 26:
				frame, nothing = video_camera.zoom_object(scale,object_classifier1,object_classifier2,object_classifier3,False)
				output_file.write(frame)
			output_file.release()
			print ("detect release !")
			path=Save_Detect_Video
			delete_file(path,deadline)

#		except:
			#print "error"
#			print("Error : ", sys.exc_info()[0])



TPL = '''
<!--Admin Page-->
<html lang="en">
<head>
    <script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
    <script src="http://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
<style>
    input[type=range][orient=vertical]
    {
        writing-mode: bt-lr; /* IE */
        -webkit-appearance: slider-vertical; /* WebKit */
        width: 8px;
        height: 175px;
        padding: 0 5px;
    }
   
    .zoom 
    {
       
        float:left;
        background-color: green;
        width:15%;
        height: 325px;
    }
    .cam_log 
    {
        float:left;
        background-color: cadetblue;
        width:85%;
        height: 325px;
    }
    .low
    {
        float:inline-end;
        width: fit-content;
        height: fit-content;
        background-color:khaki;
        padding: 10px;
        margin-top: 360px;
        
    }
    .angle_bar
    {
        width: 300px;
        background-color: cadetblue;
    }
</style>
</head>
<body>   
    <h2>Search Tracking Drone</h2>
        
    <div style="margin-bottom: 330px; background-color: yellow;">
        <div style="float: left; background-color: red;">
          <img id="bg" src="{{ url_for('video_feed') }}" > <!--Video Feed-->
          
        </div>
        <div style="width: 450px; height:325px; float: left;">
            <div class="zoom">
                <div class="zoom_bar" style="float: left;">
                <form name="zoom_form" method="POST" action='/'>
                    <input type="range" min="0.2" max="1.0" name="data" step = "0.1" value={{scale}} 
                    orient="vertical" style="height:300px" onchange="this.form.submit()" 
                    oninput="document.getElementById('zoom_scale').innerHTML=this.value;"/> <!--Zoom-->
               </form>
               <form name="mainform" method="POST" action='/'>
                </div>
                <div style="font-size: 11px;">
                    <div style="vertical-align: top; padding-bottom: 260px;">Zoom In</div><div>Zoom Out</div>
                </div>
            </div>
            <div class="cam_log">
                 <textarea readonly name="log" id="log" style="width: 100%; height: 160px; resize: none; margin-bottom: 5px;">{{log_value}}</textarea> <!--System Log-->
                 <textarea readonly id="record_state" name="record_state" style="width: 100%; height: 160px; resize: none; margin-bottom: 5px;">{{rec_state}}</textarea>
            </div>
        </div>
    </div>
    <div class="low" >
        <input type="submit" name="data" id="screenshot" value="screenshot" /> <!--Capture Button-->
        <input type="submit" name="data" id="record"  value="record"> <!--Record start Button-->
        <input type="submit" name="data" id="stop" value="stop"> <!--Record stop Button-->
        <input type="submit" name="data" id="save"  value="save"> <!--Save record Button-->
        <input type="submit" id="log_btn" name="data" value="log_btn" /> <!--Log Button-->
    </div>
   </form>
    <hr>
</body>
</html>

'''

@app.route('/')
@basic_auth.required
def index():
	global user_choice_rec_start,rec_state,flask_ip_log,scale
	#flask_log = str(flask.request.remote.addr)+'\n'
	
#	log_msg()
	#session.clear()
	rec_state = ''
	return render_template_string(TPL,user_choice_rec_start=user_choice_rec_start,rec_state=rec_state,scale=scale)

def log_msg():
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
        frame, found_obj = camera.zoom_object(
            scale
            ,object_classifier1
            ,object_classifier2
            ,object_classifier3
            ,False
            ) # input zoom frame

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


#@app.route('/', methods = ["POST"])
def send():
    # Get slider Values
    turnlr = request.form["turnlr"]
    # Change duty cycle
    turnlr_F = float(turnlr)
    if turnlr_F < 13:
        pwm.ChangeDutyCycle(turnlr_F)
    if turnlr_F == 14 or turnlr_F == 14.5:
        GPIO.output(led_pin,1)
    elif turnlr_F == 13 or turnlr_F == 13.5:
        GPIO.output(led_pin,0)
    if turnlr_F < 13:
        print (turnlr_F)
    elif turnlr_F == 14 or turnlr_F == 14.5:
        print ("LED OFF")
    elif turnlr_F == 13 or turnlr_F == 13.5:
        print ("LED ON")
    # Give servo some time to move
    time.sleep(1)
    # Pause the servo
    if turnlr_F < 13:
        pwm.ChangeDutyCycle(0)
    return render_template_string(TPL)

@app.route('/', methods = ["POST"])
def control():
    global log_value,file_name,all_rec_save,user_choice_rec_start,save_video_file,scale,Client_Download_Video

    #if float(request.form['data']) <2:
    #	print ("zoom function activate")
    #	print ("ad"+str(request.form['data']))
    #	#print ("az"+str(request.form['zoom']))
    #	scale = float(request.form['data'])
    #	print ("scale :" + str(scale))
    #	return render_template_string(TPL,log_value=log_value,user_choice_rec_start=user_choice_rec_start,scale=scale)

    #screenshot
    if request.form['data'] == 'screenshot':
        a = request.form['data']
        print (a)
        timestamp = datetime.datetime.now()
        test_img,f = video_camera.zoom_object(scale,object_classifier1,object_classifier2,object_classifier3,False) #save photo
        p = "{}/{}.png".format(Client_Download_Photo,timestamp.strftime("%Y%m%d-%H%M%S"))
        cv2.imwrite(p,test_img) #SAVEPHOTO#
        path = Client_Download_Photo
        delete_file(path,deadline)
        log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
        log_value += log_time+' - Screenshot success\n'
        file_name = "{}.{}".format(timestamp.strftime("%Y%m%d-%H%M%S"),"png")
        print ("cap btn")
        return send_file(p,mimetype='image/gif',attachment_filename=file_name,as_attachment=True) #save in client pc
        #log button
    if request.form['data'] == 'log_btn':
        print ("log btn")
        return render_template_string(TPL,log_value=log_value)
        #save entire record
    if request.form['data'] == 'end':
        print ("record stop")
        all_rec_save = 1
        return render_template_string(TPL,log_value=log_value,user_choice_rec_start=user_choice_rec_start)
        #user record start
    if request.form['data'] == 'record':
        print ("user record start")
        timestamp = datetime.datetime.now()
        log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
        log_value += log_time+' - User record start\n'+'The file name is '+save_video_file+'.mp4\n'
        user_choice_rec_start = 1

        return render_template_string(TPL,user_choice_rec_start=user_choice_rec_start,log_value=log_value,rec_state="Recording Now")
        #user record stop
    if request.form['data'] == 'stop':
        user_choice_rec_start = 0
        path=Client_Download_Video
        delete_file(path,deadline)
        timestamp = datetime.datetime.now()
        log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
        log_value += log_time+' - Stop user record\n'+'The file name is '+save_video_file+'.mp4\n'
        return render_template_string(TPL,user_choice_rec_start=user_choice_rec_start,log_value=log_value,rec_state="Recording End")
        #user save record
    if request.form['data'] == 'save':
        print ("user save record")
        print (save_video_file)
        save_video = save_video_file + '.mp4'
        print (save_video)
        timestamp = datetime.datetime.now()
        log_time = timestamp.strftime("%Y.%m.%d %a %H:%M:%S")
        log_value += log_time+' -  User video saved\n'
        #return (render_template_string(TPL,log_value=log_value,user_choice_rec_start=user_choice_rec_start) ,
        #return send_from_directory('/home/pi/save_file/client_download_video/','20201228-223441.mp4',as_attachment=True)
        #return render_template_string(TPL,log_value=log_value,user_choice_rec_start=user_choice_rec_start),
        return send_from_directory(Client_Download_Video,str(save_video),as_attachment=True)

    print ("zoom function activate")
    #print ("ad"+str(request.form['data']))
    #print ("az"+str(request.form['zoom']))
    scale = float(request.form['data']) # 0.1-1.0
    print ("scale :" + str(scale))
    return render_template_string(TPL,user_choice_rec_start=user_choice_rec_start,scale=scale)

if __name__ == '__main__':
    # 오브젝트 감지할 때 영상 저장
    t1 = threading.Thread(target=check_for_objects, args=())
    # 오브젝트를 감지 했을 때 사진 저장
    t2 = threading.Thread(target=check_for_obj_save_photo, args=())
    t3 = threading.Thread(target=user_want_rec, args=())
    #t4 = threading.Thread(target=log, args=())

    #t4.daemon = True
    t3.daemon = True
    t2.daemon = True
    t1.daemon = True

    #t4.start()
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
