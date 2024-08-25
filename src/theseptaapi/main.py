from fastapi import FastAPI

import theseptaapi.scrapers as scrapers

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/stations")
def get_stations() -> dict[str, str]:
    return scrapers.get_station_names()

@app.get("/routes/bus")
def get_bus_routes() -> dict[str, str]:
    return scrapers.get_bus_routes()

@app.get("/routes/trolley")
def get_trolley_routes() -> dict[str, str]:
    return scrapers.get_trolley_routes()
