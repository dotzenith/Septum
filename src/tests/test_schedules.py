"""
A module to test the schedule endpoints
"""

import json

import pytest
from fastapi.testclient import TestClient

from theseptaapi.main import app, schedule


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
        [schedule.LINES.keys()],
    )
    def test_all_lines_return_stations(self, line):
        response = json.loads(self.client.get(f"/schedule/{line}/stations").content)
        assert len(response) > 0

    def test_invalid_line(self):
        assert self.client.get("/schedule/NON_EXISTENT_LINE/stations").status_code == 400

    def test_valid_single_station_schedule(self):
        request = self.client.get("/schedule/TRE/schedule?orig=Trenton&direction=0")
        assert request.status_code == 200

    def test_valid_orig_to_dest_schedule(self):
        request = self.client.get(
            "/schedule/TRE/schedule?orig=Trenton&dest=Gray 30th Street&direction=0"
        )
        assert request.status_code == 200

    def test_invalid_direction(self):
        request = self.client.get("/schedule/TRE/schedule?orig=Trenton&direction=3")
        assert request.status_code == 400

    def test_invalid_station_for_line(self):
        # Airport line does not have a stop at Trenton
        request = self.client.get("/schedule/AIR/schedule?orig=Trenton&direction=0")
        assert request.status_code == 400

    def test_invalid_dest_for_line(self):
        # Trenton line does have the Trenton station, but not the Eastwick station
        request = self.client.get("/schedule/TRE/schedule?orig=Trenton&dest=Eastwick&direction=0")
        assert request.status_code == 400

    def test_dest_cannot_be_behind_orig_inbound(self):
        # You cannot go from 30th Street to Trenton if you are traveling into the city (direction = 0)
        request = self.client.get(
            "/schedule/TRE/schedule?orig=Gray 30th Street&dest=Trenton&direction=0"
        )
        assert request.status_code == 400

    def test_dest_cannot_be_behind_orig_outbound(self):
        # You cannot go from Trenton to 30th Street if you are traveling away from the city (direction = 1)
        request = self.client.get(
            "/schedule/TRE/schedule?orig=Trenton&dest=Gray 30th Street&direction=1"
        )
        assert request.status_code == 400
