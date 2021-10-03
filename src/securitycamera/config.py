import json
import os
from typing import Dict

from securitycamera.gstreamer import GstreamerCamera


class Config:
    cameras: Dict[str, GstreamerCamera] = {}
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
            identifier: GstreamerCamera(identifier, **camera_details)
            for identifier, camera_details in details['cameras'].items()
        }

        cls.log_level = details.get('log_level', 'DEBUG')
