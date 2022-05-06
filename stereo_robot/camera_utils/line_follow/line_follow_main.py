"""
A collection of functions that are inspired/borrowed from AutomaticAddison's `tutorial`_ using the Sliding Window Technique.

.. _tutorial: https://automaticaddison.com/the-ultimate-guide-to-real-time-lane-detection-using-opencv/>

This

"""

import cv2, json, os
import numpy as np # Import the NumPy scientific computing library
os.chdir(os.path.dirname(os.path.realpath(__file__)))
from pyzbar import pyzbar
# Author: Addison Sears-Collins
# https://automaticaddison.com
# Description: A collection of methods to detect help with edge detection

# Read threshhold data This should will be taken out and substituted with the new config module
with open("./thresh_data.json",'r') as f:
    thresh_data = json.load(f)
    thresh_HI = thresh_data['bounds_HI']
    thresh_LO = thresh_data['bounds_LO']

with open("./ROI_JSON.json",'r') as f:
    ROI_data = json.load(f)
    BL,TL,TR,BR = ROI_data['ROI_POINTS']
    ROI_POINTS = np.float32([TL,BL,BR,TR,])
    

def get_perspective_transform_matricies(roi_points,desired_roi_points):
    """Perform the perspective transform.
    
    Extended Summary
    ----------------
    Takes the original frame, along with
     
    
    Parameters
    ----------
        roi_points : <class 'numpy.ndarray'>
            ROI points selected using ROI_select.py
        
        desired_roi_points : <class 'numpy.ndarray'>
            The shape of the original frame
    Returns
    -------
        transformation_matrix : <class 'numpy.ndarray'>
            the transformation matrix used to convert original frame coords to birds eye view
        
        inv_transformation_matrix : <class 'numpy.ndarray'>
            the transformation matrix used to convert birds eye view coords to original frame coords
            
    Notes
    -----
    From Addison Sears Collins:
     | "Imagine you’re a bird. You’re flying high above the road lanes below.  From a birds-eye view, the lines on either side of the lane look like they are parallel
     | However, from the perspective of the camera mounted on a car below, the lane lines make a trapezoid-like shape. We can’t properly calculate the radius of curvature of the lane because, from the camera’s perspective, the lane width appears to decrease the farther away you get from the car.
     | In fact, way out on the horizon, the lane lines appear to converge to a point (known in computer vision jargon as vanishing point).
     
    See Also
    --------
    stereo_robot.camera_utils.line_follow.ROI_select.main
        This tool is used to select the roi_points
    
    """
    # Calculate the transformation matrix
    transformation_matrix = cv2.getPerspectiveTransform(
      roi_points, desired_roi_points)

    # Calculate the inverse transformation matrix
    inv_transformation_matrix = cv2.getPerspectiveTransform(
      desired_roi_points, roi_points)
    
    return transformation_matrix, inv_transformation_matrix

#def perspective_transform(frame,transformation_matrix):
#    """Perform the perspective transform.
#
#    Extended Summary
#    ----------------
#    Takes the original frame, along with
#
#    Notes
#    -----
#    From Addison Sears Collins:
#
#     | "Imagine you’re a bird. You’re flying high above the road lanes below.  From a birds-eye view, the lines on either side of the lane look like they are parallel
#     | However, from the perspective of the camera mounted on a car below, the lane lines make a trapezoid-like shape. We can’t properly calculate the radius of curvature of the lane because, from the camera’s perspective, the lane width appears to decrease the farther away you get from the car.
#     | In fact, way out on the horizon, the lane lines appear to converge to a point (known in computer vision jargon as vanishing point).
#
#     This was pieced together rather quickly, so the
#
#    Parameters
#    ----------
#        frame : <class 'numpy.ndarray'>
#            Current frame
#
#        orig_frame_shape : tuple
#            The shape of the original frame
#
#    Notes
#    -----
#    THIS IS DEPRECATED, ALL FUNCTIONALITY HAS BEEN PULLED OUT OF IT, SHOULD JUST USE cv2.warpPerspective
#    """
#
#    # Perform the transform using the transformation matrix
#    warped_frame = cv2.warpPerspective(
#      frame, transformation_matrix, frame.shape[::-1][1:],
#      flags=(cv2.INTER_LINEAR)
#      )
#
##     (thresh, binary_warped) = cv2.threshold(
##       warped_frame, 127, 255, cv2.THRESH_BINARY)
##     warped_frame = binary_warped
#
#    return warped_frame

