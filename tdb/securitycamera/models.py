from typing import Optional, Dict, Union, List

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


class UserDetails(BaseModel):
    username: str
    access: List[str]


class UserPassword(UserDetails):
    password: str


class UserHashed(UserDetails):
    hashed_password: str


class ConfigDetails(BaseModel):
    cameras: Dict[str, GstreamerSourceDetails]
    log_level: str
    secret_key: str
    users: List[Union[UserDetails, UserHashed]]


class Token(BaseModel):
    access_token: str
    token_type: str
