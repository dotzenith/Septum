from typing import Annotated

from fastapi import Depends, FastAPI

import theseptaapi.scrapers as scrapers
from theseptaapi.models import (BusAndTrolleyOutput, LinesOutput,
                                ScheduleInput, ScheduleMainOutput,
                                ScheduleStationOuput, StationInput,
                                StationOutput)
from theseptaapi.schedules import ScheduleGenerator

app = FastAPI()
schedule = ScheduleGenerator()


# Basic Stations endpoint
@app.get("/stations", response_model=list[StationOutput])
def get_stations():
    """
    Retrieves "Regional Rail Inputs" used by setpa's public API (e.g, the `/NextToArrive/index.php` endpoint).

    Returns:
        A list of dictionaries where `station_name` is the colloquial station name and
            `parameter` is what the API expects as input for the particular station.

    Example:
        [
            {"station_name": "49th Street", "parameter": "49th St"},
            {"station_name": "Holmesburg Junction", "parameter": "Holmesburg Jct"},
            {"station_name": "Fern Rock Transportation Center", "parameter": "Fern Rock TC"},
        ]

    Note:
        These are NOT the same the stations returned by `/schedule/stations` endpoint.
        Those are for an API that is not publicly documented. See `/schedule/stations` for more info.
    """
    return scrapers.get_station_names()


# Route Endpoints
@app.get("/routes/bus", response_model=list[BusAndTrolleyOutput])
def get_bus_routes():
    """
    Retrieve bus routes used by septa's public API (e.g, the `/TransitView/index.php` endpoint).

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given bus route,
            and `route_number` (not always a "number") is what the API expects.

    Example:
        [
            {"route_number": "1", "route_name": "parx casino to 54th-city"},
            {"route_number": "103", "route_name": "Ardmore to 69th Street Transportation Center"},
            {"route_number": "104", "route_name": "West Chester University to 69th Street Transportation Center"}
        ]
    """
    return scrapers.get_bus_routes()


@app.get("/routes/trolley", response_model=list[BusAndTrolleyOutput])
def get_trolley_routes():
    """
    Retrieve trolley routes used by septa's public API (e.g, the `/TransitView/index.php` endpoint).

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given trolley route,
            and `route_number` is what the API expects.

    Example:
        [
            {"route_number": "10", "route_name": "13th-Market to 63rd-Malvern"},
            {"route_number": "11", "route_name": "13th-Market to Darby Transportation Center"},
            {"route_number": "15", "route_name": "63rd-Girard to Richmond-Westmoreland"},
        ]
    """
    return scrapers.get_trolley_routes()


# Schedule Endpoints
@app.get("/schedule/lines", response_model=list[LinesOutput])
def get_lines():
    """
    Retrieve a list of all available lines. Each line is represented by its code and name.

    Returns:
        A list of dictionaries, each containing a `line_code` and a `line_name`

    Example:
        [
            {"line_code": "AIR", "line_name": "Airport"},
            {"line_code": "CHE", "line_name": "Chestnut Hill East"},
            {"line_code": "CHW", "line_name": "Chestnut Hill West"}
        ]
    """
    return schedule.get_lines()


@app.get("/schedule/stations", response_model=list[ScheduleStationOuput])
def get_stattions_for_lines(line: Annotated[StationInput, Depends()]):
    """
    Retrieve a list of stations for a specific line.

    This endpoint returns a list of stations (stops) that are part of the
    specified line. Each station is represented by its ID and name.

    Args:
        line: The line code as seen in `/schedule/lines`

    Returns:
        A list of dictionaries, each containing a stop_id and stop_name.

    Example:
        Request: GET /schedule/stations?line=TRE
        Response:
        [
            {"stop_id": "90701", "stop_name": "Trenton"},
            {"stop_id": "90004", "stop_name": "Gray 30th Street"},
            {"stop_id": "90007", "stop_name": "Temple University"}
        ]

    Note:
        The line parameter is automatically validated against the list of
        valid line codes as seen in `/schedule/lines`. If an invalid line code
        is provided, a 400 Bad Request error will be raised.

        These station names are not the same as `/stations`. These are to be used with the `/schedule` endpoint,
        and not with the public septa api.
    """
    return schedule.get_stations_for_line(line.line)


@app.get("/schedule", response_model=ScheduleMainOutput)
def get_schedule_for_station(query: Annotated[ScheduleInput, Depends()]):
    """
    Retrieve the schedule for a specific station on a given route.

    Args:
        line (str): The transit line code.
        direction (int): The direction of travel (0 for inbound, 1 for outbound).
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

    Example:
        Request: GET /schedule?line=TRE&direction=0&orig=Trenton&dest=Gray 30th Street&direction=0
        Response:
        {
            "weekday": [
                {"departure_time": "06:59:00", "arrival_time": "07:47:00", "train_id": "7404"},
                {"departure_time": "07:26:00", "arrival_time": "08:20:00", "train_id": "9744"}
            ],
            "weekend": [
                {"departure_time": "13:10:00", "arrival_time": "13:58:00", "train_id": "718"},
                {"departure_time": "15:05:00", "arrival_time": "15:53:00", "train_id": "722"}
            ]
        }

    Note:
        If only the origin station is provided, the schedule will show departure times only.
        If both origin and destination are provided, the schedule will include both departure
        and arrival times.

        IMPORTANT: Be very careful about the `direction` parameter.
        For example, if you are going from Trenton to Gray 30th Street on the TRE line, your direction should be 0.
        This is because Gray 30th Street, is towards the city (i.e inbound). Your direction cannot be 1,
        because you cannot go to Gray 30th Street while going away from the city (i.e outbound). The API
        will return a response even if you get the direction wrong, but the results will be unreliable.
    """
    if query.dest is not None:
        return schedule.get_schedule_for_line(query.line, query.orig, query.dest, query.direction)

    return schedule.get_schedule_for_station(query.line, query.orig, query.direction)
