import logging
from threading import Thread
from time import sleep
from typing import Dict

from test_app import FastApiBaseTester


class FastApiApiTester(FastApiBaseTester):
    def test_Status(self):
        response = self.client.get('/api/status')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'status': 'Running'})


class FastApiCameraTester(FastApiBaseTester):
    def test_FullCameraCycle(self):
        # run requests in separate thread
        threads: Dict[str, Thread] = {
            f'/camera/cam0/stream/True': Thread(target=self.get_stream_action, args=('cam0', True)),
            f'/camera/cam0/stream/video': Thread(target=self.get_stream_video, args=('cam0',)),
            f'/camera/cam0/stream/False': Thread(target=self.get_stream_action, args=('cam0', False)),
        }

        seconds = 5

        # start each thread and wait an increasing number of seconds
        for url, thread in threads.items():
            logging.debug(f'Starting Thread URL:{url}')
            thread.start()
            sleep(seconds)
            seconds = seconds * 2

        # join each thread and wait until everything completes
        for url in reversed(threads.keys()):
            logging.debug(f'Joining Thread URL:{url}')
            threads[url].join()

    def get_stream_video(self, camera_id: str):
        response = self.client.get(f'/camera/{camera_id}/stream/video')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

    def get_stream_action(self, camera_id: str, action: bool):
        response = self.client.get(f'/camera/{camera_id}/stream/{action}')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'stream': action})
