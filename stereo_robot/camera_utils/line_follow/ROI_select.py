"""Interactive GUI for selecting the region of interest.

This function should only be called from an if __name__=="__main__" wrapper,
and has a catcher if not. The script has 2 menus

Controls:
 | **[Double Click]**   - Select ROI corner. Make selection in the order BL, TL, TR, BR.
 | **[z]**              - Undoes the most recent ROI corner
 | **[s]**              - Saves ROI points to ROI_select.json. Will only save if 4 corners are selected
 | **[q]**              - Exit GUI

Notes
-----
Need to change save location from the json method to the Config Module. Further, this should be converted to SI units instead of pixels as discussed in NEXT STEPS -> CONVERT TO SI
    
This GUI should probably be moved to the calibration function. Result is saved in a ROI_select.json file. This should be converted to work with the new Config module.
"""
import cv2, json, os
import numpy as np

os.chdir(os.path.dirname(os.path.realpath(__file__)))


def cam_read(camera):
    """Camera utility to retrieve and split a stereo pair frame.
    
    Notes
    -----
    This function is sprinkled in almost every module to be used in the __name__=="__main__" scrip test. Instances of this utility should be placed in one module.
    """
    ret,frame = camera.read()
    if not ret:
        raise Exception("Could not read camera. Check cables. Might need to use legacy camera drivers")
    h,w,c = frame.shape
    print(frame.shape)
    cut_left = frame[:,:int(w/2)]
    cut_right = frame[:,int(w/2):]
    
    left = cv2.resize(cut_left,(w,h))
    right=cv2.resize(cut_right,(w,h))
    
    return ret,left

## Part 2: Select colors that fit

def perspective_transform(frame,orig_frame_shape,roi_points,desired_roi_points):
    """Perform the perspective transform.

    Extended Summary
    ----------------
    Calculates the perspective transform's transformation matrix and transforms frame.
    
    Parameters
    ----------
    frame : <class 'numpy.ndarray'>
        Current frame

    orig_frame_shape : tuple of int
        The shape of the original frame
    
    roi_points : <class 'numpy.ndarray'>
        ROI points selected using ROI_select.py
    
    desired_roi_points : <class 'numpy.ndarray'>
        The shape of the original frame
            
    Returns
    -------
    warped_frame : <class 'numpy.ndarray'>
        The  birds-eye-view frame.  [dtype=uint8], [size=(h,w,3)]
        
    inv_transformation_matrix : <class 'numpy.ndarray'>
        the transformation matrix used to convert birds eye view coords to original frame coords
    
    Notes
    -----
    From Addison Sears Collins:

     | "Imagine you’re a bird. You’re flying high above the road lanes below.  From a birds-eye view, the lines on either side of the lane look like they are parallel
     | However, from the perspective of the camera mounted on a car below, the lane lines make a trapezoid-like shape. We can’t properly calculate the radius of curvature of the lane because, from the camera’s perspective, the lane width appears to decrease the farther away you get from the car.
     | In fact, way out on the horizon, the lane lines appear to converge to a point (known in computer vision jargon as vanishing point).

    This is different from the one found in line_follow_main because it calculates perspective transform every time since it is changes every time we change the ROI corners. It's slower, but we don't need speed for this routine.

    """

    # Calculate the transformation matrix
    transformation_matrix = cv2.getPerspectiveTransform(
      roi_points, desired_roi_points)

    # Calculate the inverse transformation matrix           
    inv_transformation_matrix = cv2.getPerspectiveTransform(
      desired_roi_points, roi_points)

    # Perform the transform using the transformation matrix
    warped_frame = cv2.warpPerspective(
      frame, transformation_matrix, orig_frame_shape, flags=(
     cv2.INTER_LINEAR))
    
#     (thresh, binary_warped) = cv2.threshold(
#       warped_frame, 127, 255, cv2.THRESH_BINARY)           
#     warped_frame = binary_warped
    
    return warped_frame,inv_transformation_matrix

