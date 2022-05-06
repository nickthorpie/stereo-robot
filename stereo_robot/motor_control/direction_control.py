import time,math
import numpy as np

### This bad boy is the next to get cleaned up please
# LINE_BOTTOM_FORCE_CONST = 1
# LINE_TOP_FORCE_CONST = 1
# a time cnfd. of x means 0% cnfd. at x seconds.unfortunately no way to
#completely disable this
# TIME_CONFIDENCE_CONST = 0.25

#Dont think these are being used anymore
# TOP_CONFIDENCE_CONST = 50      # a confidence of 50 means 0% confidence
# BOTTOM_CONFIDENCE_CONST = 50   # when the line is at the edge. 25 means 50%
# MIN_TURN_PWR = 20
# MIN_FWD_PWR = 30
# # might need to reset these to 1
# HORZ_FORCE_CONST = 2
# VERT_FORCE_CONST = 3

# TURN_TIME_90 = 3 #seconds

# DEAD_RECKON_STRAIGHT_1M = 10
# DEAD_RECKON_TURN_360D = 12
# DEAD_RECKON_STRAIGHT_SPEED = 50
# DEAD_RECKON_TURN_SPEED = 100

# from scipy.interpolate import interp1d

class DirectionControl:
    """Decision Making Class.
    Description:
        Holds a set of functions to make direction decisions based on the camera state. User interacts with class using self.step()
    """
    def __init__(self,config):
    """Initializes DirectionControl class.
    
    """
        print(config.ROI)
        self.config = config.DMU
        self.current_sensor_confidence=0
        self.current_movement_confidence=0
        self.line_force0_last = 0
        self.last_elapsed_time = 0
        self.pr = np.array([0,0])
        self.v_last = 0
        self.omega_last = 0
        self.last_barcode = None
        self.do_barcode_routine=False
        self.sweep_start_time=None
        self.is_lost = False
        self.dead_reckon_list = []
    
    def step(self,controller_state,camera_state):
        #might offload this into calc_line_force
        
        USE_LINE_FOLLOW = controller_state['triangle']
        if USE_LINE_FOLLOW:
            
            if self.is_new_barcode(camera_state['barcode']):
                print("FOUND NEW BARCODE")
                self.barcode_routine(camera_state)
                
            elif not self.is_lost and (
                camera_state['top'] is None or \
                camera_state['confidence']==0):
                
                self.lost_routine(camera_state)
            
            
            if self.is_lost:
                vert,horz = self.lost_step(camera_state)
                
            elif self.dead_reckon_list:
                
                ret, vert,horz = self.dead_reckon_step()
                
            else: #usual line following
                vert,horz = self.calc_line_force(camera_state)
            
            
        else:
            DS4_vert = controller_state['vert']
            DS4_horz = controller_state['horz']
            vert,horz = DS4_vert,DS4_horz
        
        return vert/100, horz/100
    
    def lost_routine(self,camera_state):
        self.is_lost = True
        top = camera_state["top"]
        bot = camera_state["bottom"]
        print("Robot cannot find line")
        #make an educated guess of the best starting turn
        if top is not None and bot is not None:
            if (top[0]+bot[0]<10) and (abs(top[1])+abs(bot[1])<25):
                print("Likely at end of the line")
                self.add_dead_reckon_turn(360)
            else:
                direction = math.copysign(1,top[1])
                self.add_dead_reckon_turn(direction*90)
                self.add_dead_reckon_turn(-direction*(360+90))
        else:
            self.add_dead_reckon_turn(90)
            self.add_dead_reckon_turn(-(360+90))
            
    def lost_step(self,camera_state):
        confidence = camera_state["confidence"]
        if confidence > 10:
            self.is_lost = False
            self.dead_reckon_list = []
            vert,horz = 0,0
        else:
            ret, vert,horz = self.dead_reckon_step()
            
            if ret is False:
                print("Device could not find line after lost sweep")
        return vert,horz
            
    def is_new_barcode(self,barcode):
        #idk if this will work flawlessly I'm a little tired
        ret_bool = (barcode is not None) and (barcode != self.last_barcode)
        self.last_barcode = barcode
        return ret_bool
    
    def barcode_routine(self,camera_state):
        log_msg = ""
        
        # need a better way to do this dead reckoning.
        # Probably would be better with an accelerometer.
        # The problem is that with more weight, dead reckoning changes
        # Could also factor distance to QR code to get more accurate
        # estimates.
        self.add_dead_reckon_straight(0.5)
        
        degrees = self.djikstra_turn(camera_state["barcode"])
        self.add_dead_reckon_turn(degrees)
    
    def djikstra_turn(self,barcode):
        if type(barcode) is float or type(barcode) is int:
            print(f"djikstra not implemented. Using barcode value {barcode}")
            return float(barcode)
        else:
            print(f"djikstra not implemented, barcode is not a number. Using {-90}")
            return -90

    def dead_reckon_step(self):
        """TODO: Maybe should pass current_time as an arg if we're using
        it elsewhere?"""
        # Check if we have any dead reckoning in queue
        if not self.dead_reckon_list:
            return False, None, None
        # Check if we need to initialize timer
        item = self.dead_reckon_list[0]
        
        if not item["initialized"]:
            self.dead_reckon_list[0]["initialized"] = True  # don't have time to check if
            self.dead_reckon_list[0]["start_time"] = time.time() # using 'item' would break pointer
        
        # Evaluate timer. If finished, remove from queue and stop.
        duration = time.time()-item["start_time"]
        if duration > item["duration"]:
            self.dead_reckon_list.pop(0)
            horz,vert = 0,0
            print(f"{item['identifier']}: 100%")
        else:
            vert,horz = self.dead_reckon_list[0]["motors"]
        print(f"{item['identifier']}: {int(duration/item['duration']*100)}%")
        return True, vert, horz
    
    def add_dead_reckon_straight(self,dist):
        item = {"identifier":f"straight {dist}m",
         "initialized":False,
         "start_time":None,
         "duration": abs(self.config.DEAD_RECKON_STRAIGHT_1M) * dist,
         "motors": (self.config.DEAD_RECKON_STRAIGHT_SPEED,0)
         }
        self.dead_reckon_list.append(item)
    
    def add_dead_reckon_turn(self,degrees):
        direction = math.copysign(1,degrees)
        item = {"identifier":f"turn {degrees}º",
                "initialized":False,
                 "start_time":None,
                 "duration": self.config.DEAD_RECKON_TURN_360D / 360 * abs(degrees),
                 "motors": (direction*self.config.DEAD_RECKON_TURN_SPEED,0)
         }
        self.dead_reckon_list.append(item)
    
    
    def do_lost_sweep(self,camera_state):
        print("DOING LOST SWEEP")
        print("NOT IMPLEMENTED")
        return 0,0
    
    def calc_line_force(self,camera_state):
        log_msg="[DMU-LinFllw] "
        
        line_top = camera_state['top']        # as percentage of viewing area
        line_bottom = camera_state['bottom']  # from bottom or center
        last_time = camera_state['message_time']
        line_confidence = camera_state['confidence']/100
        
        line_force = (np.array(line_top) + np.array(line_bottom))/2
        
        # Line confidence calculation. Confidence restricts the
        # vertical movement, currently leaves hz movement as it is
        current_time = time.time()
        elapsed_time = current_time-last_time
        # check if this frame is new            
        
        time_confidence = max(min(
            1 - elapsed_time/self.config.TIME_CONFIDENCE_CONST, 0),1)
        time_confidence = min(max(
            time_confidence,0),1)        
        sensor_confidence = line_confidence * time_confidence
        stp = 0.01
        if sensor_confidence>self.current_sensor_confidence+stp:
            self.current_sensor_confidence+=stp
        else:
            self.current_sensor_confidence = sensor_confidence
        
        
        theta = np.arctan(
            (line_top[1]-line_bottom[1])/                    \
            (line_top[0]-line_bottom[0]))
        
        theta_confidence = min(
            max(1-abs(theta / (np.pi / 2)),0),1)
        
        lateral_confidence = max(50-abs(line_force[1]),0)/50
        #         movement_confidence = (100-abs(line_top[1])/TOP_CONFIDENCE_CONST)*\
