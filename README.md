# DetectTrack
Detect and track multiple objects in video. Detects objects by removing background with a median filter, applying blurring to remove holes in objects, applies a threshold to binary quantize the image (can be adjusted with the keyboard), then uses the FindContour command from the computer vision library (CV2) to find objects. Tracking assigns an identification label to an object by finding the closes object in the previous frame.  
## Detect.py 
Contains the function detectTrackFeature(C.VID_FILE_NAME,C.THRESH) that you call, proving a video and threshold level, defined in the file containing all the constants (Common.py). At the bottom of the code is a short test program that calls the detectTrackFeature() function. Disable this if you want to call this function from another module. Feature extraction is not included in this program so some columns of the trackOutput.csv will be zero. 
## Track.py
Called by Detect.py to track objects by matching each object in the current frame with the closest object in the past frame. Objects in the current frame that were not matched are given new ID numbers.
## Common.py 
Contains all the constants used by the programs (Detect.py and Track.py)
## detectImageGUI.py
GUI to detect objects in images in a directory
## detectVideoGUI.py
GUI to detect objects from frames of a video
## trackOutput.csv
An example of tracking output for the file blep_14sec.mp3
## blep_14sec.mp4
A 14 second video (1920x1080) taken with a lensless microscope of multiple blepharisma swimming around to test detect and tracker.

