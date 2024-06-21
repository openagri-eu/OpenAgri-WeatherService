from functools import partial
import fastapi

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document

from src.core import config
from src import utils
from src.core.dao import Dao
from src.routes import router
from src.models.point import Point, GeoJSON
from src.external_services.openweathermap import OpenWeatherMap


class Application(fastapi.FastAPI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = self.setup_db()
        self.weather_app = self.setup_weather_app()
        self.setup_routes()


    def setup_db(self):

        async def db_up(app: Application):
            try:
                await app.db.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
                # Init beanie with the Product document class
                await init_beanie(
                    database=app.db.get_database(config.DATABASE_NAME),
                    document_models=utils.load_classes('**/models/**.py', (Document,))
                )
                dao = Dao()
            except Exception as e:
                print(e)

        async def db_down(app: Application):
            try:
                app.db.close()
                print("Database closed!")
            except Exception as e:
                print(e)

        self.add_event_handler(event_type="startup", func=partial(db_up, app=self))
        self.add_event_handler(event_type='shutdown', func=partial(db_down, app=self))
        return AsyncIOMotorClient(config.DATABASE_URI)

    def setup_routes(self):

        async def add_router(app: Application):
            app.include_router(router)
            print('Routes added!')

        self.add_event_handler(event_type="startup", func=partial(add_router, app=self))
        return


    def setup_weather_app(self):
        return OpenWeatherMap()