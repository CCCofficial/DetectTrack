'''
Cam Tracker 
Thomas Zimmerman IBM Research-Almaden, Center for Cellular Construction (https://ccc.ucsf.edu/) 
This work is funded by the National Science Foundation (NSF) grant No. DBI-1548297 
Disclaimer:  Any opinions, findings and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the National Science Foundation.

"Cams" (short for "cameras") are windows that activly capture and track objects. 
Cams persist, so when an object disappears due to falling below the detection threshold, they can be tracked if and when they reapper. 
However, if they are gone for more than a max still count, the cam is released and available to track a new object.
Image is blurred then a threshold is applied to binary quantize objects, then a threshold is applied.
Tracking ID's are NOT saved

4.22.24 Adapted for holography using blur + threshold detection
'''

import numpy as np
import cv2
from random import randint
import time


vid=r'HoloVideo.mp4'   # <======== Put link to your video here
xRez=640; yRez=480;     # video is resized to this rez to speed up processing

LIVE=0 # 0=play back video 1=use live cam
MAX_CAM=150 # number of cams to run
CAM_STEP=2 # number of pixels to move tracking cam
WANDER_STEP=5 # max number of pixels to move acquiring cam
MOVES_PER_FRAME=20 # number of CAM_STEPS tracking can move in a frame

cam=np.zeros((MAX_CAM,10),dtype=int) # x,y,state
CAM_X=0; CAM_Y=1; CAM_XDIR=2; CAM_YDIR=3; CAM_STATE=4; CAM_ID=5; CAM_VEL_X=6; CAM_VEL_Y=7; CAM_STILL_COUNT=8; CAM_AREA_COUNT=9;
FREE=0; ACQUIRE=1; TRACK=2; # cam state

camStat=np.zeros((5),dtype=int)
FREE_COUNT=0; ACQUIRE_COUNT=1; TRACK_COUNT=2; MOVING_COUNT=3; STILL_COUNT=4;
    
keyState=0;
keyBuf=np.zeros((256),dtype=int)
keyBuf[ord('t')]=70     # threshold after blur
keyBuf[ord('b')]=12     # blur size
keyBuf[ord('a')]=10     # min area an object must have to be detected
keyBuf[ord('A')]=2000   # max area (minArea+value), else cam released as FREE 
keyBuf[ord('c')]=40     # cam size (length and width)
keyBuf[ord('m')]=2      # min number of pixels (x+y) a cam must move in a frame to be counted as moving, else STILL_COUNT is incremented
keyBuf[ord('M')]=30     # max still count, if exceeds, object is labeled dead 

clip = lambda x, l, u: l if x < l else u if x > u else x # clip routine clip(var,min,max)

def processKey(key):
    global keyState;

    if key==ord('='):
        keyBuf[keyState]+=1
    elif key==ord('+'):
        keyBuf[keyState]+=10
    elif key==ord('-') and keyBuf[keyState]>1:
            keyBuf[keyState]-=1
    elif key==ord('_') and keyBuf[keyState]>10:
            keyBuf[keyState]-=10
    else:
        keyState=key

    #print ("fps:",frameRate,"TRACK:",camStat[TRACK_COUNT],"ACQ:",camStat[ACQUIRE_COUNT],"FREE:",camStat[FREE_COUNT],"moving:",camStat[MOVING_COUNT],"still:",camStat[STILL_COUNT],chr(keyState),"=",keyBuf[keyState])
    print (chr(keyState),"=",keyBuf[keyState])
    return

def doCollision(im):
    # if both cams are TRACK and collide, free cam with more black (creatures are white)
    # if both ACQUIRE or FREE, let pass through each other
    # if one TRACK and other is ACQUIRE, make ACQUIRE FREE
    global cam
    
    for i in range(MAX_CAM):
        a=[cam[i,CAM_X],cam[i,CAM_Y],cam[i,CAM_X]+camSize,cam[i,CAM_Y]+camSize]
        for j in range(MAX_CAM):
            if (i!=j):
                b=[cam[j,CAM_X],cam[j,CAM_Y],cam[j,CAM_X]+camSize,cam[j,CAM_Y]+camSize]
                if intersection(a,b):
                    # if both cams are TRACK and collide, free cam with more black (creatures are white)
                    if (cam[j,CAM_STATE]==TRACK and cam[j,CAM_STATE]==TRACK):
                        sumi=np.sum(im[cam[i,CAM_Y]:cam[i,CAM_Y]+camSize,cam[i,CAM_X]:cam[i,CAM_X]+camSize])
                        sumj=np.sum(im[cam[j,CAM_Y]:cam[j,CAM_Y]+camSize,cam[j,CAM_X]:cam[j,CAM_X]+camSize])
                        if sumi>sumj:
                            cam[j,CAM_STATE]=FREE
                        else:
                            cam[i,CAM_STATE]=FREE
                    # if one TRACK and other is ACQUIRE, make ACQUIRE FREE
                    elif (cam[i,CAM_STATE]==TRACK and cam[j,CAM_STATE]==ACQUIRE):
                        cam[j,CAM_STATE]=FREE
                    elif (cam[j,CAM_STATE]==TRACK and cam[i,CAM_STATE]==ACQUIRE):
                        cam[i,CAM_STATE]=FREE
    return()

