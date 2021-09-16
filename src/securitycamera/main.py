from uvicorn import Config as UvicornConfig
from uvicorn import Server

from securitycamera import config
from securitycamera import logger


def main():
    # TODO - pass cmd args here...

    uvicorn_config = UvicornConfig(
        'src.securitycamera.app:app',
        host='0.0.0.0',
        log_level=config.Config.log_level.lower(),
    )

    server = Server(uvicorn_config)

    # override logging settings to all use loguru
    logger.setup_logging(config.Config.log_level, False)

    server.run()


if __name__ == '__main__':
    main()
