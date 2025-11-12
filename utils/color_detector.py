class ColorDetector:

    def __init__(self):
        # Reference color database with calibrated RGB values for common colors
        self.REFERENCE_COLORS = {
            "black": [8.53, 9.47, 3.47],
            "green": [125.60, 177.80, 14.93],
            "orange": [214.40, 75.67, 13.60],
            "purple": [90.87, 48.13, 42.20],
            "red": [161.33, 17.47, 7.93],
            "white": [250.00, 242.40, 108.80],
            "yellow": [277.53, 237.00, 22.20],
        }

    def _compute_color_distance(self, input_rgb, reference_rgb):

        distance_metric = ((input_rgb[0] - reference_rgb[0]) ** 2 +
                           (input_rgb[1] - reference_rgb[1]) ** 2 +
                           (input_rgb[2] - reference_rgb[2]) ** 2) ** 0.5
        return distance_metric

    def detect_color(self, rgb_values: list):

        if not rgb_values or len(rgb_values) != 3:
            return "unknown"

        # Compute distance to all reference colors
        distance_metrics = {
            color_label: self._compute_color_distance(rgb_values, ref_rgb)
            for color_label, ref_rgb in self.REFERENCE_COLORS.items()
        }

        # finds min
        return min(distance_metrics.items(), key=lambda item: item[1])[0]
