
import numpy as np
import pigpio,math, time, warnings

import signal,sys,atexit
from multiprocessing import Queue, Process
from queue import Empty
try:
    from .direction_control import DirectionControl
except:
    from direction_control import DirectionControl
## NOTES
#  This script is actually the core logic for making direction decisions.
#  It was built specifically for the dual shock controller.
#  I got a little messy when structuring the code heigherarchy, it would be better
#  to restructure it from scratch.
#
#  This script contains the logic to control the sabertooth 2x12 driver with switches
#  as | DWN | UP  | DWN | DWN | DWN | DWN |
#
#  in reality it should take input [vert, horz] and drive the motors, but it currently
#  holds other functionality too. For example, it processes the line coordinates and 
#  does the calculations for how to drive motors. This should probably be
#  line following's responsibility.
#
#  READS DS4 Queue
#     IF TRIANGLE IS PRESSED, PROCESS LINE FOLLOWING
#  READS CAMERA's LINE RESULTS

# This constants section is getting offloaded to config.py 
# collected data to map frequencies to motor voltages. Tested on Kastar 12v
# FREQS = np.array([250,  300, 350, 400, 450, 500,  550])
# VOLTS = np.array([    -12.13, -2.6, 0.0,   3, 6.8, 10.9, 11.8])
# 
# COEF = np.polyfit(VOLTS,FREQS,2)   # These coeffs stored in config.py?
# 
# freqFun = lambda x: sum(COEF*[x**2,x,1])  # use a more general func
# 
# 
# PIN_MTR_L = 13
# PIN_MTR_R = 12
# 
# MTR_PWMduty = int(0.5e6)      # Motor duty cycle range from 0 to 1e6
# # MTR_ACCEL = 0.1
# 
# # JOYSTICK_MAX = 32767  # These are used to map the position of DS4 to a motor voltage
# MTR_VOLT_MAX = 5     # V

# LINE_BOTTOM_FORCE_CONST = 1
# LINE_TOP_FORCE_CONST = 1

# # HORZ_FORCE_CONST=0.5
# # VERT_FORCE_CONST=0.5
# # 
# # Kp = 0.75
# # Kd = 0.1
# # MTR_Kp = 1e-2

# def accelMotor(current,target,_):
#     error = target-current
#     
#     control = math.copysign(MTR_ACCEL,error)
#     
#     next_ = current+control
#     
#     return target

# def accelMotor_old(current,target,step):
#     if current==target:
#         return int(target)
#     
#     direction = math.copysign(1,target-current)
#     next_ = step*direction + current
#     if direction >0:
#         if target-next_<0:     #if we overshot:
#             return int(target)
#         else:
#             return int(next_)
#     else:
#         if target-next_>0:
#             return int(target)
#         else:
#             return int(next_)

def depleteQueue(q):
    last = None
    try:
        while(True):
            last = q.get_nowait()
    except Empty:
        return last

def motor_differential(vert,horz):
    """
    Takes a vert and horz signal (both from [-1,1]) and splits it up into a left and right
    wheel command. I.e. vert = 1, horz = 0 --> left = 1, right = 1
                        vert = 1, horz = 1 --> left = 0.75, right = 0.25
    """
    L = -(vert -0.5*horz)   # TODO: get rid of negative.
    R = -(vert +0.5*horz)
    L = min(max(L,-1),1)
    R = min(max(R,-1),1)
    return L,R

## Note on atexit: doesn't work in multiprocessing, need sigterm
    #instead. Should call on sys.exit but still doesn't? This decorator
    #is currently useless.
def stopMotors(pi,config):
    print("stopMotors has been called")
    freqFun= np.poly1d(config.MOTOR.COEF)
    L_freq = freqFun(0)
    R_freq = freqFun(0)
    
    pi.hardware_PWM(config.MOTOR.PIN_MTR_L,int(L_freq),config.MOTOR.MTR_PWMduty)
    pi.hardware_PWM(config.MOTOR.PIN_MTR_R,int(R_freq),config.MOTOR.MTR_PWMduty)
    
    pi.stop()
    
    
def server(q_controller,q_camera,pi,config,verbose = False):
    freqFun= np.poly1d(config.MOTOR.COEF)
  
#     freqFun = lambda x: sum([coeff[i]*x**(len(coeff)-i-1) for i in range(len(coeff))])
    # use a more general func
    
    
    noFreq = freqFun(0.0)
    L_freq,R_freq = noFreq,noFreq
