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
CAMERA_V_FOV = math.radians(36.5625)  # approximate, assuming same vertical as horizontal resolution

# Camera location relative to Kuka World
CAM_X = 1.19846
CAM_Z = 1.48887
#CAM_Z = 1.4
CAM_ANGLE = math.radians(20.0)

OUT_SCALE = 0.5

ROI = ((350,250), (1920-350, 1080-250))

HOLE_DIAMETER = inch_to_meter(9.75)

MIN_R = 220
MAX_R = 255
MIN_G = 138
MAX_G = 166
MIN_B = 125
MAX_B = 149

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
	cv2.imshow('edge', cv2.resize(edge, None,fx=OUT_SCALE, fy=OUT_SCALE))
	contours, hierarchy = cv2.findContours(edge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	if len(contours) < 1:
		return None
	else:
		max_x = 0
		max_y = 0
		min_x = 9999
		min_y = 9999

		for cont in contours:
			for point in cont:
				min_x = min(min_x, point[0][0])
				max_x = max(max_x, point[0][0])
				min_y = min(min_y, point[0][1])
				max_y = max(max_y, point[0][1])

		x = (min_x + max_x)/2
		y = (min_y + max_y)/2
		return (x, y)

if __name__=='__main__':
	cap = cv2.VideoCapture(0)
	cap.set(3, 1920)
	cap.set(4, 1080)
	while(True):
		ret, img_read = cap.read()
		#img_read = cv2.imread("85-5.png")
		img_read = cv2.rotate(img_read, cv2.ROTATE_180)
		cv2.imwrite("im_read.png", img_read)
		img = crop_roi(img_read)

		hole_pos = find_hole(img)

		if hole_pos != None:
			h_angle = ( ( hole_pos[0] / len(img[0]) ) * CAMERA_H_FOV ) - CAMERA_H_FOV / 2
			v_angle = ( ( hole_pos[1] / len(img[1]) ) * CAMERA_V_FOV ) - CAMERA_V_FOV / 2 + CAM_ANGLE
			cam_h_distance = CAM_Z / math.tan(v_angle)

			# SAS
			throw_length = math.sqrt( CAM_X*CAM_X + cam_h_distance*cam_h_distance - 2 * CAM_X * cam_h_distance * math.cos(3.14159 - h_angle) )
			throw_angle = math.acos( ( CAM_X*CAM_X + throw_length*throw_length - cam_h_distance*cam_h_distance ) / ( 2 * CAM_X * throw_length ) )
			throw_angle = math.degrees(throw_angle)

			cv2.circle(img_read,(int(hole_pos[0]),int(hole_pos[1])), int(50),(0,255,0),3)

			print("D: {0}m, A: {1}".format(throw_length, throw_angle))
			Power = 0.866 * throw_distance + 0.476
			Angle = 0.702 * throw_angle + 6.95

		cv2.imshow('hole', cv2.resize(img_read, None, fx=OUT_SCALE, fy=OUT_SCALE))

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
