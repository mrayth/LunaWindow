from datetime import datetime, timezone

import numpy

MOON_RADIUS_KM = 1737.4
SUN_RADIUS_KM = 695700.0
EARTH_RADIUS_KM = 6378.137
FRACTION_DAYS = 30


def AngularRadius(RadiusKm, DistKm):
    return numpy.degrees(numpy.arcsin(RadiusKm / DistKm))


def FlatMask():
    return numpy.zeros(360)


def DipMask(ElevationM):
    if ElevationM <= 0:
        return numpy.zeros(360)
    HeightKm = ElevationM / 1000.0
    Dip = numpy.degrees(numpy.arccos(MOON_RADIUS_KM / (MOON_RADIUS_KM + HeightKm)))
    return numpy.full(360, -Dip)


def MaskAt(Mask, Az):
    return Mask[numpy.rint(Az).astype(int) % 360]


def PowerFull(Track, Mask):
    SunRadius = AngularRadius(SUN_RADIUS_KM, Track["SunDistKm"])
    return Track["SunAlt"] - SunRadius > MaskAt(Mask, Track["SunAz"])


def PowerPartial(Track, Mask):
    SunRadius = AngularRadius(SUN_RADIUS_KM, Track["SunDistKm"])
    return Track["SunAlt"] + SunRadius > MaskAt(Mask, Track["SunAz"])


def Comms(Track, Mask, CommsMargin):
    return Track["EarthAlt"] > MaskAt(Mask, Track["EarthAz"]) + CommsMargin


def PowerIndex(SunAlt, Lit, PanelType):
    Angle = numpy.radians(SunAlt)
    if PanelType == "Vertical":
        Raw = numpy.cos(Angle)
    else:
        Raw = numpy.maximum(0.0, numpy.sin(Angle))
    return numpy.where(Lit, Raw, 0.0)


def ToUtc64(When):
    if isinstance(When, datetime) and When.tzinfo is not None:
        When = When.astimezone(timezone.utc).replace(tzinfo=None)
    return numpy.datetime64(When, "s")


def IndexAt(Utc, When):
    Gap = numpy.abs(Utc - ToUtc64(When))
    return int(numpy.clip(numpy.argmin(Gap), 0, len(Utc) - 1))


def HoursUntilFalse(Flags, Index, StepMinutes):
    if not Flags[Index]:
        return 0.0, False
    Rest = ~Flags[Index:]
    if Rest.any():
        return int(numpy.argmax(Rest)) * StepMinutes / 60.0, False
    return (len(Flags) - Index) * StepMinutes / 60.0, True


def JointWindow(PowerFlags, CommsFlags, Index, StepMinutes):
    return HoursUntilFalse(PowerFlags & CommsFlags, Index, StepMinutes)


def Fraction(Flags, Index, Days, StepMinutes):
    Count = int(round(Days * 24 * 60 / StepMinutes))
    Window = Flags[Index:Index + Count]
    if len(Window) == 0:
        return 0.0
    return float(Window.mean())


def Verdict(PowerNow, CommsNow, JointHours, MinJointHours):
    if PowerNow and CommsNow and JointHours >= MinJointHours:
        return {"Label": "GO", "Reason": f"Sun and Earth are both up for {JointHours:.0f} h, enough for the {MinJointHours:.0f} h minimum."}
    if PowerNow and CommsNow:
        return {"Label": "RISKY", "Reason": f"Sun and Earth are both up, but only for {JointHours:.0f} h, below the {MinJointHours:.0f} h minimum."}
    if not PowerNow and not CommsNow:
        return {"Label": "NO-GO", "Reason": "No power (Sun not clear of the horizon) and no direct-to-Earth comms (Earth below the horizon)."}
    if not PowerNow:
        return {"Label": "NO-GO", "Reason": "No power: the Sun is not fully above the horizon."}
    return {"Label": "NO-GO", "Reason": "No comms: Earth is below the horizon."}


def FindRuns(Flags):
    Padded = numpy.concatenate([[0], Flags.astype(numpy.int8), [0]])
    Edges = numpy.diff(Padded)
    return list(zip(numpy.where(Edges == 1)[0], numpy.where(Edges == -1)[0]))


