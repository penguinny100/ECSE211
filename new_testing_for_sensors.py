from utils.brick import TouchSensor, EV3ColorSensor, EV3UltrasonicSensor
from utils.color_detector import ColorDetector

"""
Sensor testing module for robotic hardware validation.

This module provides isolated testing capabilities for sensor components,
enabling verification of touch, color, and ultrasonic sensor functionality
independently of the main robotic control system. Initialize the SensorController
instance and output readings to validate hardware integration and data accuracy
prior to full system deployment.
"""


class SensorController:

    def __init__(self):
        self.touch_sensor = TouchSensor("2")
        self.colour_sensor = EV3ColorSensor("4")
        self.us_sensor = EV3UltrasonicSensor("3")

    def get_colour_name(self):
        rgb = self.colour_sensor.get_rgb()
        processor = ColorDetector()
        return processor.detect_color(rgb)

    def __get_colour_raw(self):
        return self.colour_sensor.get_rgb()

    def get_touch_sensor_state(self):
        return self.touch_sensor.is_pressed()

    def get_us_sensor_distance(self):
        return self.us_sensor.get_cm()
