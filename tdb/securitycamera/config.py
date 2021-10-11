import json
import os
from typing import Dict

from tdb.securitycamera.gstreamer import GstreamerCamera
from tdb.securitycamera.models import GstreamerSourceDetails, UserHashed


class Config:
    cameras: Dict[str, GstreamerCamera] = {}
    log_level: str = 'DEBUG'
    users: Dict[str, UserHashed] = {}
    secret_key: str

    @classmethod
    def load(cls, **kwargs):
        details = kwargs or {}
        filename = kwargs.get('config', 'config.json')

        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                result = json.load(json_file)

                if isinstance(result, dict):
                    result.update(details)
                    details = result

        cls.cameras = {
            name: GstreamerCamera(name, GstreamerSourceDetails(**camera_details))
            for name, camera_details in details['cameras'].items()
        }

        cls.users = {
            name: UserHashed(**data)
            for name, data in details['users'].items()
        }

        cls.secret_key = details['secret_key']

        cls.log_level = details.get('log_level', 'DEBUG')
