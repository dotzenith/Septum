"""
A module to test the scraper endpoints
"""

# ruff: noqa: E402

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f).start()
from septum.main import app
from septum.models import BusAndTrolleyOutput, StationOutput


class TestReturnData:
    """
    A simple class for all the tests to live in
    """

    client = TestClient(app)

    def test_stations_endpoint(self):
        request = self.client.get("/api/stations")
        assert request.status_code == 200
        TypeAdapter(list[StationOutput]).validate_json(request.content)

    @pytest.mark.parametrize(
        "route",
        [
            "/api/routes/bus",
            "/api/routes/trolley",
        ],
    )
    def test_bus_and_trolley_endpoints(self, route):
        request = self.client.get(route)
        assert request.status_code == 200
        TypeAdapter(list[BusAndTrolleyOutput]).validate_json(request.content)
