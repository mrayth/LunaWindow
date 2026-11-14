from datetime import datetime, timezone

import numpy

import Engine
import Metrics
import Terrain
from Sites import SITES, SiteByName

SUN_AT_ONE_AU_KM = 149597870.7


def Close(Value, Expected, Tolerance=0.001):
    return abs(Value - Expected) < Tolerance


def HourlyUtc(Count):
    return numpy.datetime64("2026-01-01T00:00:00", "s") + numpy.arange(Count) * numpy.timedelta64(1, "h")


def Flags(Text):
    return numpy.array([Char == "1" for Char in Text])


def SyntheticTrack(SunAlt, SunAz, EarthAlt, EarthAz):
    Count = len(SunAlt)
    return {
        "SunAlt": numpy.array(SunAlt, dtype=float),
        "SunAz": numpy.array(SunAz, dtype=float),
        "SunDistKm": numpy.full(Count, SUN_AT_ONE_AU_KM),
        "EarthAlt": numpy.array(EarthAlt, dtype=float),
        "EarthAz": numpy.array(EarthAz, dtype=float),
        "EarthDistKm": numpy.full(Count, 384400.0),
        "Utc": HourlyUtc(Count),
    }


def TestAngularRadius():
    assert Close(Metrics.AngularRadius(Metrics.SUN_RADIUS_KM, SUN_AT_ONE_AU_KM), 0.2666, 0.001)
    assert Close(Metrics.AngularRadius(10.0, 10.0), 90.0)
    assert Close(Metrics.AngularRadius(Metrics.EARTH_RADIUS_KM, 384400.0), 0.9507, 0.001)


def TestMasks():
    assert Metrics.FlatMask().shape == (360,)
    assert not Metrics.FlatMask().any()
    assert Close(Metrics.DipMask(1000)[0], -1.943, 0.001)
    assert Close(Metrics.DipMask(2579)[200], -3.120, 0.001)
    assert Metrics.DipMask(2579).shape == (360,)
    assert not Metrics.DipMask(-5000).any()
    assert not Metrics.DipMask(0).any()


def TestMaskAt():
    Mask = numpy.arange(360, dtype=float)
    assert Metrics.MaskAt(Mask, 359.6) == 0
    assert Metrics.MaskAt(Mask, 10.4) == 10
    assert Metrics.MaskAt(Mask, 0.0) == 0
    assert Metrics.MaskAt(Mask, 179.6) == 180
    assert list(Metrics.MaskAt(Mask, numpy.array([359.6, 90.2]))) == [0, 90]


def TestPower():
    Track = SyntheticTrack([1.0, 0.1, -0.1, -0.5], [90, 90, 90, 90], [0, 0, 0, 0], [0, 0, 0, 0])
    assert list(Metrics.PowerFull(Track, Metrics.FlatMask())) == [True, False, False, False]
    assert list(Metrics.PowerPartial(Track, Metrics.FlatMask())) == [True, True, True, False]
    Raised = numpy.zeros(360)
    Raised[90] = 5.0
    assert list(Metrics.PowerFull(Track, Raised)) == [False, False, False, False]
    assert list(Metrics.PowerPartial(Track, Raised)) == [False, False, False, False]
    Wrapped = SyntheticTrack([1.0], [359.6], [0], [0])
    Edge = numpy.zeros(360)
    Edge[0] = 5.0
    assert not Metrics.PowerFull(Wrapped, Edge)[0]


def TestComms():
    Track = SyntheticTrack([0, 0, 0], [0, 0, 0], [0.5, 0.0, -1.0], [180, 180, 359.6])
    assert list(Metrics.Comms(Track, Metrics.FlatMask(), 0.0)) == [True, False, False]
    assert list(Metrics.Comms(Track, Metrics.FlatMask(), 1.0)) == [False, False, False]
    Edge = numpy.zeros(360)
    Edge[0] = -2.0
    assert list(Metrics.Comms(Track, Edge, 0.0)) == [True, False, True]