def _main():
    """Interactive GUI for selecting the region of interest.
    
    Extended Summary
    ----------------
    This function should only be called from an if __name__=="__main__" wrapper,
    and has a catcher if not. The script has 2 menus
    
    Controls:
     | **q** Exit GUI
     | **Double Click** Select ROI corner. Make selection in the order BL, TL, TR, BR.
     | **z** Undoes the most recent ROI corner
     | **s** Saves ROI points to ROI_select.json. Will only save if 4 corners are selected
    
    Notes
    -----
    Need to change save location from the json method to the Config Module. Further, this should be converted to SI units instead of pixels as discussed in NEXT STEPS -> CONVERT TO SI
    
    
    """
    if __name__!="__main__":
        raise Exception("Cannot use this function in this context. Only intended for use in ROI_select.py")
        return
    ROI_POINTS = []
    def mouse_event(event,x,y,flags,param):
        global mouseX,mouseY
        if event == cv2.EVENT_LBUTTONDBLCLK:
    #         cv2.circle(frame,(x,y),3,(0,255,255),-1)
            ROI_POINTS.append([x,y])
            mouseX,mouseY = x,y
            
    cam = cv2.VideoCapture(0)
    ret,frame=cam_read(cam)

    cv2.namedWindow("orig_frame")
    cv2.namedWindow("warped frame")
    cv2.setMouseCallback('orig_frame',mouse_event)
    top_adj=0
    bot_adj=0
    while True:
        ret,frame=cam_read(cam)
        
        if not ret:
            print("failed to grab frame")
            break
        
        shapes = np.zeros_like(frame)
        out = frame.copy()

        for ROI in ROI_POINTS:
            cv2.circle(out,(ROI),2,(0,255,255),-1)
        if len(ROI_POINTS)==4:
            cv2.fillPoly(shapes, np.int_([ROI_POINTS]), (0,255, 0))
            
            BL,TL,TR,BR = ROI_POINTS
            
            
            
            
            width,height = frame.shape[::-1][1:]
            padding = int(0.25 * width)
            DESIRED_ROI_POINTS = np.float32([
              [padding, 0], # Top-left corner
              [padding, height], # Bottom-left corner         
              [width-padding, height], # Bottom-right corner
              [width-padding, 0] # Top-right corner
            ])
            np_ROI_POINTS = np.float32(ROI_POINTS)
            np_ROI_POINTS[0]-=np.array([bot_adj,0])
            np_ROI_POINTS[1]-=np.array([top_adj,0])
            np_ROI_POINTS[2]+=np.array([top_adj,0])
            np_ROI_POINTS[3]+=np.array([bot_adj,0])
            warped_frame,inv_mat = perspective_transform(
                frame,
                (width,height),
                np_ROI_POINTS,
                DESIRED_ROI_POINTS)
            cv2.imshow("warped frame",warped_frame)
        mask = shapes.astype(bool)
        out[mask] = cv2.addWeighted(frame,0.5,shapes,0.5,0)[mask]

        cv2.imshow("orig_frame",out)
        
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord("q"):
            break
        if key == ord("i"):
            top_adj+=1
        if key == ord("k"):
            top_adj-=1
        if key == ord("j"):
            bot_adj-=1
        if key == ord("l"):
            bot_adj+=1
        elif key == ord("z"):
            if len(ROI_POINTS)!=0:
                ROI_POINTS.pop(-1)
            
        elif key == ord("s"):
            ROI_json = {
                'ROI_POINTS':np_ROI_POINTS
                }
            with open('./ROI_JSON.json','w') as f:
                json.dump(ROI_json,f)
            print(f"SAVED TO {os.path.abspath('./')}/ROI_POINTS.json")

    cam.release()
    cv2.destroyAllWindows()

if __name__=="__main__":
    _main()
