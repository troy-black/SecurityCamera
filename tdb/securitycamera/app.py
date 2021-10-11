import logging
import threading
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from tdb.securitycamera import routes, config

logging.debug('Starting Application')

app = FastAPI()

app.secret_key = config.Config.secret_key

# load additional routes
app.include_router(routes.router)
app.mount('/static', StaticFiles(directory=str(Path(str(Path(__file__).parent), 'static'))), name='static')


@app.on_event('startup')
async def startup_event():
    for name, camera in config.Config.cameras.items():
        if camera.source.autostart:
            thread = threading.Thread(target=camera.background_task)
            thread.start()

            if camera.recorder:
                camera.thread = threading.Thread(target=camera.recorder.background_task)
                camera.thread.start()
