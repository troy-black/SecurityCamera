from tdb.securitycamera import config
from test_app import FastApiBaseTester


class ConfigTester(FastApiBaseTester):
    def test_Config(self):
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
                    'overlay': True
                }
            },
            'log_level': 'CRITICAL',
            'secret_key': 'unittest',
            'users': {
                'admin': {
                    'username': 'fakeUsername',
                    'hashed_password': 'fakePassword'
                }
            }
        })

        self.assertIn('testCam01', config.Config.cameras)
        self.assertEqual(config.Config.log_level, 'CRITICAL')
