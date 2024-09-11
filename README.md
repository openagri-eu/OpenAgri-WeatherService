# Weather Service

## Description

This a simple service providing a 5-day weather forecast for a specific location. The service uses OpenWeatherMap API to extract necessary information.

Project is fully functional, compatible with Python 3.12. Is built using [FastAPI](https://fastapi.tiangolo.com/) framework and served with [Uvicorn](https://www.uvicorn.org).

The application is containerized using Docker. To install it please firstly install `docker`

You can follow [this guide](https://docs.docker.com/engine/install/ubuntu/) to install `docker` on Ubuntu.

## Requirements
- git
- docker
- docker-compose

## Installation
After installing `docker` you can simply run

```
docker build -t weather-srv .
docker run -p 8000:8000 weather-srv
```

to run the application.

The application is served on `http://127.0.0.1:8000`

## Documentation

**GET**
```
/forecast5?lat={latitude}&lon={longitude}
```

For more info please read the [docs](http://localhost:8000/docs)

## Contribute

Please contanct maintainer.

## License

[European Union Public Licence](LICENSE)







