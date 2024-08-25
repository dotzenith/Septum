import requests

EXAMPLE_SCHEDULE = "https://flat-api.septa.org/schedules/stops/TRE/90701/schedule.json"


class ScheduleGenerator:
    STOPS_URL = "https://flat-api.septa.org/stops/{}/stops.json"
    SCHEDULE_URL = "https://flat-api.septa.org/schedules/stops/{}/{}/schedule.json"
    LINES = [
        "AIR",
        "CHE",
        "CHW",
        "CYN",
        "FOX",
        "LAN",
        "MED",
        "NOR",
        "PAO",
        "TRE",
        "WAR",
        "WIL",
        "WTR",
    ]

    def get_lines(self) -> list[str]:
        """
        Gets the abbreviated for each line supported by the API
        """
        return self.LINES

    def get_stations_for_line(self, line: str) -> list[dict[str, str]]:
        """
        Retrieves the list of stops for a specified regional rail line.

        Args:
            line (str): The name of the regional rail line (e.g., "TRE").

        Returns:
            list: A list of dictionaries, with stop ID and name.
        """
        stops = requests.get(self.STOPS_URL.format(line)).json()
        unique_stops_str = []
        for stop in stops:
            stop_str = f"{stop['stop_id']}|{stop['stop_name']}"
            if stop_str not in unique_stops_str:
                unique_stops_str.append(stop_str)

        return [
            {"stop_id": stop.split("|")[0], "stop_name": stop.split("|")[1]}
            for stop in unique_stops_str
        ]

    def get_schedule_for_station(
        self, line: str, orig: str, direction: int
    ) -> dict[str, list[dict[str, str]]]:
        """
        Retrieves and processes the train schedule for a specific stop on a given line and direction.

        Args:
            line (str): The name of the train line for which the schedule is requested (e.g., "TRE").
            stop (str): The stop ID or stop name for which the schedule is requested (e.g., "Gray 30th Street").
            direction (int): The direction of travel. 0 indicates inbound and 1 indicates outbound.

        Returns:
            dict[str, list[dict[str, str]]]: A dictionary with two keys, "weekday" and "weekend", each containing a list of
            dictionaries. Each dictionary represents a train's schedule, with:
                - "train_id": The unique identifier for the train.
                - "arrival_time": The time at which the train arrives at the specified stop.
        """

        stop_codes = [
            stop for stop in self.get_stations_for_line(line) if (stop["stop_name"] == orig)
        ]
        stop_dict = {stop["stop_name"]: stop["stop_id"] for stop in stop_codes}
        raw_schedule = requests.get(self.SCHEDULE_URL.format(line, stop_dict[orig])).json()

        service_ids = (["M1"], ["M2", "M3"])
        sorted_trains = []

        for service_id in service_ids:
            trains = [
                train
                for train in raw_schedule
                if (train["service_id"] in service_id and train["direction_id"] == direction)
            ]
            train_ids = set(train["block_id"] for train in trains)

            # Assuming release_name implies when the schedule was released
            # and when it will start applying, we should get the latest one
            most_recent = []
            for train_id in train_ids:
                same_train_id = [train for train in trains if train["block_id"] == train_id]
                most_recent.append(max(same_train_id, key=lambda x: x["release_name"]))

            most_recent = [
                {"train_id": str(train["block_id"]), "arrival_time": train["arrival_time"]}
                for train in most_recent
            ]
            sorted_trains.append(sorted(most_recent, key=lambda x: x["arrival_time"]))

        return {"weekday": sorted_trains[0], "weekend": sorted_trains[1]}

    def get_schedule_for_line(
        self, line: str, orig: str, dest: str, direction: int
    ) -> dict[str, list[dict[str, str]]]:
        """
        Retrieves the train schedule for a specific line, origin, and destination, separated by weekday and weekend.

        Args:
            line (str): The name of the train line for which the schedule is requested (e.g., "TRE").
            orig (str): The name of the origin stop (e.g., "Trenton)".
            dest (str): The name of the destination stop (e.g., "Gray 30th Street).
            direction (int): The direction of travel. 0 indicates inbound and 1 indicates outbound.

        Returns:
            dict[str, list[dict[str, str]]]: A dictionary with two keys, "weekday" and "weekend", each containing a list of
            dictionaries. Each dictionary represents a train's schedule, with:
                - "train_id": The unique identifier for the train.
                - "depart_time": The departure time from the origin stop.
                - "arrive_time": The arrival time at the destination stop.
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
            schedule = [
                {
                    "train_id": str(k),
                    "depart_time": v["arrival_time"],
                    "arrive_time": dest_flattened[k]["arrival_time"],
                }
                for k, v in orig_flattened.items()
            ]
            return sorted(schedule, key=lambda x: x["depart_time"])

        orig_schedule = self.get_schedule_for_station(line, orig, direction)
        dest_schedule = self.get_schedule_for_station(line, dest, direction)

        weekday_schedule = flatten_schedule(orig_schedule["weekday"], dest_schedule["weekday"])
        weekend_schedule = flatten_schedule(orig_schedule["weekend"], dest_schedule["weekend"])

        return {"weekday": weekday_schedule, "weekend": weekend_schedule}
