from uvicorn import Config as UvicornConfig
from uvicorn import Server

from tdb.securitycamera import config
from tdb.securitycamera import logger


def main():
    # TODO - pass cmd args here...
    config.Config.load()

    uvicorn_config = UvicornConfig(
        'tdb.securitycamera.app:app',
        host='0.0.0.0',
        log_level=config.Config.log_level.lower(),
    )

    server = Server(uvicorn_config)

    # override logging settings to all use loguru
    logger.setup_logging(config.Config.log_level, False)

    server.run()


if __name__ == '__main__':
    main()
