import json
import os
from typing import Dict

from securitycamera.camera import CameraDriver, CameraDriverFactory


class Config:
    cameras: Dict[str, CameraDriver] = {}
    log_level: str = 'DEBUG'

    @classmethod
    def load(cls, **kwargs):
        details = kwargs or {}
        filename = kwargs.get('config', 'config.json')

        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                result = json.load(json_file)

                if isinstance(result, dict):
                    details.update(result)

        cls.cameras = {
            identifier: CameraDriverFactory.make(camera_details.pop('driver'), identifier, **camera_details)
            for identifier, camera_details in details['cameras'].items()
        }

        cls.log_level = details.get('log_level', 'DEBUG')
