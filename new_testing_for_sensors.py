from utils.brick import TouchSensor, EV3ColorSensor, EV3UltrasonicSensor
from utils.colour_processing import ColourProcessing

"""
This file currently serves as a testing utility for the sensors. It should allow for testing of individual sensors 
or color processing without running the full robot program. We should first create a simple script that initializes the 
SensorController and prints out the sensor readings to confirm they’re functioning properly before integrating it into the main robot logic.
"""


class SensorController:

    def __init__(self):
        self.touch_sensor = TouchSensor("2")
        self.colour_sensor = EV3ColorSensor("4")
        self.us_sensor = EV3UltrasonicSensor("3")

    def get_colour_name(self):

        rgb = self.colour_sensor.get_rgb()
        processor = ColourProcessing()
        return processor.identify_colour(rgb)

    def __get_colour_raw(self):

        # returns the raw color data in its original form without any processing or conversion.

        return self.colour_sensor.get_rgb()

    def get_touch_sensor_state(self):

        # Retrieves the current state of the touch sensor.

        return self.touch_sensor.is_pressed()

    def get_us_sensor_distance(self):

        # Retrieves the ultrasonic sensor distance measurement to determine the proximity of an object.

        return self.us_sensor.get_cm()
