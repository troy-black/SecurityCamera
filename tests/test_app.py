import unittest

from fastapi.testclient import TestClient

from tdb.securitycamera import config, logger
from tdb.securitycamera.app import app


class FastApiBaseTester(unittest.TestCase):
    def setUp(self):
        config.Config.load(**{
            'cameras': {
                'testCam': {
                    'element': 'videotestsrc',
                    'properties': {
                        'pattern': 'ball'
                    },
                    'caps': 'video/x-raw',
                    'width': 1280,
                    'height': 720,
                    'framerate': 5,
                    'nvvidconv': 'video/x-raw(memory:NVMM)',
                    'recorder': {
                        'record_framerate': 1,
                        'playback_framerate': 30,
                        'properties': {
                            'location': 'test_%02d.mp4',
                            'max-files': 3,
                            'max-size-bytes': 5000000
                        },
                        'overlay': True
                    }
                }
            },
            'log_level': 'DEBUG'
        })

        logger.setup_logging(config.Config.log_level, False)

        self.client = TestClient(app)
