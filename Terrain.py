import re
from datetime import datetime, timezone
from pathlib import Path

import numpy

import Engine
import Metrics
from Engine import DATA_DIR
from Sites import SITES

LOLA_DIR = Path(__file__).parent / "LolaData"
LABEL_PATH = LOLA_DIR / "LDEM_80S_80M.LBL"
IMAGE_PATH = LOLA_DIR / "LDEM_80S_80M.IMG"
SOUTH_LIMIT = -84.0
STEP_M = 100.0
RANGE_M = 150000.0
MAST_M = 2.0


def MaskPath(Name):
    return DATA_DIR / f"Mask{re.sub('[^A-Za-z0-9]', '', Name)}.npy"


def HasMask(Name):
    return MaskPath(Name).exists()


def LoadMask(Name):
    return numpy.load(MaskPath(Name))


def Supported(Site):
    return Site["Lat"] < SOUTH_LIMIT


def LabelValue(Text, Key):
    Found = re.search(rf"^\s*{Key}\s*=\s*(.+)$", Text, re.MULTILINE)
    return Found.group(1).split("<")[0].strip().strip('"')


def LabelNumber(Text, Key):
    return float(LabelValue(Text, Key).split()[0])


def ReadLabel():
    Text = LABEL_PATH.read_text()
    if LabelValue(Text, "SAMPLE_TYPE") != "LSB_INTEGER" or LabelNumber(Text, "SAMPLE_BITS") != 16:
        raise ValueError("Unexpected sample type in the LOLA label")
    return {
        "Lines": int(LabelNumber(Text, "LINES")),
        "Samples": int(LabelNumber(Text, "LINE_SAMPLES")),
        "Factor": LabelNumber(Text, "SCALING_FACTOR"),
        "Scale": LabelNumber(Text, "MAP_SCALE"),
        "RadiusM": LabelNumber(Text, "A_AXIS_RADIUS") * 1000.0,
        "LineOffset": LabelNumber(Text, "LINE_PROJECTION_OFFSET"),
        "SampleOffset": LabelNumber(Text, "SAMPLE_PROJECTION_OFFSET"),
    }


def OpenDem(Label):
    return numpy.memmap(IMAGE_PATH, dtype="<i2", mode="r", shape=(Label["Lines"], Label["Samples"]))


def ToPixels(Label, Lat, Lon):
    Rho = 2 * Label["RadiusM"] * numpy.tan(numpy.radians(90.0 + numpy.asarray(Lat)) / 2)
    X = Rho * numpy.sin(numpy.radians(Lon))
    Y = Rho * numpy.cos(numpy.radians(Lon))
    return Label["LineOffset"] - Y / Label["Scale"], Label["SampleOffset"] + X / Label["Scale"]


def HeightsAt(Dem, Label, Lat, Lon):
    Line, Sample = ToPixels(Label, Lat, Lon)
    Inside = (Line >= 0) & (Line <= Label["Lines"] - 1) & (Sample >= 0) & (Sample <= Label["Samples"] - 1)
    Row = numpy.clip(numpy.floor(Line), 0, Label["Lines"] - 2).astype(int)
    Col = numpy.clip(numpy.floor(Sample), 0, Label["Samples"] - 2).astype(int)
    FracRow = numpy.clip(Line - Row, 0, 1)
    FracCol = numpy.clip(Sample - Col, 0, 1)
    Top = Dem[Row, Col] * (1 - FracCol) + Dem[Row, Col + 1] * FracCol
    Bottom = Dem[Row + 1, Col] * (1 - FracCol) + Dem[Row + 1, Col + 1] * FracCol
    return numpy.where(Inside, (Top * (1 - FracRow) + Bottom * FracRow) * Label["Factor"], numpy.nan)


def RayPoints(Lat, Lon, Azimuths, Distances, RadiusM):
    Lat0 = numpy.radians(Lat)
    Bearing = numpy.radians(Azimuths)[:, None]
    Arc = (Distances / RadiusM)[None, :]
    PointLat = numpy.arcsin(numpy.sin(Lat0) * numpy.cos(Arc) + numpy.cos(Lat0) * numpy.sin(Arc) * numpy.cos(Bearing))
    Turn = numpy.arctan2(numpy.sin(Bearing) * numpy.sin(Arc) * numpy.cos(Lat0), numpy.cos(Arc) - numpy.sin(Lat0) * numpy.sin(PointLat))
    return numpy.degrees(PointLat), Lon + numpy.degrees(Turn)


def HorizonAngle(Heights, Distances, ObserverM, RadiusM):
    Inside = numpy.minimum.accumulate(numpy.isfinite(Heights), axis=1)
    Drop = Distances * Distances / (2 * RadiusM)
    Angles = numpy.degrees(numpy.arctan((Heights - ObserverM - Drop) / Distances))
    return numpy.where(Inside, Angles, -numpy.inf).max(axis=1)


def BuildMask(Lat, Lon, MastM=MAST_M):
    Label = ReadLabel()
    Dem = OpenDem(Label)
    Distances = numpy.arange(STEP_M, RANGE_M + STEP_M / 2, STEP_M)
    ObserverM = float(HeightsAt(Dem, Label, Lat, Lon)) + MastM
    PointLat, PointLon = RayPoints(Lat, Lon, numpy.arange(360), Distances, Label["RadiusM"])
    Heights = HeightsAt(Dem, Label, PointLat, PointLon)
    return HorizonAngle(Heights, Distances, ObserverM, Label["RadiusM"])


def SunlitCompare(Name, Flat, Terrain):
    Site = next(Item for Item in SITES if Item["Name"] == Name)
    Track = Engine.ComputeTrack(Site["Lat"], Site["Lon"], "2026-10-16T12:00:00+00:00", 120, 10)
    Index = Metrics.IndexAt(Track["Utc"], datetime(2026, 11, 15, 12, tzinfo=timezone.utc))
    FlatShare = Metrics.Fraction(Metrics.PowerFull(Track, Flat), Index, 30, 10)
    TerrainShare = Metrics.Fraction(Metrics.PowerFull(Track, Terrain), Index, 30, 10)
    FlatComms = Metrics.Fraction(Metrics.Comms(Track, Flat, 0.0), Index, 30, 10)
    TerrainComms = Metrics.Fraction(Metrics.Comms(Track, Terrain, 0.0), Index, 30, 10)
    print(f"  30-day sunlit from 2026-11-15 12:00 UTC: flat {FlatShare:.1%}, terrain {TerrainShare:.1%}")
    print(f"  30-day comms  from 2026-11-15 12:00 UTC: flat {FlatComms:.1%}, terrain {TerrainComms:.1%}")


if __name__ == "__main__":
    for Site in SITES:
        if not Supported(Site):
            continue
        Mask = BuildMask(Site["Lat"], Site["Lon"])
        numpy.save(MaskPath(Site["Name"]), Mask)
        print(f"{Site['Name']}: {len(Mask)} values, all finite {bool(numpy.isfinite(Mask).all())}, file {MaskPath(Site['Name']).name}")
        print(f"  mask min {Mask.min():.2f}, median {numpy.median(Mask):.2f}, max {Mask.max():.2f} deg")
        SunlitCompare(Site["Name"], Metrics.FlatMask(), Mask)
