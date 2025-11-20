from threading import Thread
from time import sleep
from enum import Enum
from utils.sound import Sound
from utils.brick import (
    TouchSensor,
    EV3ColorSensor,
    _color_names_by_code,
    EV3UltrasonicSensor,
    Motor
)

# motors and speed
SPEED = 180
DRIFT = 10
MOTOR_R = Motor("D")
MOTOR_L = Motor("A")
MOTOR_R.reset_encoder()
MOTOR_L.reset_encoder()

TOUCH_SENSOR = TouchSensor("2")
ULTRASONIC_SENSOR = EV3UltrasonicSensor("3")

# colors
COLOR_SENSOR = EV3ColorSensor("4", mode="id")
# Note from ben to whoever's working on it today: line threshold is the average between
# the black reading and white reading. to tune it. build the robot so you know what height
# the colour sensor's at. Then, print a reading when its over the black line. Then,
# print a reading when its over the white line. Then, compute the average.
# Turn constant is how sharply it corrects. Tune this up or down as needed as well.
# Color detection now uses color_detector (from utils) for modularity, thresholds removed as redundant.

# line following
LINE_CORRECTION = 20

# turning
MAP_LENGTH = 1200  # 1200cm map length
HALFWAY_DOWN_MAP = 1200 / 2  # cm
QUARTER_DOWN_MAP = 1200 / 4  # cm
#DISTANCE_OF_BLACK_LINE_FROM_WALL = 5  # cm
wall_target_distance=None

# sounds
DELIVERY_SOUND = Sound(duration=1, volume=80, pitch="C5")
MISSION_COMPLETE_SOUND = Sound(duration=1, volume=80, pitch="G5")


# Note from ben to whoever's working on it today: RB is the distance between the middle of the thickness
# of one wheel to the middle of the thickness of the other wheel divided by two (aka the turning radius)
# RW is the radius of a wheel. This needs to be remeasured as you rebuild the robot. This makes sure
# it actually turns the right angle when we want it to
RB = 5  # radius of turning circle
RW = 2  # wheel radius
ORIENT_TO_DEG = RB / RW

# states


class State(Enum):
    FOLLOWING_LINE = "FOLLOWING_LINE"
    CHECKING_DOORWAY = "CHECKING_DOORWAY"
    # AVOIDING_RESTRICTED = "AVOIDING_RESTRICTED"
    ENTERING_ROOM = "ENTERING_ROOM"
    SCANNING_ROOM = "SCANNING_ROOM"
    DELIVERING = "DELIVERING"
    EXITING_ROOM = "EXITING_ROOM"
    MISSION_COMPLETE = "MISSION_COMPLETE"


emergency_stopped = False
color_check_timer = 0
packages_delivered = 0
current_state = State.FOLLOWING_LINE
# ============= UTILITY FUNCTIONS =============


def stop_movement():
    """Stop both motors"""
    MOTOR_R.set_dps(0)
    MOTOR_L.set_dps(0)


def move_forward():
    """Move both motors forward at a specified speed"""
    MOTOR_R.set_dps(SPEED)
    MOTOR_L.set_dps(SPEED)


def move_backward():
    """Move both motors backward at a specified speed"""
    MOTOR_R.set_dps(-SPEED)
    MOTOR_L.set_dps(-SPEED)


