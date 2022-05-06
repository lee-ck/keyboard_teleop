# Copyright 2011 Brown University Robotics.
# Copyright 2017 Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Software License Agreement (BSD License 2.0)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the Willow Garage nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys

import geometry_msgs.msg
from std_msgs.msg import Float64
import rclpy

if sys.platform == 'win32':
    import msvcrt
else:
    import termios
    import tty


msg = """
This node takes keypresses from the keyboard and publishes them
as Twist messages. It works best with a US keyboard layout.
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .
For Holonomic mode (strafing), hold down the shift key:
---------------------------
   U    I    O
   J    K    L
   M    <    >
t : up (+z)
b : down (-z)
anything else : stop
q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%
CTRL-C to quit
"""

moveBindings_right = { # X Y N
    #'i': (1, 0, 0),
    #'k': (-1, 0, 0),
    'u': (0, 0, -1), 
    'o': (0, 0, 1),
    'j': (0, -1, 0),
    'l': (0, 1, 0),
}

moveBindings_left = { # X Y N
    's': (0, -1, 0),
    'f': (0, 1, 0),
}
speedBindings_right = {
    'i': (140, 0),
    'k': (-140, 0),
}
speedBindings_left = {
    'e': (140, 0),
    'd': (-140, 0),
}


def getKey(settings):
    if sys.platform == 'win32':
        # getwch() returns a string on Windows
        key = msvcrt.getwch()
    else:
        tty.setraw(sys.stdin.fileno())
        # sys.stdin.read() returns a string on Linux
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def saveTerminalSettings():
    if sys.platform == 'win32':
        return None
    return termios.tcgetattr(sys.stdin)


def restoreTerminalSettings(old_settings):
    if sys.platform == 'win32':
        return
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def vels(sl,al,sr,ar):
    return 'Left: \tspeed %s [perc] \t angle %s [deg], Right: \tspeed %s [perc] \t angle %s [deg]' % (sl/1000,al*180/3.14159,sr/1000,ar*180/3.14159) 


def main():
    settings = saveTerminalSettings()

    rclpy.init()

    node = rclpy.create_node('teleop_twist_keyboard')
    pub_lt = node.create_publisher(Float64, '/usv/left/thrust/cmd_thrust', 10)
    pub_rt = node.create_publisher(Float64, '/usv/right/thrust/cmd_thrust', 10)
    pub_la = node.create_publisher(Float64, '/usv/left/thrust/joint/cmd_pos', 10)
    pub_ra = node.create_publisher(Float64, '/usv/right/thrust/joint/cmd_pos', 10)
    
    
    pub_ra = node.create_publisher(Float64, '/usv/right/thrust/joint/cmd_pos', 10)

    
    speed_right = 0.0
    angle_right = 0.0
    
    speed_left = 0.0
    angle_left = 0.0

    speed_max = 10000.0
    try:
        while True:
            print(vels(speed_left,angle_left,speed_right,angle_right))
            key = getKey(settings)
            if key in moveBindings_right.keys():
                # X = moveBindings[key][0]
                angle_right = angle_right + moveBindings_right[key][1]/10
                if angle_right > 1.571:
                    angle_right = 1.571
                elif angle_right < -1.571:
                    angle_right = -1.571                        

                N = moveBindings_right[key][2]
            elif key in speedBindings_right.keys():
                speed_right = speed_right + speedBindings_right[key][0]
                if speed_right > speed_max:
                    speed_right = speed_max
                elif speed_right < -speed_max:
                    speed_right = -speed_max

            elif key in moveBindings_left.keys():
                # X = moveBindings[key][0]
                angle_left = angle_left + moveBindings_left[key][1]/10
                if angle_left > 1.571:
                    angle_left = 1.571
                elif angle_left < -1.571:
                    angle_left = -1.571                        

                N = moveBindings_left[key][2]
            elif key in speedBindings_left.keys():
                speed_left = speed_left + speedBindings_left[key][0]
                if speed_left > speed_max:
                    speed_left = speed_max
                elif speed_left < -speed_max:
                    speed_left = -speed_max                        
            else:
                speed_left = 0.0
                angle_left = 0.0
                speed_right = 0.0
                angle_right = 0.0
                
                if (key == '\x03'):
                    break


            Thrust_right = Float64()
            Thrust_right.data = speed_right
            Angle_right = Float64()
            Angle_right.data = angle_right

            pub_rt.publish(Thrust_right)
            pub_ra.publish(Angle_right)

            Thrust_left = Float64()
            Thrust_left.data = speed_left
            Angle_left = Float64()
            Angle_left.data = angle_left

            pub_lt.publish(Thrust_left)
            pub_la.publish(Angle_left)


    except Exception as e:
        print(e)

    finally:
        Thrust = Float64()
        Thrust.data = 0.0
        Angle = Float64()
        Angle.data = 0.0
        pub_lt.publish(Thrust)
        pub_rt.publish(Thrust)
        pub_la.publish(Angle)
        pub_ra.publish(Angle)

        restoreTerminalSettings(settings)


if __name__ == '__main__':
    main()