def get_line_markings(orig_frame):
    """Isolates yellow line from surroundings using color thresholding
   
    Parameters
    ----------
    orig_frame : <class 'numpy.ndarray'>
        The camera frame that contains the lanes we want to detect
    Returns
    -------
        yellow_mask : <class 'numpy.ndarray'>
            A binary (i.e. black and white) image containing the lane lines.
    
    Notes
    -----
    This process to isolate lane markings is extremely rudimentary. There are much more rigorous approaches such as that used in Addison Sears Collins' Lane Detection tutorial, however this simple thresholding was sufficient for lane testing.
    """
    hsv = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array(thresh_LO)
    upper_yellow = np.array(thresh_HI)
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
#     yellow_image = cv2.bitwise_and(image, image, mask=yellow_mask)
    
    # Combine the two above images
    
    return yellow_mask

def calculate_histogram_vert(warped_frame):
    """Calculate the image histogram to find peaks in white pixel count, to find starting position for sliding window search
    
    Parameters
    ----------
    
    warped_frame : <class 'numpy.ndarray'>
        The thresholded birds-eye-view frame.  [dtype=uint8], [size=(h,w)]
        
    Returns
    -------
    histogram : <class 'numpy.ndarray'>
        An array where each element the sum of its corresponding column in the warped_frame. Only takes into account the bottom half of the frame. [dtype=uint8], [size=(w)]
    
    Notes
    -----
    From Addison Sears Collins:
     | Looking at the warped image, we can see that white pixels represent pieces of the lane lines.
     | We start lane line pixel detection by generating a histogram to locate areas of the image that have high concentrations of white pixels.
    """
    frame = warped_frame
             
    # Generate the histogram
    histogram = np.sum(frame[int(
              frame.shape[0]/2):,:], axis=0)
        
    return histogram

def histogram_peak(warped_frame):
    """Creates a histogram and determines the index where the maximum histogram value is.
    
    Parameters
    ----------
        warped_frame : <class 'numpy.ndarray'>
            The thresholded birds-eye-view frame.  [dtype=uint8], [size=(h,w)]
    
    Returns
    -------
        x_base : int
            The index of the maximum histogram value.
    """
    histogram = calculate_histogram_vert(warped_frame)
    x_base = np.argmax(histogram)
    return x_base

