"""
A module to test the scraper endpoints
"""

import pytest
from fastapi.testclient import TestClient
from theseptaapi.models import StationOutput, BusAndTrolleyOutput
from pydantic import TypeAdapter

from theseptaapi.main import app


class TestReturnData:
    """
    A simple class for all the tests to live in
    """

    client = TestClient(app)

    def test_stations_endpoint(self):
        request = self.client.get("/stations")
        assert request.status_code == 200
        TypeAdapter(list[StationOutput]).validate_json(request.content)

    @pytest.mark.parametrize(
        "route",
        [
            "/routes/bus",
            "/routes/trolley",
        ],
    )
    def test_bus_and_trolley_endpoints(self, route):
        request = self.client.get(route)
        assert request.status_code == 200
        TypeAdapter(list[BusAndTrolleyOutput]).validate_json(request.content)
