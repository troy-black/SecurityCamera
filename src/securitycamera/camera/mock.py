import io
import time

import numpy
from PIL import Image

from securitycamera.camera import CameraDriver


class MockDriver(CameraDriver):
    def __init__(self, identifier: str, *, width: int = 1920, height: int = 1080, fps: int = 5):
        super().__init__(identifier)
        self.width = width
        self.height = height
        self.mock_fps = fps

    def _background_loop(self):
        while self.running:
            t = time.time()

            self._set_threading_event()

            # Random color array
            array = numpy.random.rand(self.height, self.width, 3) * 255
            image = Image.fromarray(array.astype('uint8')).convert('RGB')
            _bytes = io.BytesIO()
            image.save(_bytes, format='JPEG')

            self._last_image_bytes = _bytes.getvalue()

            self._clear_threading_event()

            s = (1 / self.mock_fps) - (time.time() - t)

            time.sleep(s if s > 0 else 0)
