from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from uvicorn import Config

from src.core import app

def create_app() -> FastAPI:
    return app.Application()
