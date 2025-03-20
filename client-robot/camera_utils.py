import cv2
import logging
from typing import Optional

def find_available_camera(max_checks: int = 10) -> Optional[int]:
    """
    Find the first available camera index.
    
    Args:
        max_checks (int): Maximum camera indices to check.
    
    Returns:
        Optional[int]: The index of the available camera, or None if not found.
    """
    for i in range(max_checks):
        cap = cv2.VideoCapture(i, cv2.CAP_V4L)
        if cap.isOpened():
            logging.info(f"Camera found at index {i}")
            cap.release()
            return i
        cap.release()
    return None
