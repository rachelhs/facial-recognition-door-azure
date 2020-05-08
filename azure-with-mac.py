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
from io import BytesIO
import cv2

KEY = os.environ['FACE_SUBSCRIPTION_KEY']
ENDPOINT = os.environ['FACE_ENDPOINT']

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

#start cam
cap = cv2.VideoCapture(0)

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

while(True):
	#read cam frame by frame
	ret, frame = cap.read()	
	timestamp = round(time.time()*10)
    #how often to take a picture and analyse
	frequency = 10
	if(timestamp%(frequency*10) == 0):
		save_image(timestamp, frame)

		    # Detect a face in an image that contains a single face
		latest_image = latest_file()
		detected_faces = face_client.face.detect_with_stream(latest_image, return_face_attributes=['age', 'gender'])

		if (detected_faces):
			age = detected_faces[0].face_attributes.age
			gender = detected_faces[0].face_attributes.gender
			print(age, gender)
		else:
			print('no face')
			pass

cap.release()