def intersection(a,b):
    intersect=0 # assume no intersection
    count=0
    if (b[0]>=a[0] and b[0]<=a[2]) or (b[2]>=a[0] and b[2]<=a[2]):
        count+=1
    if (b[1]>=a[1] and b[1]<=a[3]) or (b[3]>=a[1] and b[3]<=a[3]):
        count+=1
    if count==2:
        intersect=1
    return(intersect)

def wander(camID):
    global cam
    # return place to move cam, to center edge in cam
    cam[camID,CAM_X]+=cam[camID,CAM_XDIR]
    cam[camID,CAM_Y]+=cam[camID,CAM_YDIR]
    if cam[camID,CAM_X]+camSize>=xRez or cam[camID,CAM_X]<0:
        cam[camID,CAM_XDIR]=-cam[camID,CAM_XDIR]
        cam[camID,CAM_X]+=cam[camID,CAM_XDIR]
    if cam[camID,CAM_Y]+camSize>=yRez or cam[camID,CAM_Y]<0:
        cam[camID,CAM_YDIR]=-cam[camID,CAM_YDIR]
        cam[camID,CAM_Y]+=cam[camID,CAM_YDIR]
    return()

def moveCenter(im,camID):
    startX=cam[camID,CAM_X]; startY=cam[camID,CAM_Y]; 
    lastX=0; lastY=0;
    for s in range(MOVES_PER_FRAME):
        x0=cam[camID,CAM_X]; x1=int(x0+camSize/2);  x2=x0+camSize;
        y0=cam[camID,CAM_Y];  y1=int(y0+camSize/2);  y2=y0+camSize;
        topLeft=np.sum(im[y0:y1,x0:x1])
        topRight=np.sum(im[y0:y1,x1:x2])
        bottomLeft=np.sum(im[y1:y2,x0:x1])    
        bottomRight=np.sum(im[y1:y2,x1:x2])
        dX=0; dY=0;
        if (topLeft+topRight)>(bottomLeft+bottomRight):
            dY=-CAM_STEP
        elif (topLeft+topRight)<(bottomLeft+bottomRight):
            dY=CAM_STEP
        if (topLeft+bottomLeft)>(topRight+bottomRight):
            dX=-CAM_STEP
        elif (topLeft+bottomLeft)<(topRight+bottomRight):
            dX=CAM_STEP
        newX=clip(x0+dX,0,xRez-camSize);
        newY=clip(y0+dY,0,yRez-camSize);
        cam[camID,CAM_X]=newX;
        cam[camID,CAM_Y]=newY;
        if newX==lastX and newY==lastY: # quit loop if no change to save time
            break
        lastX=newX; lastY=newY;
    cam[camID,CAM_VEL_X]=newX-startX
    cam[camID,CAM_VEL_Y]=newY-startY

    movement=abs(cam[camID,CAM_VEL_X])+abs(cam[camID,CAM_VEL_Y])
    #area=topLeft+topRight+bottomLeft+bottomRight
    x0=cam[camID,CAM_X]; y0=cam[camID,CAM_Y];
    area=int(np.sum(im[y0:y0+camSize,x0:x0+camSize])/256)  # divide by 256 because each binary pixel brighness=256
    return(movement,area)


def createCam(camID):
    global cam
    
    #set random cam movement direction
    cam[camID,CAM_XDIR]=randint(-WANDER_STEP,WANDER_STEP)
    cam[camID,CAM_YDIR]=randint(-WANDER_STEP,WANDER_STEP)

    # do again if both are zero, assume retry won't both be zero
    if (cam[camID,CAM_XDIR]==0 and cam[camID,CAM_YDIR]==0):
        cam[camID,CAM_XDIR]=randint(-WANDER_STEP,WANDER_STEP)
        cam[camID,CAM_YDIR]=randint(-WANDER_STEP,WANDER_STEP)
    
    # assign random position 
    cam[camID,CAM_X]=randint(0,xRez);
    cam[camID,CAM_Y]=randint(0,yRez);

    # reset other variables
    cam[camID,CAM_STATE]=ACQUIRE
    cam[camID,CAM_STILL_COUNT]=0;
    cam[camID,CAM_AREA_COUNT]=0;
    cam[camID,CAM_VEL_X]=0;
    cam[camID,CAM_VEL_Y]=0;
    return

