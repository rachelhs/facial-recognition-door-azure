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
age = 30
gender = "female"
detected_age = 0
detected_gender = "none"
enter = False
fontsize = 23

#select random persona on start and after accepted
def random_persona():
	gender = random.choice(['female', 'male'])
	age = random.randint(12, 80)
	return age, gender

#draw background for display (mode, (w, h), colour)
canvas = Image.new('RGB', (800, 600), (255, 255, 255))

#for writing text to screen
def GenerateText(size, fontsize, bg, fg, text):
	#generate a piece of canvas and draw text on it
	canvas = Image.new('RGB', size, bg)
	draw = ImageDraw.Draw(canvas)
	grotesk = ImageFont.truetype("fonts/PxGrotesk-Screen.otf", fontsize)
	#first parameter is top left corner of text
	draw.text((0, 0), text, fg, font=grotesk)
	#change to BGR for opencv
	return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)

def set_background(gender):
	# sets white background image with target gender highlighted and static text
	global background
	if (gender == 'female'):
		background = cv2.imread('new-f-w.png')	

	elif (gender == 'genderless'):
		background = cv2.imread('new-g-w.png')

	else:
		background = cv2.imread('new-m-w.png')

# call function immediately
age, gender = random_persona()
print(age, gender)
set_background(gender)

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

#display target age and target gender
def display_target_cat():
	target_age_text = GenerateText((35, 20), fontsize, 'white', 'black', f"{age}")
	background[46: (46+20) ,717: (717+35)] = target_age_text

#display age and gender from last photo categorisation
def display_last_cat():
	last_gender_text = GenerateText((143, 25), fontsize, 'white', 'black', f"{detected_gender}")
	background[520:(520+25), 100:(100+143)] = last_gender_text
	detected_int_age = int(detected_age)
	last_age_text = GenerateText((60, 35), fontsize, 'white', 'black', f"{detected_int_age}")
	background[520:(520+35), 288:(288+60)] = last_age_text
	print(detected_gender, detected_age)

#display last photo
def display_last_image(latest_image_string):
	latest_image = cv2.imread(latest_image_string)

	last_photo_width = 240
	last_photo_height = 300

	last_img = cv2.resize(latest_image, (last_photo_width, last_photo_height))
	background[194:(194+last_photo_height), 85: (85+last_photo_width)] = last_img
	return latest_image_stream

#display yes / no box
def access_granted_display(latest_image_string):
	global green_background
	target_age_text = GenerateText((35, 20), fontsize, '#0f0', 'black', f"{age}")

	latest_image = cv2.imread(latest_image_string)
	access_granted_image_alpha = cv2.imread('access-granted-alpha-2.png')
	green_mask = cv2.imread('green-mask.png')

	last_photo_width = 750
	last_photo_height = 450

	last_img = cv2.resize(latest_image, (last_photo_width, last_photo_height))
	layered_img = cv2.add(last_img, green_mask)
	layered_img_2 = cv2.bitwise_and(layered_img,access_granted_image_alpha)

	if (enter == True):
		if (gender == 'female'):
			green_background = cv2.imread('female-green-stretched.png')
			green_background[120:(120+last_photo_height), 25: (25+last_photo_width)] = layered_img_2
			green_background[46: (46+20) ,717: (717+35)] = target_age_text

		elif (gender == 'genderless'):
			green_background = cv2.imread('genderless-green-stretched.png')

		else:
			green_background = cv2.imread('male-green-stretched.png')
	else:
		pass

display_target_cat()
latest_image_stream, latest_image_string = latest_file()
access_granted_display(latest_image_string)

while(True):

	#magnets normally on
	GPIO.output(37, GPIO.HIGH)

	#read cam frame by frame
	ret, frame = cap.read()

	#turn it up the right way
	frame = cv2.flip(frame, 1)
	# make it black and white
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	frame = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)

	just_capture = frame.copy()	
	timestamp = round(time.time()*10)
	#draw it on the screen
	#[(y0, yn), (x0, xn)]
	draw_frame = cv2.resize(frame, (240, 300))

	#draw current frame on this part of background
	background[194: 494, 470: 710] = draw_frame

	# choose which background to display
	if (enter == True):
		cv2.imshow('Target', green_background)
	else:
		#display live cam feed to screen, quit if q pressed
		cv2.imshow('Target', background)
		#(height, width, channels) = background.shape
		
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

    # how often to send an image to api for analysis, frequency in seconds
	frequency = 2
	if(timestamp%(frequency*10) == 0):
		# take the most recent image
		latest_image_stream, latest_image_string = latest_file()

		# detect a face in an image that contains a single face
		detected_faces = face_client.face.detect_with_stream(latest_image_stream, return_face_attributes=['age', 'gender'])

		if (detected_faces):
			print('detecting face', timestamp)
			# display the categorised image
			display_last_image(latest_image_string)
			detected_age = detected_faces[0].face_attributes.age
			detected_gender = detected_faces[0].face_attributes.gender
			if (detected_gender == gender and detected_age == age):
				enter = True
				print('enter')
				GPIO.output(37, GPIO.LOW)
				access_granted_display(latest_image_string)
				time.sleep(20)
				# reset white background after 20 seconds
				# choose a new random persona
				age, gender = random_persona()
				set_background(gender)
				display_target_cat()
				save_image(timestamp, just_capture)

				pass

			else: 
				enter = False
				print('do not enter')
				display_last_cat()
				save_image(timestamp, just_capture)
		else:
			enter = False
			print('face not detected')
			detected_age = 0
			detected_gender = 'none'
			display_last_image(latest_image_string)
			display_last_cat()
			save_image(timestamp, just_capture)

			pass

cap.release()
cv2.destroyAllWindows()
