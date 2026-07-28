import datetime
import time
from typing import Optional, OrderedDict

import requests

from septum.enums import Direction


class ScheduleGenerator:
    STOPS_URL = "https://flat-api.septa.org/stops/{}/stops.json"
    SCHEDULE_URL = "https://flat-api.septa.org/schedules/stops/{}/{}/schedule.json"
    CALENDAR_URL = "https://flat-api.septa.org/calendar.json"
    CALENDAR_TTL = 3600
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

    # (monotonic timestamp, {"YYYYMMDD": ["SID...", ...]}) shared by every instance
    _calendar: Optional[tuple[float, dict[str, list[str]]]] = None

    @classmethod
    def _get_calendar(cls) -> dict[str, list[str]]:
        """
        Fetches septa's calendar, which maps each date to the service_ids running
        that day. Cached for CALENDAR_TTL since it only changes on a new release.
        """
        cached = cls._calendar
        if cached is not None and (time.monotonic() - cached[0]) < cls.CALENDAR_TTL:
            return cached[1]

        try:
            raw = requests.get(cls.CALENDAR_URL, timeout=10).json()
        except requests.RequestException:
            if cached is not None:
                return cached[1]  # better a stale calendar than no schedules at all
            raise

        calendar = {
            date: [sid for sid in entry.get("service_id", []) if sid.startswith("SID")]
            for date, entry in raw.items()
        }
        cls._calendar = (time.monotonic(), calendar)
        return calendar

    @classmethod
    def get_service_ids(cls) -> tuple[list[str], list[str]]:
        """
        Works out which service_ids are weekday ones and which are weekend ones
        for the schedule currently in effect.

        Returns:
            tuple: (weekday service_ids, weekend service_ids)

        Note:
            These used to be hardcoded, which meant updating them by hand every
            time septa cut a release. The calendar tells us which service_ids run
            on a given date, so the day of the week that date lands on is all we
            actually need to tell weekday and weekend apart.

            septa also rotates variants between weeks (one gets swapped out for
            another for a stretch of days), and those variants disagree about a
            handful of late night trains. So each bucket comes from a single
            upcoming date rather than everything in the feed, which would splice
            two different weeks' timetables together.
        """
        calendar = cls._get_calendar()
        today = datetime.date.today()
        dates = sorted(datetime.datetime.strptime(date, "%Y%m%d").date() for date in calendar)

        def ids_on(target: datetime.date) -> set[str]:
            return set(calendar.get(target.strftime("%Y%m%d"), []))

        def soonest(*days: int) -> Optional[datetime.date]:
            matching = [date for date in dates if date.weekday() in days]
            upcoming = [date for date in matching if date >= today]

            # fall back to the most recent past date if the feed has gone stale
            if upcoming:
                return upcoming[0]
            return matching[-1] if matching else None

        weekday_date = soonest(0, 1, 2, 3, 4)
        weekday = ids_on(weekday_date) if weekday_date is not None else set()

        # Saturday and Sunday get their own service_ids and don't always agree,
        # so take both, but anchor them to the same Saturday. Otherwise asking on
        # a Sunday would pair today with next weekend's Saturday and splice two
        # different weeks together.
        weekend_date = soonest(5, 6)
        weekend: set[str] = set()
        if weekend_date is not None:
            saturday = weekend_date - datetime.timedelta(days=weekend_date.weekday() - 5)
            weekend = ids_on(saturday) | ids_on(saturday + datetime.timedelta(days=1))

        return sorted(weekday), sorted(weekend)

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

        # First one is for weekdays, second one is for weekends. Both are lists
        # because a single day can have more than one service_id attached to it
        service_ids = self.get_service_ids()
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
