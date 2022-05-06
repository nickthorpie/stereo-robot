import sys,os
# sys.path.append("/home/pi/PycharmProjects/StereoRobot/src")

# import stereo_robot
# from stereo_robot import StereoCamera
import cv2, json
import numpy as np

# os.chdir(os.path.dirname(os.path.realpath(__file__)))
# print("Trying to import config")
# import config
# print("Success")

## PART 1: Capture image for calibration
def cam_read(cam):
#     ret,frame = cam.read()
    ret,frame =  True,cv2.imread("/home/pi/stereoRobot/stereo_robot/camera_utils/stereo_camera/calibration/scenes/photo.png")

    if not ret:
        raise Exception("Could not read camera. Check cables. Might need to use legacy camera drivers")
    h,w,c = frame.shape
    print(frame.shape)
    cut_left = frame[:,:int(w/2)]
    cut_right = frame[:,int(w/2):]
    
    left = cv2.resize(cut_left,(w,h))
    right= cv2.resize(cut_right,(w,h))
    
    return ret,left


if __name__=="__main__" :#and False:
    cam = None#cv2.VideoCapture(0)
    cv2.namedWindow("test")

    while True:
        ret,frame=cam_read(cam)
        if not ret:
            print("failed to grab frame")
            break
        cv2.imshow("test",frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break


#     cam.release()
    cv2.destroyAllWindows()

    ## Part 2: Select colors that fit

    saved_colors = []
    HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    def mouse_event(event,x,y,flags,param):
        global mouseX,mouseY
        if event == cv2.EVENT_LBUTTONDBLCLK:
    #         cv2.circle(frame,(x,y),3,(0,255,255),-1)
            saved_colors.append(HSV[y,x])
            mouseX,mouseY = x,y

    cv2.namedWindow('image')
    cv2.setMouseCallback('image',mouse_event)

    while(1):
        cv2.imshow('image',frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()


    ## part 3: allow user to adjust with sliders
    saved_colors = np.array(saved_colors)
    H_max = np.max(saved_colors[:,0])
    S_max = np.max(saved_colors[:,1])
    V_max = np.max(saved_colors[:,2])

    H_min = np.min(saved_colors[:,0])
    S_min = np.min(saved_colors[:,1])
    V_min = np.min(saved_colors[:,2])

    def nothing(x):
        pass
    cv2.namedWindow('threshold')
    cv2.createTrackbar('H_HI','threshold',H_max,255,nothing)
    cv2.createTrackbar('S_HI','threshold',S_max,255,nothing)
    cv2.createTrackbar('V_HI','threshold',V_max,255,nothing)
    cv2.createTrackbar('H_LO','threshold',H_min,255,nothing)
    cv2.createTrackbar('S_LO','threshold',S_min,255,nothing)
    cv2.createTrackbar('V_LO','threshold',V_min,255,nothing)

    while True:
        H_HI = cv2.getTrackbarPos('H_HI','threshold')
        S_HI = cv2.getTrackbarPos('S_HI','threshold')
        V_HI = cv2.getTrackbarPos('V_HI','threshold')
        H_LO = cv2.getTrackbarPos('H_LO','threshold')
        S_LO = cv2.getTrackbarPos('S_LO','threshold')
        V_LO = cv2.getTrackbarPos('V_LO','threshold')
        
        bounds_HI = (H_HI,S_HI,V_HI)
        bounds_LO = (H_LO,S_LO,V_LO)
        thresh_mask = cv2.inRange(HSV,bounds_LO,bounds_HI)
        thresh_mask = cv2.cvtColor(thresh_mask,cv2.COLOR_GRAY2BGR)
        thresh_frame = HSV & thresh_mask
        thresh_frame_BGR = cv2.cvtColor(thresh_frame,cv2.COLOR_HSV2BGR)
        cv2.imshow("threshold",thresh_frame_BGR)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        
        if key == ord("s"):
            bounds_json = {
                'bounds_HI':bounds_HI,
                'bounds_LO':bounds_LO
                }
            with open('./thresh_data.json','w') as f:
                json.dump(bounds_json,f)
            print(f"SAVED TO {os.path.abspath('./')}/thresh_data.json")
    cv2.destroyAllWindows()
