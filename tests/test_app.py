import unittest

from fastapi import FastAPI

from tdb.securitycamera import config, logger


class FastApiBaseTester(unittest.TestCase):
    app: FastAPI = None

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
                    'nvvidconv': 'video/x-raw(memory:NVMM)',
                    'overlay': True,
                    'recorder': {
                        'record_framerate': 1,
                        'playback_framerate': 30,
                        'properties': {
                            'location': 'test_%02d.mp4',
                            'max-files': 3,
                            'max-size-bytes': 5000000
                        }
                    }
                },
                'testCam02': {
                    'element': 'videotestsrc',
                    'properties': {
                        'pattern': 'ball'
                    },
                    'caps': 'video/x-raw',
                    'width': 1280,
                    'height': 720,
                    'framerate': 15,
                    'nvvidconv': 'video/x-raw(memory:NVMM)',
                    'autostart': False,
                    'recorder': {
                        'record_framerate': 30,
                        'playback_framerate': 30,
                        'properties': {
                            'location': 'testCam02_%02d.mp4',
                            'max-files': 3,
                            'max-size-bytes': 5000000
                        }
                    }
                }
            },
            'log_level': 'DEBUG',
            'secret_key': 'thisismeantasanexamplefordevelopmentpurposesonlypleaseupdatethis',
            'users': {
                'admin': {
                    'username': 'admin',
                    'hashed_password': '$2b$12$0808RGj0w02ApEj6Z/aTWOBxTVH0mIJmvJYpP6PRPOrRNa2lmrrRa'
                }
            }
        })

        logger.setup_logging(config.Config.log_level, False)

        # Lazy load app
        if not self.app:
            from tdb.securitycamera.app import app
            self.app = app
