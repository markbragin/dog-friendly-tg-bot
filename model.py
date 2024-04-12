from math import cos, sin, acos, radians

import db
from datatypes import PlaceInfo, Coordinates
from environment import ENV


def load_data() -> list[PlaceInfo]:
    data = []
    raw_data = db.fetch_all_data()
    for row in raw_data:
        data.append(PlaceInfo(
            row[0], row[1], row[2],
            Coordinates(float(row[3]), float(row[4])), row[5], None
        ))
    return data


def count_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    la1 = radians(lat1)
    la2 = radians(lat2)
    lo1 = radians(lon1)
    lo2 = radians(lon2)
    return round(acos(sin(la1)*sin(la2) + cos(la1)*cos(la2)*cos(lo1 - lo2)) * R, 2)


def get_location_info(lat: float, lon: float, chat_id: int) -> list[PlaceInfo]:
    pred = lambda val: count_distance(val.loc.lat, val.loc.lon, lat, lon)
    ordered = sorted(data, key=pred)
    res = []
    for item in ordered[:10]:
        new_item = item
        new_item.dist = count_distance(item.loc.lat, item.loc.lon, lat, lon)
        res.append(new_item)
    ENV[chat_id] = res[5:]
    return res[:5]


def get_coords_by_id(id: int) -> Coordinates | None:
    for row in data:
        if row.id == id:
            return Coordinates(row.loc.lat, row.loc.lon)


def get_more_location_info(chat_id: int) -> list[PlaceInfo] | None:
    if chat_id in ENV:
        return ENV[chat_id]
    else:
        return None


data = load_data()
print("Data fetched")
