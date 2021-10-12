import logging
from threading import Thread
from time import sleep

from starlette.testclient import TestClient

from tdb.securitycamera import config
from tdb.securitycamera.gstreamer import GstreamerCamera
from test_app import FastApiBaseTester


class FastApiCameraTester(FastApiBaseTester):
    def test_Cameras(self):
        with TestClient(self.app) as client:
            def login():
                auth = client.post('/auth/login', data={
                    'username': 'unittest',
                    'password': 'unittest'
                })

                self.assertEqual(auth.status_code, 200)

                return auth.cookies

            def stop_camera_thread(cam: GstreamerCamera, seconds: int):
                logging.debug(f'Waiting for Camera Thread')
                sleep(seconds)
                logging.debug(f'Stopping Camera Thread')
                cam.running = False

            for name, camera in config.Config.cameras.items():
                cookies = login()

                response = client.get(f'/camera/dashboard', cookies=cookies)
                self.assertEqual(response.status_code, 200)

                response = client.get(f'/camera/{name}/jpeg', cookies=cookies)
                self.assertEqual(response.status_code, 200)

                thread = Thread(target=stop_camera_thread, args=(camera, 10))
                thread.start()

                response = client.get(f'/camera/{name}/video', cookies=cookies)
                self.assertEqual(response.status_code, 200)

                thread.join()

    def test_Login(self):
        client = TestClient(self.app)

        response = client.get('/auth/login')

        self.assertEqual(response.status_code, 200)

    def test_Status(self):
        client = TestClient(self.app)

        response = client.get('/status')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'status': 'Running'})
