from pathlib import Path

import matplotlib.pyplot as plt
import numpy
from matplotlib.patches import Ellipse, Patch

import Engine
import Metrics
from Sites import SiteByName

CREDIT = "Made with Python matplotlib"
STRIP_Y_MIN = -5.0
STRIP_Y_MAX = 12.0
PATH_DAYS = 30
SUN_COLOR = "darkorange"
EARTH_COLOR = "tab:blue"
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def WindowKeep(Utc, When, WindowDays):
    Centre = Metrics.ToUtc64(When)
    Before = Centre - numpy.timedelta64(2, "D")
    After = Centre + numpy.timedelta64(int(WindowDays), "D")
    return Centre, (Utc >= Before) & (Utc <= After)


def ShadeRuns(Ax, Utc, Flags, Color):
    for First, Last in Metrics.FindRuns(Flags):
        Ax.axvspan(Utc[First], Utc[min(Last, len(Utc) - 1)], color=Color, alpha=0.2)


def TimelineFigure(Track, When, PowerFlags, CommsFlags, WindowDays=30):
    Utc = Track["Utc"]
    Centre, Keep = WindowKeep(Utc, When, WindowDays)
    Fig, Ax = plt.subplots(figsize=(11, 4.5))
    Ax.plot(Utc[Keep], Track["SunAlt"][Keep], color=SUN_COLOR, label="Sun elevation")
    Ax.plot(Utc[Keep], Track["EarthAlt"][Keep], color=EARTH_COLOR, label="Earth elevation")
    Ax.axhline(0, color="black", linewidth=0.8)
    ShadeRuns(Ax, Utc[Keep], PowerFlags[Keep], "yellow")
    ShadeRuns(Ax, Utc[Keep], CommsFlags[Keep], "blue")
    Ax.axvline(Centre, color="red", linestyle="--", label="Landing date")
    Handles, Labels = Ax.get_legend_handles_labels()
    Handles += [Patch(color="yellow", alpha=0.2), Patch(color="blue", alpha=0.2)]
    Labels += ["Power (Sun fully above horizon)", "Comms (Earth above horizon)"]
    Ax.legend(Handles, Labels, loc="upper right")
    Ax.set_xlabel("Date (UTC)")
    Ax.set_ylabel("Elevation above horizon (degrees)")
    Ax.set_title("Sun and Earth elevation over time")
    Fig.autofmt_xdate()
    Fig.tight_layout()
    return Fig


def CompareFigure(Tracks, Names, When, Key, Title, WindowDays=30):
    Utc = Tracks[0]["Utc"]
    Centre, Keep = WindowKeep(Utc, When, WindowDays)
    Fig, Ax = plt.subplots(figsize=(11, 3.8))
    for Track, Name in zip(Tracks, Names):
        Ax.plot(Utc[Keep], Track[Key][Keep], label=Name)
    Ax.axhline(0, color="black", linewidth=0.8)
    Ax.axvline(Centre, color="red", linestyle="--", label="Landing date")
    Ax.legend(loc="upper right")
    Ax.set_xlabel("Date (UTC)")
    Ax.set_ylabel("Elevation above horizon (degrees)")
    Ax.set_title(Title)
    Fig.autofmt_xdate()
    Fig.tight_layout()
    return Fig


def SkyPoint(Ax, Az, Alt, Label, Color):
    Theta = numpy.radians(Az)
    Radius = 90.0 - max(Alt, 0.0)
    Face = Color if Alt >= 0 else "none"
    Ax.scatter([Theta], [Radius], s=220, facecolors=Face, edgecolors=Color, linewidths=2, zorder=3, clip_on=False)
    Text = f"{Label} {Alt:.1f}°" if Alt >= 0 else f"{Label} {Alt:.1f}° (below horizon)"
    Ax.annotate(Text, (Theta, Radius), xytext=(10, 10), textcoords="offset points")


def SkyDomeFigure(Result):
    Fig = plt.figure(figsize=(5.5, 5.5))
    Ax = Fig.add_subplot(projection="polar")
    Ax.set_theta_zero_location("N")
    Ax.set_theta_direction(-1)
    Ax.set_rlim(0, 90)
    Ax.set_rticks([0, 30, 60, 90])
    Ax.set_yticklabels(["90°", "60°", "30°", "0° horizon"])
    Ax.set_xticks(numpy.radians(numpy.arange(0, 360, 45)))
    Ax.set_xticklabels(COMPASS)
    SkyPoint(Ax, Result["SunAz"], Result["SunAlt"], "Sun", SUN_COLOR)
    SkyPoint(Ax, Result["EarthAz"], Result["EarthAlt"], "Earth", EARTH_COLOR)
    Ax.set_title("Sky dome: centre is overhead, outer ring is the horizon", fontsize=10)
    Fig.tight_layout()
    return Fig


