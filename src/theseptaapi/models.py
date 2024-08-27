from fastapi import HTTPException
from pydantic import BaseModel, field_validator, model_validator

from theseptaapi.schedules import ScheduleGenerator

schedule = ScheduleGenerator()


class StationInput(BaseModel):
    line: str

    @field_validator("line")
    def validate_line(cls, value):
        if value not in schedule.LINES.keys():
            raise HTTPException(status_code=400, detail=f"Invalid Line: {value}")
        return value


class ScheduleInput(BaseModel):
    line: str
    direction: int
    orig: str
    dest: str | None = None

    @staticmethod
    def validate_station_for_line(line: str, station: str):
        stations_for_line = [stop["stop_name"] for stop in schedule.get_stations_for_line(line)]
        if station not in stations_for_line:
            raise HTTPException(
                status_code=400, detail=f"Invalid Station: {station} for line: {line}"
            )

    @field_validator("line")
    def validate_line(cls, value):
        if value not in schedule.LINES.keys():
            raise HTTPException(status_code=400, detail=f"Invalid Line: {value}")
        return value

    @field_validator("direction")
    def validate_direction(cls, value):
        if not (value == 0 or value == 1):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Direction: {value}. Use 0 for inbound, and 1 for outbound",
            )
        return value

    @model_validator(mode="after")
    def validate_mode(self):

        self.validate_station_for_line(self.line, self.orig)
        if self.dest is not None:
            self.validate_station_for_line(self.line, self.dest)
            return self

        return self


class StationOuput(BaseModel):
    stop_id: str
    stop_name: str


class ScheduleDestOnlyOutput(BaseModel):
    arrival_time: str
    train_id: str


class ScheduleDestAndOrigItemOutput(BaseModel):
    arrival_time: str
    departure_time: str
    train_id: str


class ScheduleMainOutput(BaseModel):
    weekday: list[ScheduleDestOnlyOutput | ScheduleDestAndOrigItemOutput]
    weekend: list[ScheduleDestOnlyOutput | ScheduleDestAndOrigItemOutput]
