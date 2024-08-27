"""
A module to test the schedule endpoints
"""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from theseptaapi.main import app, schedule
from theseptaapi.models import ScheduleMainOutput, StationOuput


class TestReturnData:
    """
    A simple class for all the tests to live in
    """

    client = TestClient(app)

    def test_num_of_lines(self):
        num_lines_internal = len(schedule.LINES.keys())
        num_lines_endpoint = len(json.loads(self.client.get("/schedule/lines").content))
        assert num_lines_internal == num_lines_endpoint

    @pytest.mark.parametrize(
        "line",
        list(schedule.LINES.keys()),
    )
    def test_all_lines_return_stations(self, line):
        request = self.client.get(f"/schedule/stations?line={line}")
        assert request.status_code == 200
        TypeAdapter(list[StationOuput]).validate_json(request.content)

    def test_invalid_line(self):
        assert self.client.get("/schedule/stations?line=NON_EXISTENT_LINE").status_code == 400

    def test_valid_single_station_schedule(self):
        request = self.client.get("/schedule?line=TRE&orig=Trenton&direction=0")
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_inbound_schedule(self):
        request = self.client.get(
            "/schedule?line=TRE&orig=Trenton&dest=Gray 30th Street&direction=0"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_valid_orig_to_dest_outbound_schedule(self):
        request = self.client.get(
            "/schedule?line=TRE&orig=Gray 30th Street&dest=Trenton&direction=1"
        )
        assert request.status_code == 200
        ScheduleMainOutput.model_validate_json(request.content)

    def test_invalid_direction(self):
        request = self.client.get("/schedule?line=TRE&orig=Trenton&direction=3")
        assert request.status_code == 400

    def test_invalid_station_for_line(self):
        # Airport line does not have a stop at Trenton
        request = self.client.get("/schedule?line=AIR&orig=Trenton&direction=0")
        assert request.status_code == 400

    def test_invalid_dest_for_line(self):
        # Trenton line does have the Trenton station, but not the Eastwick station
        request = self.client.get("/schedule?line=TRE&orig=Trenton&dest=Eastwick&direction=0")
        assert request.status_code == 400
