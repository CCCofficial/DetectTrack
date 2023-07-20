# Detect and Track objects to get location, features and ID
# V12 7/20/23 Added text to display tracking ID on bounding box of diplay image rectIM
# V11 4/25/23
# Thomas Zimmerman IBM Research-Almaden, Center for Cellular Construction (https://ccc.ucsf.edu/) 
# This work is funded by the National Science Foundation (NSF) grant No. DBI-1548297 
# Disclaimer:  Any opinions, findings and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the National Science Foundation.

import Track as T
import numpy as np
import cv2
import Common as C

# set up text for displaying track id on tracking rectangle
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_OFFSET_X = 10
FONT_OFFSET_Y = 10
FONT_SCALE = 2
FONT_COLOR = (0,255,0) #GREEN
FONT_THICKNESS = 2

def checkROI(xMaxRez, yMaxRez, xx0, yy0, xx1, yy1):
    xx0 -= C.ENLARGE
    yy0 -= C.ENLARGE 
    xx1 += C.ENLARGE
    yy1 += C.ENLARGE
    touch = 0         # assume enlarged ROI does not touch boundary
    #print (xMaxRez, yMaxRez, xx0, yy0, xx1, yy1)
    x0 = max(xx0, 0)   # check for negative
    x1 = min(xx1, xMaxRez) # check for too big 
    y0 = max(yy0, 0)
    y1 = min(yy1, yMaxRez)
    #print (x0, x1, y0, y1)
    if x0 != xx0 or x1 != xx1 or y0 != yy0 or y1 != yy1: # if changed any, report touch image boarder
        touch = 1
    return(touch, x0, y0, x1, y1)

def maskIM(colorIM, threshIM, cnt, x0, y0, x1, y1):
    # create a mask based on image contour
    blackIM = np.zeros_like(threshIM)
    cv2.drawContours(blackIM, [cnt], -1, 255, -1) # function takes array of arrays so need [objContour] !!!
    binaryROI = blackIM[y0:y1,x0:x1]
    colorROI = colorIM[y0:y1,x0:x1]
    colorROI = cv2.bitwise_and(colorROI,colorROI,mask = binaryROI)
    grayROI = cv2.cvtColor(colorROI, cv2.COLOR_BGR2GRAY)     # convert color to grayscale image
    return(colorROI, grayROI, binaryROI)

def getMedian(VID, numberMedianFrames, PROCESS_REZ):
    # Open Video
    print ('openVideo:', VID)
    cap = cv2.VideoCapture(VID)
    if(cap.isOpened()):  # get median if video can be opened
        maxFrame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print('maxFrame', maxFrame)
        
        # Randomly select N frames
        print('calculating median with',numberMedianFrames,'frames')
        frameIds = C.skipFrames + (maxFrame - C.skipFrames) * np.random.uniform(size = numberMedianFrames)
        frames = [] # Store selected frames in an array
        
        for fid in frameIds:
            #print (fid) 
            cap.set(cv2.CAP_PROP_POS_FRAMES, fid)
            ret, frame = cap.read()
            colorIM = cv2.resize(frame, PROCESS_REZ)
            grayIM = cv2.cvtColor(colorIM, cv2.COLOR_BGR2GRAY)
            frames.append(grayIM)
        
        medianFrame = np.median(frames, axis = 0).astype(dtype = np.uint8)     # Calculate the median along the time axis   
        cv2.imshow('BkgIM', cv2.resize(medianFrame, C.DISPLAY_REZ))      # display reduced imag        
        print('full frame shape',frame.shape)
        print('processing frame shape',medianFrame.shape,'\n')
        cap.release()
    else:
        print('ERROR: Could not open video', VID)
        medianFrame=0
    return (medianFrame)

