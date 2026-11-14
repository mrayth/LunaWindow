# LunaWindow

Lunar Landing Site Navigator, built for the NASA Space Apps Challenge 2026.

Pick a Moon landing site and a date. LunaWindow shows where the Sun and Earth are relative to the horizon and answers three questions: is there power, is there direct-to-Earth comms, and how long until that changes. A "Mission Delay" slider moves the landing date by -30 to +30 days and everything updates instantly.

## How to run

Python 3.12 or newer is needed for the pinned versions in `requirements.txt`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run App.py
```

Run the checks:

```bash
.venv/bin/python Tests.py
.venv/bin/python Engine.py
.venv/bin/python Validate.py
```

`Validate.py` needs a network connection. The app itself never downloads anything: the ephemeris and lunar kernels are in `Data/`.

## What each file does

| File | Job |
|---|---|
| `App.py` | The Streamlit app: sidebar inputs, verdict, metric cards and the three tabs. |
| `Engine.py` | Sun and Earth positions seen from a spot on the Moon, using Skyfield and the NASA kernels in `Data/`. |
| `Metrics.py` | Pure numpy decisions: power and comms flags, time until they end, best windows, verdict. |
| `Plots.py` | All matplotlib figures. Run it to save sample PNGs. |
| `Sites.py` | The catalog of nine landing sites with coordinates, notes and sources. |
| `Validate.py` | Compares Engine against JPL Horizons and writes `Data/HorizonsCheck.csv`. |
| `Tests.py` | Plain assert tests. Prints `ALL TESTS PASSED`. |
| `Terrain.py` | Builds and loads real terrain horizon masks from the LOLA polar elevation map. |
| `Data/` | Kernel files, the Horizons comparison table and the two small terrain masks. |

### Main functions

`Engine.py`
- `SiteObserver(Lat, Lon, ElevationM)`: an observer fixed to the Moon's surface at that spot.
- `TimeGrid(StartUtc, Days, StepMinutes)`: a Skyfield time array in UTC.
- `SkyTrack(Lat, Lon, Times)`: Sun and Earth altitude, azimuth and distance at each time.
- `ComputeTrack(Lat, Lon, StartIso, Days, StepMinutes)`: the track plus a UTC array, built from plain values so Streamlit can cache it.

`Metrics.py`
- `AngularRadius(RadiusKm, DistKm)`: apparent radius of the Sun or Earth in degrees.
- `FlatMask()` and `DipMask(ElevationM)`: the horizon model, 360 values, one per degree of azimuth.
- `PowerFull(Track, Mask)` and `PowerPartial(Track, Mask)`: the whole Sun disc, or any part of it, above the horizon.
- `Comms(Track, Mask, CommsMargin)`: Earth above the horizon plus a margin.
- `PowerIndex(SunAlt, Lit, PanelType)`: a relative power number for a vertical or horizontal panel.
- `IndexAt(Utc, When)`: the grid sample nearest to a time.
- `HoursUntilFalse(Flags, Index, StepMinutes)`: hours until a condition ends, and whether the grid ended first.
- `JointWindow(...)`: hours until power or comms is lost, whichever comes first.
- `Fraction(Flags, Index, Days, StepMinutes)`: share of the next days where a condition holds.
- `Verdict(...)`: GO, RISKY or NO-GO with a reason.
- `BestWindows(...)`: the longest runs where power and comms both hold.
- `Summary(...)`: everything the UI needs for one site and time.
- `FormatHours(Hours, Capped)`: text such as `4d 6h` or `at least 60d 0h`.
- `CompareSentence(...)`: one sentence comparing the maximum Sun elevation at two sites.

`Terrain.py`
- `ReadLabel()`: reads the map size, scale, projection centre and units from the LOLA `.LBL` file.
- `BuildMask(Lat, Lon, MastM)`: for each of 360 azimuths, the highest terrain angle within 150 km as seen from a 2 m mast.
- `HasMask(Name)` and `LoadMask(Name)`: find and load the saved mask of a site.

`Plots.py`
- `TimelineFigure(...)`: Sun and Earth elevation over time with power and comms shading.
- `SkyDomeFigure(Result)`: a polar view of where the Sun and Earth are now.
- `HorizonStripFigure(...)`: azimuth against elevation, with the horizon mask, true-size discs and 30-day paths.
- `CompareFigure(...)`: two sites on one plot.

## Conventions

- All times are UTC. The sidebar also shows the UTC+3 time as a convenience.
- Longitude is east-positive, -180 to 180. Values from 0 to 360 are wrapped.
- Azimuth is 0 at north, 90 at east, increasing clockwise.
- Altitude is geometric, measured above the horizon. The Moon has no atmosphere, so there is no refraction.
- The horizon is an ideal sphere of radius 1737.4 km. This is a smooth Moon. Hills, crater rims and ridges are not modeled, and near the poles, where the Sun and Earth stay within a few degrees of the horizon, real terrain can matter a lot.
- The "Use site elevation (horizon dip)" option lowers the horizon of a site above the reference sphere by arccos(R / (R + H)), for example about 1.94 degrees at 1000 m. It does not lower anything for sites below the sphere (the far-side basins), and it is not a terrain model.
- The "LOLA terrain" option (IM-2 Athena and Shackleton Connecting Ridge only) replaces the sphere with a 360-value horizon mask from the LOLA south polar map (80 m per pixel). The mask is the highest terrain angle within 150 km, with Moon curvature removed, seen from 2 m above the ground at the site. Edge of the map stops a ray early.
- The vertical panel index is cos(Sun elevation) and assumes the panel always faces the Sun. The horizontal index is sin(Sun elevation).
- Power means the whole Sun disc is above the horizon. Comms means the centre of Earth is above the horizon plus the CommsMargin set in "Advanced".

## Verdict rule

- GO: power and comms are both available now, and they stay available together for at least `MinJointHours` (default 72 h).
- RISKY: both are available now, but the joint window is shorter than `MinJointHours`.
- NO-GO: power, comms, or both are missing now. The reason says which.

The app computes a 120-day grid at 10-minute steps, starting 30 days before the chosen landing date. A window that is still going at the end of the grid is reported as "at least".

## Rebuilding the terrain masks

The two masks are saved in `Data/` (`MaskIM2Athena.npy`, `MaskShackletonConnectingRidge.npy`), so the app needs nothing else. To rebuild them, download `LDEM_80S_80M.LBL` and `LDEM_80S_80M.IMG` (about 111 MB) from https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/ into a folder called `LolaData/` (not committed), then run `.venv/bin/python Terrain.py`. The script reads the label first and prints each mask's minimum, median and maximum plus the sunlit and comms share with and without terrain.

Two choices differ slightly from the usual recipe. The label gives the map centre as pixel 3799.5, so that value is used instead of 3800. And sites north of -84 degrees are not supported, so that IM-2 Athena (-84.79) is included; the map itself only reaches -80.

## Validation

`Validate.py` compares Engine against JPL Horizons at three sites (Apollo 11, IM-2 Athena, Shackleton Connecting Ridge), five dates (2026-11-15, 2026-12-01, 2027-01-10, 2027-03-20, 2027-06-21, all at 12:00 UTC) and both bodies, 30 rows in all (`Data/HorizonsCheck.csv`).

Result: PASS. The worst difference is 0.000066 degrees in azimuth and 0.00001 degrees in elevation, against a limit of 0.01 degrees.

## Deploy on Streamlit Community Cloud

1. Put the project in a GitHub repository, including the `Data/` folder (about 18 MB) and `requirements.txt`. Do not commit `.venv/`.
2. In Streamlit Community Cloud choose "New app", pick the repository and branch, and set the main file to `App.py`.
3. Under advanced settings choose Python 3.12 or newer, then deploy.

## Limitations and next steps

- Terrain exists only for two polar sites. Everywhere else the horizon is a smooth sphere, so verdicts there are optimistic. Next step: build masks for more sites, or use finer terrain data. Terrain masks ignore the Sun's and Earth's own motion and any shadows beyond 150 km.
- The kernels cover 1900 to 2050.
- Earth is treated as a point for comms. There is no antenna pointing, relay satellite or data-rate model.
- Power is a Sun-above-horizon test and a simple panel index, not an energy budget. Eclipses of the Sun by Earth are not modeled.
- Site coordinates come from the public sources listed in `Sites.py` and are only as accurate as those sources.

## Contributors

- iceblenderr

## Data credits

- NASA/JPL DE421 planetary ephemeris (`de421.bsp`).
- NASA NAIF lunar kernels: `moon_080317.tf`, `pck00008.tpc` and `moon_pa_de421_1900-2050.bpc`.
- NASA/JPL Horizons, used for validation.
- LOLA / LRO (NASA GSFC, PDS Geosciences Node): the LDEM_80S_80M south polar elevation map behind the terrain masks.
- Site coordinates from the sources listed in `Sites.py`.
- Libraries: Skyfield, Streamlit, matplotlib, numpy, pandas, astroquery and requests.