def get_lane_line_indices_sliding_windows(warped_frame,MINPIX,MARGIN):
    """Get the indices of the lane line pixels using the sliding windows technique.
    
    Parameters
    ----------
    warped_frame : <class 'numpy.ndarray'>
        The thresholded birds-eye-view frame.  [dtype=uint8], [size=(h,w)]
        
    MINPIX : int
        the minimum number of pixels for a sliding window to count as a valid lane index.
    
    MARGIN : int
        The width of each sliding window (times 2)
        
    Returns
    -------
    fit : <class np.ndarray>
        the coefficients of the 1st degree polynomial used to fit the line in the form x = fit[0]*y+fit[1].
    confidence:
        the confidence level of the line.
        
    
        
    Notes
    -----
    Starts at the starting index found with :py:meth:`histogram_peak`.
     
    From Addison Sears-Collins
     The next step is to use a sliding window technique where we start at the bottom of the image and scan all the way to the top of the image. Each time we search within a sliding window, we add potential lane line pixels to a list. If we have enough lane line pixels in a window, the mean position of these pixels becomes the center of the next sliding window.
     Once we have identified the pixels that correspond to the left and right lane lines, we draw a polynomial best-fit line through the pixels. This line represents our best estimate of the lane lines.
    
    The confidence level is calculated as follows: for each window i, the confidence Ci is calculated as Ci = num_valid_pixels/MINPIX. The total confidence is the average of all Ci. This is a very basic method which could be thought out better.
    """
    #TODO: move no_of_windows, MINPIX, MARGIN to Config Module
    
    no_of_windows = 20
    
    
    minpix = MINPIX #????
    # Sliding window width is +/- margin
    margin = MARGIN #???
 
    frame_sliding_window = warped_frame.copy()
 
    # Set the height of the sliding windows
    window_height = np.int(warped_frame.shape[0]/no_of_windows)       
 
    # Find the x and y coordinates of all the nonzero 
    # (i.e. white) pixels in the frame. 
    nonzero = warped_frame.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1]) 
         
    # Store the pixel indices for the left and right lane lines
    lane_inds = []
         
    # Current positions for pixel indices for each window,
    # which we will continue to update
    x_base = histogram_peak(warped_frame)
    x_current = x_base
 
    # Go through one window at a time
    confidence = 0
    for window in range(no_of_windows):
       
      # Identify window boundaries in x and y (and right and left)
      win_y_low = warped_frame.shape[0] - (window + 1) * window_height
      win_y_high = warped_frame.shape[0] - window * window_height
      win_x_low = x_current - margin
      win_x_high = x_current + margin
      cv2.rectangle(frame_sliding_window,(win_x_low,win_y_low),(
        win_x_high,win_y_high), (255,255,255), 2)

 
      # Identify the nonzero pixels in x and y within the window
      good_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
                          (nonzerox >= win_x_low) & (
                           nonzerox < win_x_high)).nonzero()[0]
                           
      # Append these indices to the lists
      lane_inds.append(good_inds)
         
      # If you found > minpix pixels, recenter next window on mean position
      if len(good_inds) > minpix:
        x_current = np.int(np.mean(nonzerox[good_inds]))
      confidence+=len(good_inds)/minpix        
    # Concatenate the arrays of indices
    lane_inds = np.concatenate(lane_inds)
 
    # Extract the pixel coordinates for the left and right lane lines
    x = nonzerox[lane_inds]
    y = nonzeroy[lane_inds]
    if len(y)<2:
        confidence = 0
    elif (max(y)-min(y)) == 0:
          confidence=0
    else:
        confidence/=(max(y)-min(y))
    if len(x)<3 or len(y)<3:
        return None,0
    # Fit a second order polynomial curve to the pixel coordinates for
    # the left and right lane lines
    fit = np.polyfit(y, x, 1)
             
    return fit, confidence

def get_lane_line_previous_window(warped_frame, fit,MARGIN):
    """Gets x and y coordinates of the fit line used to overlay lane line on plot.
    
    Extended Summary
    ----------------
    Use the lane line from the previous sliding window to get the parameters
    for the polynomial line for filling in the lane line
    
    Parameters
    ----------
    warped_frame : <class 'numpy.ndarray'>
        The thresholded birds-eye-view frame.  [dtype=uint8], [size=(h,w)]
        
    fit : <class 'numpy.ndarray'>
        the coefficients of the 1st degree polynomial used to fit the line in the form x = fit[0]*y+fit[1].
    
    Returns
    -------
    ploty : <class 'numpy.ndarray'>
        The y indicies of the overlay polygon
    fitx : <class 'numpy.ndarray'>
        The x indicies of the overlay polygon
                    
    Notes
    -----
    
    """
    # margin is a sliding window parameter
    margin = MARGIN
 
    # Find the x and y coordinates of all the nonzero 
    # (i.e. white) pixels in the frame.         
    nonzero = warped_frame.nonzero()  
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
         
    # Store lane pixel indices
    lane_inds = (
        (nonzerox > (fit[0]*(nonzeroy) + fit[1] - margin)) & \
        (nonzerox < (fit[0]*(nonzeroy) + fit[1] + margin))
        )
 
    # Get the lane line pixel locations
    x = nonzerox[lane_inds]
    y = nonzeroy[lane_inds]  
 
    # Fit a second order polynomial curve to each lane line
    fit = np.polyfit(y, x, 1)
    
    # Create the x and y values to plot on the image
#     ploty = np.linspace(
#       0, warped_frame.shape[0]-1, warped_frame.shape[0])
    ploty = np.linspace(min(y),max(y),int(max(y)-min(y)),dtype=int)
    fitx = fit[0]*ploty + fit[1] 
    
    
    return ploty,fitx

