"""
Stores the CameraClient class to grab frames, along with a camera utility"""

# relative imports.
try:
    from .line_follow import LineFollow
except:
    print("Can't import .line_follow relatively, trying import linefollow")
    from line_follow import LineFollow

# standard imports
import cv2,time
import numpy as np
from pyzbar import pyzbar


def display(im, bbox):
    bbox = np.array(bbox,dtype=int)
    n = len(bbox)
    for j in range(n):
        print(j)
        arg1 = tuple(bbox[j][0])
        arg2 = tuple(bbox[ (j+1) % n][0])
        
        cv2.line(im, arg1, arg2, (255,0,0), 3)

    # Display results
    cv2.imshow("Results", im)



def cam_read(cam):
    """Reads camera and returns the left half of frame
    
    Extended Summary
    ----------------
    This function was intended to split an image pair that results from using a stereo camera. Reads a cv2.VideoCapture(0) frame, and the left half of the frame. The left frame is resized to dimensions of the original frame. Uses the same output as camera.read() so that it is easy to go back and forth.
    
    Parameters
    ----------
    cam : <class 'cv2.VideoCapture'>
        The OpenCV camera interface, which should be initialized globally as camera =  cv2.VideoCapture(0)
    
    Returns
    -------
    ret : bool
        Indicates whether the camera was successfully read. Always returns true, otherwise exception an exception is raised. Only implemented for continuity between camera.read()
    left_frame_resized : <class 'numpy.ndarray'>
        The resized left image as a numpy array with [dtype=uint8], [size=(h,w,3)]
    
    """
    ret,frame = cam.read()
    if not ret:
        errmsg = "Could not read camera. \n(1) try sudo pkill python\n"
        errmsg+= "(2) Check cables. \n(3) Might need to use legacy camera drivers"
        raise Exception(errmsg)
    h,w = frame.shape[:2]
    left_frame_cut = frame[:,:int(w/2)]
    right_frame_cut = frame[:,int(w/2):]
    
    left_frame_resized = cv2.resize(left_frame_cut,(w,h))
    right_frame_resized =cv2.resize(right_frame_cut,(w,h))
    
    return ret,left_frame_resized


def CameraClient(q_camera,cam):
    """Camera client that handles all image capture and processing
    
    Extended Summary
    ----------------
    This camera client reads a camera, then processes the camera to extract information about the line and QR codes. The camera client is designed to be run on a separate multiprocessing thread. Initialize using multiprocessing's  Process(target = CameraClient, args = (q_camera,cam)) (see :py:mod:`stereo_robot.main` for an example). This client processes the line and qr features and publishes new information into the queue. It also shows a live preview of the processed video feed.
    
    Parameters
    ----------
    q_camera : <class 'multiprocessing.queues.Queue'>
        A multiprocessing queue used to publish the most recent camera data. This data is stored as a dictionary in the form {"top":int,"bottom":(int),"confidence":(int),"barcode":(str)}. See notes for more detailed information about what these values are.
    cam : <class 'cv2.VideoCapture'>
        The OpenCV camera interface, which should be initialized globally as camera =  cv2.VideoCapture(0)
    
    Notes
    -----
    This module will also be used to process depth mapping. See NEXT STEPS.
    Details about each of the q_camera dictionary values are as follows:
    "top" : (float)
    FINISH THIS WHEN DONE WRITING LINE FOLLOW CLASS hi
    
    """
    
    message = {"top":None,"bottom":None,"confidence":0,"barcode":None}
    q_camera.put(message)
#     cam = cv2.VideoCapture(0)
    ret,frame = cam_read(cam)
    
    line = LineFollow(frame)
    barcodeData = None
    
    cv2.namedWindow("lane_line_markings")
    cv2.namedWindow("result")
#     cv2.namedWindow("warped_frame")
    while True:
        ret,frame = cam_read(cam)
        
        (ret,
        lane_line_markings,
        result,
        p1,p2,
        confidence,
        barcodeData) = line.find_line(frame,)
        
        capture_time = time.time()
        h,w = lane_line_markings.shape[:2]
        
        #TODO: This is a messy way of passing the QR code info.
        # The QR reader is burried in LineFollow(), but we need the
        # information in direction_control.py. It's path looks like
        # LineFollow.step() -> camera_client -> camera_queue -> direction_control
        # It is initiallized in camera_queue as None, then we update
        # to the QR value when it's first found. in direction_control
        # we check if the QR value is new by comparing it with most recent value
        
        if barcodeData is not None:           
            message["barcode"] = barcodeData
        if ret:
            message["top"] = p2
            message["bottom"] = p1
            message["confidence"] = max(min(confidence*100,100),0)
            message["message_time"]=capture_time
            q_camera.put(message)
            
        if ret:
            cv2.imshow("result",result)
        else:
            cv2.imshow("result",frame)
        cv2.imshow("lane_line_markings",lane_line_markings)
        cv2.waitKey(1)

if __name__=="__main__":
    from multiprocessing import Queue
    cam = cv2.VideoCapture(0)
    q = Queue()
    try:
        proc = CameraClient(q,cam)
    finally:
        cv2.destroyAllWindows()
