#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2022-10-18 16:08:35
# @Author  : BrightSoul (653538096@qq.com)

import rospy
from mavros_msgs.msg import GlobalPositionTarget, State, RCIn, PositionTarget, AttitudeTarget
from mavros_msgs.srv import CommandLong, CommandBool, CommandTOL, SetMode
from geometry_msgs.msg import PoseStamped, Twist, TwistStamped, Point,PointStamped 
from sensor_msgs.msg import Imu, NavSatFix, Temperature
from std_msgs.msg import Float32, Float64, String, Float32MultiArray, Int8
from nav_msgs.msg import Odometry



import time
import numpy as np
import threading
from collections import OrderedDict


from utils import constrain_rad,eulerAngleToMatrix

# 结束线程的函数
import inspect
import ctypes


PX4_CTRL_DICT = {
    "vel":{
        "mavros_vel_ctrl": True,
        "mavros_att_ctrl": False,
    },
    "att":{
        "mavros_vel_ctrl": False,
        "mavros_att_ctrl": True,
    }
}


class Px4Controller:
    def __init__(self,pos_swarm_init=[0,0,0]):
        self.arm_state = False
        self.offboard_state = False

        self.command_vel = construct_vel_target()

        self.mav_roll = None
        self.mav_pitch = None
        self.mav_yaw = None

        # R_eo是odom系到ENU系的旋转矩阵   
        self.mav_yaw_offset = 0
        self.R_eo = np.identity(3)
        
        self.mav_yaw_odom = None

        # 相对于起飞点的enu位置
        self.pos_enu = None
        self.pos_enu_offset = np.zeros(3)
        self.vel_enu = None


        # 相对于起飞点的odom位置和速度
        self.pos_odom = None
        self.vel_odom = None

        # 相对于集群原点的位置
        self.pos_swarm = np.zeros(3)
        self.pos_swarm_init = np.array(pos_swarm_init)

        self.rc_dict = OrderedDict()
        for i in range(5,10):
            self.rc_dict["ch{}".format(i)] = -1

        
        self.pos_init_done = False
        self.vel_init_done = False
        self.rc_init_done = False

        self.mavros_vel_ctrl = False
        self.mavros_att_ctrl = False 


        '''
        ros publishers
        '''
        self.setpt_pva_pub =  rospy.Publisher('/mavros/setpoint_raw/local', PositionTarget, queue_size=10)
        self.setpt_att_pub =  rospy.Publisher('/mavros/setpoint_raw/attitude', AttitudeTarget, queue_size=10)
        self.mav_sw_pos_pub =  rospy.Publisher('/bs_swarm_pos/mav_pos', PointStamped, queue_size=10)

        
        '''
        ros subscribers
        '''
        self.local_pose_sub = rospy.Subscriber("/mavros/local_position/pose", PoseStamped, self.local_pose_callback)
        self.mavros_sub = rospy.Subscriber("/mavros/state", State, self.mavros_state_callback)
        self.rcin_sub = rospy.Subscriber("/mavros/rc/in", RCIn, self.rcin_callback)
        


        '''
        ros services
        '''
        self.cmdLongService = rospy.ServiceProxy('/mavros/cmd/command', CommandLong)
        self.armService = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
        # rospy.wait_for_service('/mavros/cmd/land')
        self.landService = rospy.ServiceProxy("mavros/cmd/land", CommandTOL)
        self.flightModeService = rospy.ServiceProxy('/mavros/set_mode', SetMode)
    

    # ============================== ROS 推送相关 start ============================================
          
    def mavros_pub_loop(self):
        pub_time = time.time()
        while (not rospy.is_shutdown()):
            if (time.time() - pub_time) > 1/50.0:
                pub_time = time.time()
                if self.mavros_vel_ctrl:
                    self.setpt_pva_pub.publish(self.command_vel)
                if self.mavros_att_ctrl:
                    self.setpt_att_pub.publish(self.command_att)
            time.sleep(0.01)
                
        self.stop_thread(self.mavros_pub_th)


    def swarm_pos_loop(self):
        pub_time = time.time()
        while (not rospy.is_shutdown()):
            if (time.time() - pub_time) > 1/50.0:
                pub_time = time.time()
                mav_sw_pos = PointStamped()
                mav_sw_pos.point.x = self.pos_swarm[0]
                mav_sw_pos.point.y = self.pos_swarm[1]
                mav_sw_pos.point.z = self.pos_swarm[2]
                self.mav_sw_pos_pub.publish(mav_sw_pos)
            time.sleep(0.01)
                
        self.stop_thread(self.mavros_pub_th)


    def start_pub(self):
        self.controller_swith(ctrl_type="vel")
        self.mavros_pub_th = threading.Thread(target=self.mavros_pub_loop, args=())
        self.mavros_pub_th.start()

        self.swarm_pos_th = threading.Thread(target=self.swarm_pos_loop, args=())
        self.swarm_pos_th.start()

        time.sleep(1)
        print("start pub threading")


    def stop_thread(self, thread_id):
        _async_raise(thread_id, SystemExit)
        time.sleep(1)
        print("a thread  is dead")
    # ============================== ROS 推送相关 end ============================================
    


    # ============================== ROS 回调函数 start ============================================
    def local_pose_callback(self, msg):       
        self.pos_init_done = True
        
        # 地理系ENU下的位置
        pos_enu = np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])
        self.pos_enu = pos_enu
        # self.pos_enu = pos_enu - self.pos_enu_offset
        self.mav_height = self.pos_enu[2]


        # odom系朝向为起飞的方向
        self.pos_odom = np.dot(self.R_eo.T,self.pos_enu)
        self.pos_swarm = self.pos_odom + self.pos_swarm_init


        q0, q1, q2, q3 = msg.pose.orientation.w, msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z
        
        self.quat = np.array([q0, q1, q2, q3])
        self.mav_yaw = np.arctan2(2*(q0*q3 + q1*q2), 1-2*(q2*q2 + q3*q3))
        self.mav_yaw_odom = constrain_rad(self.mav_yaw - self.mav_yaw_offset)

        self.mav_roll = np.arctan2(2*(q0*q1 + q2*q3), 1-2*(q1*q1 + q2*q2))
        self.mav_pitch = np.arcsin(2*(q0*q2 - q3*q1))

        self.R_be = eulerAngleToMatrix([self.mav_roll,self.mav_pitch,self.mav_yaw])


    def local_vel_callback(self, msg):
        self.vel_init_done = True
        # 地理系ENU下的速度
        self.vel_enu = np.array([msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z])
        self.vel_odom = np.dot(self.R_eo.T,self.vel_enu)

    # def odometry_callback(self, msg):
    #     self.pos_init_done = True
    #     self.vel_init_done = True
    #     self.pos_enu_odom = np.array([msg.pose.pose.position.x, msg.pose.pose.position.y, msg.pose.pose.position.z])
    #     self.vel_enu_odom = np.array([msg.twist.twist.linear.x, msg.twist.twist.linear.y, msg.twist.twist.linear.z])
        
    #     q0, q1, q2, q3 = msg.pose.pose.orientation.w, msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z
    #     self.mav_R_odom = np.array([
    #         [q0**2+q1**2-q2**2-q3**2, 2*(q1*q2-q0*q3), 2*(q1*q3+q0*q2)],
    #         [2*(q1*q2+q0*q3), q0**2-q1**2+q2**2-q3**2, 2*(q2*q3-q0*q1)],
    #         [2*(q1*q3-q0*q2), 2*(q2*q3+q0*q1), q0**2-q1**2-q2**2+q3**2]
    #     ])
    #     print("pos_enu_odom: {}, vel_enu_odom: {}, mav_yaw_odom: {}, mav_R_odom: {}".format(self.pos_enu_odom, self.vel_enu_odom, self.mav_yaw_odom, self.mav_R_odom))

    def mavros_state_callback(self, msg):
        self.mavros_state = msg
        self.arm_state = msg.armed
        self.mode_str = msg.mode
        self.offboard_state = True if msg.mode == "OFFBOARD" else False

    def rcin_callback(self, msg):
        def pwm_map(pwm):
            # 0-1300->0/1301-1700->1/1701-2000->2
            result = None
            if 0 < pwm <= 1300:
                result = 0
            if 1300 < pwm <= 1700:
                result = 1
            if 1700 < pwm <= 2100:
                result = 2
            return result


        self.rc_init_done = True
        last_rc_dict = self.rc_dict.copy()
        rc_chL = msg.channels
        
        for k,v in zip(last_rc_dict.keys(),rc_chL[4:10]):
            self.rc_dict[k] = pwm_map(v)

        if self.rc_dict != last_rc_dict:
            print("ch5: {}, ch6: {}, ch7: {}, ch8: {}, ch9: {}".format(*self.rc_dict.values()))

    # ============================== ROS 回调函数 end ============================================



    # ============================== PX4 起飞降落解锁控制接口 start ============================================  
    @property
    def task_ready(self):
        # print("offboard:",self.offboard_state)
        # print("rc_dict:",(self.rc_dict["ch7"] == 2))
        # print("rc_dict:", self.rc_dict["ch7"])
        # return ((self.rc_dict["ch7"] == 2) and self.offboard_state)
        return (self.rc_dict["ch7"] == 2)
    
    def land(self):
        try:
            #http://wiki.ros.org/mavros/CustomModes for custom modes
            self.landService(altitude = 0, latitude = 0, longitude = 0, min_pitch = 0, yaw = 0)
        except:
            print("land error!!!")

    def arm(self):
        ret = self.armService(True)
        if ret:
            print("Vehicle arming success!")
        else:
            print("Vehicle arming failed!")
        return ret
    

    # 强制解锁
    def arm_force(self):
        ret = self.cmdLongService(
            command=400,confirmation=0,
            param1=1.0,param2=21196.0
        )
        if ret:
            print("Vehicle arming success!")
        else:
            print("Vehicle arming failed!")
        return ret

    def disarm(self):
        ret = self.armService(False)
        if ret:
            print("Vehicle arming success!")
        else:
            print("Vehicle arming failed!")
        return ret

    def offboard(self):
        offbd_set_mode = SetMode()
        offbd_set_mode.custom_mode = "OFFBOARD"
        resp1 = self.flightModeService(0, offbd_set_mode.custom_mode)
        if resp1.mode_sent:
            print("Offboard enabled")
            return True
        else:
            print("Vechile Offboard failed")
            return False
    
    def takeoff_check(self):
        check_result = True
        if not self.offboard_state:
            print("not in offboard, switch in offboard mannualy")
            check_result = False

        if self.arm_state:
            print("mav is in sky")
            check_result = False

        return check_result

    def takeoff(self, vz=0.8, h=1.5):
        '''
        需要先
        直接给速度起飞，好像有啥问题来着
        起飞完成后速度清零
        '''
        # 切换到速度控制模式
        self.controller_swith(ctrl_type="vel")

        # 更新初始化参数
        self.pos_enu_offset = self.pos_enu

        self.mav_yaw_offset = self.mav_yaw
        self.R_eo = eulerAngleToMatrix([0,0,self.mav_yaw_offset])


        self.arm_force()
        time.sleep(0.5)
        self.offboard()
        time.sleep(0.5)

        print("takeoff pre task OK")
        print("mav_yaw_offset:{}".format(np.rad2deg(self.mav_yaw_offset)))
        print("pos_enu_offset:{}".format(self.pos_enu_offset))
        print("R_eo:\n{}".format(self.R_eo))



        self.command_vel = construct_vel_target(vz=vz)
        takeoff_done = False
        while not takeoff_done:
            # print("takeoff height: {}".format(self.mav_height))
            takeoff_done = (self.mav_height > h)
            time.sleep(0.1)
        print("takeoff done!")
        self.command_vel = construct_vel_target()


    
    def takeoff_pos(self,h=1.8):
        '''
        直接给
        '''

        if not self.takeoff_check():
            print("takeoff_check failure")
            return

        # 切换到速度控制模式
        self.controller_swith(ctrl_type="vel")
        self.mav_yaw_offset = self.mav_yaw
        self.arm()

        self.moveByPosENU(z=h)
        takeoff_done = False
        while not takeoff_done:
            # print("takeoff height:",{self.pos_enu[2]})
            takeoff_done = (self.pos_enu[2] > h)
            time.sleep(0.01)
        self.command_vel = construct_vel_target()

    # ============================== PX4 起飞降落解锁控制接口 end ============================================






    # ============================== PX4 速度位置控制接口 start ============================================
    def controller_swith(self,ctrl_type="vel"):
        ctrl_dict = PX4_CTRL_DICT[ctrl_type]
        self.__dict__.update(ctrl_dict)


    def moveByVelocityYawrateBodyFrame(self, vx=0, vy=0, vz=0, yaw_rate=0):
        '''
        机体系FLU的速度
        '''
        self.controller_swith(ctrl_type="vel")
        self.command_vel = construct_vel_target(vx, vy, vz, yaw_rate)

    def moveByVelocityYawrateENU(self, vx=0, vy=0, vz=0, yaw_rate=0):
        '''
        世界系ENU的速度,E是地理东
        '''
        self.controller_swith(ctrl_type="vel")
        self.command_vel = construct_vel_target(vx, vy, vz, yaw_rate, frame="ENU")

    
    def moveByPosENU(self, x=None, y=None, z=None, yaw_rad=None):
        self.controller_swith(ctrl_type="vel")
        yaw_rad = yaw_rad if yaw_rad is not None else self.mav_yaw
        x = x if x is not None else self.pos_enu[0]
        y = y if y is not None else self.pos_enu[1]
        z = z if z is not None else self.pos_enu[2]
        self.command_vel = construct_pos_target(x, y, z, yaw_rad, frame="ENU")
    
    # ENU下的角yaw_rad
    def moveByYaw(self, yaw_rad):
        self.controller_swith(ctrl_type="vel")
        x, y, z = self.pos_enu
        self.command_vel = construct_pos_target(x, y, z, yaw_rad, frame="ENU")

    

    # 移动至Swarm系下的位置，只控制x和y
    def moveBySwarmPosENU(self, x, y, z, vel=0.5):
        print("start moveBySwarmPosEN x:{:.2f} y:{:.2f}".format(x,y))
        self.controller_swith(ctrl_type="vel")
        tag_pos = np.array([x,y,z])

        # tgt_arrow = tag_pos - self.pos_swarm
        tgt_arrow = tag_pos - self.pos_enu
        
        
        
        while np.linalg.norm(tgt_arrow) > 0.5:
            # tgt_arrow = tag_pos - self.pos_swarm
            tgt_arrow = tag_pos - self.pos_enu
            # 转换到世界系
            tag_vel_xy_enu = np.dot(self.R_eo,tgt_arrow)
            tag_vel_xy = tag_vel_xy_enu/np.linalg.norm(tag_vel_xy_enu)*vel
            self.command_vel = construct_vel_target(tag_vel_xy[0], tag_vel_xy[1], tag_vel_xy[2], frame="ENU")




            # print("pos_enu: {}".format(self.pos_enu))
            # print("pos_odom: {}".format(self.pos_odom))
            # print("pos_swarm: {}".format(self.pos_swarm))
            print("pos_enu:[{:.2f} {:.2f} {:.2f}] norm:{:.3f}".format(self.pos_enu[0],self.pos_enu[1],self.pos_enu[2],np.linalg.norm(tgt_arrow)))

            time.sleep(0.02)
        
        self.command_vel = construct_vel_target()
        print("moveBySwarmPosEN end")
    
    
    # ============================== 控制接口 end ============================================