#     L_freq_target,R_freq_target = noFreq,noFreq
    
    camera_state = {'LINE_FOLLOW':False}
    controller_state = None
    ESTOP=False
    
    DMU = DirectionControl(config)  # Route config into here too
    
    # Setup PIGPIO
    pi.set_mode(config.MOTOR.PIN_MTR_L,pigpio.OUTPUT)
    pi.set_mode(config.MOTOR.PIN_MTR_R,pigpio.OUTPUT)
    
    # Sigterm catcher for if process is terminated from main
    def clean_exit(num,frame):
        print("clean_exit")
        stopMotors(pi,config)
        sys.exit()
    signal.signal(signal.SIGTERM,clean_exit)
    
    # Main loop
    try:
        while True:
        # read the controller and camera queue. Have to use an
        # exception catcher to make sure motors shut down on exit
            message = depleteQueue(q_controller)
            if message is not None:
                controller_state = message
                ESTOP = controller_state['circle']
            
            message = depleteQueue(q_camera)
            if message is not None:
                camera_state = message
            
            if ESTOP:
                raise Exception("ESTOP TRIGGERED")
            
            if controller_state is None:
                continue # Don't start until we've made contact with DS4
            
            
            vert,horz = DMU.step(controller_state,camera_state)
                        
            L,R = motor_differential(vert,horz)
            
            #accelMotor Deprecated. Using smoothing directly in follow routines
#             L_freq_target = freqFun(L*MTR_VOLT_MAX)
#             R_freq_target = freqFun(R*MTR_VOLT_MAX)
            
#             L_freq = accelMotor(L_freq,L_freq_target,MTR_ACCEL)
#             R_freq = accelMotor(R_freq,R_freq_target,MTR_ACCEL)
            
            L_freq = freqFun(L*config.MOTOR.MTR_VOLT_MAX)
            R_freq = freqFun(R*config.MOTOR.MTR_VOLT_MAX)
            
            pi.hardware_PWM(config.MOTOR.PIN_MTR_L,int(L_freq),config.MOTOR.MTR_PWMduty)
            pi.hardware_PWM(config.MOTOR.PIN_MTR_R,int(R_freq),config.MOTOR.MTR_PWMduty)
            
            if verbose:
                print(f"VrtHz:{str((round(vert,2),round(horz,2))) : <15} ",
                      f"LR:{str((round(L,2),round(R,2))) : <15} ",
                      f"LRFq:{str((int(L_freq),int(R_freq))) : <15}")
    except Exception as E:
        stopMotors(pi,config)
        raise E

if __name__=="__main__":
    # This test sequence creates a client, then launches a sabertooth server object
    
    print("[TstSeq] - Creating Test Sequence")
    print("[TstSeq] - Creating a fake client to launch server")
    from multiprocessing import Queue, Process
    import sys,pigpio
    sys.path.insert(0,"/home/pi/stereoRobot/stereo_robot")
    from configuration import Config
    from motor_control import SabertoothServer
    
    q_camera = Queue()
    q_controller = Queue()
    
    config = Config()
    pi = pigpio.pi()
    
    process_a = Process(
        target = SabertoothServer,
        args=(q_controller,q_camera,pi,config,True)
    )
    process_a.start()
    start_time = time.time()
    toggle = True
    try:
        while True:
            current_time = time.time()
            if current_time-start_time < 1:
                msg_controller = {'vert':0,'horz':0,'triangle':False,'circle':False}
                msg_camera = {"top":None,"bottom":None,"confidence":0,"barcode":None}
                
            elif current_time-start_time < 2: 
                if toggle:
                    print("\n[TstSeq] - Random Controller vals\n")
                    toggle = False
                msg_controller = {'vert':np.random.rand()*100,
                                  'horz':(np.random.rand()-0.5)*100,
                                  'triangle':False,'circle':False}
                msg_camera = {"top":None,"bottom":None,"confidence":0,"barcode":None}
            
            elif current_time-start_time < 5:
                if not toggle:
                    print("\n[TstSeq] - Triangle Pressed, Random Line vals")
                    toggle = True
                msg_controller = {'vert':np.random.rand()*100,           
                                      'horz':(np.random.rand()-0.5)*50,
                                      'triangle':True,'circle':False}
                msg_camera = {"top":(np.random.rand()*100,(np.random.rand()-0.5)*100),
                              "bottom":(np.random.rand()*10,(np.random.rand()-0.5)*50),
                              "confidence":np.random.rand()*50+50,"barcode":None,
                              "message_time":current_time}
            else:
                print("\n[TstSeq] - End of test sequence. Aborting now\n")
                raise KeyboardInterrupt
            
            q_camera.put(msg_camera)
            q_controller.put(msg_controller)
            
            time.sleep(1/15)    # refresh rate of sabertoothServer is about 1/200
            if not process_a.is_alive():
                print(process_a.exitcode)
                raise KeyboardInterrupt
            
    except KeyboardInterrupt:
        print("User terminated program")
        pass
    except:
        print("Exception")
    
    process_a.terminate()
    process_a.join()
    pi.stop()
        
