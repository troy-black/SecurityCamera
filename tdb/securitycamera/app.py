import logging

from fastapi import FastAPI

from tdb.securitycamera import routes

logging.debug('Starting Application')

app = FastAPI()

# TODO - security
# app.secret_key = secret_key

# load additional routes
app.include_router(routes.router,
                   # prefix='/camera',
                   tags=['camera'])