def construct_vel_target(vx=0, vy=0, vz=0, yaw_rate=0,frame="FLU"):   
    '''
    uint8 FRAME_LOCAL_NED = 1
    uint8 FRAME_LOCAL_OFFSET_NED = 7
    uint8 FRAME_BODY_NED = 8
    uint8 FRAME_BODY_OFFSET_NED = 9
    '''
    
    coordinate_frame = 8
    if frame == "FLU": 
        coordinate_frame = 8
    elif frame == "ENU": 
        coordinate_frame = 1

    target_raw_pose = PositionTarget()
    target_raw_pose.header.stamp = rospy.Time.now()

    target_raw_pose.coordinate_frame = coordinate_frame 
    target_raw_pose.velocity.x = vx
    target_raw_pose.velocity.y = vy
    target_raw_pose.velocity.z = vz

    target_raw_pose.type_mask = (
        PositionTarget.IGNORE_PX + PositionTarget.IGNORE_PY + PositionTarget.IGNORE_PZ 
        + PositionTarget.IGNORE_AFX + PositionTarget.IGNORE_AFY + PositionTarget.IGNORE_AFZ 
        + PositionTarget.FORCE + PositionTarget.IGNORE_YAW 
    )

    target_raw_pose.yaw_rate = yaw_rate
    return target_raw_pose




