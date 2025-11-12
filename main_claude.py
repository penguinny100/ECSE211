from threading import Thread
from time import sleep, time
from utils.sound import Sound
from utils.brick import TouchSensor, EV3ColorSensor, EV3UltrasonicSensor, Motor

# ============= CONFIGURATION =============
SPEED = 180
SLOW_SPEED = 100
MOTOR_R = Motor("D")
MOTOR_L = Motor("A")

COLOR_SENSOR = EV3ColorSensor("4")
TOUCH_SENSOR = TouchSensor("2")
ULTRASONIC_SENSOR = EV3UltrasonicSensor("3")

# Sound effects
DELIVERY_SOUND = Sound(duration=0.5, volume=80, pitch="C5")
MISSION_COMPLETE_SOUND = Sound(duration=1, volume=80, pitch="G5")

# Motor calibration
MOTOR_R.reset_encoder()
MOTOR_L.reset_encoder()

# Turning constants
RB = 7  # radius of turning circle (cm)
RW = 2  # wheel radius (cm)
ORIENT_TO_DEG = RB / RW

# Line following
LINE_THRESHOLD = 40  # Adjust based on your line color
TURN_CONSTANT = 1.5  # Start conservative, tune as needed

# Color detection thresholds
COLOR_CHECK_INTERVAL = 0.15
YELLOW_THRESHOLD = 0.30
BLUE_THRESHOLD = 0.28
GREEN_THRESHOLD = 0.28
RED_THRESHOLD = 0.30

# Distance thresholds
WALL_DISTANCE = 15  # cm
DOORWAY_DETECT_DISTANCE = 30  # cm

# States
STATE_FOLLOWING_LINE = "FOLLOWING_LINE"
STATE_YELLOW_DETECTED = "YELLOW_DETECTED"
STATE_CHECKING_DOORWAY = "CHECKING_DOORWAY"
STATE_ENTERING_ROOM = "ENTERING_ROOM"
STATE_SCANNING_ROOM = "SCANNING_ROOM"
STATE_DELIVERING = "DELIVERING"
STATE_EXITING_ROOM = "EXITING_ROOM"
STATE_BLUE_DETECTED = "BLUE_DETECTED"
STATE_MISSION_COMPLETE = "MISSION_COMPLETE"
STATE_AVOIDING_RESTRICTED = "AVOIDING_RESTRICTED"

# Global state
current_state = STATE_FOLLOWING_LINE
emergency_stopped = False
packages_delivered = 0
color_check_timer = 0

# ============= UTILITY FUNCTIONS =============

def stop_movement():
    """Stop both motors immediately"""
    MOTOR_R.set_dps(0)
    MOTOR_L.set_dps(0)

def move_forward(speed=SPEED):
    """Move forward at specified speed"""
    MOTOR_R.set_dps(speed)
    MOTOR_L.set_dps(speed)

def move_backward(speed=SPEED):
    """Move backward at specified speed"""
    MOTOR_R.set_dps(-speed)
    MOTOR_L.set_dps(-speed)

