import logging
from threading import Thread
from time import sleep
from typing import Dict

from starlette.testclient import TestClient

from test_app import FastApiBaseTester


class FastApiCameraTester(FastApiBaseTester):
    def test_FullCameraCycle(self):
        with TestClient(self.app) as client:
            def get_stream(_url: str):
                response = client.get(_url)

                self.assertEqual(response.status_code, 200)

            threads: Dict[str, Thread] = {}
            for action in (True, 'video', False):
                for camera_id in ('testCam01', 'testCam02'):
                    url = f'/{camera_id}/stream/{action}'
                    thread = Thread(target=get_stream, args=(url,))
                    threads[url] = thread

            seconds = [30, 30, 30, 30, 1, 1]

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

    def test_Status(self):
        client = TestClient(self.app)

        response = client.get('/status')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'status': 'Running'})
