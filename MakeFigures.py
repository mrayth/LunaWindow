import io
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy
import pandas

import Engine
import Metrics
import Plots
import Terrain
from Sites import SITES, SiteByName

OUT_DIR = Path(__file__).parent / "Slides" / "Figures"
DPI = 200
BASE = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
LEAD_DAYS = 30
MIN_JOINT_HOURS = 72
NEAR_COLOR = "tab:blue"
FAR_COLOR = "tab:orange"


def TrackFor(Name):
    Site = SiteByName(Name)
    Start = (BASE - timedelta(days=LEAD_DAYS)).isoformat()
    return Engine.ComputeTrack(Site["Lat"], Site["Lon"], Start, 120, 10)


def SummaryAt(Track, When, Mask):
    return Metrics.Summary(Track, When, Mask, 0.0, MIN_JOINT_HOURS, "Vertical")


def ToImage(Fig):
    Buffer = io.BytesIO()
    Fig.savefig(Buffer, format="png", dpi=DPI)
    plt.close(Fig)
    Buffer.seek(0)
    return plt.imread(Buffer)


def ShowImages(Images, Ratios, Size):
    Fig, Panels = plt.subplots(1, len(Images), figsize=Size, gridspec_kw={"width_ratios": Ratios})
    for Panel, Image in zip(numpy.atleast_1d(Panels), Images):
        Panel.imshow(Image)
        Panel.axis("off")
    Fig.tight_layout()
    return Fig


def StackImages(Images, Titles, Size):
    Fig, Panels = plt.subplots(len(Images), 1, figsize=Size)
    for Panel, Image, Title in zip(Panels, Images, Titles):
        Panel.imshow(Image)
        Panel.axis("off")
        Panel.set_title(Title, fontsize=13)
    Fig.tight_layout()
    return Fig


def ProblemStrip():
    Track = TrackFor("Shackleton Connecting Ridge")
    When = datetime(2026, 11, 14, 22, tzinfo=timezone.utc)
    Mask = Metrics.FlatMask()
    Fig = Plots.HorizonStripFigure(Track, When, Mask, SummaryAt(Track, When, Mask))
    Fig.axes[0].set_title("Shackleton Connecting Ridge, 2026-11-14 22:00 UTC: the Sun skims the horizon while Earth is below it")
    return Fig


def MissionCheck():
    Track = TrackFor("IM-2 Athena")
    Mask = Metrics.FlatMask()
    Result = SummaryAt(Track, BASE, Mask)
    Verdict = Result["Verdict"]
    Dome = ToImage(Plots.SkyDomeFigure(Result))
    Strip = ToImage(Plots.HorizonStripFigure(Track, BASE, Mask, Result))
    Fig = ShowImages([Dome, Strip], [1, 1.8], (16, 6.2))
    Fig.suptitle(f"IM-2 Athena, 2026-11-15 12:00 UTC: {Verdict['Label']}. {Verdict['Reason']}", fontsize=14)
    Fig.subplots_adjust(top=0.9)
    return Fig, Verdict["Label"]


def FindFlip(Track, Mask):
    Before = SummaryAt(Track, BASE, Mask)["Verdict"]["Label"]
    for Delay in list(range(1, 31)) + list(range(-1, -31, -1)):
        After = SummaryAt(Track, BASE + timedelta(days=Delay), Mask)["Verdict"]["Label"]
        if After != Before:
            return Delay, Before, After
    return None


def TimelineImage(Track, Mask, When):
    PowerFlags = Metrics.PowerFull(Track, Mask)
    CommsFlags = Metrics.Comms(Track, Mask, 0.0)
    return ToImage(Plots.TimelineFigure(Track, When, PowerFlags, CommsFlags))


def DelayBeforeAfter():
    Track = TrackFor("IM-2 Athena")
    Mask = Metrics.FlatMask()
    Delay, Before, After = FindFlip(Track, Mask)
    Moved = BASE + timedelta(days=Delay)
    Images = [TimelineImage(Track, Mask, BASE), TimelineImage(Track, Mask, Moved)]
    Titles = [f"IM-2 Athena, delay 0 d (2026-11-15): {Before}", f"IM-2 Athena, delay {Delay:+d} d ({Moved:%Y-%m-%d}): {After}"]
    return StackImages(Images, Titles, (11, 9.5)), (Delay, Before, After)


def ValidationRows():
    Rows = pandas.read_csv(Engine.DATA_DIR / "HorizonsCheck.csv")
    Rows["AltDiff"] = Rows["AltDiff"].abs()
    Rows["AzDiff"] = Rows["AzDiff"].abs()
    return Rows.groupby(["Site", "Body"], sort=False)[["AltDiff", "AzDiff"]].max().reset_index()


