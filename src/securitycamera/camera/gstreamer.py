# import logging
#
# import gi  # noqa:F401,F402
#
# from securitycamera.camera import CameraDriver
#
# gi.require_version('GObject', '2.0')
# gi.require_version('Gst', '1.0')
# gi.require_version('GstApp', '1.0')
# from gi.repository import GObject, Gst, GstApp  # noqa:F401,F402
#
#
# class GstreamerDriver(CameraDriver):
#     def __init__(self, identifier: str, sensor_id: int, width: int, height: int, framerate: int,
#                  overlay: bool, file_sink: bool = False, debug: bool = False):
#
#         super().__init__(identifier)
#
#         if debug:
#             Gst.debug_set_active(True)
#             Gst.debug_set_colored(True)
#             Gst.debug_set_default_threshold(Gst.DebugLevel.DEBUG)
#
#         GObject.threads_init()
#         Gst.init(None)
#
#         # Create Pipeline
#         self.pipeline = Gst.Pipeline.new('pipeline')
#
#         last_element = self.build_camera_source(sensor_id, width, height, framerate)
#
#         if overlay:
#             last_element = self.build_clockoverlay(source=last_element)
#
#         # if file_sink:
#         #     last_element = self.build_tee(source=last_element)
#
#         self.build_jpeg_sink(source=last_element)
#
#         # if file_sink:
#         #     self.build_file_sink(source=last_element)
#
#         # noinspection PyUnresolvedReferences
#         self.loop = GObject.MainLoop()
#
#         # Setup Bus Message function
#         bus = self.pipeline.get_bus()
#         bus.add_signal_watch()
#         bus.connect('message', self.pipeline_bus_messages, self.loop)
#
#     def _background_loop(self):
#         self.pipeline.set_state(Gst.State.PLAYING)
#
#         logging.debug(f'[{self._id}] Entering Gstreamer loop')
#
#         # start gstreamer pipeline thread (blocking)
#         self.loop.run()
#
#         logging.debug(f'[{self._id}] Gstreamer Pipeline has ended')
#
#         self.pipeline.set_state(Gst.State.NULL)
#
#     def build_camera_source(self, sensor_id: int, width: int, height: int, framerate: int) -> Gst.Element:
#         src: Gst.Element = Gst.ElementFactory.make('nvarguscamerasrc', 'src')
#         src.set_property('sensor-id', sensor_id)
#         self.pipeline.add(src)
#
#         src_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
#         src_caps.set_property(
#             'caps',
#             Gst.Caps.from_string(f'video/x-raw(memory:NVMM),width={width},height={height},framerate={framerate}/1')
#         )
#         self.pipeline.add(src_caps)
#         src.link(src_caps)
#
#         return src_caps
#
#     def build_clockoverlay(self, source: Gst.Element) -> Gst.Element:
#         raw: Gst.Element = Gst.ElementFactory.make('nvvidconv')
#         self.pipeline.add(raw)
#         source.link(raw)
#
#         raw_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
#         raw_caps.set_property('caps', Gst.Caps.from_string('video/x-raw'))
#         self.pipeline.add(raw_caps)
#         raw.link(raw_caps)
#
#         clockoverlay: Gst.Element = Gst.ElementFactory.make('clockoverlay')
#         clockoverlay.set_property('time-format', '"%D %H:%M:%S"')
#         self.pipeline.add(clockoverlay)
#         raw_caps.link(clockoverlay)
#
#         nvmm: Gst.Element = Gst.ElementFactory.make('nvvidconv')
#         self.pipeline.add(nvmm)
#         clockoverlay.link(nvmm)
#
#         nvmm_caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
#         nvmm_caps.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM)'))
#         self.pipeline.add(nvmm_caps)
#         nvmm.link(nvmm_caps)
#
#         return nvmm_caps
#
#     # def build_file_sink(self, source: Gst.Element) -> Gst.Element:
#     #     queue = self.build_queue(source=source)
#     #
#     #     videorate: Gst.Element = Gst.ElementFactory.make('videorate')
#     #     self.pipeline.add(videorate)
#     #     queue.link(videorate)
#     #
#     #     caps: Gst.Element = Gst.ElementFactory.make('capsfilter')
#     #     caps.set_property(
#     #         'caps',
#     #         Gst.Caps.from_string(f'video/x-raw(memory:NVMM),framerate=1/1')
#     #     )
#     #     self.pipeline.add(caps)
#     #     videorate.link(caps)
#     #
#     #     nvv4l2h264enc: Gst.Element = Gst.ElementFactory.make('nvv4l2h264enc')
#     #     self.pipeline.add(nvv4l2h264enc)
#     #     caps.link(nvv4l2h264enc)
#     #
#     #     h264parse: Gst.Element = Gst.ElementFactory.make('h264parse')
#     #     self.pipeline.add(h264parse)
#     #     nvv4l2h264enc.link(h264parse)
#     #
#     #     splitmuxsink: Gst.Element = Gst.ElementFactory.make('splitmuxsink')
#     #     splitmuxsink.set_property('location', f'{self._id}_%02d.mp4')
#     #     splitmuxsink.set_property('max-size-bytes', 10000000)
#     #     splitmuxsink.set_property('max-files', 10)
#     #     self.pipeline.add(splitmuxsink)
#     #     h264parse.link(splitmuxsink)
#     #
#     #     return splitmuxsink
#     #
#     def build_jpeg_sink(self, source: Gst.Element) -> Gst.Element:
#         # queue = self.build_queue(source=source)
#
#         jpegenc: Gst.Element = Gst.ElementFactory.make('nvjpegenc')
#         self.pipeline.add(jpegenc)
#         source.link(jpegenc)
#
#         appsink: Gst.Element = Gst.ElementFactory.make('appsink')
#         appsink.set_property('emit-signals', True)
#         appsink.set_property('drop', True)
#         appsink.connect('new-sample', self.jpeg_sink, None)
#         self.pipeline.add(appsink)
#         jpegenc.link(appsink)
#
#         return appsink
#
#     # def build_queue(self, source: Gst.Element) -> Gst.Element:
#     #     queue: Gst.Element = Gst.ElementFactory.make('queue')
#     #     queue.set_property('max-size-buffers', 1)
#     #     queue.set_property('leaky', 'downstream')
#     #     self.pipeline.add(queue)
#     #     source.link(queue)
#     #
#     #     return queue
#     #
#     # def build_tee(self, source: Gst.Element) -> Gst.Element:
#     #     tee: Gst.Element = Gst.ElementFactory.make('tee')
#     #     self.pipeline.add(tee)
#     #     source.link(tee)
#     #
#     #     return tee
#     #
#     def jpeg_sink(self, sink, data) -> Gst.FlowReturn:
#         self._set_threading_event()
#
#         sample: Gst.Sample = sink.emit('pull-sample')
#         buffer: Gst.Buffer = sample.get_buffer()
#         self._last_image_bytes = buffer.extract_dup(0, buffer.get_size())
#
#         self._clear_threading_event()
#
#         if not self.running:
#             logging.debug(f'[{self._id}] Closing Pipeline')
#             self.pipeline.set_state(Gst.State.NULL)
#
#         return Gst.FlowReturn.OK
#
#     def pipeline_bus_messages(self, bus, message, loop) -> bool:
#         t = message.type
#         logging.debug(f'[{self._id}] {t}')
#
#         if t in (Gst.MessageType.ERROR, Gst.MessageType.EOS):
#             self.running = False
#             logging.debug(f'[{self._id}] Loop Quit')
#             loop.quit()
#
#         return True
