import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

STATION_NAMES_URL = "https://www3.septa.org/VIRegionalRail.html"
BUS_AND_TROLLEY_ROUTES_URL = "https://www3.septa.org/VIBusAndTrolley.html"

def get_station_names() -> list[dict[str, str]]:
    """
    Scrapes STATION_NAMES_URL to get the inputs used by `/NextToArrive/index.php`

    Returns:
        A list of dictionaries where `station_name` is the colloquial station name and
            `parameter` is what the API expects as input for the particular station.
    """
    page = requests.get(STATION_NAMES_URL)

    if not page.status_code == 200:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch station names. The request to {STATION_NAMES_URL} returned {page.status_code}",
        )
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")
    stations = []

    for table in tables:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = [cell.get_text() for cell in row.find_all("td")]
            stations.append({"station_name": cells[0].strip(), "parameter": cells[1].strip()})

    return stations

def get_bus_routes() -> list[dict[str, str]]:
    """
    Scrapes BUS_AND_TROLLEY_ROUTES_URL to get inputs used by `/TransitView/index.php`

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given bus route,
            and `route_number` (not always a "number") is what the API expects.
    """
    page = requests.get(BUS_AND_TROLLEY_ROUTES_URL)

    if not page.status_code == 200:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch bus routes. The request to {BUS_AND_TROLLEY_ROUTES_URL} returned {page.status_code}",
        )
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")[:-1]  # The last one is trolleys
    routes = []

    for table in tables:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = [cell.get_text() for cell in row.find_all("td")]
            routes.append({"route_number": cells[0].strip(), "route_name": cells[1].strip()})

    return routes


def get_trolley_routes() -> list[dict[str, str]]:
    """
    Scrapes BUS_AND_TROLLEY_ROUTES_URL to get inputs used by `/TransitView/index.php`

    Returns:
        A list of dictionaries where `route_name` is the colloquial name of a given trolley route,
            and `route_number` is what the API expects.
    """
    page = requests.get(BUS_AND_TROLLEY_ROUTES_URL)

    if not page.status_code == 200:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch trolley routes. The request to {BUS_AND_TROLLEY_ROUTES_URL} returned {page.status_code}",
        )
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("table")
    routes = []

    # The last one is trolleys
    rows = tables[-1].find_all("tr")[1:]
    for row in rows:
        cells = [cell.get_text() for cell in row.find_all("td")]
        routes.append({"route_number": cells[0].strip(), "route_name": cells[1].strip()})

    return routes