def BestWindows(PowerFlags, CommsFlags, Utc, StartIndex, SearchDays, StepMinutes, Top=3):
    Total = len(Utc)
    SearchCount = int(round(SearchDays * 24 * 60 / StepMinutes))
    SearchEnd = min(Total, StartIndex + SearchCount)
    Windows = []
    for RunStart, RunEnd in FindRuns(PowerFlags & CommsFlags):
        Begin = max(int(RunStart), StartIndex)
        if RunEnd <= StartIndex or Begin >= SearchEnd:
            continue
        Windows.append({"Start": Utc[Begin], "Hours": (int(RunEnd) - Begin) * StepMinutes / 60.0, "Capped": int(RunEnd) == Total})
    Windows.sort(key=lambda Item: -Item["Hours"])
    return Windows[:Top]


def StepOf(Utc):
    return int((Utc[1] - Utc[0]) / numpy.timedelta64(1, "m"))


def Summary(Track, When, Mask, CommsMargin, MinJointHours, PanelType):
    Utc = Track["Utc"]
    Step = StepOf(Utc)
    Index = IndexAt(Utc, When)
    PowerFlags = PowerFull(Track, Mask)
    CommsFlags = Comms(Track, Mask, CommsMargin)
    PowerNow = bool(PowerFlags[Index])
    CommsNow = bool(CommsFlags[Index])
    SunsetHours, SunsetCapped = HoursUntilFalse(PowerFlags, Index, Step)
    EarthsetHours, EarthsetCapped = HoursUntilFalse(CommsFlags, Index, Step)
    JointHours, JointCapped = JointWindow(PowerFlags, CommsFlags, Index, Step)
    SunAlt = float(Track["SunAlt"][Index])
    return {
        "SunAlt": SunAlt,
        "SunAz": float(Track["SunAz"][Index]),
        "EarthAlt": float(Track["EarthAlt"][Index]),
        "EarthAz": float(Track["EarthAz"][Index]),
        "SunRadius": float(AngularRadius(SUN_RADIUS_KM, Track["SunDistKm"][Index])),
        "EarthRadius": float(AngularRadius(EARTH_RADIUS_KM, Track["EarthDistKm"][Index])),
        "PowerNow": PowerNow,
        "CommsNow": CommsNow,
        "PowerIndex": float(PowerIndex(SunAlt, PowerNow, PanelType)),
        "SunsetHours": SunsetHours,
        "SunsetCapped": SunsetCapped,
        "EarthsetHours": EarthsetHours,
        "EarthsetCapped": EarthsetCapped,
        "JointHours": JointHours,
        "JointCapped": JointCapped,
        "SunlitFraction": Fraction(PowerFlags, Index, FRACTION_DAYS, Step),
        "CommsFraction": Fraction(CommsFlags, Index, FRACTION_DAYS, Step),
        "Verdict": Verdict(PowerNow, CommsNow, JointHours, MinJointHours),
    }


def FormatHours(Hours, Capped):
    if Hours <= 0 and not Capped:
        return "now"
    Days, Rest = divmod(int(round(Hours)), 24)
    Text = f"{Days}d {Rest}h"
    if Capped:
        return f"at least {Text}"
    return Text


def CompareSentence(NameA, NameB, TrackA, TrackB):
    MaxA = float(TrackA["SunAlt"].max())
    MaxB = float(TrackB["SunAlt"].max())
    Gap = abs(MaxA - MaxB)
    if Gap < 0.05:
        return f"Over the whole grid the Sun peaks at about the same elevation at {NameA} ({MaxA:.1f}°) and {NameB} ({MaxB:.1f}°)."
    HighName, HighMax, LowName, LowMax = (NameA, MaxA, NameB, MaxB) if MaxA > MaxB else (NameB, MaxB, NameA, MaxA)
    return f"Over the whole grid the Sun reaches {HighMax:.1f}° at {HighName}, which is {Gap:.1f}° higher than at {LowName} ({LowMax:.1f}°)."
