from abc import ABC, abstractmethod

class DetectionManager(ABC):
    @abstractmethod
    def initialize(self):
        """Initialize the detector."""
        pass

    @abstractmethod
    def process_frame(self, frame):
        """
        Process a single frame to detect objects.
        Should return the processed frame (e.g., with drawings) and detection results.
        """
        pass

    @abstractmethod
    def get_detection_data(self, results):
        """
        Extract relevant data from the detection results.
        This will be specific to each detector (e.g., hand landmarks, ball coordinates).
        """
        pass