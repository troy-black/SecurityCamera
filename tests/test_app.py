import unittest

from fastapi.testclient import TestClient

from securitycamera import config, logger
from securitycamera.app import app


class FastApiBaseTester(unittest.TestCase):
    def setUp(self):
        config.Config.load(**{
            'cameras': {
                'cam0': {
                    'driver': 'MockDriver',
                    'width': 1280,
                    'height': 720,
                    'framerate': 5
                },
                'cam1': {
                    'driver': 'MockDriver',
                    'width': 1280,
                    'height': 720,
                    'framerate': 5
                }
            },
            'log_level': 'DEBUG'
        })

        logger.setup_logging(config.Config.log_level, False)

        self.client = TestClient(app)
