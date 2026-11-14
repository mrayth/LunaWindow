from datetime import datetime, time, timedelta, timezone

import matplotlib.pyplot as plt
import numpy
import pandas
import streamlit as st

import Engine
import Metrics
import Plots
import Terrain
from Sites import SITES, SiteByName

GRID_DAYS = 120
STEP_MINUTES = 10
GRID_LEAD_DAYS = 30
LOCAL_OFFSET_HOURS = 3
WINDOW_SEARCH_DAYS = 60
CUSTOM = "Custom"
SPHERE = "Ideal sphere"
TERRAIN = "LOLA terrain"
NO_SITE = "None"
COUNTDOWNS = {"Sun": ("Time to sunset", "Time to sunrise"), "Earth": ("Time to Earthset", "Time to Earthrise")}
SET_HELP = {
    "Sun": "Time until the whole Sun disc is no longer above the horizon, which ends power.",
    "Earth": "Time until Earth drops below the horizon (plus any CommsMargin), which ends direct comms.",
}
RISE_HELP = {
    "Sun": "The Sun is not fully above the horizon now. Time until the whole disc is up and power returns.",
    "Earth": "Earth is below the horizon now. Time until it is up and direct comms return.",
}
FOOTER_PATH = Engine.DATA_DIR / "Footer.txt"
HORIZON_NOTE = "Real terrain can block the Sun and Earth, especially near the pole."
POLE_REASONS = [
    "Near the poles the Sun never climbs far above the horizon, so it slides around the sky at a very low angle and even a small hill can hide it.",
    "Earth also sits close to the horizon as seen from the south pole and drifts up and down with the Moon's libration, so the direct link switches on and off during the month.",
    "Because both the Sun and Earth hug the horizon, the landing day and the exact spot matter far more than they do near the equator.",
]


@st.cache_data(show_spinner="Computing Sun and Earth tracks")
def CachedTrack(Lat, Lon, StartIso, Days, StepMinutes):
    return Engine.ComputeTrack(Lat, Lon, StartIso, Days, StepMinutes)


def DefaultNow():
    if "DefaultNow" not in st.session_state:
        Now = datetime.now(timezone.utc) + timedelta(minutes=30)
        st.session_state["DefaultNow"] = Now.replace(minute=0, second=0, microsecond=0)
    return st.session_state["DefaultNow"]


def CustomSite():
    Lat = st.sidebar.number_input("Latitude (deg)", -90.0, 90.0, 0.0, format="%.5f")
    Lon = st.sidebar.number_input("Longitude (deg, east positive)", -360.0, 360.0, 0.0, format="%.5f")
    ElevationM = st.sidebar.number_input("ElevationM (m)", -10000.0, 10000.0, 0.0)
    return {"Name": CUSTOM, "Lat": Lat, "Lon": Lon, "ElevationM": ElevationM}


def SiteA():
    Choice = st.sidebar.selectbox("Site A", [Site["Name"] for Site in SITES] + [CUSTOM])
    if Choice == CUSTOM:
        return CustomSite()
    Site = SiteByName(Choice)
    st.sidebar.caption(f"{Site['Agency']}: {Site['Note']}")
    return Site


def HorizonChoice(Site):
    if not Terrain.HasMask(Site["Name"]):
        return False
    return st.sidebar.radio("Horizon", [SPHERE, TERRAIN]) == TERRAIN


def SiteB():
    Choice = st.sidebar.selectbox("Site B (optional, for Compare)", [NO_SITE] + [Site["Name"] for Site in SITES])
    if Choice == NO_SITE:
        return None
    return SiteByName(Choice)


def DateInputs():
    Default = DefaultNow()
    Left, Right = st.sidebar.columns(2)
    Day = Left.date_input("Landing date (UTC)", Default.date())
    Clock = Right.time_input("Time (UTC)", time(Default.hour, Default.minute))
    Base = datetime.combine(Day, Clock, tzinfo=timezone.utc)
    Local = Base.astimezone(timezone(timedelta(hours=LOCAL_OFFSET_HOURS)))
    st.sidebar.caption(f"UTC+{LOCAL_OFFSET_HOURS}: {Local:%Y-%m-%d %H:%M}")
    return Base


