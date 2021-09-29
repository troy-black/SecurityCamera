import logging
import threading
from abc import ABC, abstractmethod
from time import time
from typing import Optional

import gi  # noqa:F401,F402

gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import GObject, Gst, GstApp, GLib  # noqa:F401,F402


class Gstreamer(ABC):
    debug: bool
    running: bool

    width: int
    height: int

    _id: str

    def __init__(self, identifier: str, *, debug: bool = False, **kwargs):
        self._id = identifier
        self.running = False

        for k, v in kwargs.items():
            setattr(self, k, v)

        if debug:
            Gst.debug_set_active(True)
            Gst.debug_set_colored(True)
            Gst.debug_set_default_threshold(Gst.DebugLevel.DEBUG)

        GObject.threads_init()
        Gst.init(None)

        # threading vars
        self._threading_lock = threading.Lock()
        self._threading_event = threading.Event()
        self._threading_event.clear()

        # Create Pipeline
        self.pipeline = Gst.Pipeline.new('pipeline')

        self._build_pipeline()

        # noinspection PyUnresolvedReferences
        self.loop = GObject.MainLoop()

        # Setup Bus Message function
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.pipeline_bus_messages, self.loop)

    def background_task(self):
        lock = self._threading_lock.acquire(False)

        if lock:
            self.running = True

            self.pipeline.set_state(Gst.State.PLAYING)

            logging.debug(f'[{self._id}] Entering Gstreamer loop')

            # start gstreamer pipeline thread (blocking)
            self.loop.run()

            logging.debug(f'[{self._id}] Gstreamer Pipeline has ended')

            self.pipeline.set_state(Gst.State.NULL)

            self._threading_lock.release()

    @abstractmethod
    def _build_pipeline(self):
        pass

    def pipeline_bus_messages(self, bus, message, loop) -> bool:
        t = message.type
        logging.debug(f'[{self._id}] {t}')

        if t in (Gst.MessageType.ERROR, Gst.MessageType.EOS):
            self.running = False
            logging.debug(f'[{self._id}] Loop Quit')
            loop.quit()

        return True


class GstreamerRecorder(Gstreamer):
    playback_framerate: int
    record_framerate: int

    _src: Gst.Element
    _pts: int
    _dts: int
    _duration: int

    def _build_pipeline(self):
        self._pts = 0
        self._dts = GLib.MAXUINT64
        self._duration = 10 ** 9 / (self.playback_framerate / 1)

        last_element = self.build_jpeg_app_source()

        self.build_file_sink(source=last_element)

    def build_jpeg_app_source(self) -> Gst.Element:
        src: Gst.Element = Gst.ElementFactory.make('appsrc', 'src')
        src.set_property('format', Gst.Format.TIME)
        src.set_property('block', True)
        src.set_property(
            'caps',
            Gst.Caps.from_string(
                # f'video/x-raw,format=RGB,width={self.width},height={self.height},framerate={self.playback_framerate}/1'
                f'image/jpeg,width={self.width},height={self.height},framerate={self.playback_framerate}/1'
            )
        )  # image/jpeg
        self.pipeline.add(src)

        self._src = src

        return src

    def build_file_sink(self, source: Gst.Element) -> Gst.Element:
        # Works
        multifilesink: Gst.Element = Gst.ElementFactory.make('multifilesink')
        multifilesink.set_property('location', f'/home/camerasuite/{self._id}_%03d.jpeg')
        self.pipeline.add(multifilesink)
        source.link(multifilesink)

        return multifilesink

        # No Error; but no files
        # nvvidconv: Gst.Element = Gst.ElementFactory.make('nvvidconv')
        # self.pipeline.add(nvvidconv)
        # source.link(nvvidconv)
        #
        # nvv4l2h264enc: Gst.Element = Gst.ElementFactory.make('nvv4l2h264enc')
        # self.pipeline.add(nvv4l2h264enc)
        # nvvidconv.link(nvv4l2h264enc)
        #
        # h264parse: Gst.Element = Gst.ElementFactory.make('h264parse')
        # self.pipeline.add(h264parse)
        # nvv4l2h264enc.link(h264parse)
        #
        # splitmuxsink: Gst.Element = Gst.ElementFactory.make('splitmuxsink')
        # splitmuxsink.set_property('location', f'/home/camerasuite/{self._id}_test_%02d.mp4')
        # splitmuxsink.set_property('max-size-bytes', 10000000)
        # splitmuxsink.set_property('max-files', 10)
        # self.pipeline.add(splitmuxsink)
        # h264parse.link(splitmuxsink)
        #
        # return splitmuxsink

    def push(self, jpeg: bytes):
        logging.debug(f'[{self._id}] Pushing Bytes')

        self._pts += self._duration
        offset = int(self._pts / self._duration)

        gst_buffer = Gst.Buffer.new_wrapped(jpeg)

        gst_buffer.pts = self._pts
        gst_buffer.dts = self._dts
        gst_buffer.offset = offset
        gst_buffer.duration = self._duration

        logging.debug(f'[{self._id}] gst_buffer {gst_buffer}')

        self._src.emit("push-buffer", gst_buffer)