#                               (100-abs(line_bottom[1])/BOTTOM_CONFIDENCE_CONST)
        movement_confidence = theta_confidence*lateral_confidence#min(max(movement_confidence,0),1)

        stp = 0.01
        if movement_confidence>self.current_movement_confidence+stp:
            self.current_movement_confidence+=stp
        else:
            self.current_movement_confidence = movement_confidence
        
        log_msg+=f"| Cline:{int(line_confidence*100) : 3}"
        log_msg+=f"| Ctime:{int(time_confidence*100) : 3}"
        log_msg+=f"| Ctheta:{int(theta_confidence*100) : 3}"
        log_msg+=f"| Clat:{int(lateral_confidence*100) : 3}"
        log_msg+=f"| Cmov:{int(self.current_movement_confidence*100) : 3}"
        
        log_msg+=f"| Csens:{int(self.current_sensor_confidence*100) : 3}"
        log_msg+=f"| Fo:{tuple(line_force.astype(int))}"
        
        line_force[0]*= self.config.VERT_FORCE_CONST * \
                        self.current_sensor_confidence * \
                        self.current_movement_confidence
#         print("v after horz adj:",line_force[0])
        line_force[1]*= self.config.HORZ_FORCE_CONST * \
                        self.current_sensor_confidence
        
        log_msg+=f"|Fadj:{tuple(line_force.astype(int))}"
        
        ## This is some crap used to adjust for the fact that the motors
        # stall out at low voltages. TODO: make notes for how one might adjust
        # crawl voltage. 
        if abs(line_force[1])>1 and line_force[0]<5:
            line_force[1]=math.copysign(self.config.MIN_TURN_PWR,line_force[1])
            
        elif line_force[0]>5:
            line_force[0]=max(line_force[0],self.config.MIN_FWD_PWR)
    
        log_msg+=f"|Ffin:{tuple(line_force.astype(int))}"


        if len(log_msg)!=0:
            print(log_msg)
        return -line_force[0], line_force[1]
        
