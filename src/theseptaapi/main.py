from typing import Union

from fastapi import FastAPI

import theseptaapi.scrapers as scrapers
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


@app.get("/schedule/{line}/stations")
def get_stattions_for_lines(line: str) -> list[dict[str, str]]:
    schedule.validate_line(line)
    return schedule.get_stations_for_line(line)


@app.get("/schedule/{line}/schedule")
def get_schedule_for_station(
    line: str, direction: int, orig: str, dest: Union[str, None] = None
) -> dict[str, list[dict[str, str]]]:
    schedule.validate_line(line)
    schedule.validate_direction(direction)
    schedule.validate_station_for_line(line, orig)

    if dest is not None:
        schedule.validate_station_for_line(line, dest)
        schedule.validate_orig_dest_for_direction(line, orig, dest, direction)
        return schedule.get_schedule_for_line(line, orig, dest, direction)
    else:
        return schedule.get_schedule_for_station(line, orig, direction)
