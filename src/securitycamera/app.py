import logging

from fastapi import FastAPI
from securitycamera.routes import api, camera

logging.debug('Starting Application')

app = FastAPI()

# TODO - security
# app.secret_key = secret_key

# load additional routes
app.include_router(api.router, prefix='/api', tags=['api'])
app.include_router(camera.router, prefix='/camera', tags=['camera'])
