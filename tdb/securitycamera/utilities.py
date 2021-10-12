from typing import Dict
from typing import Optional

from fastapi import HTTPException
from fastapi import Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette import status

from tdb.securitycamera import config
from tdb.securitycamera.gstreamer import GstreamerCamera

HTTP_NOT_AUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Not authenticated',
    headers={'WWW-Authenticate': 'Bearer'},
)

HTTP_BAD_USER_PASS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Incorrect username or password',
    headers={'WWW-Authenticate': 'Bearer'},
)

HTTP_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail='Access forbidden',
    headers={'WWW-Authenticate': 'Bearer'},
)


def get_camera(camera_id: str) -> GstreamerCamera:
    if camera_id not in config.Config.cameras:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Camera {camera_id} not found',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return config.Config.cameras[camera_id]


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, *, auth_url: str, scheme_name: Optional[str] = None,
                 scopes: Optional[Dict[str, str]] = None, auto_error: bool = True):

        if not scopes:
            scopes = {}

        super().__init__(
            scheme_name=scheme_name,
            auto_error=auto_error,
            flows=OAuthFlowsModel(password={'tokenUrl': auth_url, 'scopes': scopes})
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get('access_token')
        scheme, param = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != 'bearer':
            if self.auto_error:
                raise HTTP_NOT_AUTHENTICATED
            else:
                return None

        return param
