import unittest

from tdb.securitycamera import config, logger


class FastApiBaseTester(unittest.TestCase):
    def setUp(self):
        config.Config.load(**{
            'cameras': {
                'testCam01': {
                    'element': 'videotestsrc',
                    'properties': {
                        'pattern': 'ball'
                    },
                    'caps': 'video/x-raw',
                    'width': 1280,
                    'height': 720,
                    'framerate': 5,
                    'overlay': True,
                    'autostart': True,
                    'nvvidconv': 'video/x-raw(memory:NVMM)',
                    'recorder': {
                        'record_framerate': 1,
                        'playback_framerate': 30,
                        'properties': {
                            'location': 'testCam01_%02d.mp4',
                            'max-files': 3,
                            'max-size-bytes': 5000000
                        }
                    }
                },
                'testCam02': {
                    'element': 'videotestsrc',
                    'properties': {
                        'pattern': 'colors'
                    },
                    'caps': 'video/x-raw',
                    'width': 1280,
                    'height': 720,
                    'framerate': 5,
                    'overlay': True,
                    'nvvidconv': 'video/x-raw(memory:NVMM)',
                    'recorder': {
                        'record_framerate': 1,
                        'playback_framerate': 30,
                        'properties': {
                            'location': 'testCam02_%02d.mp4',
                            'max-files': 3,
                            'max-size-bytes': 5000000
                        }
                    }
                }
            },
            'log_level': 'DEBUG'
        })

        logger.setup_logging(config.Config.log_level, False)
