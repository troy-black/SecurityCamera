import threading

from fastapi import APIRouter, BackgroundTasks, HTTPException
from starlette.responses import StreamingResponse

from tdb.securitycamera import config
from tdb.securitycamera.gstreamer import GstreamerCamera

router = APIRouter()


def get_camera(camera_id: str) -> GstreamerCamera:
    if camera_id not in config.Config.cameras:
        raise HTTPException(status_code=404, detail=f'Camera {camera_id} not found')

    return config.Config.cameras[camera_id]


@router.get('/status')
async def get_status():
    return {'status': 'Running'}


@router.get('/{camera_id}/stream/video')
async def get_stream_video(camera_id: str):
    camera = get_camera(camera_id)

    # return mjpeg video
    return StreamingResponse(
        camera.stream_images(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@router.get('/{camera_id}/stream/{action}')
async def get_stream_action(camera_id: str, action: bool, background_tasks: BackgroundTasks):
    camera = get_camera(camera_id)

    camera.running = action

    if action:
        background_tasks.add_task(camera.background_task)

        if camera.recorder:
            camera.recorder_thread = threading.Thread(target=camera.recorder.background_task)
            camera.recorder_thread.start()

    return {
        'stream': action
    }
