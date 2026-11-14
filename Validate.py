import re
from datetime import datetime, timezone

import numpy
import pandas
import requests
from astroquery.jplhorizons import Horizons

import Engine
from Sites import SiteByName

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
THRESHOLD_DEG = 0.01
CSV_PATH = Engine.DATA_DIR / "HorizonsCheck.csv"
SITE_NAMES = ["Apollo 11", "IM-2 Athena", "Shackleton Connecting Ridge"]
BODIES = [("Sun", "10", "sun"), ("Earth", "399", "earth")]
EPOCHS = [
    datetime(2026, 11, 15, 12, tzinfo=timezone.utc),
    datetime(2026, 12, 1, 12, tzinfo=timezone.utc),
    datetime(2027, 1, 10, 12, tzinfo=timezone.utc),
    datetime(2027, 3, 20, 12, tzinfo=timezone.utc),
    datetime(2027, 6, 21, 12, tzinfo=timezone.utc),
]


def JulianDate(Moment):
    return 2440587.5 + Moment.timestamp() / 86400.0


def HorizonsAstroquery(Code, Lat, Lon, Jds):
    Place = {"lon": Lon, "lat": Lat, "elevation": 0, "body": 301}
    Table = Horizons(id=Code, id_type=None, location=Place, epochs=Jds).ephemerides(quantities="4")
    return numpy.array(Table["AZ"], dtype=float), numpy.array(Table["EL"], dtype=float)


def HorizonsRequests(Code, Lat, Lon, Jds):
    Params = {
        "format": "text",
        "COMMAND": f"'{Code}'",
        "OBJ_DATA": "NO",
        "CENTER": "'coord@301'",
        "COORD_TYPE": "GEODETIC",
        "SITE_COORD": f"'{Lon},{Lat},0'",
        "TLIST": "\n".join(f"'{Jd}'" for Jd in Jds),
        "TLIST_TYPE": "JD",
        "QUANTITIES": "'4'",
    }
    Text = requests.get(HORIZONS_URL, params=Params, timeout=60).text
    Body = Text.split("$$SOE")[1].split("$$EOE")[0]
    Pairs = [re.findall(r"-?\d+\.\d+", Line)[-2:] for Line in Body.strip().splitlines()]
    return numpy.array([float(Pair[0]) for Pair in Pairs]), numpy.array([float(Pair[1]) for Pair in Pairs])


def HorizonsAzEl(Code, Lat, Lon, Jds):
    try:
        return HorizonsAstroquery(Code, Lat, Lon, Jds)
    except Exception as Problem:
        print(f"astroquery failed ({type(Problem).__name__}), using the requests fallback")
        return HorizonsRequests(Code, Lat, Lon, Jds)


def WrapDegrees(Diff):
    return (Diff + 180.0) % 360.0 - 180.0


def CompareBody(Site, Label, Code, EngineName, Times, Jds):
    Observer = Engine.SiteObserver(Site["Lat"], Site["Lon"])
    OurAlt, OurAz = Engine.BodyTrack(Observer, Times, EngineName)[:2]
    TheirAz, TheirAlt = HorizonsAzEl(Code, Site["Lat"], Site["Lon"], Jds)
    return pandas.DataFrame({
        "Site": Site["Name"],
        "Body": Label,
        "Epoch": [Moment.strftime("%Y-%m-%d %H:%M") for Moment in EPOCHS],
        "JulianDate": Jds,
        "EngineAz": OurAz,
        "EngineAlt": OurAlt,
        "HorizonsAz": TheirAz,
        "HorizonsAlt": TheirAlt,
        "AltDiff": OurAlt - TheirAlt,
        "AzDiff": WrapDegrees(OurAz - TheirAz),
    })


def RunChecks():
    Times = Engine.Ts.from_datetimes(EPOCHS)
    Jds = [JulianDate(Moment) for Moment in EPOCHS]
    Frames = [CompareBody(SiteByName(Name), Label, Code, EngineName, Times, Jds) for Name in SITE_NAMES for Label, Code, EngineName in BODIES]
    return pandas.concat(Frames, ignore_index=True)


def SummaryTable(Rows):
    Worst = Rows.assign(AltDiff=Rows["AltDiff"].abs(), AzDiff=Rows["AzDiff"].abs())
    Table = Worst.groupby(["Site", "Body"], sort=False)[["AltDiff", "AzDiff"]].max()
    return Table.rename(columns={"AltDiff": "MaxAltDiff", "AzDiff": "MaxAzDiff"}).reset_index()


def FinalLine(Rows):
    Size = Rows[["AltDiff", "AzDiff"]].abs().max(axis=1)
    if (Size < THRESHOLD_DEG).all():
        return f"PASS (worst difference {Size.max():.6f} deg, limit {THRESHOLD_DEG} deg)"
    return f"FAIL worst row: {Rows.loc[Size.idxmax()].to_dict()}"


if __name__ == "__main__":
    Rows = RunChecks()
    Rows.to_csv(CSV_PATH, index=False)
    print(SummaryTable(Rows).to_string(index=False, float_format=lambda Value: f"{Value:.6f}"))
    print(f"{len(Rows)} rows written to {CSV_PATH}")
    print(FinalLine(Rows))