def TestPowerIndex():
    Lit = numpy.array([True, True, False])
    Alt = numpy.array([0.0, 60.0, 30.0])
    Vertical = Metrics.PowerIndex(Alt, Lit, "Vertical")
    Horizontal = Metrics.PowerIndex(Alt, Lit, "Horizontal")
    assert Close(Vertical[0], 1.0) and Close(Vertical[1], 0.5) and Vertical[2] == 0
    assert Close(Horizontal[0], 0.0) and Close(Horizontal[1], 0.8660) and Horizontal[2] == 0
    Negative = Metrics.PowerIndex(numpy.array([-5.0]), numpy.array([True]), "Horizontal")
    assert Negative[0] == 0


def TestIndexAt():
    Utc = HourlyUtc(10)
    assert Metrics.IndexAt(Utc, numpy.datetime64("2026-01-01T03:00:00")) == 3
    assert Metrics.IndexAt(Utc, numpy.datetime64("2026-01-01T03:20:00")) == 3
    assert Metrics.IndexAt(Utc, numpy.datetime64("2026-01-01T03:40:00")) == 4
    assert Metrics.IndexAt(Utc, numpy.datetime64("2025-12-01T00:00:00")) == 0
    assert Metrics.IndexAt(Utc, numpy.datetime64("2027-01-01T00:00:00")) == 9
    assert Metrics.IndexAt(Utc, datetime(2026, 1, 1, 5, 0, tzinfo=timezone.utc)) == 5


def TestHoursUntilFalse():
    assert Metrics.HoursUntilFalse(Flags("11101"), 0, 60) == (3.0, False)
    assert Metrics.HoursUntilFalse(Flags("11101"), 1, 30) == (1.0, False)
    assert Metrics.HoursUntilFalse(Flags("11101"), 3, 60) == (0.0, False)
    assert Metrics.HoursUntilFalse(Flags("11111"), 1, 60) == (4.0, True)
    assert Metrics.HoursUntilFalse(Flags("00000"), 2, 60) == (0.0, False)
    assert Metrics.HoursUntilFalse(Flags("00111"), 2, 60) == (3.0, True)


def TestJointWindow():
    Power = Flags("1111100")
    Earth = Flags("0111111")
    assert Metrics.JointWindow(Power, Earth, 1, 60) == (4.0, False)
    assert Metrics.JointWindow(Power, Earth, 0, 60) == (0.0, False)
    assert Metrics.JointWindow(Flags("111"), Flags("111"), 0, 60) == (3.0, True)


def TestFraction():
    Ones = Flags("1100" * 6)
    assert Close(Metrics.Fraction(Ones, 0, 1, 60), 0.5)
    assert Close(Metrics.Fraction(Flags("1111"), 0, 1, 60), 1.0)
    assert Close(Metrics.Fraction(Flags("0000"), 0, 1, 60), 0.0)
    assert Close(Metrics.Fraction(Flags("0011"), 2, 5, 60), 1.0)
    assert Metrics.Fraction(Flags("0011"), 4, 1, 60) == 0.0


def TestVerdict():
    Go = Metrics.Verdict(True, True, 100.0, 72.0)
    Risky = Metrics.Verdict(True, True, 10.0, 72.0)
    Edge = Metrics.Verdict(True, True, 72.0, 72.0)
    NoPower = Metrics.Verdict(False, True, 0.0, 72.0)
    NoComms = Metrics.Verdict(True, False, 0.0, 72.0)
    NoBoth = Metrics.Verdict(False, False, 0.0, 72.0)
    assert Go["Label"] == "GO" and Risky["Label"] == "RISKY" and Edge["Label"] == "GO"
    assert NoPower["Label"] == "NO-GO" and "power" in NoPower["Reason"].lower() and "comms" not in NoPower["Reason"].lower()
    assert NoComms["Label"] == "NO-GO" and "comms" in NoComms["Reason"].lower() and "power" not in NoComms["Reason"].lower()
    assert NoBoth["Label"] == "NO-GO" and "power" in NoBoth["Reason"].lower() and "comms" in NoBoth["Reason"].lower()


