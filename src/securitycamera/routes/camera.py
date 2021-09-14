from fastapi import APIRouter, BackgroundTasks
from starlette.responses import StreamingResponse

from securitycamera.config import config

router = APIRouter()


@router.get('/{camera_id}/stream/video')
async def get_stream_video(camera_id: str):
    camera = config.cameras[camera_id]

    # return mjpeg video
    return StreamingResponse(
        camera.stream_images(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@router.get('/{camera_id}/stream/{action}')
async def get_stream_action(camera_id: str, action: bool, background_tasks: BackgroundTasks):
    camera = config.cameras[camera_id]

    camera.running = action

    if action:
        background_tasks.add_task(camera.background_task)

    return {
        'stream': action
    }
