"""
A module to test the scraper endpoints
"""

import pytest
from fastapi.testclient import TestClient

from theseptaapi.main import app


class TestReturnData:
    """
    A simple class for all the tests to live in
    """

    client = TestClient(app)

    @pytest.mark.parametrize(
        "route",
        [
            "/stations",
            "/routes/bus",
            "/routes/trolley",
        ],
    )
    def test_all_scraper_endpoints(self, route):
        request = self.client.get(route)
        assert request.status_code == 200
