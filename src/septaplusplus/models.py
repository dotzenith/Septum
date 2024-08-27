from fastapi import HTTPException
from pydantic import BaseModel, field_validator, model_validator

from septaplusplus.enum import Direction
from septaplusplus.schedules import ScheduleGenerator

schedule = ScheduleGenerator()


class StationInput(BaseModel):
    line: str
    direction: Direction | None = None

    @field_validator("line")
    def validate_line(cls, value):
        if value not in [line["line_code"] for line in schedule.LINES]:
            raise HTTPException(status_code=400, detail=f"Invalid Line: {value}")
        return value


class ScheduleInput(BaseModel):
    line: str
    direction: Direction
    orig: str
    dest: str | None = None

    @staticmethod
    def validate_orig_dest_for_direction(line: str, orig: str, dest: str, direction: Direction):
        stations = [stop["stop_name"] for stop in schedule.get_stations_for_line(line, direction)]
        orig_index = stations.index(orig)

        if dest not in stations[orig_index + 1 :]:
            raise HTTPException(
                status_code=400, detail=f"cannot go from {orig} to {dest} going {direction.value}"
            )

    @staticmethod
    def validate_station_for_line(line: str, station: str):
        stations_for_line = [stop["stop_name"] for stop in schedule.get_stations_for_line(line)]
        if station not in stations_for_line:
            raise HTTPException(
                status_code=400, detail=f"Invalid Station: {station} for line: {line}"
            )

    @field_validator("line")
    def validate_line(cls, value):
        if value not in [line["line_code"] for line in schedule.LINES]:
            raise HTTPException(status_code=400, detail=f"Invalid Line: {value}")
        return value

    @model_validator(mode="after")
    def validate_mode(self):

        self.validate_station_for_line(self.line, self.orig)
        if self.dest is not None:
            self.validate_station_for_line(self.line, self.dest)
            self.validate_orig_dest_for_direction(self.line, self.orig, self.dest, self.direction)
            return self

        return self


class StationOutput(BaseModel):
    station_name: str
    parameter: str


class BusAndTrolleyOutput(BaseModel):
    route_number: str
    route_name: str


class LinesOutput(BaseModel):
    line_code: str
    line_name: str


class ScheduleStationOuput(BaseModel):
    stop_id: str
    stop_name: str


class ScheduleDestOnlyOutput(BaseModel):
    departure_time: str
    train_id: str


class ScheduleDestAndOrigItemOutput(BaseModel):
    departure_time: str
    arrival_time: str
    train_id: str


class ScheduleMainOutput(BaseModel):
    weekday: list[ScheduleDestOnlyOutput | ScheduleDestAndOrigItemOutput]
    weekend: list[ScheduleDestOnlyOutput | ScheduleDestAndOrigItemOutput]