def construct_pos_target(x=0, y=0, z=0, yaw=0, yaw_rate=0, frame="FLU"):
    '''
    uint8 FRAME_LOCAL_NED = 1
    uint8 FRAME_LOCAL_OFFSET_NED = 7
    uint8 FRAME_BODY_NED = 8
    uint8 FRAME_BODY_OFFSET_NED = 9
    '''

    coordinate_frame = 8
    if frame == "FLU": 
        coordinate_frame = 8
    elif frame == "ENU": 
        coordinate_frame = 1

    target_raw_pose = PositionTarget()
    target_raw_pose.header.stamp = rospy.Time.now()
    target_raw_pose.coordinate_frame = coordinate_frame

    target_raw_pose.position.x = x
    target_raw_pose.position.y = y
    target_raw_pose.position.z = z

    target_raw_pose.type_mask = (
        PositionTarget.IGNORE_VX + PositionTarget.IGNORE_VY + PositionTarget.IGNORE_VZ 
        + PositionTarget.IGNORE_AFX + PositionTarget.IGNORE_AFY + PositionTarget.IGNORE_AFZ 
        + PositionTarget.FORCE
    )

    target_raw_pose.yaw = yaw
    target_raw_pose.yaw_rate = yaw_rate
    return target_raw_pose

# 用于结束线程的函数
def _async_raise(tid, exctype):
    
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")   


if __name__ == '__main__':
    con = Px4Controller()
    con.start()