class GstreamerCamera(Gstreamer):
    sensor_id: int
    overlay: int
    save: dict

    framerate: int

    _calculated_fps: float
    _fps_timestamp: float
    _last_image_bytes: Optional[bytes]
    # _last_image_timestamp: float

    _recorder: GstreamerRecorder

    def _build_pipeline(self):
        self._last_image_bytes = None
        self._fps_timestamp = time()
        self._calculated_fps = 0.0

        last_element = self.build_camera_source()

        if self.overlay:
            last_element = self.build_clockoverlay(source=last_element)

        self.build_jpeg_sink(source=last_element)

        if self.save:
            self._recorder = GstreamerRecorder(f'{self._id}_record', width=self.width, height=self.height, **self.save)
            self._recorder_thread = threading.Thread(target=self._recorder.background_task)
            self._recorder_thread.start()

    def build_camera_source(self) -> Gst.Element:
        src: Gst.Element = Gst.ElementFactory.make('nvarguscamerasrc', 'src')
        src.set_property('sensor-id', self.sensor_id)
        self.pipeline.add(src)

        src_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
        src_caps.set_property(
            'caps',
            Gst.Caps.from_string(
                f'video/x-raw(memory:NVMM),width={self.width},height={self.height},framerate={self.framerate}/1'
            )
        )
        self.pipeline.add(src_caps)
        src.link(src_caps)

        return src_caps

    def build_clockoverlay(self, source: Gst.Element) -> Gst.Element:
        raw: Gst.Element = Gst.ElementFactory.make('nvvidconv')
        self.pipeline.add(raw)
        source.link(raw)

        raw_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
        raw_caps.set_property('caps', Gst.Caps.from_string('video/x-raw'))
        self.pipeline.add(raw_caps)
        raw.link(raw_caps)

        clockoverlay: Gst.Element = Gst.ElementFactory.make('clockoverlay')
        clockoverlay.set_property('time-format', '"%D %H:%M:%S"')
        self.pipeline.add(clockoverlay)
        raw_caps.link(clockoverlay)

        nvmm: Gst.Element = Gst.ElementFactory.make('nvvidconv')
        self.pipeline.add(nvmm)
        clockoverlay.link(nvmm)

        nvmm_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
        nvmm_caps.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM)'))
        self.pipeline.add(nvmm_caps)
        nvmm.link(nvmm_caps)

        return nvmm_caps

    def build_jpeg_sink(self, source: Gst.Element) -> Gst.Element:
        jpegenc: Gst.Element = Gst.ElementFactory.make('nvjpegenc')
        self.pipeline.add(jpegenc)
        source.link(jpegenc)

        appsink: Gst.Element = Gst.ElementFactory.make('appsink')
        appsink.set_property('emit-signals', True)
        appsink.set_property('drop', True)
        appsink.connect('new-sample', self.jpeg_sink, None)
        self.pipeline.add(appsink)
        jpegenc.link(appsink)

        return appsink

    def jpeg_sink(self, sink, data) -> Gst.FlowReturn:
        # set threading event
        self._threading_event.set()

        logging.debug(f'[{self._id}] Generating image')

        sample: Gst.Sample = sink.emit('pull-sample')
        buffer: Gst.Buffer = sample.get_buffer()
        self._last_image_bytes = buffer.extract_dup(0, buffer.get_size())

        if self._recorder:
            self._recorder.push(self._last_image_bytes)

        # clear threading event
        self._threading_event.clear()

        self.calculate_fps()

        if not self.running:
            logging.debug(f'[{self._id}] Closing Pipeline')
            self.pipeline.set_state(Gst.State.NULL)

        return Gst.FlowReturn.OK

    def calculate_fps(self):
        # calculate fps based on current time - last timestamp
        fps = 1.0 / (time() - self._fps_timestamp)

        self._fps_timestamp = time()
        self._calculated_fps = fps

        logging.debug(f'[{self._id}] Average FPS: {fps}')

        return fps

    def stream_images(self):
        while self.running:
            if self._last_image_bytes:
                # format as html mjpeg stream
                yield b'--frame\r\nContent-Type:image/jpeg\r\n\r\n' + self._last_image_bytes + b'\r\n'

            # block this thread until threading event is cleared
            self._threading_event.wait(1)