def BreakWraps(Az, Alt):
    Cuts = numpy.where(numpy.abs(numpy.diff(Az)) > 180)[0] + 1
    return numpy.insert(Az.astype(float), Cuts, numpy.nan), numpy.insert(Alt.astype(float), Cuts, numpy.nan)


def Disc(Ax, Az, Alt, Radius, Color, XPerY):
    for Shift in (-360, 0, 360):
        Ax.add_patch(Ellipse((Az + Shift, Alt), 2 * Radius * XPerY, 2 * Radius, facecolor=Color, edgecolor="black", zorder=3))


def OffScale(Ax, Az, Alt, Label, Color):
    Above = Alt > STRIP_Y_MAX
    Edge = STRIP_Y_MAX - 0.7 if Above else STRIP_Y_MIN + 0.7
    Ax.plot([Az], [Edge], marker="^" if Above else "v", color=Color, markersize=9, zorder=3)
    Ax.annotate(f"{Label} {Alt:.0f}° (off scale)", (Az, Edge), xytext=(8, -4), textcoords="offset points")


def StripBody(Ax, Az, Alt, Radius, Label, Color, XPerY):
    if STRIP_Y_MIN <= Alt <= STRIP_Y_MAX:
        Disc(Ax, Az, Alt, Radius, Color, XPerY)
        Ax.annotate(Label, (Az, Alt), xytext=(0, 12), textcoords="offset points", ha="center")
    else:
        OffScale(Ax, Az, Alt, Label, Color)


def HorizonStripFigure(Track, When, Mask, Result):
    Index = Metrics.IndexAt(Track["Utc"], When)
    Stop = Index + int(PATH_DAYS * 24 * 60 / Metrics.StepOf(Track["Utc"])) + 1
    Fig, Ax = plt.subplots(figsize=(10, 4.2))
    Azimuths = numpy.arange(360)
    Ax.fill_between(Azimuths, STRIP_Y_MIN, Mask, step="mid", color="grey", alpha=0.5, label="Below the horizon mask")
    Ax.step(Azimuths, Mask, where="mid", color="black", linewidth=1.2)
    for Key, Color, Label in [("Sun", SUN_COLOR, "Sun path, next 30 days"), ("Earth", EARTH_COLOR, "Earth path, next 30 days")]:
        PathAz, PathAlt = BreakWraps(Track[f"{Key}Az"][Index:Stop], Track[f"{Key}Alt"][Index:Stop])
        Ax.plot(PathAz, PathAlt, color=Color, linewidth=0.8, label=Label)
    Ax.set_xlim(0, 360)
    Ax.set_ylim(STRIP_Y_MIN, STRIP_Y_MAX)
    Ax.set_xticks(numpy.arange(0, 361, 45))
    Ax.set_xlabel("Azimuth (degrees, 0 = north, 90 = east)")
    Ax.set_ylabel("Elevation above horizon (degrees)")
    Ax.set_title("Horizon strip: Sun and Earth discs drawn at true angular size")
    Ax.legend(loc="upper right", fontsize=8)
    Fig.tight_layout()
    Box = Ax.get_window_extent()
    XPerY = (360.0 / Box.width) / ((STRIP_Y_MAX - STRIP_Y_MIN) / Box.height)
    StripBody(Ax, Result["SunAz"], Result["SunAlt"], Result["SunRadius"], "Sun", SUN_COLOR, XPerY)
    StripBody(Ax, Result["EarthAz"], Result["EarthAlt"], Result["EarthRadius"], "Earth", EARTH_COLOR, XPerY)
    return Fig


def SaveFigure(Fig, Name):
    Target = Path(__file__).parent / Name
    Fig.text(0.99, 0.01, CREDIT, ha="right", fontsize=8)
    Fig.savefig(Target, dpi=150)
    plt.close(Fig)
    return Target


def SampleCase(Name, StartIso):
    Site = SiteByName(Name)
    Track = Engine.ComputeTrack(Site["Lat"], Site["Lon"], StartIso, 120, 10)
    return Track, Metrics.FlatMask()


def Report(Saved):
    print(f"{Saved.name}: {Saved.stat().st_size} bytes")


if __name__ == "__main__":
    When = numpy.datetime64("2026-11-15T12:00:00")
    Track, Mask = SampleCase("IM-2 Athena", "2026-10-16T12:00:00+00:00")
    Report(SaveFigure(TimelineFigure(Track, When, Metrics.PowerFull(Track, Mask), Metrics.Comms(Track, Mask, 0.0)), "Timeline.png"))
    Track, Mask = SampleCase("Shackleton Connecting Ridge", "2026-10-16T12:00:00+00:00")
    Result = Metrics.Summary(Track, When, Mask, 0.0, 72, "Vertical")
    Report(SaveFigure(SkyDomeFigure(Result), "SkyDome.png"))
    Report(SaveFigure(HorizonStripFigure(Track, When, Mask, Result), "HorizonStrip.png"))
