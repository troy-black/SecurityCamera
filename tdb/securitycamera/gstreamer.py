import logging
import threading
from abc import ABC, abstractmethod
from threading import Thread
from time import time
from typing import Optional, Callable

import gi  # noqa:F401,F402

from tdb.securitycamera.models import GstreamerSourceDetails

gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import GObject, Gst, GstApp, GLib  # noqa:F401,F402


class Gstreamer(ABC):
    name: str
    debug: bool
    running: bool

    source: GstreamerSourceDetails

    def __init__(self, name: str, source_details: GstreamerSourceDetails, *, debug: bool = False):  # , **kwargs):
        self.name = name
        self.running = False

        self.pipeline: Gst.Pipeline = None

        self.thread: Optional[Thread] = None

        self.source = source_details

        self._setup()

        if debug:
            Gst.debug_set_active(True)
            Gst.debug_set_colored(True)
            Gst.debug_set_default_threshold(Gst.DebugLevel.DEBUG)

        # GObject.threads_init()
        Gst.init(None)

        # threading vars
        self._threading_lock = threading.Lock()
        self._threading_event = threading.Event()
        self._threading_event.clear()

    def background_task(self):
        lock = self._threading_lock.acquire(False)

        if lock:
            self.running = True

            self.create_pipeline()

            self.pipeline.set_state(Gst.State.PLAYING)

            logging.debug(f'[{self.name}] Entering Gstreamer loop')

            bus = self.pipeline.get_bus()

            # Thread blocking
            message = bus.timed_pop_filtered(
                Gst.CLOCK_TIME_NONE,
                Gst.MessageType.ERROR | Gst.MessageType.EOS
            )

            self.handle_message(message)

            logging.debug(f'[{self.name}] Gstreamer Pipeline has ended')

            self.pipeline.set_state(Gst.State.NULL)

            self._threading_lock.release()

    def build_nvvidconv(self, source: Gst.Element, caps_string: str) -> Gst.Element:
        nvvidconv: Gst.Element = Gst.ElementFactory.make('nvvidconv')
        self.pipeline.add(nvvidconv)
        source.link(nvvidconv)

        capsfilter: Gst.Element = Gst.ElementFactory.make('capsfilter')
        capsfilter.set_property('caps', Gst.Caps.from_string(caps_string))
        self.pipeline.add(capsfilter)
        nvvidconv.link(capsfilter)

        return capsfilter

    def create_pipeline(self):
        self.pipeline = Gst.Pipeline.new('pipeline')
        self._build_pipeline()

    def handle_message(self, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()

            logging.debug(f'[{self.name}] ERROR: {msg.src.get_name()}: {err.message}')

            if dbg:
                logging.debug(f'[{self.name}] DMG: {dbg}')

        elif t == Gst.MessageType.EOS:
            logging.debug(f'[{self.name}] EOS: End-Of-Stream reached')

        else:
            logging.debug(f'[{self.name}] Unexpected msg.type: {t}')

    @abstractmethod
    def _build_pipeline(self):
        pass

    @abstractmethod
    def _setup(self):
        pass


class GstreamerRecorder(Gstreamer):
    _src: Gst.Element
    _pts: int
    _dts: int
    _duration: float

    def _setup(self):
        self._pts = 0
        self._dts = GLib.MAXUINT64
        self._duration = 10 ** 9 / (self.source.recorder.playback_framerate / 1)

    def _build_pipeline(self):
        last_element = self.build_app_source()

        self.build_file_sink(source=last_element)

    def build_app_source(self) -> Gst.Element:
        src: Gst.Element = Gst.ElementFactory.make('appsrc', 'src')
        src.set_property('format', Gst.Format.TIME)
        src.set_property('block', True)
        src.set_property(
            'caps',
            Gst.Caps.from_string(
                f'image/jpeg,'
                f'width={self.source.width},'
                f'height={self.source.height},'
                f'framerate={self.source.recorder.playback_framerate}/1'
            )
        )
        self.pipeline.add(src)

        self._src = src

        return src

    def build_file_sink(self, source: Gst.Element) -> Gst.Element:
        nvjpegdec: Gst.Element = Gst.ElementFactory.make('nvjpegdec')
        self.pipeline.add(nvjpegdec)
        source.link(nvjpegdec)

        capsfilter: Gst.Element = Gst.ElementFactory.make('capsfilter')
        capsfilter.set_property('caps', Gst.Caps.from_string('video/x-raw'))
        self.pipeline.add(capsfilter)
        nvjpegdec.link(capsfilter)

        nvvidconv = self.build_nvvidconv(capsfilter, 'video/x-raw(memory:NVMM),format=NV12')

        nvv4l2h264enc: Gst.Element = Gst.ElementFactory.make('nvv4l2h264enc')
        self.pipeline.add(nvv4l2h264enc)
        nvvidconv.link(nvv4l2h264enc)

        h264parse: Gst.Element = Gst.ElementFactory.make('h264parse')
        self.pipeline.add(h264parse)
        nvv4l2h264enc.link(h264parse)

        splitmuxsink: Gst.Element = Gst.ElementFactory.make('splitmuxsink')
        for prop, val in self.source.recorder.properties.items():
            splitmuxsink.set_property(prop, val)
        self.pipeline.add(splitmuxsink)
        h264parse.link(splitmuxsink)

        return splitmuxsink

    def push(self, _bytes: bytes):
        logging.debug(f'[{self.name}] Pushing Bytes')

        self._pts += self._duration
        offset = int(self._pts / self._duration)

        gst_buffer = Gst.Buffer.new_wrapped(_bytes)

        gst_buffer.pts = self._pts
        gst_buffer.dts = self._dts
        gst_buffer.offset = offset
        gst_buffer.duration = self._duration

        logging.debug(f'[{self.name}] Pushing Buffer')

        self._src.emit('push-buffer', gst_buffer)


class GstreamerCamera(Gstreamer):
    recorder: Optional[GstreamerRecorder]

    _calculated_fps: float
    _fps_timestamp: float
    last_image_bytes: Optional[bytes]

    _record_fps: float
    _record_timestamp: float

    def _setup(self):
        self._calculated_fps = 0.0
        self._fps_timestamp = time()
        self.last_image_bytes = None
        self.recorder = None

        if self.source.recorder:
            self._record_fps = 1 / self.source.recorder.record_framerate
            self._record_timestamp = time()

            self.recorder = GstreamerRecorder(f'{self.name}_recorder', self.source)

    def _build_pipeline(self):
        last_element = self.build_camera_source()

        if self.source.overlay:
            last_element = self.build_clockoverlay(source=last_element)

        self.build_jpeg_sink(source=last_element)

    def build_camera_source(self) -> Gst.Element:
        src: Gst.Element = Gst.ElementFactory.make(self.source.element, 'src')
        for prop, val in self.source.properties.items():
            src.set_property(prop, val)
        self.pipeline.add(src)

        src_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
        src_caps.set_property('caps', Gst.Caps.from_string(
            f'{self.source.caps},'
            f'width={self.source.width},'
            f'height={self.source.height},'
            f'framerate={self.source.framerate}/1'
        ))
        self.pipeline.add(src_caps)
        src.link(src_caps)

        if self.source.nvvidconv:
            return self.build_nvvidconv(src_caps, self.source.nvvidconv)

        return src_caps

    def build_clockoverlay(self, source: Gst.Element) -> Gst.Element:
        nvvidconv = self.build_nvvidconv(source, 'video/x-raw')

        clockoverlay: Gst.Element = Gst.ElementFactory.make('clockoverlay')
        clockoverlay.set_property('time-format', '"%D %H:%M:%S"')
        self.pipeline.add(clockoverlay)
        nvvidconv.link(clockoverlay)

        return self.build_nvvidconv(clockoverlay, 'video/x-raw(memory:NVMM)')

    def build_app_sink(self, source: Gst.Element, sink: Callable) -> Gst.Element:
        appsink: Gst.Element = Gst.ElementFactory.make('appsink')
        appsink.set_property('emit-signals', True)
        appsink.set_property('drop', True)
        appsink.connect('new-sample', sink, None)
        self.pipeline.add(appsink)
        source.link(appsink)

        return appsink

    def build_jpeg_sink(self, source: Gst.Element) -> Gst.Element:
        jpegenc: Gst.Element = Gst.ElementFactory.make('nvjpegenc')
        self.pipeline.add(jpegenc)
        source.link(jpegenc)

        return self.build_app_sink(jpegenc, self.jpeg_sink)

    # def build_queue(self, source: Gst.Element) -> Gst.Element:
    #     queue: Gst.Element = Gst.ElementFactory.make('queue')
    #     queue.set_property('max-size-buffers', 1)
    #     queue.set_property('leaky', 'downstream')
    #     self.pipeline.add(queue)
    #     source.link(queue)
    #
    #     return queue
    #
    # def build_raw_sink(self, source: Gst.Element) -> Gst.Element:
    #     queue = self.build_queue(source=source)
    #
    #     return self.build_app_sink(queue, self.raw_sink)
    #
    # def build_tee(self, source: Gst.Element) -> Gst.Element:
    #     tee: Gst.Element = Gst.ElementFactory.make('tee')
    #     self.pipeline.add(tee)
    #     source.link(tee)
    #
    #     return tee

    def jpeg_sink(self, sink, data) -> Gst.FlowReturn:
        # set threading event
        self._threading_event.set()

        logging.debug(f'[{self.name}] Pulling jpeg')

        sample: Gst.Sample = sink.emit('pull-sample')
        buffer: Gst.Buffer = sample.get_buffer()
        self.last_image_bytes = buffer.extract_dup(0, buffer.get_size())

        # pass frames @ record_framerate to recorder
        if self._record_timestamp + self._record_fps <= time():
            self._record_timestamp = time()
            self.recorder.push(self.last_image_bytes)

        # clear threading event
        self._threading_event.clear()

        self.calculate_fps()

        if not self.running:
            logging.debug(f'[{self.name}] Closing Pipeline')

            if self.recorder:
                self.recorder.running = False
                self.recorder.pipeline.send_event(Gst.Event.new_eos())

            self.pipeline.send_event(Gst.Event.new_eos())

        return Gst.FlowReturn.OK

    # def raw_sink(self, sink, data) -> Gst.FlowReturn:
    #     logging.debug(f'[{self._id}] Pulling raw')
    #
    #     sample: Gst.Sample = sink.emit('pull-sample')
    #     buffer: Gst.Buffer = sample.get_buffer()
    #
    #     self._recorder.push_buffer(buffer)
    #     # raw = buffer.extract_dup(0, buffer.get_size())
    #     # self._recorder.push(raw)
    #
    #     if not self.running:
    #         logging.debug(f'[{self._id}] Closing Pipeline')
    #         self.pipeline.set_state(Gst.State.NULL)
    #
    #     return Gst.FlowReturn.OK

    def calculate_fps(self):
        # calculate fps based on current time - last timestamp
        fps = 1.0 / (time() - self._fps_timestamp)

        self._fps_timestamp = time()
        self._calculated_fps = fps

        logging.debug(f'[{self.name}] Average FPS: {fps}')

        return fps

    def stream_images(self):
        while self.running:
            if self.last_image_bytes:
                # format as html mjpeg stream
                yield b'--frame\r\nContent-Type:image/jpeg\r\n\r\n' + self.last_image_bytes + b'\r\n'

            # block this thread until threading event is cleared
            self._threading_event.wait(1)

        logging.debug(f'[{self.name}] Exiting Stream')
