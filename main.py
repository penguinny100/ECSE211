from threading import Thread
from time import sleep
from utils.sound import Sound
from utils.brick import TouchSensor, EV3ColorSensor, EV3UltrasonicSensor, Motor

SPEED = 180
MOTOR_R = Motor("D")
MOTOR_L = Motor("A")
COLOR_SENSOR = EV3ColorSensor("1")
TOUCH_SENSOR = TouchSensor("2")
ULTRASONIC_SENSOR = EV3UltrasonicSensor("3")

DELIVERY_SOUND = Sound(duration=1, volume=80, pitch="C5")
MISSION_COMPLETE_SOUND = Sound(duration=1, volume=80, pitch="G5")
MOTOR_R.reset_encoder()
MOTOR_L.reset_encoder()

RB = 7 # radius of turning circle
RW = 2 # wheel radius
ORIENT_TO_DEG = RB / RW

THRESHOLD = 40
turn_constant = 3.0

emergency_stopped = False

def emergency_stop():
    global emergency_stopped
    while not emergency_stopped:
        if TOUCH_SENSOR.is_pressed():
            emergency_stopped = True
            print("Emergency stop activated")
            
def follow_line():
    global emergency_stopped
    print("Starting line following")
    while not emergency_stopped:
        light_value = COLOR_SENSOR.get_red()
        if light_value is None:
            continue

        error = light_value - THRESHOLD
        turn = error * turn_constant
        left_speed = SPEED - turn
        right_speed = SPEED + turn

        MOTOR_L.set_dps(left_speed)
        MOTOR_R.set_dps(right_speed)

        sleep(0.05)
        
    stop_movement()
    print("Stopping line following")

def stop_movement():
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
    stop_movement()
    MOTOR_L.set_limits(dps=SPEED)
    MOTOR_R.set_limits(dps=SPEED)
    sleep(0.25)
    if angle < 0: # left
        MOTOR_L.set_position_relative(-int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(int(angle * ORIENT_TO_DEG))
    else: # right
        MOTOR_L.set_position_relative(int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(-int(angle * ORIENT_TO_DEG))

def main():
    movement_thread = Thread(target=follow_line)
    emergency_stop_thread = Thread(target=emergency_stop)

    movement_thread.start()
    emergency_stop_thread.start()

    movement_thread.join()
    emergency_stop_thread.join()

if __name__=='__main__':
    main()