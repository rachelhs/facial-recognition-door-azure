import cognitive_face as CF
import cv2
import numpy as np
import time
import os
import glob
import json
import sys
from pyfirmata import Arduino, util
import keys

chosen_gender = sys.argv[1]
chosen_age = float(sys.argv[2])

#connect to Arduino
#board = Arduino("/dev/cu.usbmodem14101")
#board.digital[13].write(0)

#for debugging and initialising
zuckerberg = cv2.imread('faces/zuckerberg.jpg')
latest_file = 'faces/zuckerberg.jpg'
enter = False
width = 10
height = 10
gender = 'Unknown'
age = 'Unknown'

CF.Key.set(KEY)

BASE_URL = 'https://uksouth.api.cognitive.microsoft.com/face/v1.0/'  # Replace with your regional Base URL
CF.BaseUrl.set(BASE_URL)

#display live cam feed
cap = cv2.VideoCapture(0)

cv2.namedWindow("Target", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Target",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

def take_photo(timestamp, image):
	photo = cv2.imwrite(os.path.join('faces', str(timestamp)+'.jpg'), image)
	print('take_photo')

def analyse():
	#go to most recently taken photo
	list_of_files = glob.glob('faces/*.jpg')
	latest_file = max(list_of_files, key=os.path.getctime)
	#return analysis
	result = CF.face.detect(latest_file, attributes='age,gender')
	print(result)
	return result, latest_file

#open the door if certain age, gender
def action(analysis):
	if(len(analysis) > 0):
		analysis_dict = analysis[0]
		attributes = analysis_dict.get('faceAttributes', 0)
		gender = attributes.get('gender', 'unknown')
		age = attributes.get('age', 0)
	else: 
		gender = 'unknown'
		age = 'unknown'

	print(gender)
	print(age)
	if(gender == chosen_gender and age == chosen_age):
		print("ENTER")
		#board.digital[13].write(1)
		enter = True
		return (True, gender, age)
	else:
		enter = False
		#board.digital[13].write(0)
		return (False, gender, age)

#give feedback (last photo taken + age, gender and if the door is open)
def display(latest_file):
	image = cv2.imread(latest_file)
	return image

while(True):
	#reset magnet
	
    #board.digital[13].write(0)
    # Capture frame-by-frame
    ret, frame = cap.read()
    # Display the resulting frame
    size_width = int(width / 3)
    size_height = int(size_width*(height/width))

    x_offset= 0
    y_offset= (size_height*2)

    #
    just_capture = frame.copy()

    #display last photo
    l_img = frame
    s_img = display(latest_file)
    s_img_left = cv2.resize(s_img,(size_width, size_height))

    l_img[y_offset:y_offset+size_height, x_offset:x_offset+size_width] = s_img_left

    # display red / green
    if(enter == False):
    	cv2.rectangle(l_img, (0, 0), (size_width, size_height), (0, 0, 255), -1)
    else:
    	cv2.rectangle(l_img, (0, 0), (size_width, size_height), (0, 255, 0), -1)

    #display result
    cv2.rectangle(l_img, (0, size_height), (size_width, (size_height*2)), (255, 255, 255), -1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(l_img,f"Gender: {gender}",(0,(size_height+int(size_height/2))-30), font, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.putText(l_img,f"Age: {age}",(0,int((size_height*2)-70)), font, 1,(0,0,0),2,cv2.LINE_AA)

	
    cv2.imshow('Target', l_img)
    (height, width, channels) = (l_img.shape)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    current = round(time.time()*10)
    #how often to take a picture and analyse
    num_secs = 4
    if(current%(num_secs*10) == 0):
    	take_photo(current, just_capture)
    	#add in if face detected then...
    	analysis, latest_file = analyse()
    	(enter, gender, age) = action(analysis) 

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