if __name__ == "__main__":
    import sys
    sys.path.insert(0,"/home/pi/stereoRobot/stereo_robot")
    from calibration import Config
    
    print("[TstSeq] - Creating Test Sequence") 
    controller_state = {
        "triangle":True,
        }
    camera_state = {
        "barcode":None,
        "top":[10,10],
        "bottom":[20,100],
        "confidence":10,
        "message_time":time.time()
    }
    DMU = DirectionControl(Config())
    
    print("[TstSeq] - line at 10% confidence")
    for _ in range(3):
        vert,horz = DMU.step(controller_state,camera_state)
        time.sleep(1)
    
    print("[TstSeq] - camera sees a barcode")
    camera_state['barcode'] = -90
    for _ in range(15):
        vert,horz = DMU.step(controller_state,camera_state)
        time.sleep(1)
    
    print("[TstSeq] - camera looses line")
    camera_state["confidence"]=0
    for _ in range(10):
        vert,horz = DMU.step(controller_state,camera_state)
        time.sleep(1)
    
    print("[TstSeq] - camera sees line again")
    camera_state["confidence"]=25
    for _ in range(10):
        vert,horz = DMU.step(controller_state,camera_state)
        time.sleep(1)
    print("[TstSeq] - Test Sequence Complete")
#     def get_path_plan(camera_state,current_time):
#         line_top = camera_state['top']        # as percentage of viewing area
#         line_bottom = camera_state['bottom']  # from bottom or center
#         last_time = camera_state['message_time']
#         line_confidence = camera_state['confidence']/100
#         
#         elapsed_time = current_time-last_time
#         #check for a new time
#         if self.last_elapsed_time > elapsed_time:
#             print("GENERATING NEW TRAJECTORY")
#             self.fit_thetas = generate_path_plan(line_top,line_bottom,elapsed_time)
#             dt = elapsed_time
#             self.cum_dist = 0
#         else:
#             print("INTERPOLATING FROM OLD TRAJECTORY")
#             dt = self.last_elapsed_time-elapsed_time
#         horz=self.interpolate_from_path_plan(dt)
#         
#         self.last_elapsed_time = elapsed_time
#         return horz
#     
#     def update_path_plan(self,dt):
#         self.theta = self.theta + omega_last * dt
#         self.pr = self.pr + self.v_last * dt
#         
#         desired_theta = self.fit_thetas(self.pr[0])
#         
#         desired_omega = (desired_theta-self.theta)/dt
#         
#         return desired_omega
#         
#         
#     def generate_path_plan(self,line_top,line_bottom,elapsed_time):
#         p1,p2 = line_bottom,line_top
#         vlcty = self.v_last
#         omega = self.omega_last
#         
#         pr = self.pr = np.array(0,0)  #position of robot
#         pr2 = pr+vlcty*elapsed_time
#         
#         # fit a trajectory
#         xs = (pr[0],pr2[0],0.9*(p2[0]-p1[0])+p1[0],p2[0],)
#         ys = (pr[1],pr2[1],0.9*(p2[1]-p1[1])+p1[1],p2[1],)
#         coeff = np.polyfit(ys,xs,3)
#         
#         fit = lambda y: sum([coeff[i]*y**(len(coeff)-i-1) for i in range(len(coeff))])
#         
#         y = np.arange(p1[0],p2[0])
#         x = [fit(y) for y in y]
#         
#         # pull dist and thetas from this
#         dist = np.array([((x[i+1]-x[i])**2+(y[i+1]-y[i])**2)**0.5 for i in range(len(x)-1)])
#         cum_dist = np.array([sum(dist[:i]) for i in range(len(dist))])
#         
#         thetas = [np.arctan2(x[i+1]-x[i],y[i+1]-y[i]) for i in range(len(x)-1)]
# 
#         fit_thetas = interp1d(y,thetas)
#         
#         self.pr = pr2
#         self.theta = 0 + omega*elapsed_time
#         return fit_thetas
#     
#     def calc_line_force_pathplan(self,camera_state):
#         line_top = camera_state['top']        # as percentage of viewing area
#         line_bottom = camera_state['bottom']  # from bottom or center
#         last_time = camera_state['message_time']
#         line_confidence = camera_state['confidence']/100
#         
#         current_time = time.time()
#         elapsed_time = current_time-last_time
#         
#         time_confidence = max(1 - elapsed_time/TIME_CONFIDENCE_CONST,0)
#         time_confidence = min(max(time_confidence,0),1)
#         
#         confidence = line_confidence * time_confidence
#         
#         stp = 0.01
#         if confidence>self.current_confidence+stp:
#             self.current_confidence+=stp
#         else:
#             self.current_confidence = confidence
#             
#         horz = get_path_plan(camera_state,current_time)
#         
#         vert = 1-line_top[0]
                
        
