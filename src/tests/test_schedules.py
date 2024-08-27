"""
A module to test the schedule endpoints
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from theseptaapi.main import app, schedule
from theseptaapi.models import LinesOutput, ScheduleMainOutput, ScheduleStationOuput


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
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&direction=0")
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_inbound_schedule(self):
        request = self.client.get(
            "/api/schedule?line=TRE&orig=Trenton&dest=Gray 30th Street&direction=0"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_outbound_schedule(self):
        request = self.client.get(
            "/api/schedule?line=TRE&orig=Gray 30th Street&dest=Trenton&direction=1"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_invalid_direction(self):
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&direction=3")
        assert request.status_code == 400

    def test_invalid_station_for_line(self):
        # Airport line does not have a stop at Trenton
        request = self.client.get("/api/schedule?line=AIR&orig=Trenton&direction=0")
        assert request.status_code == 400

    def test_invalid_dest_for_line(self):
        # Trenton line does have the Trenton station, but not the Eastwick station
        request = self.client.get("/api/schedule?line=TRE&orig=Trenton&dest=Eastwick&direction=0")
        assert request.status_code == 400