def updateCam(im):
    global cam
    
    for camID in range(MAX_CAM):
        case=cam[camID,CAM_STATE]
        if case==FREE: #unassigned so drop in a random place with no other cam around
            createCam(camID)
        elif case==ACQUIRE:
            wander(camID)
            (movement,area)=moveCenter(im,camID)  # if nothing in cam, will free cam after empty for too long
            if area>=minArea and area<maxArea:
                #print(camID,area)
                cam[camID,CAM_STATE]=TRACK
        elif case==TRACK:
            (movement,area)=moveCenter(im,camID)
            # check area
            if area<minArea:
                cam[camID,CAM_AREA_COUNT]+=1
            else:
                cam[camID,CAM_AREA_COUNT]=0
            if cam[camID,CAM_AREA_COUNT]>maxArea:
                cam[camID,CAM_STATE]=FREE
            #check movement
            if movement<minMovement:
                cam[camID,CAM_STILL_COUNT]+=1
                if cam[camID,CAM_STILL_COUNT]>maxStillCount:  # not moving for awhile so tread as dead and release cam
                    cam[camID,CAM_STATE]=FREE
            else:
                cam[camID,CAM_STILL_COUNT]=0
        else:
            print ('ERROR CAM_STATE:'),cam[camID,CAM_STATE]
    return
    

def markCam(im):
    global camStat
    camStat[:]=0
    #FREE_COUNT=0; ACQUIRE_COUNT=1; TRACK_COUNT=2; MOVING_COUNT=3; STILL_COUNT=4;
    
    for i in range(MAX_CAM):
        x0=cam[i,CAM_X]; y0=cam[i,CAM_Y]; x1=x0+camSize; y1=y0+camSize
        if cam[i,CAM_STATE]==FREE:
            camStat[FREE_COUNT]+=1
        elif cam[i,CAM_STATE]==ACQUIRE:
            camStat[ACQUIRE_COUNT]+=1
            color=(255,0,0) #BGR
            #cv2.rectangle(im,(x0,y0),(x1,y1), color, 2)
        elif cam[i,CAM_STATE]==TRACK:
            camStat[TRACK_COUNT]+=1
            tinyWarn=0; stillWarn=0;
            if cam[i,CAM_AREA_COUNT]>0:    
                tinyWarn=1
            if cam[i,CAM_STILL_COUNT]>0: 
                stillWarn=1;
            else:
                camStat[MOVING_COUNT]+=1

            # color BGR
            if (tinyWarn==0 and stillWarn==0):     
                color=(0,255,0)                     # good track=GREEN
            elif (tinyWarn==1 and stillWarn==0):
                color=(0,255,255)                   # tiny= YELLOW
            elif (tinyWarn==0 and stillWarn==1):
                color=(255,0,255)                   # still = MAGENTA
            elif (tinyWarn==1 and stillWarn==1):
                color=(0,0,255)                     # still and tiny = RED
                
            cv2.rectangle(im,(x0,y0),(x1,y1), color, 2)
    return(im)

##################### MAIN ############################
# set up video 
if (LIVE==1):
    cap = cv2.VideoCapture(1)
    HORIZ=640; VERT=480; #cap.set(3,1280),    #cap.set(4,960)
    #HORIZ=1280; VERT=960; #cap.set(3,1280),    #cap.set(4,960)
    cap.set(3,HORIZ)
    cap.set(4,VERT)
else:
    cap = cv2.VideoCapture(vid)   
    print ('totalFrames:',cap.get(cv2.CAP_PROP_FRAME_COUNT))

xFullRez=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
yFullRez=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print ('Original Rez:',xFullRez,yFullRez)

firstPass=1;
firstFrame=None
camView=np.zeros((yRez,xRez,3))    

# start capturing frames of video 
while(cap.isOpened()):
    start_time = time.time()
    ret, frameFull = cap.read()
    if not ret:
        print ('fractionPlayed:',cap.get(cv2.CAP_PROP_POS_AVI_RATIO))
        break
    frame = cv2.resize(frameFull, (xRez, yRez)) # resize for faster processing
      
# process keyboard
    key=cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
      
    if key!=255:
        processKey(key)
    
# define keyboard modifiable variable
    blurK=keyBuf[ord('b')]*2+1 # must be an odd value
    threshK=keyBuf[ord('t')]
    minArea=keyBuf[ord('a')]
    maxArea=minArea+keyBuf[ord('A')]
    camSize=keyBuf[ord('c')]
    minMovement=keyBuf[ord('m')]
    maxStillCount=keyBuf[ord('M')]
    
# image processing
    grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurFrame = cv2.GaussianBlur(grayFrame, (blurK, blurK), 0)
    threshFrame = cv2.threshold(blurFrame, threshK, 255, cv2.THRESH_BINARY_INV)[1]
    #print ('threshDeltaSum:',threshDelta.sum())
    
# update cams
    updateCam(threshFrame);        
    doCollision(threshFrame) # if two cams collide, free cam with more white

# view cams  
    camView[:,:,0]=threshFrame
    camView[:,:,1]=threshFrame
    camView[:,:,2]=threshFrame
    
    color=(255,255,255)

    camView=markCam(camView)
            
    cv2.imshow('gray',grayFrame)
    cv2.imshow('blur',blurFrame)
    cv2.imshow('detect',threshFrame)
    cv2.imshow('camView',camView)
        
#restart video if at end
    if cap.get(cv2.CAP_PROP_POS_AVI_RATIO)>0.6:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

# calculate frame rate
    dTime=time.time() - start_time
    frameRate=int(1/dTime)
# quit program

print ('done')
cap.release()
cv2.destroyAllWindows()

