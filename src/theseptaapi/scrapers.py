import requests
from bs4 import BeautifulSoup

STATION_NAMES_URL = "https://www3.septa.org/VIRegionalRail.html"
BUS_AND_TROLLEY_ROUTES_URL = "https://www3.septa.org/VIBusAndTrolley.html"


def get_station_names() -> dict[str, str]:
    page = requests.get(STATION_NAMES_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")
    stations = {}

    for table in tables:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = [cell.get_text() for cell in row.find_all("td")]
            stations[cells[0]] = cells[1]

    return stations


def get_bus_routes() -> dict[str, str]:
    page = requests.get(BUS_AND_TROLLEY_ROUTES_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")[:-1]  # The last one is trolleys
    routes = {}

    for table in tables:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = [cell.get_text() for cell in row.find_all("td")]
            routes[cells[0]] = cells[1]

    return routes


def get_trolley_routes() -> dict[str, str]:
    page = requests.get(BUS_AND_TROLLEY_ROUTES_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")
    routes = {}

    rows = tables[-1].find_all("tr")[1:]
    for row in rows:
        cells = [cell.get_text() for cell in row.find_all("td")]
        routes[cells[0]] = cells[1]

    return routes