def turn(angle):
    """Turns the robot at by the specified angle (pos right, neg left)"""
    stop_movement()
    MOTOR_L.set_limits(dps=SPEED)
    MOTOR_R.set_limits(dps=SPEED)
    sleep(0.25)
    if angle < 0:  # left
        MOTOR_L.set_position_relative(-int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(int(angle * ORIENT_TO_DEG))
    else:  # right
        MOTOR_L.set_position_relative(int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(-int(angle * ORIENT_TO_DEG))
    sleep(abs(angle) / 90.0 * 0.5)
    stop_movement()
    sleep(0.2)


def turn_left():
    print("Turning left")
    turn(-90)


def drift_left():
    MOTOR_L.set_dps(SPEED - DRIFT)
    MOTOR_R.set_dps(SPEED + DRIFT)


def turn_right():
    print("Turning left")
    turn(90)


def drift_right():
    MOTOR_L.set_dps(SPEED + DRIFT)
    MOTOR_R.set_dps(SPEED - DRIFT)


def turn_around():
    print("Turning around")
    turn(180)


def get_distance():
    """Gets the distance measured by the US sensor"""
    dist = ULTRASONIC_SENSOR.get_cm()
    return dist

# ============= COLOR DETECTION =============


def get_color_name():
    """Get the name of the detected color using ColorDetector"""
    color_code = COLOR_SENSOR.get_value()
    return _color_names_by_code.get(color_code, "Unknown")


def detect_black():
    """Detect black line"""
    return get_color_name().lower() == "black"


def detect_white():
    """Detect white tile (off the line)"""
    return get_color_name().lower() == "white"


def detect_yellow():
    """Detect yellow tile (office)"""
    return get_color_name().lower() == "yellow"


def detect_blue():
    """Detect blue tile (mail room)"""
    return get_color_name().lower() == "blue"


def detect_green():
    """Detect green sticker (recipient present)"""
    return get_color_name().lower() == "green"


def detect_red():
    """Detect red sticker (restricted area)"""
    return get_color_name().lower() == "red"


def detect_orange():
    """Detect orange doorway"""
    return get_color_name().lower() == "orange"

# ============= LINE FOLLOWING =============


def follow_line():
    """Follows the black line and detects colour changes for doors etc"""
    global current_state, emergency_stopped
    global wall_target_distance

    distance = get_distance()
    if wall_target_distance is None:
        if distance is not None:
            wall_target_distance=distance
            print(f"Locked Wall target distance at {wall_target_distance} cm")
            move_forward()

    else:
        if distance is None:
            pass
        elif distance > 100:
            pass
        elif distance < wall_target_distance:
            print(f"Distance: {distance}. Drifting right")
            drift_left()
            sleep(0.1)
        elif distance > wall_target_distance:
           print(f"Distance: {distance}. Drifting left")
           drift_right()
           sleep(0.1)

    if detect_orange():
        if packages_delivered < 2:
            print("Orange detected - Doorway")
           # current_state = State.CHECKING_DOORWAY
        else:
            print("Orange detected - Mission already complete")
            #current_state = State.CHECKING_DOORWAY

    elif detect_black():
        print("Black detected - Corner or mail room")
        #turn_left()  # turn 90 degrees ccw
        if not get_distance():  # error handling
            pass
        elif get_distance() < DISTANCE_OF_BLACK_LINE_FROM_WALL + 5:
            print("It's a corner!")
            # to add: turn the corner on the outer boundary if this is the case
        else:
            print("It's the mail room!")
            if packages_delivered < 2:
                print("Not ready yet...")
                #turn_right()  # this rotates it back to state that it was before
                # correction for infinite loop
                #move_forward()
                sleep(0.5)
            else:
                print("Go to the mail room!")
                #current_state = State.MISSION_COMPLETE  # to change

    elif detect_red():
        print("Red detected - Restricted")
        # current_state = State.AVOIDING_RESTRICTED

    elif detect_blue():
        if packages_delivered >= 2:
            print("Blue detected - Entering")
            # current_state = State.MAIL_ROOM_FOUND
        else:
            print("Blue detected - Mission not yet complete")
            # current_state = State.AVOIDING_RESTRICTED

    sleep(0.05)


# ============= ROOM OPERATIONS =============


def avoid_restricted():
    turn_around()


def scan_room():
    return


def drop_package():
    DELIVERY_SOUND.play()
    print("Package delivered")


def return_to_mailroom():
    MISSION_COMPLETE_SOUND.play()
    print("Mission complete")

# ============= EMERGENCY STOP =============

def emergency_stop():
    global emergency_stopped
    while not emergency_stopped:
        if TOUCH_SENSOR.is_pressed():
            emergency_stopped = True
            print("Emergency stop activated")
            sleep(0.1)

# ============= CHECKING DOORWAY ===========

# this state encapsulates checking the doorway once orange is detected
def checking_doorway():

    global current_state, emergency_stopped

    print("Checking doorway for restriction...")

    # move forward slowly while we check
    MOTOR_L.set_dps(SPEED)
    MOTOR_R.set_dps(SPEED)

    STEP = 0.05              # seconds between checks
    HALF_DOOR_TIME = 0.5     # current hardcode assumption of 0.5 seconds to get halfway

    elapsed = 0.0
    saw_red = False

    while elapsed < HALF_DOOR_TIME and not emergency_stopped:
        if not COLOR_SENSOR.set_mode("id"):
            print("Could not switch color sensor to id mode in checking_doorway")
        else:
            color_name = get_color_name().lower()
            if color_name == "red":
                print("Red detected in doorway -> restricted room. Skipping.")
                saw_red = True
                break

        sleep(STEP)
        elapsed += STEP

    # stop where we are (either at halfway or when we saw red)
    stop_movement()

    if saw_red:
        # We hit a restricted doorway: go back to following line.
        MOTOR_L.set_dps(SPEED)
        MOTOR_R.set_dps(SPEED)
        sleep(0.5)   # tune: just enough to pass the doorway
        stop_movement()
        current_state = State.FOLLOWING_LINE

    else:
        # No red seen by halfway: safe doorway, enter the room.
        print("Doorway clear (no red) -> entering room.")
        current_state = State.ENTERING_ROOM

    return


# ============= STATE MACHINE =============

def state_machine():
    """Main state machine for robot behavior"""
    global current_state, emergency_stopped
    sleep(3)
    while not emergency_stopped:
        if current_state == State.FOLLOWING_LINE:
            follow_line()

        elif current_state == State.CHECKING_DOORWAY:
            pass

        elif current_state == State.AVOIDING_RESTRICTED:
            avoid_restricted()
            current_state = State.FOLLOWING_LINE

        elif current_state == State.ENTERING_ROOM:
            pass

        elif current_state == State.SCANNING_ROOM:
            pass

        elif current_state == State.DELIVERING:
            pass

        elif current_state == State.EXITING_ROOM:
            pass

        elif current_state == State.MAIL_ROOM_FOUND:
            pass

        elif current_state == State.MISSION_COMPLETE:
            pass

        sleep(0.05)


def main():
    state_thread = Thread(target=state_machine)
    emergency_stop_thread = Thread(target=emergency_stop)

    state_thread.start()
    emergency_stop_thread.start()

    state_thread.join()
    emergency_stop_thread.join()

    print("Program terminated")


if __name__ == '__main__':
    main()
