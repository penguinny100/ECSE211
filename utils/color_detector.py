class ColorDetector:
    """
    Handles color analysis and identification for robotic vision tasks.

    This utility class offers methods to compare and classify colors based on
    RGB input data, useful for navigation and object recognition in autonomous systems.

    Author: Jack McDonald
    """

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
        # RALPH

    def _compute_color_distance(self, input_rgb, reference_rgb):
        """
        Computes the Euclidean distance metric between two RGB color vectors.
        """
        distance_metric = ((input_rgb[0] - reference_rgb[0]) ** 2 +
                           (input_rgb[1] - reference_rgb[1]) ** 2 +
                           (input_rgb[2] - reference_rgb[2]) ** 2) ** 0.5
        return distance_metric
    # RALPH

    def detect_color(self, rgb_values: list):
        """
        Determines the closest matching color from the reference database.

        This method evaluates the input RGB values against a set of predefined
        color references and returns the name of the most similar color.

        :param rgb_values: A list containing three RGB intensity values.
        :type rgb_values: list
        :return: The identified color name or 'unknown' if input is invalid.
        :rtype: str
        Author: Jack McDonald
        """
        if not rgb_values or len(rgb_values) != 3:
            return "unknown"

        # Compute distance metrics for all reference colors
        distance_metrics = {
            color_label: self._compute_color_distance(rgb_values, ref_rgb)
            for color_label, ref_rgb in self.REFERENCE_COLORS.items()
        }

        # Select the color with the minimal distance
        return min(distance_metrics.items(), key=lambda item: item[1])[0]
    # RALPH
