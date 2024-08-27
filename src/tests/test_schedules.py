"""
A module to test the schedule endpoints
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from septaplusplus.main import app, schedule
from septaplusplus.models import LinesOutput, ScheduleMainOutput, ScheduleStationOuput


class TestReturnData:
    """
    A simple class for all the tests to live in
    """

    client = TestClient(app)

    def test_get_lines(self):
        request = self.client.get("/api/schedule/lines")
        assert request.status_code == 200
        TypeAdapter(list[LinesOutput]).validate_json(request.content)

    @pytest.mark.parametrize(
        "line",
        [line["line_code"] for line in schedule.LINES],
    )
    def test_all_lines_return_stations(self, line):
        request = self.client.get(f"/api/schedule/stations?line={line}")
        assert request.status_code == 200
        TypeAdapter(list[ScheduleStationOuput]).validate_json(request.content)

    def test_invalid_line(self):
        assert self.client.get("/api/schedule/stations?line=NON_EXISTENT_LINE").status_code == 400

    def test_valid_single_station_schedule(self):
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&direction=inbound")
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_inbound_schedule(self):
        request = self.client.get(
            "/api/schedule?line=TRE&orig=Trenton&dest=Gray 30th Street&direction=inbound"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_outbound_schedule(self):
        request = self.client.get(
            "/api/schedule?line=TRE&orig=Gray 30th Street&dest=Trenton&direction=outbound"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_invalid_direction(self):
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&direction=NON_EXISTENT_DIRECTION")
        assert request.status_code == 422

    def test_invalid_station_for_line(self):
        # Airport line does not have a stop at Trenton
        request = self.client.get("/api/schedule?line=AIR&orig=Trenton&direction=inbound")
        assert request.status_code == 400

    def test_invalid_dest_for_line(self):
        # Trenton line does have the Trenton station, but not the Eastwick station
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&dest=Eastwick&direction=inbound")
        assert request.status_code == 400

    @pytest.mark.parametrize(
        "line, orig, dest, direction",
        [
            ("AIR", "Airport Terminal B", "Temple University", "inbound"),
            ("CHE", "Chestnut Hill East", "Temple University", "inbound"),
            ("CYN", "Cynwyd", "Suburban Station", "inbound"),
            ("CHW", "Chestnut Hill West", "Temple University", "inbound"),
            ("FOX", "Fox Chase", "Suburban Station", "inbound"),
            ("LAN", "Doylestown", "Jefferson Station", "inbound"),
            ("MED", "Wawa", "Temple University", "inbound"),
            ("NOR", "Main Street", "Penn Medicine Station", "inbound"),
            ("PAO", "Thorndale", "Overbrook", "inbound"),
            ("TRE", "Trenton", "Temple University", "inbound"),
            ("WAR", "Warminster", "Fern Rock T C", "inbound"),
            ("WIL", "Newark", "Wilmington", "inbound"),
            ("WTR", "Yardley", "Elkins Park", "inbound"),
        ],
    )
    def test_valid_direction_for_orig_dest_all_lines(self, line, orig, dest, direction):
        request = self.client.get(
            f"/api/schedule?line={line}&orig={orig}&dest={dest}&direction={direction}"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    @pytest.mark.parametrize(
        "line, orig, dest, direction",
        [
            ("AIR", "Airport Terminal B", "Temple University", "outbound"),
            ("CHE", "Chestnut Hill East", "Temple University", "outbound"),
            ("CYN", "Cynwyd", "Suburban Station", "outbound"),
            ("CHW", "Chestnut Hill West", "Temple University", "outbound"),
            ("FOX", "Fox Chase", "Suburban Station", "outbound"),
            ("LAN", "Doylestown", "Jefferson Station", "outbound"),
            ("MED", "Wawa", "Temple University", "outbound"),
            ("NOR", "Main Street", "Penn Medicine Station", "outbound"),
            ("PAO", "Thorndale", "Overbrook", "outbound"),
            ("TRE", "Trenton", "Temple University", "outbound"),
            ("WAR", "Warminster", "Fern Rock T C", "outbound"),
            ("WIL", "Newark", "Wilmington", "outbound"),
            ("WTR", "Yardley", "Elkins Park", "outbound"),
        ],
    )
    def test_invalid_direction_for_orig_dest_all_lines(self, line, orig, dest, direction):
        request = self.client.get(
            f"/api/schedule?line={line}&orig={orig}&dest={dest}&direction={direction}"
        )
        assert request.status_code == 400