def overlay_lane_lines(shape,fitx,ploty):
    """Overlay lane lines on an empty image
    
    Parameters
    ----------
    shape : <class 'numpy.ndarray'>
        empty image of zeros to plot line overlay on. [dtype=uint8], [size=(h,w)]
    ploty : <class 'numpy.ndarray'>
        The y indicies of the overlay polygon
    fitx : <class 'numpy.ndarray'>
        The x indicies of the overlay polygon
            
    Returns
    -------
        shape :  <class 'numpy.ndarray'>
            empty image with overlayed fit line overlay on. [dtype=uint8], [size=(h,w)]
    
    Usage
    -----
    >>> warp_zero = np.zeros_like(lane_line_markings)        # create an empty image of warped frame
    >>> shape = np.dstack((warp_zero, warp_zero, warp_zero)) # make with 3 columns
    >>> shape = overlay_lane_lines(shape,fitx,ploty)         # overlay lane line to it
    >>> unwarped = cv2.warpPerspective(                      # unwarp overlay to original
    ...             shape1,                                  #  frame orientation
    ...             self.inv_transformation_matrix,
    ...             frame.shape[::-1][1:])
    >>> result = cv2.addWeighted(frame, 1, unwarped, 0.3, 0) # Add unwarped overlay to OG frame
    """
    # Generate an image to draw the lane lines on 
#     warp_zero = np.zeros_like(warped_frame).astype(np.uint8)
#     color_warp = np.dstack((warp_zero, warp_zero, warp_zero))       
         
    # Recast the x and y points into usable format for cv2.fillPoly()
    pts = np.array([np.transpose(np.vstack([
                         fitx, ploty]))])
    pts_left  = pts - np.array([2,0])
    pts_right = pts + np.array([2,0])
    pts = np.hstack((pts_left, pts_right))
         
    # Draw lane on the warped blank image
    cv2.fillPoly(shape, np.int_([pts]), (0,255, 0))
 
    # Warp the blank back to original image space using inverse perspective 
    # matrix (Minv)
    return shape
     
    # Combine the result with the original image


