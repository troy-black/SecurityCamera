from uvicorn import Server
from uvicorn import Config as UvicornConfig

from securitycamera import logger
from securitycamera import config


if __name__ == '__main__':
    # TODO - pass cmd args here...
    config.config = config.Config()

    uvicorn_config = UvicornConfig(
        'src.securitycamera.app:app',
        host='0.0.0.0',
        log_level=config.config.log_level,
    )

    server = Server(uvicorn_config)

    # override logging settings to all use loguru
    logger.setup_logging(config.config.log_level, False)

    server.run()