def TestBestWindows():
    Utc = HourlyUtc(12)
    Power = numpy.ones(12, dtype=bool)
    Earth = Flags("011001111011")
    Found = Metrics.BestWindows(Power, Earth, Utc, 0, 10, 60)
    assert [Item["Hours"] for Item in Found] == [4.0, 2.0, 2.0]
    assert Found[0]["Start"] == Utc[5] and not Found[0]["Capped"]
    assert Found[1]["Start"] == Utc[1] and Found[2]["Start"] == Utc[10]
    assert Found[2]["Capped"] and not Found[1]["Capped"]
    assert len(Metrics.BestWindows(Power, Earth, Utc, 0, 10, 60, Top=1)) == 1
    Running = Metrics.BestWindows(Power, Earth, Utc, 2, 10, 60)
    assert Running[0]["Start"] == Utc[5] and Running[1]["Start"] == Utc[10]
    InProgress = Metrics.BestWindows(Power, Earth, Utc, 6, 10, 60)
    assert InProgress[0]["Start"] == Utc[6] and InProgress[0]["Hours"] == 3.0
    Narrow = Metrics.BestWindows(Power, Earth, Utc, 0, 4 / 24, 60)
    assert len(Narrow) == 1 and Narrow[0]["Start"] == Utc[1]
    assert Metrics.BestWindows(Power, Flags("0" * 12), Utc, 0, 10, 60) == []
    assert Metrics.BestWindows(Flags("0" * 12), Earth, Utc, 0, 10, 60) == []


def TestFormatHours():
    assert Metrics.FormatHours(102.0, False) == "4d 6h"
    assert Metrics.FormatHours(1440.0, True) == "at least 60d 0h"
    assert Metrics.FormatHours(0.0, False) == "now"
    assert Metrics.FormatHours(5.0, False) == "0d 5h"


def TestCompareSentence():
    High = SyntheticTrack([1.0, 6.0, 2.0], [0, 0, 0], [0, 0, 0], [0, 0, 0])
    Low = SyntheticTrack([1.0, 2.0, 1.5], [0, 0, 0], [0, 0, 0], [0, 0, 0])
    Text = Metrics.CompareSentence("Alpha", "Beta", High, Low)
    assert "6.0° at Alpha" in Text and "4.0° higher than at Beta (2.0°)" in Text
    Flipped = Metrics.CompareSentence("Beta", "Alpha", Low, High)
    assert "6.0° at Alpha" in Flipped
    Same = Metrics.CompareSentence("Alpha", "Beta", High, High)
    assert "about the same" in Same




def TestSummary():
    Track = SyntheticTrack([1.0] * 6 + [-1.0] * 6, [90.0] * 12, [10.0] * 12, [180.0] * 12)
    Result = Metrics.Summary(Track, numpy.datetime64("2026-01-01T02:00:00"), Metrics.FlatMask(), 0.0, 3.0, "Vertical")
    assert Result["PowerNow"] and Result["CommsNow"]
    assert Result["SunsetHours"] == 4.0 and not Result["SunsetCapped"]
    assert Result["EarthsetHours"] == 10.0 and Result["EarthsetCapped"]
    assert Result["JointHours"] == 4.0 and not Result["JointCapped"]
    assert Result["Verdict"]["Label"] == "GO"
    assert Close(Result["PowerIndex"], numpy.cos(numpy.radians(1.0)))
    assert Close(Result["SunlitFraction"], 0.4, 0.001)
    assert Close(Result["CommsFraction"], 1.0)
    Late = Metrics.Summary(Track, numpy.datetime64("2026-01-01T08:00:00"), Metrics.FlatMask(), 0.0, 3.0, "Horizontal")
    assert not Late["PowerNow"] and Late["PowerIndex"] == 0 and Late["Verdict"]["Label"] == "NO-GO"
    assert Late["SunsetHours"] == 0.0
    for Key in ["SunAlt", "SunAz", "EarthAlt", "EarthAz", "SunRadius", "EarthRadius", "PowerNow", "CommsNow", "PowerIndex", "SunsetHours", "SunsetCapped", "EarthsetHours", "EarthsetCapped", "JointHours", "JointCapped", "SunlitFraction", "CommsFraction", "Verdict"]:
        assert Key in Result


