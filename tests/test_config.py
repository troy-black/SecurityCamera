from securitycamera import config
from test_app import FastApiBaseTester


class ConfigTester(FastApiBaseTester):
    def test_Config(self):
        config.Config.load(**{
            'cameras': {
                'testCam': {
                    'driver': 'MockDriver',
                    'width': 640,
                    'height': 480,
                    'framerate': 1
                }
            },
            'log_level': 'CRITICAL'
        })

        self.assertIn('testCam', config.Config.cameras)
        self.assertEqual(config.Config.log_level, 'CRITICAL')
