# import logging
# import threading
# from abc import ABC, abstractmethod
# from time import time
# from typing import Optional, Dict, Type
#
# from securitycamera.utilities import import_submodules
#
#
# class CameraDriver(ABC):
#     running: bool
#     _last_image_bytes: Optional[bytes]
#
#     def __init__(self, identifier: str, **kwargs):
#         self._id = identifier
#         self._last_image_bytes = None
#         self._fps_timestamp = time()
#         self._calculated_fps = 0.0
#         self.running = False
#
#         # threading vars
#         self._threading_lock = threading.Lock()
#         self._threading_event = threading.Event()
#         self._threading_event.clear()
#
#     def background_task(self):
#         lock = self._threading_lock.acquire(False)
#
#         if lock:
#             self.running = True
#
#             self._background_loop()
#
#             self._threading_lock.release()
#
#     @abstractmethod
#     def _background_loop(self):
#         pass
#
#     def _set_threading_event(self):
#         # set threading event
#         self._threading_event.set()
#
#         logging.debug(f'[{self._id}] Generating image')
#
#     def _clear_threading_event(self):
#         # clear threading event
#         self._threading_event.clear()
#
#         self.calculate_fps()
#
#     def calculate_fps(self):
#         # calculate fps based on current time - last timestamp
#         fps = 1.0 / (time() - self._fps_timestamp)
#
#         self._fps_timestamp = time()
#         self._calculated_fps = fps
#
#         logging.debug(f'[{self._id}] Average FPS: {fps}')
#
#         return fps
#
#     def stream_images(self):
#         while self.running:
#             if self._last_image_bytes:
#                 # format as html mjpeg stream
#                 yield b'--frame\r\nContent-Type:image/jpeg\r\n\r\n' + self._last_image_bytes + b'\r\n'
#
#             # block this thread until threading event is cleared
#             self._threading_event.wait(1)
#
#
# class CameraDriverFactory:
#     _classes: Dict[str, Type[CameraDriver]] = {}
#
#     @classmethod
#     def get_class(cls, name: str) -> Type[CameraDriver]:
#         # Lazy load subclasses
#         if not cls._classes:
#             import_submodules('src.securitycamera.camera')
#             cls._classes = {
#                 subclass.__name__: subclass
#                 for subclass in CameraDriver.__subclasses__()
#             }
#
#         return cls._classes[name]
#
#     @classmethod
#     def make(cls, driver_name: str, identifier: str, **kwargs) -> CameraDriver:
#         return cls.get_class(driver_name)(identifier, **kwargs)
