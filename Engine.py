from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy
from skyfield.api import Loader, PlanetaryConstants

DATA_DIR = Path(__file__).parent / "Data"
MOON_RADIUS_KM = 1737.4
SUN_RADIUS_KM = 695700.0
EARTH_RADIUS_KM = 6378.137

Load = Loader(str(DATA_DIR))
Ts = Load.timescale()
Eph = Load("de421.bsp")
Pc = PlanetaryConstants()
Pc.read_text(Load("moon_080317.tf"))
Pc.read_text(Load("pck00008.tpc"))
Pc.read_binary(Load("moon_pa_de421_1900-2050.bpc"))
Frame = Pc.build_frame_named("MOON_ME_DE421")


def WrapLon(Lon):
    return (Lon + 180.0) % 360.0 - 180.0


def SiteObserver(Lat, Lon, ElevationM=0.0):
    Spot = Pc.build_latlon_degrees(Frame, Lat, WrapLon(Lon), ElevationM)
    return Eph["moon"] + Spot


def TimeGrid(StartUtc, Days, StepMinutes):
    Count = int(round(Days * 24 * 60 / StepMinutes))
    Offsets = numpy.arange(Count) * StepMinutes
    Seconds = StartUtc.second + StartUtc.microsecond / 1e6
    return Ts.utc(StartUtc.year, StartUtc.month, StartUtc.day, StartUtc.hour, StartUtc.minute + Offsets, Seconds)


def BodyTrack(Observer, Times, Body):
    Alt, Az, Dist = Observer.at(Times).observe(Eph[Body]).apparent().altaz()
    return Alt.degrees, Az.degrees, Dist.km


def SkyTrack(Lat, Lon, Times, ElevationM=0.0):
    Observer = SiteObserver(Lat, Lon, ElevationM)
    SunAlt, SunAz, SunDist = BodyTrack(Observer, Times, "sun")
    EarthAlt, EarthAz, EarthDist = BodyTrack(Observer, Times, "earth")
    return {
        "SunAlt": SunAlt,
        "SunAz": SunAz,
        "SunDistKm": SunDist,
        "EarthAlt": EarthAlt,
        "EarthAz": EarthAz,
        "EarthDistKm": EarthDist,
    }


def ParseUtc(Iso):
    Parsed = datetime.fromisoformat(Iso)
    if Parsed.tzinfo is None:
        return Parsed.replace(tzinfo=timezone.utc)
    return Parsed.astimezone(timezone.utc)


def UtcArray(StartUtc, Days, StepMinutes):
    Count = int(round(Days * 24 * 60 / StepMinutes))
    Start = numpy.datetime64(StartUtc.replace(tzinfo=None), "s")
    Steps = (numpy.arange(Count) * StepMinutes * 60).astype("timedelta64[s]")
    return Start + Steps


def ComputeTrack(Lat, Lon, StartIso, Days, StepMinutes, ElevationM=0.0):
    StartUtc = ParseUtc(StartIso)
    Times = TimeGrid(StartUtc, Days, StepMinutes)
    Track = SkyTrack(Lat, Lon, Times, ElevationM)
    Track["Utc"] = UtcArray(StartUtc, Days, StepMinutes)
    return Track


def CheckValue(Name, Value, Expected):
    Diff = abs(Value - Expected)
    Status = "OK" if Diff < 0.001 else "FAIL"
    print(f"{Name:<28}{Value:12.4f}{Expected:12.4f}{Diff:10.5f} {Status}")
    return Diff < 0.001


def CheckPoint(Label, Lat, Lon, Expected):
    Now = Ts.utc(2026, 11, 15, 12, 0, 0)
    Track = SkyTrack(Lat, Lon, Now)
    Results = [CheckValue(f"{Label} {Key}", float(Track[Key]), Value) for Key, Value in Expected.items()]
    return all(Results)


def CheckFarSide():
    Start = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
    Track = SkyTrack(-45.4561, 177.5885, TimeGrid(Start, 120, 10))
    Worst = float(Track["EarthAlt"].max())
    print(f"Chang'e 4 max EarthAlt over 120 days: {Worst:.4f} (need < -35)")
    return Worst < -35


def CheckSpeed():
    Began = perf_counter()
    Track = ComputeTrack(-84.7906, 29.1957, "2026-11-15T12:00:00+00:00", 120, 10)
    Elapsed = perf_counter() - Began
    Count = len(Track["Utc"])
    print(f"ComputeTrack samples: {Count}, seconds: {Elapsed:.2f}, first {Track['Utc'][0]}, last {Track['Utc'][-1]}")
    return Count == 17280 and Elapsed < 5 and len(Track["SunAlt"]) == 17280


if __name__ == "__main__":
    Passed = [
        CheckPoint("Apollo 11", 0.67416, 23.47314, {"SunAlt": 5.1114, "SunAz": 91.6232, "EarthAlt": 63.0430, "EarthAz": 274.6537}),
        CheckPoint("IM-2", -84.7906, 29.1957, {"SunAlt": 2.5294, "EarthAlt": 1.4469, "EarthAz": 327.5202}),
        CheckFarSide(),
        CheckSpeed(),
    ]
    print("M1 PASS" if all(Passed) else "M1 FAIL")
