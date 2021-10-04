import logging
from threading import Thread
from time import sleep
from typing import Dict

from test_app import FastApiBaseTester


class FastApiApiTester(FastApiBaseTester):
    def test_Status(self):
        response = self.client.get('/status')

        self.assertEqual(response.status_code, 200)
        # self.assertDictEqual(response.json(), {'status': 'Running'})


class FastApiCameraTester(FastApiBaseTester):
    def test_FullCameraCycle(self):
        # run requests in separate thread
        threads: Dict[str, Thread] = {
            f'/testCam/stream/True': Thread(target=self.get_stream_action, args=('testCam', True)),
            f'/testCam/stream/video': Thread(target=self.get_stream_video, args=('testCam',)),
            f'/testCam/stream/False': Thread(target=self.get_stream_action, args=('testCam', False)),
        }

        seconds = [60, 30, 1]

        # start each thread and wait an increasing number of seconds
        for url, thread in threads.items():
            logging.debug(f'Starting Thread URL:{url}')
            thread.start()
            sleep(seconds.pop(0))

        # join each thread and wait until everything completes
        for url in reversed(list(threads.keys())):
            logging.debug(f'Joining Thread URL:{url}')
            threads[url].join()

        logging.debug(f'Threading Complete')

    def get_stream_video(self, camera_id: str):
        response = self.client.get(f'/{camera_id}/stream/video')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

    def get_stream_action(self, camera_id: str, action: bool):
        response = self.client.get(f'/{camera_id}/stream/{action}')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'stream': action})