def AdvancedInputs(UseTerrain):
    with st.sidebar.expander("Advanced"):
        CommsMargin = st.slider("CommsMargin (deg)", 0.0, 5.0, 0.0, 0.1)
        MinJointHours = st.number_input("MinJointHours", 0, 2880, 72)
        PanelType = st.selectbox("PanelType", ["Vertical", "Horizontal"])
        UseDip = st.checkbox("Use site elevation (horizon dip)", False)
    return {"CommsMargin": CommsMargin, "MinJointHours": MinJointHours, "PanelType": PanelType, "UseDip": UseDip, "Terrain": UseTerrain}


def HorizonMask(Site, Settings):
    if Settings["Terrain"] and Terrain.HasMask(Site["Name"]):
        return Terrain.LoadMask(Site["Name"])
    if Settings["UseDip"]:
        return Metrics.DipMask(Site["ElevationM"])
    return Metrics.FlatMask()


def Evaluate(Site, GridStartIso, When, Settings):
    Track = CachedTrack(Site["Lat"], Site["Lon"], GridStartIso, GRID_DAYS, STEP_MINUTES)
    Mask = HorizonMask(Site, Settings)
    Result = Metrics.Summary(Track, When, Mask, Settings["CommsMargin"], Settings["MinJointHours"], Settings["PanelType"])
    return {
        "Name": Site["Name"],
        "Track": Track,
        "Mask": Mask,
        "PowerFlags": Metrics.PowerFull(Track, Mask),
        "CommsFlags": Metrics.Comms(Track, Mask, Settings["CommsMargin"]),
        "Result": Result,
    }


def ShowFigure(Fig):
    st.pyplot(Fig)
    plt.close(Fig)
    st.caption(Plots.CREDIT)


def HorizonCaption(Settings):
    Model = "Horizon model: ideal sphere"
    if Settings["Terrain"]:
        Model = "Horizon model: LOLA terrain (80 m grid, 150 km range, 2 m mast)"
    elif Settings["UseDip"]:
        Model += " (with elevation dip)"
    st.caption(f"{Model}. {HORIZON_NOTE}")


def ShowVerdict(Result):
    Label = Result["Verdict"]["Label"]
    Reason = Result["Verdict"]["Reason"]
    st.header(f"Verdict: {Label}")
    if Label == "GO":
        st.success(Reason)
    elif Label == "RISKY":
        st.warning(Reason)
    else:
        st.error(Reason)


def ElevationCard(Column, Label, Alt, Az):
    Note = f"Azimuth {Az:.1f}°. A negative elevation means the body is below the horizon."
    Column.metric(Label, f"{Alt:.1f}°", delta="Down" if Alt < 0 else None, delta_color="off", delta_arrow="off", help=Note)


def CountdownCard(Column, Result, Body, IsUp):
    SetLabel, RiseLabel = COUNTDOWNS[Body]
    Label = SetLabel if IsUp else RiseLabel
    Key = f"{Body}set" if IsUp else f"{Body}rise"
    Hours, Capped = Result[f"{Key}Hours"], Result[f"{Key}Capped"]
    Meaning = SET_HELP[Body] if IsUp else RISE_HELP[Body]
    Column.metric(Label, Metrics.FormatShort(Hours, Capped), help=f"{Meaning} A value starting with ≥ means this lasts to the end of the computed grid.")


def ShowCards(Result):
    First, Second, Third, Fourth = st.columns(4)
    ElevationCard(First, "Sun elevation", Result["SunAlt"], Result["SunAz"])
    CountdownCard(Second, Result, "Sun", Result["PowerNow"])
    ElevationCard(Third, "Earth elevation", Result["EarthAlt"], Result["EarthAz"])
    CountdownCard(Fourth, Result, "Earth", Result["CommsNow"])


