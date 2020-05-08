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
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, SnapshotObjectType, OperationStatusType
import cv2
from gpiozero import LED, Button
import random

KEY = os.environ['FACE_SUBSCRIPTION_KEY']
ENDPOINT = os.environ['FACE_ENDPOINT']

#set initial age and gender states
age = 25
gender = "female"

#initialise GPIO pin 17 to trigger magnets
magnets = LED(17)
button = Button(2)

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
	return image_stream

#select random persona on doorbell press
def random_persona():
	gender = random.choice(['female', 'male', 'genderless'])
	age = random.randrange(100)

while(True):
	#for testing generate random personas automatically
	#age, gender = random_persona()
	button.when_pressed = random_persona()


	#magnets normally on
	magnets.on()

	#read cam frame by frame
	ret, frame = cap.read()	
	timestamp = round(time.time()*10)
	
	#display live cam feed to screen, quit if q pressed
	cv2.imshow('Target', frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

    	#how often to take a picture and analyse
	frequency = 10
	if(timestamp%(frequency*10) == 0):
		save_image(timestamp, frame)

		    # Detect a face in an image that contains a single face
		latest_image = latest_file()
		detected_faces = face_client.face.detect_with_stream(latest_image, return_face_attributes=['age', 'gender'])

		if (detected_faces):
			detected_age = detected_faces[0].face_attributes.age
			detected_gender = detected_faces[0].face_attributes.gender
			print('target age', age, 'target gender', gender)
			print('detected age', detected_age, 'detected gender', detected_gender)
			if (detected_age == age and detected_gender == gender):
				magnets.off()
				time.sleep(3)
		else:
			print('no face')
			pass

cap.release()
cv2.destroyAllWindows()