def imageProcessing(colorIM, medianFrame, thresh):
    grayIM = cv2.cvtColor(colorIM, cv2.COLOR_BGR2GRAY)      # convert color to grayscale image
    diffIM = cv2.absdiff(grayIM, medianFrame)   # Calculate absolute difference of current frame and the median frame
    blurIM = cv2.blur(diffIM,(C.BLUR*2+1, C.BLUR*2+1)) # must be odd number 
    ret, threshIM = cv2.threshold(blurIM, thresh, 255, cv2.THRESH_BINARY) # threshold image to make pixels 0 or 255
    contourList, hierarchy = cv2.findContours(threshIM, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[-2:] # all countour points, uses more memory
    return(grayIM, diffIM, threshIM, blurIM, contourList)

# display the image processing and tracking results, pausing if tracking error occurs
def display(frameCount,rectIM,diffIM,threshIM,objectArray,begin0,end0,end1):  
    printError=1        # 1=print errors 0=don't print errors
    anyError=0          # 1=at least one error occured in frame  
    for i in range(end0,end1):
        # draw bounding box in color representing ID
        x0 = int(objectArray[i, C.X0])
        x1 = int(objectArray[i, C.X1])
        y0 = int(objectArray[i, C.Y0])
        y1 = int(objectArray[i, C.Y1])
        match = objectArray[i, C.MATCH_STATUS]
        trackID = int(objectArray[i, C.TRACK_ID])
        #print(frameCount,i,x0,x1,y0,y1,match,trackID)
        # make colors for display
        if match == C.GOOD_MATCH:    # Color of ID, good match
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (0, 255, 0), C.THICK)        # GREEN good match
        elif match == C.BIG_DISTANCE:   
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (0, 0, 255), C.THICK)         # RED big distance
            if printError: 
                print('Frame',frameCount,'i:',i,'Max Distance Error:',round(objectArray[i,C.TRACK_DISTANCE]))    
        elif match == C.BIG_DELTA_AREA:  
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (255, 0, 0), C.THICK)         # BLUE big delta area 
            if printError: 
                print('Frame',frameCount,'i:',i,'Max dArea Error:',round(objectArray[i,C.DELTA_AREA],2))    
        elif match == C.ALL_ASSIGNED:   
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (255, 255, 0), C.THICK)       # CYAN all assigned
            if printError: 
                print('Frame',frameCount,'i:',i,'All Assigned Error')    
        elif match == C.ZERO_AREA:             
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (0, 255, 255), C.THICK)       # MAGENTA zero area
            if printError: 
                print('Frame',frameCount,'i:',i,'Zero Area Error')    
        else:
            cv2.rectangle(rectIM, (x0, y0), (x1, y1), (255, 255, 255), C.THICK)     # WHITE unknown areazero area
            if printError: 
                print('Frame',frameCount,'i:',i,'Unknown Error')    
                
        # put trackID text on tracking bounding box
        rectIM = cv2.putText(rectIM, str(trackID), (x1+C.FONT_OFFSET_X,y1+C.FONT_OFFSET_Y), C.FONT, C.FONT_SCALE, C.FONT_COLOR, C.FONT_THICKNESS, cv2.LINE_AA)
        
        if match!=C.GOOD_MATCH: # pause to see error display
            anyError=1          # indicate a tracking error occured             
    #cv2.imshow('rectIM', cv2.resize(rectIM, C.DISPLAY_REZ))
    cv2.imshow('rectIM', cv2.resize(rectIM, C.DISPLAY_REZ))
    cv2.imshow('diffIM', cv2.resize(diffIM, C.DISPLAY_REZ))        # display thresh image
    cv2.imshow('threshIM', cv2.resize(threshIM, C.DISPLAY_REZ))      # display reduced imag        
    if anyError:    #delay display when any tracking error occurs for good visibility
        cv2.waitKey(1000)
    return

# update threshold with keyboard, return flag if 'q' hit to end program
def updateKbd(thresh):
    key=chr(cv2.waitKey(C.PAUSE) & 0xFF) # pause in msec from common constant file
    endProgram=0
    if key== 'q':
        endProgram=1
    elif key=='=':
        thresh+=1
        print ('Thresh=',thresh)
    elif key=='+':
        thresh+=10
        print ('Thresh=',thresh)
    elif key=='-' and thresh>1:
        thresh-=1
        print ('Thresh=',thresh)
    elif key=='_' and thresh>11:
        thresh-=10
        print ('Thresh=',thresh)
    return(thresh,endProgram)            
    