# # The following code used to be the server, but it's responsibilities
# have been offloaded to the DirectionalControl class
# def old_server(q_controller,q_camera):
#     # Setup PIGPIO
#     pi = pigpio.pi()
#     pi.set_mode(PIN_MTR_L,pigpio.OUTPUT)
#     pi.set_mode(PIN_MTR_R,pigpio.OUTPUT)
#     
#     noFreq = int(freqFun(0.0))
#     L_freq,L_freq_target = noFreq,noFreq
#     R_freq,R_freq_target = noFreq,noFreq
#     USE_LINE_FOLLOW=False
#     line_confidence=0
#     line_top=np.array([0,0])
#     line_bottom=np.array([0,0])
#     line_force_last = np.array([0,0])
#     while True:
#         # read the controller and camera queue. Have to use an exception catcher
#         # in case the queue hasn't updated yet
#         try:
#             message = q_controller.get_nowait()
# 
#             # not necessary, but reminds us that controller state only updates
#             # when queue is not empty
#             controller_state = message  
#             
#             DS4_vert = controller_state['vert']/JOYSTICK_MAX
#             DS4_horz = controller_state['horz']/JOYSTICK_MAX
#             USE_LINE_FOLLOW = controller_state['triangle']
#             
#         except Empty:
#             pass
#         
#         if USE_LINE_FOLLOW:
#             print("LINEFOLLOW")
#             try:
#                 print("RECIEVED CAM")
#                 
#                 message = depleteQueue(q_camera)
#     #             print('recieved: ', message)
#                 if message is not None:
#                     camera_state = message
#                     
#                     line_top = camera_state['top']        # as percentage of viewing area
#                     line_bottom = camera_state['bottom']  # from bottom or center
#                     line_confidence = camera_state['confidence']
#                 else:
#                     line_confidence = max(line_confidence-5,0)
#                 print("TOP OF LINE COORDINATE:",line_top)                
#             
#             except Empty:
#                 # if the camera hasn't given us anything new, slow down
#                 line_confidence = max(line_confidence-5,0)
#                 pass
#             
#             try:
#                 line_top_force = LINE_TOP_FORCE_CONST*np.array(line_top)
#                 line_bottom_force = LINE_BOTTOM_FORCE_CONST*np.array(line_bottom)
#                 
#                 theta = np.arctan((line_top-line_bottom)[0]/(line_top-line_bottom)[1])
#                 line_force = line_top_force + line_bottom_force
#                 
#                 line_force[0] = min(max(line_force[0],0),100) * line_confidence/100
#                 line_force[1] = min(max(line_force[1],-20),20) * line_confidence/100
#                 
# #                 line_force[0] *= 1-abs(line_top_force[1])/50
#                 
#                 line_force = line_force 
#                 line_force = line_force * np.array([VERT_FORCE_CONST,HORZ_FORCE_CONST])
#                 line_force*= max(1-abs(theta)/np.pi,0)
#                 line_force_derivative = line_force-line_force_last
#                 line_force_PD = Kp*line_force+Kd*line_force_derivative
#                 # TODO: I don't like that the input to motor_differential is
#                 # y,x. Go back and change it
#                 L,R = motor_differential(-line_force[0]/100, line_force[1]/50)  
#                 
#                 L_freq_target = freqFun(L*MTR_VOLT_MAX)
#                 R_freq_target = freqFun(R*MTR_VOLT_MAX)
#                 
#                 L_freq = accelMotor(L_freq,L_freq_target,MTR_ACCEL)
#                 R_freq = accelMotor(R_freq,R_freq_target,MTR_ACCEL)
#                 
#                 L_freq=int(L_freq_target)
#                 R_freq=int(R_freq_target)
#                 
#                 line_force_last = line_force
#                 print("L/R",L,R)
#                 print("Line Top/Bot Force:", line_top_force,line_bottom_force)
#                 print("CONFIDENCE:",line_confidence, line_force[0],line_force[1])
#             except Exception as E:
#                 warnings.warn(str(E))
#                 L_freq = noFreq
#                 R_freq = noFreq
#                 L_freq_target=noFreq
#                 R_freq_target=noFreq
#                 
#         else:  # Purely manual motor control
#             L,R = motor_differential(DS4_vert,DS4_horz)  
#             
#             L_freq_target = freqFun(L*MTR_VOLT_MAX)
#             R_freq_target = freqFun(R*MTR_VOLT_MAX)
#             
#             L_freq = accelMotor(L_freq,L_freq_target,MTR_ACCEL)
#             R_freq = accelMotor(R_freq,R_freq_target,MTR_ACCEL)
# #         print(f'left:  L: {L*MTR_VOLT_MAX}  freq:{L_freq}')
# #         print(f'right: R: {R*MTR_VOLT_MAX}  freq:{R_freq}')
#         
# #         print(type(PIN_MTR_L),type(L_freq),type(PIN_MTR_L))
#         try:
#             pi.hardware_PWM(PIN_MTR_L,L_freq,MTR_PWMduty)
#             pi.hardware_PWM(PIN_MTR_R,R_freq,MTR_PWMduty)
#         except Exception as E:
#             print([type(x) for x in (PIN_MTR_L,L_freq,MTR_PWMduty)])
#             raise E