def Validation():
    Rows = ValidationRows()
    Labels = [f"{textwrap.fill(Site, 14)}\n{Body}" for Site, Body in zip(Rows["Site"], Rows["Body"])]
    Spots = numpy.arange(len(Rows))
    Fig, Ax = plt.subplots(figsize=(11, 5))
    Alt = Ax.bar(Spots - 0.2, Rows["AltDiff"], 0.4, label="Elevation difference")
    Az = Ax.bar(Spots + 0.2, Rows["AzDiff"], 0.4, label="Azimuth difference")
    Ax.bar_label(Alt, fmt="%.1e", fontsize=7)
    Ax.bar_label(Az, fmt="%.1e", fontsize=7)
    Ax.axhline(0.01, color="red", linestyle="--", label="0.01 deg target")
    Ax.set_yscale("log")
    Ax.set_ylim(1e-6, 0.05)
    Ax.set_xticks(Spots)
    Ax.set_xticklabels(Labels, fontsize=8)
    Ax.set_ylabel("Largest difference over 5 dates (degrees, log scale)")
    Ax.set_title("Our Sun and Earth positions vs NASA/JPL Horizons: 30 comparisons, all far below the target")
    Ax.legend(loc="center right")
    Fig.tight_layout(rect=(0, 0.04, 1, 1))
    return Fig, float(Rows[["AltDiff", "AzDiff"]].max().max())


def Share(Flags, Index):
    return 100.0 * Metrics.Fraction(Flags, Index, 30, 10)


def TerrainVsFlat():
    Name = "Shackleton Connecting Ridge"
    Track = TrackFor(Name)
    Flat = Metrics.FlatMask()
    Real = Terrain.LoadMask(Name)
    Index = Metrics.IndexAt(Track["Utc"], BASE)
    SunFlat, SunReal = [Share(Metrics.PowerFull(Track, Mask), Index) for Mask in (Flat, Real)]
    CommsFlat, CommsReal = [Share(Metrics.Comms(Track, Mask, 0.0), Index) for Mask in (Flat, Real)]
    Fig = Plots.HorizonStripFigure(Track, BASE, Real, SummaryAt(Track, BASE, Real))
    Ax = Fig.axes[0]
    Ax.axhline(0, color="red", linestyle="--", linewidth=1.2, label="Flat horizon (ideal sphere)")
    Handles, Labels = Ax.get_legend_handles_labels()
    Ax.legend(Handles, Labels, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=8)
    Ax.set_title(f"{Name}, 30 days from 2026-11-15. Flat horizon: sunlit {SunFlat:.0f}%, comms {CommsFlat:.0f}%. LOLA terrain: sunlit {SunReal:.0f}%, comms {CommsReal:.0f}%.", fontsize=9.5)
    return Fig


def SitesMap():
    Fig, Ax = plt.subplots(figsize=(12, 6))
    Ax.axvspan(-180, -90, color="grey", alpha=0.12)
    Ax.axvspan(90, 180, color="grey", alpha=0.12)
    Ax.axhspan(-90, -80, color="tab:cyan", alpha=0.15)
    Ax.text(-175, 25, "far side", color="dimgrey")
    Ax.text(-10, 25, "near side", color="dimgrey")
    Ax.text(125, 25, "far side", color="dimgrey")
    for Site in SITES:
        Near = abs(Site["Lon"]) < 90
        Polar = Site["Lat"] <= -80
        Ax.scatter([Site["Lon"]], [Site["Lat"]], s=140 if Polar else 60, marker="*" if Polar else "o", color=NEAR_COLOR if Near else FAR_COLOR, zorder=3)
        Side = -1 if Site["Lon"] > 120 else 1
        Ax.annotate(Site["Name"], (Site["Lon"], Site["Lat"]), xytext=(8 * Side, 4), textcoords="offset points", ha="left" if Side > 0 else "right", fontsize=9)
    Ax.scatter([], [], color=NEAR_COLOR, label="Near side")
    Ax.scatter([], [], color=FAR_COLOR, label="Far side")
    Ax.scatter([], [], color="black", marker="*", s=140, label="South polar site (80°S or further south)")
    Ax.set_xlim(-180, 180)
    Ax.set_ylim(-95, 30)
    Ax.set_xlabel("Longitude (degrees east)")
    Ax.set_ylabel("Latitude (degrees)")
    Ax.set_title("Landing sites in the LunaWindow catalog")
    Ax.legend(loc="center right")
    Fig.tight_layout()
    return Fig


def Save(Fig, Name):
    Saved = Plots.SaveFigure(Fig, Name, OUT_DIR, DPI)
    print(f"{Saved.relative_to(Path(__file__).parent)}: {Saved.stat().st_size} bytes")


if __name__ == "__main__":
    Save(ProblemStrip(), "ProblemStrip.png")
    Fig, Label = MissionCheck()
    print(f"MissionCheck verdict: {Label}")
    Save(Fig, "MissionCheck.png")
    Fig, Flip = DelayBeforeAfter()
    print(f"Delay flip found: delay {Flip[0]:+d} d changes {Flip[1]} to {Flip[2]}")
    Save(Fig, "DelayBeforeAfter.png")
    Fig, Worst = Validation()
    print(f"Validation worst difference: {Worst:.6f} deg")
    Save(Fig, "Validation.png")
    Save(TerrainVsFlat(), "TerrainVsFlat.png")
    Save(SitesMap(), "Sites.png")