def RealTrack(Name, StartIso, Days):
    Site = SiteByName(Name)
    return Engine.ComputeTrack(Site["Lat"], Site["Lon"], StartIso, Days, 10)


def TestCatalog():
    assert len(SITES) == 9
    for Site in SITES:
        assert set(Site) == {"Name", "Lat", "Lon", "ElevationM", "Agency", "Note", "Source"}
        assert -90 <= Site["Lat"] <= 90 and -180 <= Site["Lon"] <= 180
        assert Site["Note"] and Site["Source"].startswith("https://")


def TestTerrainMath():
    Label = {"Scale": 80.0, "RadiusM": 1737400.0, "LineOffset": 3799.5, "SampleOffset": 3799.5}
    Line, Sample = Terrain.ToPixels(Label, -90.0, 0.0)
    assert Close(float(Line), 3799.5, 1e-6) and Close(float(Sample), 3799.5, 1e-6)
    Line, Sample = Terrain.ToPixels(Label, -89.0, 90.0)
    assert Close(float(Line), 3799.5, 1e-6) and float(Sample) > 3799.5
    Line, Sample = Terrain.ToPixels(Label, -89.0, 0.0)
    assert float(Line) < 3799.5 and Close(float(Sample), 3799.5, 1e-6)
    Distances = numpy.arange(100.0, 5000.0, 100.0)
    Wall = numpy.zeros((2, len(Distances)))
    Wall[0, 9] = 100.0
    Angles = Terrain.HorizonAngle(Wall, Distances, 0.0, 1737400.0)
    assert Close(Angles[0], 5.695, 0.005) and Angles[1] < 0
    Cut = numpy.full((1, len(Distances)), 50.0)
    Cut[0, 5:] = numpy.nan
    Short = Terrain.HorizonAngle(Cut, Distances, 0.0, 1737400.0)
    assert Close(Short[0], numpy.degrees(numpy.arctan(50.0 / 100.0)), 0.01)
    assert Terrain.MaskPath("IM-2 Athena").name == "MaskIM2Athena.npy"
    assert Terrain.Supported(SiteByName("IM-2 Athena")) and Terrain.Supported(SiteByName("Shackleton Connecting Ridge"))
    assert not Terrain.Supported(SiteByName("IM-1 Odysseus")) and not Terrain.HasMask("Apollo 11")


def TestMaskFiles():
    for Site in SITES:
        if Terrain.Supported(Site):
            Mask = Terrain.LoadMask(Site["Name"])
            assert Mask.shape == (360,) and numpy.isfinite(Mask).all()
            assert -20 < Mask.min() and Mask.max() < 20


def TestRealData():
    Flat = Metrics.FlatMask()
    Apollo = RealTrack("Apollo 11", "2026-11-15T12:00:00+00:00", 120)
    assert Metrics.Comms(Apollo, Flat, 0.0).all()
    Change = RealTrack("Chang'e 4", "2026-11-15T12:00:00+00:00", 120)
    assert not Metrics.Comms(Change, Flat, 0.0).any()
    Ridge = RealTrack("Shackleton Connecting Ridge", "2026-10-16T00:00:00+00:00", 90)
    assert Metrics.PowerFull(Ridge, Flat).all()


if __name__ == "__main__":
    TestAngularRadius()
    TestMasks()
    TestMaskAt()
    TestPower()
    TestComms()
    TestPowerIndex()
    TestIndexAt()
    TestHoursUntilFalse()
    TestJointWindow()
    TestFraction()
    TestVerdict()
    TestBestWindows()
    TestFormatHours()
    TestCompareSentence()
    TestSummary()
    TestCatalog()
    TestTerrainMath()
    TestMaskFiles()
    TestRealData()
    print("ALL TESTS PASSED")
