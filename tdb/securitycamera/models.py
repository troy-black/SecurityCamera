from typing import Optional

from pydantic import BaseModel


class GstreamerRecorderDetails(BaseModel):
    playback_framerate: int
    record_framerate: int
    properties: dict


class GstreamerSourceDetails(BaseModel):
    element: str
    properties: dict
    caps: str
    width: int
    height: int
    framerate: int
    nvvidconv: Optional[str]
    recorder: Optional[GstreamerRecorderDetails]
    overlay: bool = False
    autostart: bool = False