def turn(angle, speed=SPEED):
    """Turn by specified angle (positive = right, negative = left)"""
    stop_movement()
    MOTOR_L.set_limits(dps=speed)
    MOTOR_R.set_limits(dps=speed)
    sleep(0.1)
    
    if angle < 0:  # Turn left
        MOTOR_L.set_position_relative(-int(abs(angle) * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(int(abs(angle) * ORIENT_TO_DEG))
    else:  # Turn right
        MOTOR_L.set_position_relative(int(angle * ORIENT_TO_DEG))
        MOTOR_R.set_position_relative(-int(angle * ORIENT_TO_DEG))
    
    sleep(abs(angle) / 90.0 * 0.5)  # Wait for turn to complete
    stop_movement()
    sleep(0.2)

def get_distance():
    """Get ultrasonic sensor reading"""
    dist = ULTRASONIC_SENSOR.get_cm()
    return dist if dist is not None else 999

# ============= COLOR DETECTION =============

def get_normalized_rgb():
    """Get normalized RGB values"""
    rgb = COLOR_SENSOR.get_rgb()
    if rgb is None:
        return None
    r, g, b = rgb
    total = r + g + b
    if total == 0:
        return None
    return (r/total, g/total, b/total)

def detect_yellow():
    """Detect yellow tile (office)"""
    rgb = get_normalized_rgb()
    if rgb is None:
        return False
    r, g, b = rgb
    # Yellow = high red + high green, low blue
    return (r > YELLOW_THRESHOLD and g > YELLOW_THRESHOLD and 
            b < 0.25 and abs(r - g) < 0.15)

def detect_blue():
    """Detect blue tile (mail room)"""
    rgb = get_normalized_rgb()
    if rgb is None:
        return False
    r, g, b = rgb
    # Blue = high blue, low red and green
    return b > BLUE_THRESHOLD and b > r + 0.1 and b > g + 0.1

def detect_green():
    """Detect green sticker (recipient present)"""
    rgb = get_normalized_rgb()
    if rgb is None:
        return False
    r, g, b = rgb
    # Green = high green, low red and blue
    return g > GREEN_THRESHOLD and g > r + 0.1 and g > b + 0.1

def detect_red():
    """Detect red sticker (restricted area)"""
    rgb = get_normalized_rgb()
    if rgb is None:
        return False
    r, g, b = rgb
    # Red = high red, low green and blue
    return r > RED_THRESHOLD and r > g + 0.15 and r > b + 0.15

def detect_orange():
    """Detect orange doorway"""
    rgb = get_normalized_rgb()
    if rgb is None:
        return False
    r, g, b = rgb
    # Orange = high red, medium green, low blue
    return r > 0.35 and 0.15 < g < 0.35 and b < 0.20

# ============= LINE FOLLOWING =============

def follow_line_step():
    """Single step of line following with color detection"""
    global color_check_timer, current_state, packages_delivered
    
    light_value = COLOR_SENSOR.get_red()
    if light_value is None:
        return
    
    # PID-style line following
    error = LINE_THRESHOLD - light_value
    turn = error * TURN_CONSTANT
    left_speed = SPEED - turn
    right_speed = SPEED + turn
    
    MOTOR_L.set_dps(left_speed)
    MOTOR_R.set_dps(right_speed)
    
    # Periodic color checking
    color_check_timer += 0.05
    if color_check_timer >= COLOR_CHECK_INTERVAL:
        color_check_timer = 0
        
        # Check for yellow tile (office)
        if detect_yellow() and packages_delivered < 2:
            print("YELLOW DETECTED - Office ahead!")
            current_state = STATE_YELLOW_DETECTED
        
        # Check for blue tile (mail room)
        elif detect_blue() and packages_delivered >= 2:
            print("BLUE DETECTED - Mail room!")
            current_state = STATE_BLUE_DETECTED

# ============= ROOM OPERATIONS =============

def check_doorway():
    """Check doorway for red sticker BEFORE entering"""
    print("Checking doorway for restrictions...")
    stop_movement()
    sleep(0.3)
    
    # Move forward slowly to doorway
    move_forward(SLOW_SPEED)
    start_time = time()
    orange_found = False
    
    while time() - start_time < 2:  # Look for orange doorway
        if detect_orange():
            print("Orange doorway detected!")
            orange_found = True
            stop_movement()
            sleep(0.3)
            break
        sleep(0.1)
    
    if not orange_found:
        print("Warning: No orange doorway found")
    
    # NOW check for red sticker at doorway
    if detect_red():
        print("RED STICKER AT DOOR - Restricted area!")
        return "RESTRICTED"
    
    return "CLEAR"

def enter_room():
    """Enter office through doorway (after checking it's clear)"""
    print("Entering room...")
    
    # Move through doorway into room
    move_forward(SLOW_SPEED)
    sleep(1.2)  # Move past doorway into room
    stop_movement()
    sleep(0.3)

def scan_room():
    """Scan room for green recipient sticker only"""
    print("Scanning room for recipient...")
    
    # Do a slow 360 degree scan looking for GREEN only
    for angle_step in range(0, 360, 30):
        turn(30, speed=SLOW_SPEED)
        sleep(0.3)
        
        # Check for green sticker (recipient)
        if detect_green():
            print("GREEN STICKER FOUND - Recipient present!")
            return "GREEN"
        
        sleep(0.2)
    
    print("No recipient found in room")
    return "NONE"

def drop_package():
    """Simulate package drop with sound"""
    global packages_delivered
    print(f"Delivering package #{packages_delivered + 1}")
    DELIVERY_SOUND.play()
    DELIVERY_SOUND.wait_done()
    packages_delivered += 1
    print(f"Packages delivered: {packages_delivered}/2")
    sleep(0.5)

def exit_room():
    """Exit room and return to line"""
    print("Exiting room...")
    # Turn around
    turn(180)
    sleep(0.3)
    
    # Move forward until back on line
    move_forward(SLOW_SPEED)
    sleep(1.5)
    
    # Find the line
    find_line()

def find_line():
    """Search for line after exiting room"""
    print("Finding line...")
    start_time = time()
    
    while time() - start_time < 2:
        light = COLOR_SENSOR.get_red()
        if light is not None and abs(light - LINE_THRESHOLD) < 15:
            print("Line found!")
            stop_movement()
            return True
        sleep(0.1)
    
    # If not found, do small search pattern
    turn(-45)
    move_forward(SLOW_SPEED)
    sleep(0.5)
    stop_movement()
    return True

def avoid_restricted_area():
    """Back up and reroute around restricted office"""
    print("Avoiding restricted area...")
    stop_movement()
    
    # Back up
    move_backward(SLOW_SPEED)
    sleep(1.0)
    stop_movement()
    
    # Turn to avoid
    turn(-90)
    
    # Move forward to bypass
    move_forward(SPEED)
    sleep(1.0)
    
    # Turn back toward path
    turn(90)

# ============= STATE MACHINE =============

def state_machine():
    """Main state machine for robot behavior"""
    global current_state, emergency_stopped, packages_delivered
    
    while not emergency_stopped:
        
        if current_state == STATE_FOLLOWING_LINE:
            follow_line_step()
        
        elif current_state == STATE_YELLOW_DETECTED:
            stop_movement()
            sleep(0.3)
            current_state = STATE_CHECKING_DOORWAY
        
        elif current_state == STATE_CHECKING_DOORWAY:
            doorway_status = check_doorway()
            
            if doorway_status == "RESTRICTED":
                current_state = STATE_AVOIDING_RESTRICTED
            else:
                current_state = STATE_ENTERING_ROOM
        
        elif current_state == STATE_ENTERING_ROOM:
            enter_room()
            current_state = STATE_SCANNING_ROOM
        
        elif current_state == STATE_SCANNING_ROOM:
            result = scan_room()
            
            if result == "GREEN":
                current_state = STATE_DELIVERING
            else:
                # No recipient, just exit
                current_state = STATE_EXITING_ROOM
        
        elif current_state == STATE_DELIVERING:
            drop_package()
            current_state = STATE_EXITING_ROOM
        
        elif current_state == STATE_AVOIDING_RESTRICTED:
            avoid_restricted_area()
            current_state = STATE_FOLLOWING_LINE
        
        elif current_state == STATE_EXITING_ROOM:
            exit_room()
            current_state = STATE_FOLLOWING_LINE
        
        elif current_state == STATE_BLUE_DETECTED:
            stop_movement()
            sleep(0.5)
            print("Moving to mail room...")
            move_forward(SLOW_SPEED)
            sleep(1.5)
            current_state = STATE_MISSION_COMPLETE
        
        elif current_state == STATE_MISSION_COMPLETE:
            stop_movement()
            print("MISSION COMPLETE!")
            MISSION_COMPLETE_SOUND.play()
            MISSION_COMPLETE_SOUND.wait_done()
            emergency_stopped = True
        
        sleep(0.05)
    
    stop_movement()
    print("Robot stopped")

# ============= EMERGENCY STOP =============

def emergency_stop():
    """Monitor touch sensor for emergency stop"""
    global emergency_stopped
    while not emergency_stopped:
        if TOUCH_SENSOR.is_pressed():
            emergency_stopped = True
            stop_movement()
            print("EMERGENCY STOP ACTIVATED")
        sleep(0.1)

# ============= MAIN =============

def main():
    print("Smart Courier Robot Starting...")
    print("Press touch sensor for emergency stop")
    sleep(1)
    
    # Start threads
    state_thread = Thread(target=state_machine)
    emergency_thread = Thread(target=emergency_stop)
    
    state_thread.start()
    emergency_thread.start()
    
    state_thread.join()
    emergency_thread.join()
    
    print("Program terminated")

if __name__ == '__main__':
    main()