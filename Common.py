# User defined files
# V12 7/20/23 Added text to display tracking ID on bounding box of display image rectIM
# V11 4/25/23
# Thomas Zimmerman IBM Research-Almaden, Center for Cellular Construction (https://ccc.ucsf.edu/) 
# This work is funded by the National Science Foundation (NSF) grant No. DBI-1548297 
# Disclaimer:  Any opinions, findings and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the National Science Foundation.

import cv2 # for font

# files
VID_FILE_NAME = r'blep_14sec.mp4' # video you want to process
OBJECT_ARRAY_FILE_NAME = 'trackOutput.csv' # provide a file name where all the detection, tracking and features are stored

# Video processing
THRESH=60 
MIN_AREA=1000
MAX_AREA=11000
BLUR=7

MAX_FRAME = 999           # number of frames to process, if max frame is greater than framcount, read all the frames of the movie
START_FRAME = 1
PAUSE = 10                  # number of milliseconds between frame read, using waitKey(PAUSE) command
DEBUG = 1                 # shows detection and tracking frame-by-frame (but slows down processing)
PROCESS_REZ = (1920,1080) # processing resolution, video frames reduced in size to speed up processing
#DISPLAY_REZ = PROCESS_REZ     # display resolution
DISPLAY_REZ = (640,360)     # display resolution
THICK=3                 # ROI box line thickness

NUMBER_MEDIAN_FRAMES=25 # number of random frames to calculate median frame brightness
skipFrames=1  # give video image autobrightness (AGC) time to settle

# tracker
MAX_MATCH_DISTANCE=50  # obj must be this close or better to track ID, couold be as low as 20 based on analysis
MAX_DELTA_AREA=0.6      # use to be .3, tracker won't match with object if caused large percent change in area
[GOOD_MATCH,BIG_DISTANCE,BIG_DELTA_AREA,ALL_ASSIGNED,ZERO_AREA]=range(0,5)


# obj file header and index pointers
header='FRAME,TRACK_ID,MATCH_STATUS,ASSIGNED,TRACK_DISTANCE,DELTA_AREA,X0,Y0,X1,Y1,XC,YC,AREA,SPEED,ASPECT_RATIO'
OBJ_ARRAY_COL=15 # used to create objectArray
[FRAME,TRACK_ID,MATCH_STATUS,ASSIGNED,TRACK_DISTANCE,DELTA_AREA,X0,Y0,X1,Y1,XC,YC,AREA,SPEED,ASPECT_RATIO]=range(0,OBJ_ARRAY_COL)

# Text to display tracking id next to bounding box
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_OFFSET_X = 10
FONT_OFFSET_Y = 10
FONT_SCALE = 2
FONT_COLOR = (0,255,0) #GREEN
FONT_THICKNESS = 2