def get_endpoints(ploty,fitx,h,w):
    """Gets top and bottom of fit line as a percentage of the ROI area.
    
    Extended Summary
    ----------------
    The top/bottom points are expressed as (y,x), where y is the percentage of the point's height from the bottom (0-100), and x is the percentage of the point's distance from the center of the frame (-50 - 50).
    
    Parameters
    ----------
    shape : <class 'numpy.ndarray'>
        empty image of zeros to plot line overlay on. [dtype=uint8], [size=(h,w)]
    ploty : <class 'numpy.ndarray'>
        The y indicies of the overlay polygon
    fitx : <class 'numpy.ndarray'>
        The x indicies of the overlay polygon
    h : int
        the height of the warped frame
    w : int
        the width of the warped frame
    
    Returns
    -------
    pts : tuple
        the coordinates of the top and bottom line coord expressed respectively as ((y_bot,x_bot),(y_top,x_top))
    
    circle_overlays : tuple
        data to overlay circles on warped, threshed frame. See usage.
    
    text_overlays  : tuple
        data to overlay coordinate text on warped, threshed frame. See usage.
        
    Usage
    -----
    >>> pts,circles,putTexts = get_endpoints(ploty,fitx,h,w)
    >>> for circle,putText in zip(circle_overlays,text_overlays):
    ...     cv2.putText(lane_line_markings_col,*putText)          # overlays are designed to easily be passed
    ...     cv2.circle(lane_line_markings_col, *circle)           # using the astrix notation
    
    """
    bot_ind = np.where(ploty==max(ploty))[0][0]  #min b/c camera is positioned at
    top_ind = np.where(ploty==min(ploty))[0][0]  #         the bottom of frame
    
    top_y_pixel = int(ploty[top_ind])
    bot_y_pixel = int(ploty[bot_ind])
    top_x_pixel = int(fitx[top_ind])
    bot_x_pixel = int(fitx[bot_ind])
    
    top_y = 100-top_y_pixel/h*100
    bot_y = 100-bot_y_pixel/h*100
    
    top_x = top_x_pixel/w*100 - 50
    bot_x = bot_x_pixel/w*100 - 50
    
    rad = 3
    font_size = 2
    top_text =  "TOP: ({}, {})".format(int(top_y),int(top_x))
    top_cv2_circle = ((top_x_pixel,top_y_pixel),rad,(0,0,255),2)
    top_cv2_putText = (top_text,
                        (top_x_pixel, top_y_pixel + (rad+10*font_size)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)
    
    bot_text =  "(BOT: {},{})".format(int(bot_y),int(bot_x))
    bot_cv2_circle = ((bot_x_pixel,bot_y_pixel),rad,(0,0,255),2)
    bot_cv2_putText = (bot_text,
                        (bot_x_pixel, bot_y_pixel - (rad+2*font_size)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)

    
    return (
        ((bot_y,bot_x),(top_y,top_x)),
        (top_cv2_circle,bot_cv2_circle),
        (top_cv2_putText,bot_cv2_putText)
        )

class LineFollow:
    """A container to initialize, store and access find_line and it's attributes.
    
    Extended Summary
    ----------------
    Look at LineFollow.find_line for details about how this works
    
    Parameters
    ----------
    init_frame : <class 'numpy.ndarray'>
        a camera frame used to get size information used for find_line
        
    Returns
    -------
    self
    
    Notes
    -----
    This class also contains QR reading. See QR_scan for some implementation notes and future changes.
    
    See Also
    --------
    get_perspective_transform_matricies
    
    
    """
    CONFIG = {
        'padding_percentage':0.25,
        'plot':True
        }
    def __init__(self,init_frame):
        frame = init_frame
        
        width,height = frame.shape[::-1][1:]
        padding = int(0.25 * width)
        DESIRED_ROI_POINTS = np.float32([
          [padding, 0], # Top-left corner
          [padding, height], # Bottom-left corner         
          [width-padding, height], # Bottom-right corner
          [width-padding, 0] # Top-right corner
        ])
        
        self.width,self.height,self.DESIRED_ROI_POINTS = (
             width,     height,     DESIRED_ROI_POINTS)
        
        self.MARGIN = int((1/12) * width)  # Window width is +/- margin
        self.MINPIX = int((1/24) * width)
        
        self.transformation_matrix,self.inv_transformation_matrix = get_perspective_transform_matricies(ROI_POINTS,DESIRED_ROI_POINTS)
                      
    def find_line(self,frame):
        """Processes a frame to detect Line, and QR code.
        
        Extended Summary
        ----------------
        This processes the
        
        Parameters
        ----------
        frame : <class 'numpy.ndarray'>
            Current frame
        
        Returns
        -------
            ret : bool
                True if a lane line or barcode were detected
            lane_line_markings_col : <class 'numpy.ndarray'>
                The warped and thresholded frame annotated with line top/bottom and QR code result. [size=(h,w,3)]
            result : <class 'numpy.ndarray'>
                The original frame annotated with line the fit line and QR code result.
            p1 : tuple of int
                bottom coordinate of line in the warped coordinate system
            p2 : tuple of int
                top coordinate of line in the warped coordinate system
            confidence : int
                confidence estimate of the line. (0-100)
            barcodeData : str or None
                the data from the scanned barcode. If no new data is found, the value is none.
        
        Notes
        -----
        Psuedo Code for this function:
         - Warps frame to birds eye view
         - Scans QR code.
         - Thresholds line markings
         - Fits curve to line with confidence
         - Creates overlay
         
        May be better to threshold before warp for line following, however the warp is used in QR code scanning too so it currently makes more sense to warp the full picture. I also don't like that QR scanning happens inline with the line following. It slows down loop times. If I were to prioritize things for safety, person detection should be first priority, line following should be second priority, and QR should be third. May be better to move QR scanning into its own process, however we already have 3 processes and only 4 cores.
        
        Should add functionality to disable plotting and save steps
        
        See Also
        --------
        stereo_robot.camera_utils.line_follow.ROI_select.main:
            A UI is used to select the roi_points
        stereo_robot.camera_utils.line_follow.calib_color_thresh.main:
            A UI used to select yellow Threshold
        get_line_markings : Thresholds line markings
        get_lane_line_indices_sliding_windows : Fits curve to line with confidence
        get_lane_line_previous_window : Gets points fit curve for overlay
        LineFollow.QR_scan : looks for QR
        """
        # Grab class attributes to make code cleaner.
        width,height,DESIRED_ROI_POINTS=self.width,self.height,self.DESIRED_ROI_POINTS
        MARGIN,MINPIX=self.MARGIN,self.MINPIX
        
        # Get birds eye view
        warped_frame = cv2.warpPerspective(
                            frame,
                            self.transformation_matrix,
                            frame.shape[::-1][1:],
                            flags=(cv2.INTER_LINEAR)
                            )
        
        #Thresholds line markings
        lane_line_markings=get_line_markings(warped_frame)
        
        cv2.imshow("warped_frame",warped_frame)  # Probably shouldn't have this in here? Another good reason to
                                                # move warpPerspective to CameraClient level.
        # Fit line
        fit,confidence = get_lane_line_indices_sliding_windows(
            lane_line_markings,MINPIX,MARGIN)
        
        #Check for barcode
        barcodeData,cv2_rectangle,cv2_putText = self.QR_scan(warped_frame)
        
        lane_line_markings_col = cv2.cvtColor(
                        lane_line_markings,
                        cv2.COLOR_GRAY2BGR).astype(np.float32)
                        
        # If there is something to display (either QR or line), make a blank shape to overlay
        if (fit is not None) or (barcodeData is not None):
            h,w = lane_line_markings.shape[:2]
            warp_zero = np.zeros_like(lane_line_markings)
            shape1 = np.dstack((warp_zero, warp_zero, warp_zero))
            # if there is a line to overlay
            if fit is not None:
                # get line polygon to overlay
                ploty,fitx = get_lane_line_previous_window(
                    lane_line_markings, fit,MARGIN)
                # overlay line polygon on the blank shape
                shape1 = overlay_lane_lines(
                    shape1,
                    fitx,ploty)
                # grab top and bottom points in birds eye view coords (i.e. 1-100) and their overlays
                (p1,p2),circles,putTexts = get_endpoints(ploty,fitx,h,w)
                # plot overlays
                for circle,putText in zip(circles,putTexts):
                    cv2.putText(lane_line_markings_col,*putText)
                    cv2.circle(lane_line_markings_col,*circle)            
            else:
                p1,p2 = (None,None)
            # if there is a QR code to overlay
            if barcodeData is not None:
                cv2.putText(shape1,*cv2_putText)
                cv2.rectangle(shape1,*cv2_rectangle)
            # unwarp the overlay from birds eye view
            unwarped = cv2.warpPerspective(
                shape1,
                self.inv_transformation_matrix,
                frame.shape[::-1][1:]
                )
            # and add it to the original
            result = cv2.addWeighted(frame, 1, unwarped, 0.3, 0)
            # TODO: consider moving all perspective warping and QR code out of line follow
            
#             print("CKP Z1")
            return True,lane_line_markings_col,result,p1,p2,confidence,barcodeData
        else:
#             print("CKP Z2")
            return False,lane_line_markings_col,result,None,None,0,barcodeData
            
    
    
    def QR_scan(self,warped_frame):
        """Checks birds eye view for barcodes
        Parameters
        ----------
        warped_frame : <class 'numpy.ndarray'>
            The thresholded birds-eye-view frame.  [dtype=uint8], [size=(h,w)]
        
        Returns
        -------
        barcodeData : str or None
            The contents of the QR code. Returns None if no QR code was detected
        cv2_rectangle : tuple of args or None
            A set of arguments to overlay a bounding box with cv2.Rectangle. see usage for example.
            
        cv2_putText : tuple of args or None
            A set of arguments to overlay barcodeData in cv2.Rectangle. see usage for example.
        
        Usage
        -----
        >>> barcodeData,cv2_rectangle,cv2_putText = LineFollow.QR_scan(warped_frame)
        >>> if barcodeData is not None:
        ...     cv2.putText(warped_frame,*cv2_putText)
        ...     cv2.rectangle(warped_frame,*cv2_rectangle)
            
        Notes
        -----
        Would be cleaner to have QR scanning happen outside of this class. As a continuation of the notes in line_follow, one solution of this is to warp the frame outside of this class and pass the warped frame in. If this were done, QR_scan could be moved to its own module about global navigation. The warped frame would be passed in to it at the camera_client level instead, where camera client could fork another process for QR reading.
        """
        frame = warped_frame
        barcodes = pyzbar.decode(frame)
        if len(barcodes)>0:
            for barcode in barcodes:  # don't have time to check if its indexable
                (x,y,w,h) = barcode.rect
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type
                text = "{} ({})".format(barcodeData, barcodeType)
                cv2_rectangle = ((x,y),(x+w,y+h),(0,0,255),2)
                cv2_putText = (text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)
                return barcodeData,cv2_rectangle,cv2_putText
        else:
            return None,None,None
        
        
        
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
    cut_left = frame[:,:int(w/2)]
    cut_right = frame[:,int(w/2):]
    
    left = cv2.resize(cut_left,(w,h))
    right=cv2.resize(cut_right,(w,h))
    
    return ret,left
    
if __name__ == '__main__':
    cv2.namedWindow('original')
    cv2.namedWindow('lane_line_markings')
    cv2.namedWindow('result')
    
    cam = cv2.VideoCapture(0)
    ret,frame = cam_read(cam)
    
    line = LineFollow(frame)
    
    while True:
        ret,frame = cam_read(cam)
        
        ret,lane_line_markings,result,p1,p2,confidence,barcodeData = line.find_line(frame,)
        cv2.imshow('original',frame)
        cv2.imshow('lane_line_markings',lane_line_markings)
        if ret:
            cv2.imshow('result',result)
        else:
            cv2.imshow('result',frame)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            cv2.destroyAllWindows()
            break
        
        
        
        
        
#
#
#if False:#__name__ == '__main__':  overwriting this to use the find_line class
#    cam = cv2.VideoCapture(0)
#    ret,frame = cam_read(cam)
#    result = frame
#
#
#    cv2.namedWindow('original')
#    cv2.namedWindow('result')
#
#
#    width,height = frame.shape[::-1][1:]
#    padding = int(0.25 * width)
#    DESIRED_ROI_POINTS = np.float32([
#      [padding, 0], # Top-left corner
#      [padding, height], # Bottom-left corner
#      [width-padding, height], # Bottom-right corner
#      [width-padding, 0] # Top-right corner
#    ])
#
#    MARGIN = int((1/12) * width)  # Window width is +/- margin
#    MINPIX = int((1/24) * width)
#
#    while True:
#        ret,frame = cam_read(cam)
#        cv2.imshow('original',frame)
#
#
#
#        warped_frame,inv_mat = perspective_transform(
#            frame,
#            (width,height),
#            ROI_POINTS,
#            DESIRED_ROI_POINTS)
#
#        lane_line_markings=get_line_markings(warped_frame)
#
#        fit = get_lane_line_indices_sliding_windows(
#            lane_line_markings)
#        if fit is not None:
#            ploty,fitx = get_lane_line_previous_window(
#                lane_line_markings, fit)
#
#            shape = overlay_lane_lines(
#                lane_line_markings,
#                fitx,ploty)
#
#            unwarped = cv2.warpPerspective(
#                shape,
#                inv_mat,
#                (frame.shape[1],
#                 frame.shape[0])
#                )
#
#            result = cv2.addWeighted(frame, 1, unwarped, 0.3, 0)
#
#
#        cv2.imshow('lane_line_markings',lane_line_markings)
#        cv2.imshow('result',result)
#        key = cv2.waitKey(1)
#        if key == ord('q'):
#            cv2.destroyAllWindows()
#            break
#
#        if key == ord('s'):
#            cv2.imwrite('./QR_CLOSE.png',result)
#
#        if key == ord('d'):
#            cv2.imwrite('./QR_FAR.png',result)
#
