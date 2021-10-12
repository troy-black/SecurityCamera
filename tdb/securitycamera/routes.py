from datetime import timedelta
from pathlib import Path

from fastapi import Depends, APIRouter
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import StreamingResponse
from starlette.templating import Jinja2Templates

from tdb.securitycamera import config
from tdb.securitycamera import security
from tdb.securitycamera.models import UserDetails
from tdb.securitycamera.utilities import HTTP_BAD_USER_PASS, get_camera, HTTP_FORBIDDEN

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(str(Path(__file__).parent), 'templates')))


@router.get('/status', tags=['Status'])
async def get_status():
    return {'status': 'Running'}


@router.get('/camera/dashboard', tags=['Camera'])
async def get_dashboard(request: Request, current_user: UserDetails = Depends(security.get_current_active_user)):
    if 'Camera' not in current_user.access:
        raise HTTP_FORBIDDEN

    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'camera_details': config.Config.camera_details
    })


@router.get('/camera/{camera_id}/jpeg', tags=['Camera'])
async def get_stream_video(camera_id: str, current_user: UserDetails = Depends(security.get_current_active_user)):
    if 'Camera' not in current_user.access:
        raise HTTP_FORBIDDEN

    camera = get_camera(camera_id)

    return Response(camera.last_image_bytes, media_type='image/jpeg')


@router.get('/camera/{camera_id}/video', tags=['Camera'])
async def get_stream_video(camera_id: str, current_user: UserDetails = Depends(security.get_current_active_user)):
    if 'Camera' not in current_user.access:
        raise HTTP_FORBIDDEN

    camera = get_camera(camera_id)

    # return mjpeg video
    return StreamingResponse(
        camera.stream_images(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@router.get('/auth/login', response_class=HTMLResponse, tags=['Auth'])
async def get_auth_login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/auth/login', tags=['Auth'])
async def post_auth_login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTP_BAD_USER_PASS

    access_token_expires = timedelta(minutes=60 * 24)
    access_token = security.create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )

    response.set_cookie(key='access_token', value=f'Bearer {access_token}', httponly=True)

    return {'success': True}
