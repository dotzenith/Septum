import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

import septum.scrapers as scrapers
from septum.models import (
    BusAndTrolleyOutput,
    LinesOutput,
    ScheduleInput,
    ScheduleMainOutput,
    ScheduleStationOuput,
    StationInput,
    StationOutput,
)
from septum.schedules import ScheduleGenerator

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield


app = FastAPI(docs_url=None, lifespan=lifespan)
schedule = ScheduleGenerator()
SECONDS_IN_A_WEEK = 604800
SECONDS_IN_A_DAY = 86400


@app.get("/", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Septum",
        swagger_favicon_url="https://danshu.co/favicon.ico",
    )


# Basic Stations endpoint
@app.get("/api/stations", response_model=list[StationOutput])
@cache(expire=SECONDS_IN_A_WEEK)
async def get_stations():
    """
    Retrieves "Regional Rail Inputs" used by setpa's public API (e.g, the `/NextToArrive/index.php` endpoint).

    Returns:
        A list of dictionaries where `station_name` is the colloquial station name and
            `parameter` is what the API expects as input for the particular station.

    Note:
        These are NOT the same the stations returned by `/schedule/stations` endpoint.
        Those are for an API that is not publicly documented. See `/schedule/stations` for more info.
    """
    return scrapers.get_station_names()


# Route Endpoints
@app.get("/api/routes/bus", response_model=list[BusAndTrolleyOutput])
@cache(expire=SECONDS_IN_A_WEEK)
async def get_bus_routes():
    """
    Retrieve bus routes used by septa's public API (e.g, the `/TransitView/index.php` endpoint).

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given bus route,
            and `route_number` (not always a "number") is what the API expects.
    """
    return scrapers.get_bus_routes()


@app.get("/api/routes/trolley", response_model=list[BusAndTrolleyOutput])
@cache(expire=SECONDS_IN_A_WEEK)
async def get_trolley_routes():
    """
    Retrieve trolley routes used by septa's public API (e.g, the `/TransitView/index.php` endpoint).

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given trolley route,
            and `route_number` is what the API expects.
    """
    return scrapers.get_trolley_routes()


# Schedule Endpoints
@app.get("/api/schedule/lines", response_model=list[LinesOutput])
async def get_lines():
    """
    Retrieve a list of all available lines. Each line is represented by its code and name.

    Returns:
        A list of dictionaries, each containing a `line_code` and a `line_name`
    """
    return schedule.get_lines()


@app.get("/api/schedule/stations", response_model=list[ScheduleStationOuput])
async def get_stations_for_lines(line: Annotated[StationInput, Depends()]):
    """
    Retrieve a list of stations for a specific line.

    This endpoint returns a list of stations (stops) that are part of the
    specified line. Each station is represented by its ID and name.

    Args:
        line: The line code as seen in `/schedule/lines`
        direction: (str, None): "inbound" (default)/"outbound"

    Returns:
        A list of dictionaries, each containing a stop_id and stop_name.

    Note:
        The line parameter is automatically validated against the list of
        valid line codes as seen in `/schedule/lines`. If an invalid line code
        is provided, a 400 Bad Request error will be raised.

        These station names are not the same as `/stations`. These are to be used with the `/schedule` endpoint,
        and not with the public septa api.
    """
    return schedule.get_stations_for_line(line.line, line.direction)


@app.get("/api/schedule", response_model=ScheduleMainOutput)
async def get_schedule_for_station(query: Annotated[ScheduleInput, Depends()]):
    """
    Retrieve the schedule for a specific station on a given route.

    Args:
        line (str): The transit line code.
        direction (Direction): The direction of travel. "inbound" or "outbound"
        orig (str): The origin station name.
        dest (str, optional): The destination station name.

    Returns:
        A dictionary containing two lists of schedule items:
            - weekday: List of schedule items for weekdays.
            - weekend: List of schedule items for weekends.
            Each schedule item is a dictionary with the keys:
                - departure_time (str): The departure time from the orig station
                - arrival_time (str, optional): The arrival time at the dest station.
                    (only present if both origin and destination are specified).
                - train_id (str): The unique identifier for the train.

    Note:
        If only the origin station is provided, the schedule will show departure times only.
        If both origin and destination are provided, the schedule will include both departure
        and arrival times.

        IMPORTANT: Be very careful about the `direction` parameter.
        For example, if you are going from Trenton to Gray 30th Street on the TRE line, your direction should be 0.
        This is because Gray 30th Street, is towards the city (i.e inbound). Your direction cannot be 1,
        because you cannot go to Gray 30th Street while going away from the city (i.e outbound). The API the best it
        can to validate this and return an error message, but there might be edge cases that still slip away, please
        open an issue on https://github.com/dotzenith/septum

        Also note that schedule items returned when `dest` is not passed in might have inconsistencies.
        Some of the items might be for trains that don't go anywhere after this station. Therefore passing in `dest`
        is recommended.
    """
    if query.dest is not None:
        return schedule.get_schedule_for_line(query.line, query.orig, query.dest, query.direction)

    return schedule.get_schedule_for_station(query.line, query.orig, query.direction)
