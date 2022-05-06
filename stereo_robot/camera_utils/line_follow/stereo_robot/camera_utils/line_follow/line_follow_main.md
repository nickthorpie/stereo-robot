Module stereo_robot.camera_utils.line_follow.line_follow_main
=============================================================

Functions
---------

    
`calculate_histogram_vert(warped_frame)`
:   Calculate the image histogram to find peaks in white pixel count
         
    :param frame: The warped image
    :param plot: Create a plot if True

    
`cam_read(camera)`
:   

    
`get_endpoints(ploty, fitx, h, w)`
:   

    
`get_lane_line_indices_sliding_windows(warped_frame, MINPIX, MARGIN)`
:   Get the indices of the lane line pixels using the 
    sliding windows technique.
         
    :param: plot Show plot or not
    :return: Best fit lines for the left and right lines of the current lane

    
`get_lane_line_previous_window(warped_frame, fit, MINPIX, MARGIN)`
:   Use the lane line from the previous sliding window to get the parameters
    for the polynomial line for filling in the lane line
    :param: left_fit Polynomial function of the left lane line
    :param: right_fit Polynomial function of the right lane line
    :param: plot To display an image or not

    
`get_line_markings(orig_frame)`
:   Isolates lane lines.
    
      :param frame: The camera frame that contains the lanes we want to detect
    :return: Binary (i.e. black and white) image containing the lane lines.

    
`histogram_peak(warped_frame)`
:   

    
`overlay_lane_lines(shape, fitx, ploty)`
:   Overlay lane lines on the original frame
    :param: Plot the lane lines if True
    :return: Lane with overlay

    
`perspective_transform(frame, orig_frame_shape, roi_points, desired_roi_points)`
:   Perform the perspective transform.
    :param: frame Current frame
    :param: plot Plot the warped image if True
    :return: Bird's eye view of the current lane

Classes
-------

`LineFollow(init_frame)`
:   

    ### Class variables

    `CONFIG`
    :

    ### Methods

    `QR_scan(self, warped_frame)`
    :

    `find_line(self, frame)`
    :