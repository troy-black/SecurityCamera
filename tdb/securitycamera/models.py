from typing import Optional

from pydantic import BaseModel


class GstreamerRecorderDetails(BaseModel):
    playback_framerate: int
    record_framerate: int
    properties: dict
    overlay: bool = False


class GstreamerSourceDetails(BaseModel):
    element: str
    properties: dict
    # caps: GstreamerCaps
    caps: str
    width: int
    height: int
    framerate: int
    nvvidconv: Optional[str]
    recorder: Optional[GstreamerRecorderDetails]
