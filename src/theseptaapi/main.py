from typing import Annotated, Any

from fastapi import Depends, FastAPI

import theseptaapi.scrapers as scrapers
from theseptaapi.models import (StationInput, StationOuput, ScheduleMainOutput,
                                ScheduleInput)
from theseptaapi.schedules import ScheduleGenerator

app = FastAPI()
schedule = ScheduleGenerator()


# Basic Stations endpoint
@app.get("/stations")
def get_stations() -> dict[str, str]:
    return scrapers.get_station_names()


# Route Endpoints
@app.get("/routes/bus")
def get_bus_routes() -> dict[str, str]:
    return scrapers.get_bus_routes()


@app.get("/routes/trolley")
def get_trolley_routes() -> dict[str, str]:
    return scrapers.get_trolley_routes()


# Schedule Endpoints
@app.get("/schedule/lines")
def get_lines() -> dict[str, str]:
    return schedule.get_lines()


@app.get("/schedule/stations", response_model=list[StationOuput])
def get_stattions_for_lines(line: Annotated[StationInput, Depends()]) -> Any:
    return schedule.get_stations_for_line(line.line)


@app.get("/schedule", response_model=ScheduleMainOutput)
def get_schedule_for_station(query: Annotated[ScheduleInput, Depends()]) -> Any:

    if query.dest is not None:
        return schedule.get_schedule_for_line(query.line, query.orig, query.dest, query.direction)

    return schedule.get_schedule_for_station(query.line, query.orig, query.direction)
