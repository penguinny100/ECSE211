from threading import Thread
import time
from utils.sound import Sound
from utils.brick import TouchSensor, EV3ColorSensor, EV3UltrasonicSensor, Motor

SPEED = 90
MOTOR_R = Motor("A")
MOTOR_L = Motor("B")
COLOR_SENSOR = EV3ColorSensor()
TOUCH_SENSOR = TouchSensor()
ULTRASONIC_SENSOR = EV3UltrasonicSensor()

DELIVERY_SOUND = Sound(duration=1, volume=80, pitch="C5")
MISSION_COMPLETE_SOUND = Sound(duration=1, volume=80, pitch="G5")

MOTOR_R.reset_encoder()
MOTOR_L.reset_encoder()

RB = 7 # radius of turning circle
RW = 2 # wheel radius
ORIENT_TO_DEG = RB / RW

def follow_line():
    pass

def stop():
    MOTOR_R.set_dps(0)
    MOTOR_L.set_dps(0)

def move_forward():
    MOTOR_R.set_dps(SPEED)
    MOTOR_L.set_dps(SPEED)

def move_backward():
    MOTOR_R.set_dps(-SPEED)
    MOTOR_L.set_dps(-SPEED)

def return_to_road():
    return

def scan_room():
    return

def drop_package():
    DELIVERY_SOUND.play()
    print("Package delivered")

def return_to_mailroom():
    MISSION_COMPLETE_SOUND.play()
    print("Mission complete")

def turn(angle):
    if angle < 0: # left
        MOTOR_L.set_position_relative(-int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(int(angle * ORIENT_TO_DEG))
    else: # right
        MOTOR_L.set_position_relative(int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(-int(angle * ORIENT_TO_DEG))

def main():
    movement_thread = Thread(target=move_forward)
    movement_thread.start()
    movement_thread.join()

if __name__=='__main__':
    main()