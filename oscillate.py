from time import sleep

"""
oscillate.py
Blocking "windshield wiper" scan for green tile.

Usage (in main.py):
    from oscillate import EnterRoomScanner

    scanner = EnterRoomScanner(
        motor_l=MOTOR_L,
        motor_r=MOTOR_R,
        motor_sensor=MOTOR_SENSOR,
        color_sensor=COLOR_SENSOR,
        detect_green_fn=detect_green,
        emergency_flag_fn=lambda: emergency_stopped
    )

    # inside enter_room state:
    found = scanner.search_for_green()
    if found:
        drop_package()
        ...
"""
class EnterRoomScanner:
    def __init__(
        self,
        motor_l,
        motor_r,
        motor_sensor,
        color_sensor,
        detect_green_fn,
        emergency_flag_fn=lambda: False,
        speed=180,
        cm_step_time=0.15,
        sweep_dps=180,
        sweep_power=60,
        sweep_half_deg=90,
    ):
        # injected hardware
        self.motor_l = motor_l
        self.motor_r = motor_r
        self.motor_sensor = motor_sensor
        self.color_sensor = color_sensor

        # injected logic
        self.detect_green = detect_green_fn
        self.emergency_flag = emergency_flag_fn

        # tuning params
        self.speed = speed
        self.cm_step_time = cm_step_time
        self.sweep_dps = sweep_dps
        self.sweep_power = sweep_power
        self.sweep_half_deg = sweep_half_deg

        # derived speeds
        self.step_dps = self.speed / 4

    # ----------------------------
    # Public API
    # ----------------------------
    def search_for_green(self):
        """
        Implements your pseudo:
        - stop
        - center sensor
        - loop:
            move forward ~1cm
            sweep 180° until green or done
        Returns True if green found, else False (emergency stop).
        """
        detects_green = False

        # pause everything
        self.motor_l.set_dps(0)
        self.motor_r.set_dps(0)

        # center sensor
        self.center_color_sensor()

        while not detects_green and not self.emergency_flag():
            self.move_forward_1cm()
            detects_green = self.windshieldwiper_detect_green()

        return detects_green

    # ----------------------------
    # Helpers
    # ----------------------------
    def center_color_sensor(self):
        """
        Rotate sensor to middle. Assumes encoder 0 = center.
        If your physical center is different, change the target.
        """
        ms = self.motor_sensor
        ms.set_limits(dps=self.sweep_dps, power=self.sweep_power)
        ms.reset_encoder()

        ms.set_position(0)
        ms.set_dps(self.sweep_dps)

        while abs(ms.get_dps()) > 5 and not self.emergency_flag():
            sleep(0.01)

        ms.set_dps(0)

    def move_forward_1cm(self):
        """
        Tiny forward step. Time-based: tune cm_step_time.
        """
        self.motor_l.set_dps(self.step_dps)
        self.motor_r.set_dps(self.step_dps)
        sleep(self.cm_step_time)
        self.motor_l.set_dps(0)
        self.motor_r.set_dps(0)

    def windshieldwiper_detect_green(self):
        """
        Sweep center -> right -> left (180° total),
        checking detect_green continuously.
        Returns True if green found mid-sweep.
        """
        ms = self.motor_sensor
        ms.set_limits(dps=self.sweep_dps, power=self.sweep_power)

        # ensure we're centered
        ms.set_position(0)
        ms.set_dps(self.sweep_dps)
        while abs(ms.get_dps()) > 5 and not self.emergency_flag():
            sleep(0.005)

        # --- sweep to right ---
        ms.set_position_relative(+self.sweep_half_deg)
        ms.set_dps(self.sweep_dps)
        while abs(ms.get_dps()) > 5 and not self.emergency_flag():
            if self.detect_green():
                ms.set_dps(0)
                return True
            sleep(0.005)

        # --- sweep to left (full 180 from right end) ---
        ms.set_position_relative(-2 * self.sweep_half_deg)
        ms.set_dps(self.sweep_dps)
        while abs(ms.get_dps()) > 5 and not self.emergency_flag():
            if self.detect_green():
                ms.set_dps(0)
                return True
            sleep(0.005)

        # optional: return to center
        ms.set_position(0)
        ms.set_dps(self.sweep_dps)
        while abs(ms.get_dps()) > 5 and not self.emergency_flag():
            sleep(0.005)

        ms.set_dps(0)
        return False