def MissionTab(Mission, When, Settings):
    ShowVerdict(Mission["Result"])
    ShowCards(Mission["Result"])
    Left, Right = st.columns([1, 2])
    with Left:
        ShowFigure(Plots.SkyDomeFigure(Mission["Result"]))
    with Right:
        ShowFigure(Plots.HorizonStripFigure(Mission["Track"], When, Mission["Mask"], Mission["Result"]))
    HorizonCaption(Settings)
    with st.expander("Why is the south pole hard?"):
        for Reason in POLE_REASONS:
            st.write(Reason)


def WindowTable(Mission, When):
    Track = Mission["Track"]
    Step = Metrics.StepOf(Track["Utc"])
    Index = Metrics.IndexAt(Track["Utc"], When)
    Found = Metrics.BestWindows(Mission["PowerFlags"], Mission["CommsFlags"], Track["Utc"], Index, WINDOW_SEARCH_DAYS, Step)
    if not Found:
        st.info(f"No window with both power and comms in the next {WINDOW_SEARCH_DAYS} days.")
        return
    Rows = [{"Start (UTC)": str(numpy.datetime_as_string(Item["Start"], unit="m")).replace("T", " "), "Length": Metrics.FormatHours(Item["Hours"], Item["Capped"])} for Item in Found]
    st.table(pandas.DataFrame(Rows))


def TimelineTab(Mission, When, Settings):
    ShowFigure(Plots.TimelineFigure(Mission["Track"], When, Mission["PowerFlags"], Mission["CommsFlags"]))
    HorizonCaption(Settings)
    st.subheader(f"Best joint power and comms windows, next {WINDOW_SEARCH_DAYS} days")
    WindowTable(Mission, When)


def CompareColumn(Column, Mission):
    Result = Mission["Result"]
    Column.subheader(Mission["Name"])
    Column.metric("Verdict", Result["Verdict"]["Label"], help=Result["Verdict"]["Reason"])
    Column.metric("Sunlit, next 30 days", f"{Result['SunlitFraction']:.0%}")
    Column.metric("Comms, next 30 days", f"{Result['CommsFraction']:.0%}")
    Column.metric("Joint window", Metrics.FormatHours(Result["JointHours"], Result["JointCapped"]))


def CompareTab(Mission, Other, When):
    if Other is None:
        st.info("Pick a Site B in the sidebar to compare two sites.")
        return
    Left, Right = st.columns(2)
    CompareColumn(Left, Mission)
    CompareColumn(Right, Other)
    Tracks = [Mission["Track"], Other["Track"]]
    Names = [Mission["Name"], Other["Name"]]
    ShowFigure(Plots.CompareFigure(Tracks, Names, When, "SunAlt", "Sun elevation at both sites"))
    ShowFigure(Plots.CompareFigure(Tracks, Names, When, "EarthAlt", "Earth elevation at both sites"))
    st.write(Metrics.CompareSentence(Names[0], Names[1], Tracks[0], Tracks[1]))


def Main():
    st.set_page_config(page_title="LunaWindow", layout="wide")
    st.title("LunaWindow")
    st.caption("Where are the Sun and Earth at a Moon landing site? Is there power, and is there a direct link to Earth?")
    First = SiteA()
    UseTerrain = HorizonChoice(First)
    Second = SiteB()
    Base = DateInputs()
    Delay = st.sidebar.slider("Mission Delay (days)", -30, 30, 0, 1)
    Settings = AdvancedInputs(UseTerrain)
    GridStartIso = (Base - timedelta(days=GRID_LEAD_DAYS)).isoformat()
    When = Base + timedelta(days=Delay)
    Mission = Evaluate(First, GridStartIso, When, Settings)
    Other = Evaluate(Second, GridStartIso, When, Settings) if Second else None
    st.subheader(f"{Mission['Name']} on {When:%Y-%m-%d %H:%M} UTC (delay {Delay:+d} d)")
    MissionPane, TimelinePane, ComparePane = st.tabs(["Mission Check", "Timeline", "Compare"])
    with MissionPane:
        MissionTab(Mission, When, Settings)
    with TimelinePane:
        TimelineTab(Mission, When, Settings)
    with ComparePane:
        CompareTab(Mission, Other, When)
    st.divider()
    st.caption(FOOTER_PATH.read_text().strip())


if __name__ == "__main__":
    Main()
