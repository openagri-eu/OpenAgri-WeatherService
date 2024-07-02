from fastapi import FastAPI

from src.core import app, log, config

log.setup_logging(config.LOGGING_LEVEL)

def create_app() -> FastAPI:
    return app.Application()