# processes video, returns obj file with obj location, features, etc for video
def detectTrackFeature(VID, thresh):
    # Create objectArray to store object features
    objectArray = np.zeros((0, C.OBJ_ARRAY_COL), dtype = 'float') # array of all objects for all frames
    objectArrayZero = np.zeros((1, C.OBJ_ARRAY_COL), dtype = 'float') # one row filled with zeros to append at beginning of loop
    cap = cv2.VideoCapture(VID)
    cap.set(cv2.CAP_PROP_POS_FRAMES, C.START_FRAME)
    frameCount = C.START_FRAME    # keep video reader and object processing in sync
    oi = 0          # current object index, points into objectArray
    begin0 = 0      # first obj of last frame
    end0 = 0        # last obj of last frame (begin1 = end0 so no need for this variable!)
    end1 = 0        # last obj of current frame
    nextID=0 # start ID with 0
    
    medianFrame = getMedian(VID, C.NUMBER_MEDIAN_FRAMES, C.PROCESS_REZ) # create median frame
    
    # process video frames 
    while(cap.isOpened()):  # start frame capture
        (thresh,endProgram)=updateKbd(thresh)
        if frameCount > C.MAX_FRAME or endProgram:
            print ("Last Frame or 'q' pressed to End Program, bye")
            break
        
        # get image
        ret, colorIM = cap.read()
        if not ret: # check to make sure there was a frame to read
            print('No frame detected, bye')
            break        
        colorIM = cv2.resize(colorIM, C.PROCESS_REZ)
        (yColorIM, xColorIM, color) = colorIM.shape        
        rectIM = np.copy(colorIM) # make copy that can be marked up with rectangles

        
        # detect objects in image, put object data into objectArray
        (grayIM, diffIM, threshIM, blurIM, contourList) = imageProcessing(colorIM, medianFrame, thresh)
        for objContour in contourList:
            # only take objects within acceptable area
            area = cv2.contourArea(objContour)
            if area > C.MIN_AREA and area<C.MAX_AREA:
                # Get bounding box and center coordinates
                PO = cv2.boundingRect(objContour)
                x0 = PO[0];                 y0 = PO[1]
                x1 = x0 + PO[2];            y1 = y0 + PO[3]
                xc = x0 + (x0 + x1) / 2;    yc = y0 + (y0 + y1) / 2
                
                # Save object features into objectArray
                objectArray = np.append(objectArray, objectArrayZero, axis = 0)  # append empty row to objectArray, then fill with values 
                objectArray[oi, C.FRAME] = frameCount
                objectArray[oi, C.X0 : C.YC + 1] = (x0, y0, x1, y1, xc, yc)
                objectArray[oi, C.AREA] = area
                oi += 1                                                   # end of processing object so increment obj index
            elif area>C.MAX_AREA: # print area of large rejected object
                print('reject max area:',int(area))
                
        # Finished processing objects in frame. Get indexing locations for tracker
        if frameCount == C.START_FRAME:
            begin0 = 0      # first obj of last frame 
            end0 = oi       # last obj of last frame
            objectArray,nextID = T.trackObjects(frameCount,nextID,objectArray,begin0,end0,end1)  # track frame
        else:
            end1=oi         # pointer is end of current frame
            objectArray,nextID = T.trackObjects(frameCount,nextID,objectArray,begin0,end0,end1)  # track frame
            display(frameCount,rectIM,diffIM,threshIM,objectArray,begin0,end0,end1)  
            
            #move points for next frame
            begin0=end0     # end of last frame become beginning of last frame 
            end0=end1       # end of current frame becomes end of last frame
        frameCount += 1           # increment frame counter
        
    #objectArray = F.calcSpeed(objectArray)  # calc speed and place in obj feature columns    
    cap.release()
    cv2.destroyAllWindows()
    return(objectArray)


########## TEST ###########
if True:
    print('Processing Video',C.VID_FILE_NAME,'with threshold',C.THRESH)
    objectArray = detectTrackFeature(C.VID_FILE_NAME,C.THRESH)
    np.savetxt(C.OBJECT_ARRAY_FILE_NAME, objectArray, header = C.header, fmt = '%f', delimiter = ',') # saves numpy array as a csv file    
    print('Saved objectArray in file:',C.OBJECT_ARRAY_FILE_NAME)        

