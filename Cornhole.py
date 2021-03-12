#!/usr/bin/env python3

import cv2
import math
import numpy as np
import sys

def inch_to_meter(x):
	return x * 0.0254

# Papalook AF925
# taken from https://www.amazon.ca/PAPALOOK-AF925-360-Degree-Reduction-Microphone/dp/B07HGXGKQD
CAMERA_H_FOV = math.radians(65.0)
CAMERA_V_FOV = math.radians(48.75)  # approximate, assuming same vertical as horizontal resolution

ROI = ((512,256), (1536, 768))

HOLE_DIAMETER = inch_to_meter(6.0 + 2.0 + 2.0)

MIN_R = 190
MAX_R = 255
MIN_G = 75
MAX_G = 92
MIN_B = 13
MAX_B = 86

def smooth_image(img):
	return cv2.medianBlur(img, 5)

def crop_roi(img):
	"""
	Blank out everything except the ROI
	"""
	mask = img.copy()
	cv2.rectangle(mask, (0,0), (len(img[0]), len(img)), (0,0,0), -1)
	cv2.rectangle(mask, ROI[0], ROI[1], (255,255,255), -1)

	img = cv2.bitwise_and(img, mask)
	return img

def find_hole(img):
	img = smooth_image(img)

	binary_img = cv2.inRange(img, (MIN_B, MIN_G, MIN_R), (MAX_B, MAX_G, MAX_R))
	kernel = np.ones((5,5),np.uint8)
	binary_img = cv2.dilate(binary_img, kernel)
	binary_img = cv2.erode(binary_img, kernel)

	edge = cv2.Canny(binary_img, 30, 100)
	cv2.imshow('edge', edge)
	_, contours, hierarchy = cv.findContours(edge, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
#	_, contours, hierarchy = cv.findContours(edge, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

	max_x, max_y = 0
	min_x, min_y = 9999

	for cont in contours:
		for point in cont:
			min_x = min(min_x, point[0])
			max_x = max(max_x, point[0])
			min_y = min(min_y, point[1])
			max_y = max(max_y, point[1])

	x = (min_x + max_x)/2
	y = (min_y + max_y)/2
	width = max_x - min_x
	return (x, y, width)

	return None

if __name__=='__main__':
	cap = cv2.VideoCapture(0)
	cap.set(3, 1920)
	cap.set(4, 1080)
	while(True):
		ret, img_read = cap.read()

		cv2.imwrite("im_read.png", img_read)
		img = crop_roi(img_read)

		hole_dims = find_hole(img)

		if hole_dims != None:
			angular_width = CAMERA_H_FOV / len(img[0]) * hole_dims[2]

			cv2.circle(img_read,(int(hole_dims[0]),int(hole_dims[1])), hole_dims[2]/2,(0,255,0),3)
			distance = HOLE_DIAMETER/2 / math.tan(angular_width/2)

			angle = ( )( x / len(img[0]) ) * CAMERA_H_FOV ) - CAMERA_H_FOV / 2
			print("D: {0}m, A: {1}".format(distance, angle))

		cv2.imshow('hole', img_read)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
