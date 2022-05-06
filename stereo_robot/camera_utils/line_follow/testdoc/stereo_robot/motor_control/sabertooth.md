Module stereo_robot.motor_control.sabertooth
============================================

Functions
---------

    
`depleteQueue(q)`
:   

    
`motor_differential(vert, horz)`
:   Takes a vert and horz signal (both from [-1,1]) and splits it up into a left and right
    wheel command. I.e. vert = 1, horz = 0 --> left = 1, right = 1
                        vert = 1, horz = 1 --> left = 0.75, right = 0.25

    
`server(q_controller, q_camera, pi, config, verbose=False)`
:   

    
`stopMotors(pi, config)`
: