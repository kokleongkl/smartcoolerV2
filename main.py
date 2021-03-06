import os
import cv2
import time
import cognitive_face as CF
import requests
import threading
import serial
import multiprocessing
import pygame as PG
from Call import *
from Frame import *
from Session import *
from Query import *
from Switch import *
from PIL import Image
from requests.packages.urllib3.exceptions import InsecureRequestWarning

#Prevent warning request dialogue when calling Face API
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#Instantiate object from defined classes
smartCooler = Session()
demograph = Query()
temp = Frameimage()
switch = Switch(serial)
voice = Call()

#Clear pre-exsiting image which might contain a face already
os.remove("frame.jpg")

#Start camera session for realtime recording and PyGame
smartCooler.startSession(CF)
liquidStudio = CF.person.lists(smartCooler.getGroup())
PG.mixer.init()

#Args (0 or 1) based on in-built or webcam camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#Function to control anything inside the camera window
def camCapture():	
	while True:
		#Capture every single frame
		ret,frame = cap.read()
		frame = cv2.resize(frame, (1080,720), interpolation = cv2.INTER_LINEAR)
		frame = cv2.copyMakeBorder(frame,155,155,450,450,cv2.BORDER_CONSTANT,value=[0,0,0])

		#Make shape and text around face detected (Max:1)
		#cv2.rectangle(frame, (0, ), (300,20),(255, 255, 255), cv2.FILLED)
		cv2.putText(frame,"Welcome to Liquid Studio Smart Cooler",(700,100),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
		cv2.rectangle(frame, (temp.left, temp.top), (temp.left + temp.width, temp.top + temp.height),(0, 255, 0), 3)
		cv2.putText(frame, '{},{},{}'.format(temp.getIdentity(),temp.gender, int(temp.age)), (temp.left, temp.top),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255))

		#Display webcam footage
		smartCooler.setWindow(cv2,frame)	
		
		if cv2.waitKey(10) == 27:
			break

#Function to perform video analytics within each frame
def frameProcess():
	while True:
		try:
			#Define the detection parameters
			result = CF.face.detect("frame.jpg",attributes = "age,gender,smile,emotion,hair")
			if not result:
				temp.setCounter()
				temp.setDefaultFraming()
				temp.clearIdentityName()
				temp.clearIdentitySound()

			else:
				for face in result:
					#Reset the identification counter when face matches
					temp.resetCounter()

					#Face Attributes
					faceID = face["faceId"]
					gender = face['faceAttributes']['gender']
					age = face['faceAttributes']['age']
					smile = face['faceAttributes']['smile']
					emotion = face['faceAttributes']['emotion']
					hair = face['faceAttributes']['hair']

					#demograph.create(gender,age,smile,emotion,hair)

					temp.setAttributes(faceID,gender,age,smile)

					#Face rectangle framing
					rect = face['faceRectangle']
					temp.setFraming(rect)
					temp.setIdentificationSound()
		except:
			pass

#Function to perform face idetification
def faceIdentify():
	while True:
		try:
			#Captured frame is stored in an array
			faceArray = []
			faceArray.append(temp.faceID)

			#Iterates and check if face matches anyone with a PersonGroup
			for person in liquidStudio:
				verifyPerson = CF.face.verify(temp.faceID,None,smartCooler.getGroup(),None,person["personId"])
				if verifyPerson["isIdentical"] == True:
					temp.setIdentification(person["name"])
					sms.setMobile(person["userData"])
					if switch.checkDoor() == "Opened":
						if voice.retSpeakerFlag() == 0:
							smartCooler.actVoiceFlag()
		except:
			pass

def switchChecking():
	while True:
		#print (smartCooler.retVoiceFlag())
		if smartCooler.retVoiceFlag() == 1:
			voice.startSmartCooler(temp.getIdentity())
			smartCooler.removeVoiceFlag()
			voice.playedOnce()

		if switch.read() == "1":
			switch.openDoor()
		elif switch.read() == "0":
			switch.closeDoor()
			temp.reset()
			smartCooler.reset()
			voice.reset()
		
if __name__ == '__main__':

	#1 - Camera elements
	#2 - Face attributes
	#3 - Face verification
	#4 - Switch 

	thread1 = threading.Thread(target=camCapture)
	thread2 = threading.Thread(target=frameProcess)
	thread3 = threading.Thread(target=faceIdentify)
	thread4 = threading.Thread(target=switchChecking)

	thread1.start()
	thread2.start()
	thread3.start()
	thread4.start()

	thread1.join()
	thread2.join()
	thread3.join()
	thread4.join()

	cap.release()
	cv2.destroyAllWindows()  # destroy all the opened window
