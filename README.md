# DetectTrack
Detect and track multiple objects in video. Detects objects by removing background with a median filter, applying blurring to remove holes in objects, applies a threshold to binary quantize the image (can be adjusted with the keyboard), then uses the FindContour command from the computer vision library (CV2) to find objects. Tracking assigns an identification label to an object by finding the closes object in the previous frame.  
## Detect_11.py 
Contains the function detectTrackFeature(C.VID_FILE_NAME,C.THRESH) that you call, proving a video and threshold level, defined in the file containing all the constants (Common_11.py)
## Track_11.py
Called by Detect_11.py to track objects by matching each object in the current frame with the closest object in the past frame. Objects in the current frame that were not matched are given new ID numbers..
## Common_11.py 
Contains all the constants used by the programs (Detect_11.py and Track_11.py)

