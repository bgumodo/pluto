#!/usr/bin/env python

import roslib
import rospy
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import String, Bool
from pluto.msg import DetectResult
import time
from pluto_common import *

class Mickey:
    state                               = 0
    counter_scans                       = 0
    counter_approches                   = 0
    counter_wonder_straight             = 0
    discrete_turns_needed               = 0
    
    counter_scans_limit                 = 30
    counter_approches_limit             = 3
    
    detect_result                       = 0
    
    top_camera_detected_close_to_ball   = False
    
    emergency_stop                      = True
    emergency_stop_enforced             = False
    is_using_top_camera                 = True
    
    obstacle_found_left                 = False
    obstacle_found_right                = False
    obstacle_found_front                = False
    obstacle_first                      = True
    
    def OBSTACLE_DANGER_M_SIDE( self ):
        return 0.5
        
    def OBSTACLE_DANGER_M_FRONT_FAR( self ):
        return 1.1
        
    def OBSTACLE_DANGER_M_FRONT_CLOSE( self ):
        return 0.25
    
    def RATE( self ):
        return 5
        
    def STATE_SCAN( self ):
        return 0
        
    def STATE_SCAN_DETECT_CALLBACK( self ):
        return 1
        
    def STATE_SCAN_TURN_CALLBACK( self ):
        return 2
        
    def STATE_CORRECT_DIRECTION( self ):
        return 3
        
    def STATE_CORRECT_DIRECTION_CALLBACK( self ):
        return 4
        
    def STATE_APPROACH( self ):
        return 5
        
    def STATE_APPROACH_CALLBACK( self ):
        return 6
        
    def STATE_ARM_PICK( self ):
        return 10
        
    def STATE_ARM_PICK_CALLBACK( self ):
        return 11
        
    def STATE_ARM_CONFIG_FOR_SCAN( self ):
        return 12
        
    def STATE_ARM_CONFIG_FOR_SCAN_CALLBACK( self ):
        return 13
        
    def STATE_INIT_ARM( self ):
        return 14
        
    def STATE_INIT_ARM_CALLBACK( self ):
        return 15
        
    def correction_turn_tolerance( self ):
        if True == self.top_camera_detected_close_to_ball:
            return 0
        else:
            return 0
            
    def detector_image_width( self ):
        if True == self.is_using_top_camera:
            return 640
        else:
            if True == self.is_simulation:
                return 640
            else:
                return 640 // 2
        
    def detector_image_height( self ):
        if True == self.is_using_top_camera:
            return 480
        else:
            if True == self.is_simulation:
                return 480
            else:
                return 480 // 2
        
    def detector_discrete_turn_pixels( self ):
        if True == self.is_using_top_camera:
            if True == self.is_simulation:
                return 45
            else:
                return 60
        else:
            if True == self.is_simulation:
                return 10
            else:
                return 20
        
    def cooldown_approch( self ):
        #time.sleep( 1 )
        pass
        
    def cooldown_turn( self ):
        #time.sleep( 0.1 )
        pass
        
    def cooldown_boot( self ):
        time.sleep( 20 )
        
    def cooldown_correction( self ):
        #time.sleep( 0.5 )
        pass
        
    def obstacle_is_clear_all( self ):
        return ( False == self.obstacle_found_left    ) and \
               ( False == self.obstacle_found_right   ) and \
               ( False == self.obstacle_found_front   )
        
    def obstacle_detection_left( self, proximity ):
        self.obstacle_found_left = ( proximity.range <= self.OBSTACLE_DANGER_M_SIDE() )
        
        if ( True == self.obstacle_found_left ) and ( True == self.obstacle_first ):
            rospy.loginfo( "Obstacle detected on left, in {} m <= {} m.".format( proximity.range, self.OBSTACLE_DANGER_M_SIDE() ) )
        
    def obstacle_detection_right( self, proximity ):
        self.obstacle_found_right = ( proximity.range <= self.OBSTACLE_DANGER_M_SIDE() )
        
        if ( True == self.obstacle_found_right ) and ( True == self.obstacle_first ):
            rospy.loginfo( "Obstacle detected on right, in {} m <= {} m.".format( proximity.range, self.OBSTACLE_DANGER_M_SIDE() ) )
        
    def obstacle_detection_front( self, laser_scan ):
        distance_to_obstacle = min( laser_scan.ranges )

        if True == self.is_using_top_camera:
            danger_distance = self.OBSTACLE_DANGER_M_FRONT_FAR()
        else: 
            danger_distance = self.OBSTACLE_DANGER_M_FRONT_CLOSE()
            
        self.obstacle_found_front = ( distance_to_obstacle <= danger_distance )
        
        if ( True == self.obstacle_found_front ) and ( True == self.obstacle_first ):
            rospy.loginfo( "Obstacle detected on front, in {} m <= {} m.".format( distance_to_obstacle, danger_distance ) )
        
    def is_in_close_range( self ):

        if True == self.is_simulation:
            # Gazebo mesurments, ball distance to y value in picture:
            #     4m  : y: 286, r: 2
            #     3m  : y: 304, r: 2
            #     2m  : y: 336, r: 4
            #     1.5m: y: 366, r: 5
            #     1m  : y: 434, r: 6
            return self.detect_result.detected_y > 336;
        else:
            # Real robot, when ball placed at 1.6 m from robot, and it placed at the bottom of the top camera.
            # Make sure to initialize the camera to 1.6m (on the floor) ball, at bottom ot the top camera.
            # detected_y value should be configured to ball beeing at 2.2 m distance, placed on the bench.
            return self.detect_result.detected_y > 360;
        
        
    def __init__( self ):
        rospy.loginfo( "Mickey initialized " )
        
        init_arguments( self )

        if True == self.is_simulation:
            self.emergency_stop = False
        else:
            self.emergency_stop = True
            
        self.state = self.STATE_INIT_ARM()

        self.move_publisher = rospy.Publisher('/pluto/movement/command', String, queue_size=10)
        rospy.Subscriber("/pluto/movement/done", String, self.move_done )
        
        self.detect_publisher = rospy.Publisher('/pluto/detect/command', String, queue_size=10)
        rospy.Subscriber("/pluto/detect/result", DetectResult, self.detect_result )
        
        self.arm_move_publisher = rospy.Publisher('/pluto/move_arm/command', String, queue_size=10)
        rospy.Subscriber('/pluto/move_arm/done', String, self.arm_move_done)
        
        rospy.Subscriber( "/pluto/emergency_stop", Bool, self.emergency_stop_cb)
        self.emergency_stop_publisher = rospy.Publisher('/pluto/emergency_stop', Bool, queue_size=10)
        self.emergency_stop_publisher.publish( self.emergency_stop )
        
        if False == self.is_simulation:
            rospy.Subscriber( pluto_add_namespace( self.is_simulation, "/left_urf"    ), Range,       self.obstacle_detection_left  )
            rospy.Subscriber( pluto_add_namespace( self.is_simulation, "/right_urf"   ), Range,       self.obstacle_detection_right )
            rospy.Subscriber( pluto_add_namespace( self.is_simulation, "/scan"        ), LaserScan,   self.obstacle_detection_front )

    def emergency_stop_cb( self, emergency_stop ):
        self.emergency_stop = emergency_stop.data
        
        if ( False == self.emergency_stop ) and ( True == self.emergency_stop_enforced ):
            self.main_loop()

    def calculate_turns_needed( self ):
        #return ( self.detect_result.detected_x // self.detector_discrete_turn_pixels() ) - ( self.detector_image_width() // self.detector_discrete_turn_pixels() // 2 )
        
        offset_from_center = self.detect_result.detected_x - (self.detector_image_width() // 2)
        
        if offset_from_center < -self.detector_discrete_turn_pixels():
            turn_value = -1
        elif self.detector_discrete_turn_pixels() < offset_from_center:
            turn_value = 1
        else:
            turn_value = 0
        
        if ( False == self.is_simulation       ) and \
           ( False == self.is_using_top_camera ):
            turn_value = -turn_value
        
        rospy.loginfo( "calculate_turns_needed, x: {}, width: {}, oofeset: {}, turn {} ".format( self.detect_result.detected_x, self.detector_image_width(), offset_from_center, turn_value ) )
        
        return turn_value
        
    def arm_move_done( self, done_message ):
        done_message_str = done_message.data
        rospy.loginfo( "Mickey arm_move_done: " + done_message_str )
        
        self.main_loop()
    
    def move_done( self, done_message ):
        done_message_str = done_message.data
        rospy.loginfo( "Mickey move_done: " + done_message_str )
        
        self.main_loop()
        
    def detect_result( self, detect_result ):
        
        if self.STATE_SCAN_DETECT_CALLBACK() == self.state:
            rospy.loginfo( "Mickey detect_result " )
            
            self.detect_result = detect_result
            
            self.main_loop()


    def is_arm_camera_scan_stop_condition( self ):
        if True == self.is_simulation:
            return self.detect_result.detected_y > 360;
        else:
            # Ball placed at 0.5~ m distance
            # Arm camera is upside down
            return self.detect_result.detected_y < 30;

    
    def main_loop( self ):
        
        rospy.loginfo( "Mickey main_loop " )
        
        if True == self.emergency_stop:
            self.emergency_stop_enforced = True
            return
            
        while False == self.obstacle_is_clear_all():
            if True == self.obstacle_first:
                rospy.loginfo( "Obstacle detected, please clear the way." )
                self.obstacle_first = False
                
        self.obstacle_first = True
        
        if self.STATE_INIT_ARM() == self.state:
            
            rospy.loginfo( "Mickey STATE_INIT_ARM " )
            
            self.arm_move_publisher.publish("INIT")
            self.state = self.STATE_INIT_ARM_CALLBACK()
 
        elif self.STATE_INIT_ARM_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_INIT_ARM_CALLBACK " )
            
            self.state = self.STATE_SCAN()
            
            self.main_loop()
        
        elif self.STATE_SCAN() == self.state:
            
            rospy.loginfo( "Mickey STATE_SCAN " )
            
            self.state = self.STATE_SCAN_DETECT_CALLBACK()
            
            if True == self.is_using_top_camera:
                self.detect_publisher.publish("scan_top")
            else: 
                self.detect_publisher.publish("scan_arm")

        elif self.STATE_SCAN_DETECT_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_SCAN_DETECT_CALLBACK " )
            
            self.counter_scans = self.counter_scans + 1
            
            if True == self.detect_result.is_ball_detected:
                
                self.discrete_turns_needed = self.calculate_turns_needed()
                
                if abs( self.discrete_turns_needed ) <= self.correction_turn_tolerance():
                    
                    if (False == self.is_using_top_camera) and (True == self.is_arm_camera_scan_stop_condition() ):
                        
                        self.state = self.STATE_ARM_PICK()
                        
                    else:

                        self.state              = self.STATE_APPROACH()
                        self.counter_approches  = 0
                        
                        if (True == self.is_using_top_camera):
                            
                            if False == self.top_camera_detected_close_to_ball:
                                self.top_camera_detected_close_to_ball = self.is_in_close_range()
                            
                            if True == self.top_camera_detected_close_to_ball:
                                self.move_publisher.publish("FINE")
                                self.counter_approches_limit = 1
                                rospy.loginfo( "Mickey top_camera_detected_close_to_ball " )

                else:
                    self.state = self.STATE_CORRECT_DIRECTION()
 
                self.main_loop()
                    
            else:
                if ( True == self.is_using_top_camera ):
                    
                    if True == self.top_camera_detected_close_to_ball:
                    
                        self.state = self.STATE_ARM_CONFIG_FOR_SCAN()
                        
                        self.main_loop()
                        
                    else:
                        
                        self.state = self.STATE_SCAN_TURN_CALLBACK()
                    
                        self.move_publisher.publish("RIGHT")
                    
                else:
                    self.state = self.STATE_SCAN_TURN_CALLBACK()
                    
                    self.move_publisher.publish("RIGHT")
                    

        elif self.STATE_SCAN_TURN_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_SCAN_TURN_CALLBACK " )
            
            self.cooldown_turn()
            
            self.state = self.STATE_SCAN()
            
            self.main_loop()
            
        elif self.STATE_CORRECT_DIRECTION() == self.state:
            
            rospy.loginfo( "Mickey STATE_CORRECT_DIRECTION " )
            
            if abs(self.discrete_turns_needed) <= self.correction_turn_tolerance():
                
                # rospy.loginfo( "Mickey STATE_CORRECT_DIRECTION -> SCAN" )
                
                self.cooldown_correction()
                
                self.state = self.STATE_SCAN()
                
                self.main_loop()
                
            else:
                
                self.state = self.STATE_CORRECT_DIRECTION_CALLBACK()
                
                if 0 < self.discrete_turns_needed:
                    
                    # rospy.loginfo( "Mickey STATE_CORRECT_DIRECTION -> RIGHT {}".format(self.discrete_turns_needed) )
                    
                    self.discrete_turns_needed = self.discrete_turns_needed - 1
                    
                    self.move_publisher.publish("RIGHT")
                    
                else:
                    
                    # rospy.loginfo( "Mickey STATE_CORRECT_DIRECTION -> LEFT {}".format(self.discrete_turns_needed) )
                    
                    self.discrete_turns_needed = self.discrete_turns_needed + 1
                    
                    self.move_publisher.publish("LEFT")
                
            
        elif self.STATE_CORRECT_DIRECTION_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_CORRECT_DIRECTION_CALLBACK " )
            
            self.state = self.STATE_CORRECT_DIRECTION()
            
            self.main_loop()
            
        elif self.STATE_APPROACH() == self.state:
            
            rospy.loginfo( "Mickey STATE_APPROACH " )
            
            if self.counter_approches >= self.counter_approches_limit:
                
                self.cooldown_approch()
                
                self.counter_approches = 0
                
                self.state = self.STATE_SCAN()
                
                self.main_loop()
                
            else:
                
                self.state = self.STATE_APPROACH_CALLBACK()
                
                self.move_publisher.publish("FORWARD")
                
            
        elif self.STATE_APPROACH_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_APPROACH_CALLBACK " )
            
            self.counter_approches = self.counter_approches + 1
            
            self.state = self.STATE_APPROACH()
            
            self.main_loop()
            
        elif self.STATE_ARM_PICK() == self.state:
            
            rospy.loginfo( "Mickey STATE_ARM_PICK " )
            
            self.state = self.STATE_ARM_PICK_CALLBACK()
            self.arm_move_publisher.publish("ARM_PICK")
            

        elif self.STATE_ARM_PICK_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_ARM_PICK_CALLBACK " )
            # TODO: Add arm related code
            
        elif self.STATE_ARM_CONFIG_FOR_SCAN() == self.state:
            
            rospy.loginfo( "Mickey STATE_ARM_CONFIG_FOR_SCAN " )
            
            self.state = self.STATE_ARM_CONFIG_FOR_SCAN_CALLBACK()
            self.arm_move_publisher.publish("INIT_ARM_SCAN")
            
            
        elif self.STATE_ARM_CONFIG_FOR_SCAN_CALLBACK() == self.state:
            
            rospy.loginfo( "Mickey STATE_ARM_CONFIG_FOR_SCAN_CALLBACK " )
            
            self.state = self.STATE_SCAN()

            self.is_using_top_camera = False
            
            self.main_loop()
            
            
        else:
            raise Exception('Unexisting state.')


if __name__ == '__main__':
    try:
        rospy.init_node("pluto_mickey")
        mickey = Mickey()
        
        
        while not rospy.is_shutdown():
            
            mickey.cooldown_boot()
            mickey.main_loop()
            rospy.spin()
            
            
    except rospy.ROSInterruptException:
        pass
