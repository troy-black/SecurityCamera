import json
import logging
import os
from typing import Optional, Dict

from securitycamera.camera import CameraDriver, CameraDriverFactory


class Config:
    cameras: Dict[str, CameraDriver]

    def __init__(self, **kwargs):
        details = self.load(filename=kwargs.get('config'))
        details.update(kwargs)

        self.cameras = {}
        for identifier, camera_details in details['cameras'].items():
            driver_name = camera_details.pop('driver')
            camera = CameraDriverFactory.make(driver_name, identifier, **camera_details)
            self.cameras[identifier] = camera

        self.log_level = logging.getLevelName(details.get('log_level', 'DEBUG'))

    @staticmethod
    def load(*, filename: str = None) -> dict:
        filename = filename or 'config.json'
        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                results = json.load(json_file)

            return results


config: Optional[Config] = None
