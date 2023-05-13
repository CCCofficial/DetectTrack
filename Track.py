# Tracker
# V11 4/25/23
# Thomas Zimmerman IBM Research-Almaden, Center for Cellular Construction (https://ccc.ucsf.edu/) 
# This work is funded by the National Science Foundation (NSF) grant No. DBI-1548297 
# Disclaimer:  Any opinions, findings and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the National Science Foundation.

import numpy as np
import math
import Common as C # constants used by all programs


# find all distance combinations, sort low to high to get index, pick lowest distance for each new obj and assign ID
def findID(objectArray,frameCount,nextID, begin0,end0,end1):
    #find all distance combinations,
    nc=end1-end0            # objects in current frame
    mc=end0-begin0          # objects in previous frame
    d=np.zeros((nc*mc))     # array holding distance between all combinations of current and previous frame objects
    for n in range(nc):     # current frame
        for m in range(mc): # last frame
            i=(n*mc+m)      # creating an index based on base_mc
            dx=objectArray[end0+n,C.XC]-objectArray[begin0+m,C.XC]  # xc of new object - xc of old object
            dy=objectArray[end0+n,C.YC]-objectArray[begin0+m,C.YC]  # yc of new object - yc of old object
            d[i]=math.sqrt(dx*dx+dy*dy)
    
    #sort low to high to get index, pick lowest distance for each new obj and assign ID
    di=np.argsort(d)    # get index of distances sorted in ascending order (small to large)
    assigned=[]         # list of all new objects assigned to id's from last frame
    for i in range(nc*mc):
        j=di[i]                 # get the index from list of ascending distances 
        n=int(j/mc); m=j-n*mc;     # get current obj (n) and previous obj (m) from the index
        #print('i,j,n,m',i,j,n,m,'nc,mc',nc,mc,',begin0,end0,end1',begin0,end0,end1)
        if n not in assigned and objectArray[begin0+m,C.ASSIGNED]==0:   # if current AND previous obj not assigned, assign previous obj ID to current obj
            objectArray[end0+n,C.TRACK_ID]=objectArray[begin0+m,C.TRACK_ID] # assign current object id of matched object in previous frame
            objectArray[begin0+m,C.ASSIGNED]=1    # indicate previous object has been assigned so it won't be assigned to more than one current object!
            assigned.append(n)                  # indicate current object has been assigned in list, but not objectArray because that will be used in the next frame!
            #if len(assigned)!=nc:
            #    print('assigned',n,end0+n,'to', m, begin0+m,'ID:',objectArray[end0+n,C.TRACK_ID])
    
    # give newID's to new borns (object that appear in current frame that weren't in previous frame)
    if len(assigned)!=nc:
        fullList=list(range(nc))
        newObjList=list(set(fullList)-set(assigned))
        #print('assigned',assigned,'fullList',fullList,'newObjList',newObjList)
        for i in range(len(newObjList)):
            newObj=newObjList[i]
            objectArray[end0+newObj,C.TRACK_ID]=nextID
            print('frame',frameCount,'assigned new ID',int(objectArray[end0+newObj,C.TRACK_ID]))
            nextID+=1
            
    return(objectArray,nextID)
    
def trackObjects(frameCount,nextID,objectArray,begin0,end0,end1): 
    
    # if first frame, can't track, so give everyone object a new ID
    if frameCount==C.START_FRAME:   
        for i in range(begin0,end0):
            objectArray[i,C.TRACK_ID]=nextID
            print('frame',frameCount,'assigned new ID',int(objectArray[i,C.TRACK_ID]))
            nextID+=1
    # process all new objects
    else:
       objectArray,nextID=findID(objectArray,frameCount,nextID,begin0,end0,end1)
    return(objectArray,nextID)


