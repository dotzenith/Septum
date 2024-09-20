from typing import Optional, OrderedDict

import requests

from septum.enum import Direction


class ScheduleGenerator:
    STOPS_URL = "https://flat-api.septa.org/stops/{}/stops.json"
    SCHEDULE_URL = "https://flat-api.septa.org/schedules/stops/{}/{}/schedule.json"
    LINES = [
        {"line_code": "AIR", "line_name": "Airport"},
        {"line_code": "CHE", "line_name": "Chestnut Hill East"},
        {"line_code": "CHW", "line_name": "Chestnut Hill West"},
        {"line_code": "CYN", "line_name": "Cynwyd"},
        {"line_code": "FOX", "line_name": "Fox Chase"},
        {"line_code": "LAN", "line_name": "Lansdale/Doylestown"},
        {"line_code": "MED", "line_name": "Media/Wawa"},
        {"line_code": "NOR", "line_name": "Manayunk/Norristown"},
        {"line_code": "PAO", "line_name": "Paoli/Thorndale"},
        {"line_code": "TRE", "line_name": "Trenton"},
        {"line_code": "WAR", "line_name": "Warminster"},
        {"line_code": "WIL", "line_name": "Wilmington/Newark"},
        {"line_code": "WTR", "line_name": "West Trenton"},
    ]
    LINES_DIRECTION = {
        "AIR": {"inbound": 0, "outbound": 1},
        "CHE": {"inbound": 1, "outbound": 0},
        "CHW": {"inbound": 0, "outbound": 1},
        "CYN": {"inbound": 0, "outbound": 1},
        "FOX": {"inbound": 1, "outbound": 0},
        "LAN": {"inbound": 1, "outbound": 0},
        "MED": {"inbound": 0, "outbound": 1},
        "NOR": {"inbound": 1, "outbound": 0},
        "PAO": {"inbound": 0, "outbound": 1},
        "TRE": {"inbound": 0, "outbound": 1},
        "WAR": {"inbound": 1, "outbound": 0},
        "WIL": {"inbound": 0, "outbound": 1},
        "WTR": {"inbound": 1, "outbound": 0},
    }

    def get_lines(self) -> list[dict[str, str]]:
        """
        Gets the abbreviated for each line supported by the API
        """
        return self.LINES

    def get_stations_for_line(
        self, line: str, direction: Optional[Direction] = Direction.INBOUND
    ) -> list[dict[str, str]]:
        """
        Retrieves the list of stops for a specified regional rail line.

        Args:
            line (str): The name of the regional rail line (e.g., "TRE").
            direction (Optional[Direction]): The direction of travel. "inbound" or "outbound"

        Returns:
            list: A list of dictionaries, with stop ID and name.
        """
        if direction is None:
            direction = Direction.INBOUND

        stops = requests.get(self.STOPS_URL.format(line)).json()
        direction_int = self.LINES_DIRECTION[line][direction]

        # dict comprehension to ensure uniqueness
        hash = OrderedDict()
        for stop in stops:
            if stop["direction_id"] == direction_int:
                hash[stop["stop_id"]] = {
                    "stop_id": str(stop["stop_id"]),
                    "stop_name": stop["stop_name"],
                }

        stops_list = list(hash.values())
        return stops_list

    def get_schedule_for_station(
        self, line: str, orig: str, direction: Direction
    ) -> dict[str, list[dict[str, str]]]:
        """
        Retrieves and processes the train schedule for a specific stop on a given line and direction.

        Args:
            line (str): The name of the train line for which the schedule is requested (e.g., "TRE").
            stop (str): The stop ID or stop name for which the schedule is requested (e.g., "Gray 30th Street").
            direction (Direction): The direction of travel. "inbound" or "outbound"

        Returns:
            dict[str, list[dict[str, str]]]: A dictionary with two keys, "weekday" and "weekend", each containing a list of
            dictionaries. Each dictionary represents a train's schedule, with:
                - "train_id": The unique identifier for the train.
                - "departure_time": The time at which the train departs from the specified stop.
        """

        stop_codes = [
            stop
            for stop in self.get_stations_for_line(line, direction)
            if (stop["stop_name"] == orig)
        ]
        stop_dict = {stop["stop_name"]: stop["stop_id"] for stop in stop_codes}
        raw_schedule = requests.get(self.SCHEDULE_URL.format(line, stop_dict[orig])).json()
        direction_int = self.LINES_DIRECTION[line][direction]

        service_ids = (["M1"], ["M2", "M3"])
        sorted_trains = []

        for service_id in service_ids:
            trains = [
                train
                for train in raw_schedule
                if (train["service_id"] in service_id and train["direction_id"] == direction_int)
            ]
            train_ids = set(train["block_id"] for train in trains)

            # Assuming release_name implies when the schedule was released
            # and when it will start applying, we should get the latest one
            most_recent = []
            for train_id in train_ids:
                same_train_id = [train for train in trains if train["block_id"] == train_id]
                most_recent.append(max(same_train_id, key=lambda x: x["release_name"]))

            most_recent = [
                {"train_id": str(train["block_id"]), "departure_time": train["arrival_time"]}
                for train in most_recent
            ]
            sorted_trains.append(sorted(most_recent, key=lambda x: x["departure_time"]))

        return {"weekday": sorted_trains[0], "weekend": sorted_trains[1]}

    def get_schedule_for_line(
        self, line: str, orig: str, dest: str, direction: Direction
    ) -> dict[str, list[dict[str, str]]]:
        """
        Retrieves the train schedule for a specific line, origin, and destination, separated by weekday and weekend.

        Args:
            line (str): The name of the train line for which the schedule is requested (e.g., "TRE").
            orig (str): The name of the origin stop (e.g., "Trenton)".
            dest (str): The name of the destination stop (e.g., "Gray 30th Street).
            direction (Direction): The direction of travel. "inbound" or "outbound"

        Returns:
            dict[str, list[dict[str, str]]]: A dictionary with two keys, "weekday" and "weekend", each containing a list of
            dictionaries. Each dictionary represents a train's schedule, with:
                - "train_id": The unique identifier for the train.
                - "departure_time": The departure time from the origin stop.
                - "arrival_time": The arrival time at the destination stop.
        """

        def flatten_schedule(orig_schedule, dest_schedule):
            orig_flattened = {
                train["train_id"]: {k: v for k, v in train.items() if k != "train_id"}
                for train in orig_schedule
            }
            dest_flattened = {
                train["train_id"]: {k: v for k, v in train.items() if k != "train_id"}
                for train in dest_schedule
            }

            orig_keys = list(orig_flattened.keys())
            for key in orig_keys:
                if key not in dest_flattened.keys():
                    orig_flattened.pop(key)

            schedule = [
                {
                    "train_id": str(k),
                    "departure_time": v["departure_time"],
                    "arrival_time": dest_flattened[k]["departure_time"],
                }
                for k, v in orig_flattened.items()
            ]
            return sorted(schedule, key=lambda x: x["departure_time"])

        orig_schedule = self.get_schedule_for_station(line, orig, direction)
        dest_schedule = self.get_schedule_for_station(line, dest, direction)

        weekday_schedule = flatten_schedule(orig_schedule["weekday"], dest_schedule["weekday"])
        weekend_schedule = flatten_schedule(orig_schedule["weekend"], dest_schedule["weekend"])

        return {"weekday": weekday_schedule, "weekend": weekend_schedule}
