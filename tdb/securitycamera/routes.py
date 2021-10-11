import threading
from datetime import timedelta
from pathlib import Path

from fastapi import BackgroundTasks
from fastapi import Depends, APIRouter
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import StreamingResponse
from starlette.templating import Jinja2Templates

from tdb.securitycamera import security
from tdb.securitycamera.models import UserDetails
from tdb.securitycamera.utilities import HTTP_BAD_USER_PASS, get_camera

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(str(Path(__file__).parent), 'templates')))


@router.get('/status', tags=['Status'])
async def get_status():
    return {'status': 'Running'}


@router.get('/{camera_id}/stream/video', tags=['Camera'])
async def get_stream_video(camera_id: str):
    camera = get_camera(camera_id)

    # return mjpeg video
    return StreamingResponse(
        camera.stream_images(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@router.get('/{camera_id}/stream/{action}', tags=['Camera'])
async def get_stream_action(camera_id: str, action: bool, background_tasks: BackgroundTasks):
    camera = get_camera(camera_id)

    camera.running = action

    if action:
        background_tasks.add_task(camera.background_task)

        if camera.recorder:
            camera.thread = threading.Thread(target=camera.recorder.background_task)
            camera.thread.start()

    return {
        'stream': action
    }


@router.get('/auth/login', response_class=HTMLResponse, tags=['Auth'])
async def read_item(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/auth/login', tags=['Auth'])
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTP_BAD_USER_PASS

    access_token_expires = timedelta(minutes=60 * 24)
    access_token = security.create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )

    response.set_cookie(key='access_token', value=f'Bearer {access_token}', httponly=True)

    return {'success': True}


@router.get('/users/me/', response_model=UserDetails, tags=['Testing'])
async def read_users_me(current_user: UserDetails = Depends(security.get_current_active_user)):
    return current_user
