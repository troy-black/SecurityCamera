import logging
import threading

from fastapi import FastAPI

from tdb.securitycamera import routes, config

logging.debug('Starting Application')

app = FastAPI()

# TODO - security
# app.secret_key = secret_key

# load additional routes
app.include_router(routes.router, tags=['camera'])


@app.on_event('startup')
async def startup_event():
    for name, camera in config.Config.cameras.items():
        if camera.source.autostart:
            thread = threading.Thread(target=camera.background_task)
            thread.start()

            if camera.recorder:
                camera.thread = threading.Thread(target=camera.recorder.background_task)
                camera.thread.start()
