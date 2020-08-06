import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, SnapshotObjectType, OperationStatusType
import cv2
import random
import RPi.GPIO as GPIO
import numpy as np

KEY = os.environ['FACE_SUBSCRIPTION_KEY']
ENDPOINT = os.environ['FACE_ENDPOINT']

#set initial age and gender states
age = 26
gender = "female"
detected_age = 0
detected_gender = "none"
enter = False

#initialise board pin 11 to trigger magnets and 10 for doorbell
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

#start cam
cap = cv2.VideoCapture(0)

#create fullscreen
cv2.namedWindow("Target", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Target",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

#take and save photo
def save_image(timestamp, frame):
	snapshot = frame.copy()
	cv2.imwrite(os.path.join('faces', str(timestamp)+'.jpg'), snapshot)
	print('take_photo')

#use face from /faces folder
def latest_file():
	#go to most recently taken photo
	list_of_files = glob.glob('faces/*.jpg')
	latest_file = max(list_of_files, key=os.path.getctime)
	image_stream = open(latest_file, 'r+b')
	return image_stream, latest_file


#select random persona on doorbell press
def random_persona():
	gender = random.choice(['female', 'male', 'genderless'])
	age = random.randrange(100)
	return age, gender

#for writing text to screen
def GenerateText(size, fontsize, bg, fg, text):
	#generate a piece of canvas and draw text on it
	canvas = Image.new('RGB', size, bg)
	draw = ImageDraw.Draw(canvas)
	monospace = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf", fontsize)
	draw.text((10, 10), text, fg, font=monospace)
	#change to BGR for opencv
	return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)

while(True):
	#for testing generate random personas automatically
	#age, gender = random_persona()
	if GPIO.input(10) == GPIO.HIGH:
		print("doorbell pressed")
		age, gender = random_persona()
		print(age, gender)
	#magnets normally on
	GPIO.output(37, GPIO.HIGH)

	#draw background for display
	canvas = Image.new('RGB', (800, 480), (150, 230, 180))
	background = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)

	#read cam frame by frame
	ret, frame = cap.read()
	#turn it up the right way
	frame = cv2.flip(frame, 1)
	just_capture = frame.copy()	
	timestamp = round(time.time()*10)
	#draw it on the screen
	draw_frame = cv2.resize(frame, (200, 150))
	background[0: 150, 300: 500] = draw_frame

	#display last photo
	latest_image_stream, latest_image_string = latest_file()
	latest_image = cv2.imread(latest_image_string)

	last_photo_width = 130
	last_photo_height = 130

	last_img = cv2.resize(latest_image, (last_photo_width, last_photo_height))
	background[0:last_photo_width, 0:last_photo_height] = last_img

	#display age and gender from last photo categorisation
	last_gender_text = GenerateText((200, 40), 12, 'cyan', 'magenta', f"Gender: {detected_gender}")
	background[130:170, 0:200] = last_gender_text
	last_age_text = GenerateText((100, 40), 12, 'yellow', 'black', f"Gender: {detected_age}")
	background[170:210, 0:100] = last_age_text

	#display target age and target gender
	target_gender_text = GenerateText((200, 40), 12, 'red', 'white', f"Target Gender: {gender}")
	background[210:250, 0:200] = target_gender_text
	target_age_text = GenerateText((100, 40), 12, 'white', 'orange', f"Target Age: {age}")
	background[250:290, 0:100] = target_age_text

	#display yes / no box
	if (enter == False):
		cv2.rectangle(background, (0, 290), (100, 390), (0, 0, 255), -1)
	else:
		cv2.rectangle(background, (0, 290), (100, 390), (0, 255, 0), -1)
	
	#display live cam feed to screen, quit if q pressed
	cv2.imshow('Target', background)
	#(height, width, channels) = background.shape
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

    	#how often to take a picture and analyse
	frequency = 10
	if(timestamp%(frequency*10) == 0):
		save_image(timestamp, just_capture)

		    # Detect a face in an image that contains a single face
		detected_faces = face_client.face.detect_with_stream(latest_image_stream, return_face_attributes=['age', 'gender'])

		if (detected_faces):
			detected_age = detected_faces[0].face_attributes.age
			detected_gender = detected_faces[0].face_attributes.gender
			print('target age', age, 'target gender', gender)
			print('detected age', detected_age, 'detected gender', detected_gender)
			if (detected_age == age and detected_gender == gender):
				enter = True
				GPIO.output(37, GPIO.LOW)
				time.sleep(3)
		else:
			print('no face')
			enter = False
			pass

cap.release()
cv2.destroyAllWindows()
