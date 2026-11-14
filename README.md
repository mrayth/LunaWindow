# LunaWindow

**Sunlight and signal forecast for Moon landing sites: pick a site and a date, and get a GO / RISKY / NO-GO verdict for power and direct-to-Earth comms.**

Live app: https://lunawindow.streamlit.app

Built by Team Wildfire#8151 for the NASA Space Apps Challenge 2026, challenge "Lunar Landing Site Navigator". Built with AI assistance (Claude); see [Use of AI](#use-of-ai).

## The problem

Near the Moon's south pole the Sun climbs only a few degrees above the horizon, and Earth also sits low in the sky, so a landing site can have sunlight but no view of Earth, or the other way round. Moving the landing date by a few days, or the site by a few kilometres, can switch power and direct comms on or off. Mission planners need a fast way to ask these what-if questions before turning to heavier analysis tools.

## Features

- **Mission Check:** a verdict badge, four cards (Sun elevation, time to sunset or sunrise, Earth elevation, time to Earthset or Earthrise), a sky dome and a horizon strip. The strip shows the Sun and Earth at true angular size, with their paths over the next 30 days.
- **Timeline:** Sun and Earth elevation over time, with power and comms windows shaded.
- **Best landing windows:** a table of the longest stretches in the next 60 days where power and comms both hold.
- **Mission Delay Simulator:** a slider that moves the landing date by -30 to +30 days. Everything updates instantly, because the Sun and Earth tracks are computed once and cached.
- **Compare:** two sites side by side, with verdict, sunlit share, comms share, joint window and the Sun and Earth elevation curves.
- **LOLA terrain horizon:** for IM-2 Athena and Shackleton Connecting Ridge, a real horizon mask built from the LRO LOLA elevation map replaces the smooth-sphere horizon.

## How it works

| File | Job |
|---|---|
| `App.py` | The Streamlit app: sidebar inputs, verdict, cards and the three tabs. |
| `Engine.py` | Sun and Earth positions seen from a spot on the Moon, using Skyfield and NASA kernels in `Data/`. |
| `Metrics.py` | Pure numpy decisions: power and comms flags, countdowns, best windows, verdict. |
| `Plots.py` | All matplotlib figures. |
| `Terrain.py` | Builds and loads terrain horizon masks from the LOLA polar elevation map. |
| `Sites.py` | The catalog of nine landing sites with coordinates and sources. |
| `Validate.py` | Compares `Engine.py` with JPL Horizons and writes `Data/HorizonsCheck.csv`. |
| `Tests.py` | Plain assert tests. Prints `ALL TESTS PASSED`. |
| `MakeFigures.py` | Saves the figures used in the slides. |

The code has no comments, so here is what the main functions do.

`Engine.py`
- `SiteObserver(Lat, Lon, ElevationM)`: an observer fixed to the Moon's surface at that spot.
- `TimeGrid(StartUtc, Days, StepMinutes)`: a Skyfield time array in UTC.
- `SkyTrack(Lat, Lon, Times)`: Sun and Earth altitude, azimuth and distance at each time.
- `ComputeTrack(Lat, Lon, StartIso, Days, StepMinutes)`: the track plus a UTC array, built from plain values so Streamlit can cache it.

`Metrics.py`
- `AngularRadius(RadiusKm, DistKm)`: apparent radius of the Sun or Earth in degrees.
- `FlatMask()` and `DipMask(ElevationM)`: the ideal-sphere horizon and the elevation-dip horizon, 360 values, one per degree of azimuth.
- `PowerFull(Track, Mask)` and `PowerPartial(Track, Mask)`: the whole Sun disc, or any part of it, above the horizon.
- `Comms(Track, Mask, CommsMargin)`: Earth above the horizon plus a margin.
- `PowerIndex(SunAlt, Lit, PanelType)`: a relative power number for a vertical or horizontal panel.
- `IndexAt(Utc, When)`: the grid sample nearest to a time.
- `HoursUntilFalse(Flags, Index, StepMinutes)` and `HoursUntilTrue(...)`: hours until a condition ends or starts, and whether the grid ended first.
- `JointWindow(...)`: hours until power or comms is lost, whichever comes first.
- `Fraction(Flags, Index, Days, StepMinutes)`: share of the next days where a condition holds.
- `Verdict(...)`: GO, RISKY or NO-GO with a reason.
- `BestWindows(...)`: the longest runs where power and comms both hold.
- `Summary(...)`: everything the UI needs for one site and time.
- `FormatHours(...)` and `FormatShort(...)`: text such as `4d 6h`, `at least 60d 0h` or `≥90d`.
- `CompareSentence(...)`: one sentence comparing the maximum Sun elevation at two sites.

`Plots.py`
- `TimelineFigure(...)`: Sun and Earth elevation over time with power and comms shading.
- `SkyDomeFigure(Result)`: a polar view of where the Sun and Earth are now.
- `HorizonStripFigure(...)`: azimuth against elevation, with the horizon mask, true-size discs and 30-day paths.
- `CompareFigure(...)`: two sites on one plot.

`Terrain.py`
- `ReadLabel()`: reads the map size, scale, projection centre and units from the LOLA `.LBL` file.
- `BuildMask(Lat, Lon, MastM)`: for each of 360 azimuths, the highest terrain angle within 150 km as seen from a 2 m mast, with Moon curvature removed.
- `HasMask(Name)` and `LoadMask(Name)`: find and load the saved mask of a site.

## Conventions

- All times are UTC. The sidebar also shows the UTC+3 time as a convenience.
- Longitude is east-positive, -180 to 180. Values from 0 to 360 are wrapped.
- Azimuth is 0 at north, 90 at east, increasing clockwise.
- Altitude is geometric, measured above the horizon. The Moon has no atmosphere, so there is no refraction.
- Three horizon models:
  - **Ideal sphere** (default): a smooth Moon of radius 1737.4 km.
  - **Elevation dip** (optional checkbox): lowers the horizon of a site above the sphere by arccos(R / (R + H)), for example about 1.94 degrees at 1000 m. It does nothing for sites below the sphere.
  - **LOLA terrain** (IM-2 Athena and Shackleton Connecting Ridge): the highest terrain angle in each direction within 150 km, from the LOLA LDEM_80S_80M map (80 m per pixel), seen from a 2 m mast.
- Power means the whole Sun disc is above the horizon. Comms means the centre of Earth is above the horizon plus the CommsMargin set in "Advanced".
- The vertical panel index is cos(Sun elevation) and assumes a Sun-facing panel. The horizontal index is sin(Sun elevation).

## Verdict rule

- **GO:** power and comms are both available now, and they stay available together for at least `MinJointHours` (default 72 h).
- **RISKY:** both are available now, but the joint window is shorter than `MinJointHours`.
- **NO-GO:** power, comms, or both are missing now. The reason says which.

The app computes a 120-day grid at 10-minute steps, starting 30 days before the chosen landing date. A window still going at the end of the grid is shown with a "≥" or "at least".

## Validation

`Validate.py` compares our Sun and Earth azimuth and elevation with NASA/JPL Horizons at 3 sites, 5 dates (2026-11-15, 2026-12-01, 2027-01-10, 2027-03-20, 2027-06-21, all 12:00 UTC) and both bodies. That is 30 rows, saved in `Data/HorizonsCheck.csv`.

| Site | Body | Max elevation difference (deg) | Max azimuth difference (deg) |
|---|---|---|---|
| Apollo 11 | Sun | 0.000006 | 0.000066 |
| Apollo 11 | Earth | 0.000007 | 0.000035 |
| IM-2 Athena | Sun | 0.000009 | 0.000007 |
| IM-2 Athena | Earth | 0.000010 | 0.000007 |
| Shackleton Connecting Ridge | Sun | 0.000010 | 0.000006 |
| Shackleton Connecting Ridge | Earth | 0.000010 | 0.000007 |

Result: **PASS**. The worst difference is 0.000066 degrees, against a target of 0.01 degrees.

Terrain example, from `Terrain.py`, for the 30 days after 2026-11-15 12:00 UTC:

| Site | Sunlit, flat horizon | Sunlit, LOLA terrain | Comms, flat horizon | Comms, LOLA terrain |
|---|---|---|---|---|
| IM-2 Athena | 57.8% | 50.7% | 74.0% | 82.7% |
| Shackleton Connecting Ridge | 100.0% | 100.0% | 40.7% | 47.1% |

## Sites

| Site | Lat | Lon | Elevation (m) | Agency | Source |
|---|---|---|---|---|---|
| Apollo 11 | 0.67416 | 23.47314 | 0 | NASA | [link](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html) |
| Apollo 17 | 20.1911 | 30.7723 | 0 | NASA | [link](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html) |
| SLIM | -13.316 | 25.251 | 0 | JAXA | [link](https://www.isas.jaxa.jp/en/topics/files/SLIM-press-briefing-20241226.pdf) |
| Chandrayaan-3 | -69.373 | 32.319 | 0 | ISRO | [link](https://en.wikipedia.org/wiki/Chandrayaan-3) |
| IM-1 Odysseus | -80.13 | 1.44 | 2579 | Intuitive Machines / NASA CLPS | [link](https://www.nasa.gov/missions/lro/nasas-lro-images-intuitive-machines-odysseus-lander/) |
| IM-2 Athena | -84.7906 | 29.1957 | 0 | Intuitive Machines / NASA CLPS | [link](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html) |
| Shackleton Connecting Ridge | -89.45 | -137.31 | 0 | Artemis III candidate region | [link](https://www.leonarddavid.com/?p=35814) |
| Chang'e 4 | -45.4561 | 177.5885 | -5927 | CNSA | [link](https://www.lroc.asu.edu/images/1100) |
| Chang'e 6 | -41.6385 | -153.9852 | -5256 | CNSA | [link](https://lroc.im-ldi.com/images/1374) |

## Limitations

- Terrain horizons exist only for the two south-polar sites (IM-2 Athena at 84.8°S and Shackleton Connecting Ridge at 89.5°S). Everywhere else the horizon is a smooth sphere, so verdicts there are optimistic.
- Comms is geometry only: Earth above the horizon. It is not a link budget, and there is no antenna pointing, data rate or relay satellite.
- There is no thermal model, and power is a Sun-above-horizon test with a simple panel index, not an energy budget. Eclipses of the Sun by Earth are not modeled.
- The kernels cover 1900 to 2050.
- Site coordinates are only as accurate as the public sources linked above.

## Next steps

- Relay satellite links for sites without a direct view of Earth.
- A thermal model for the lunar night.
- A simple link budget for direct-to-Earth comms.
- Terrain masks for more sites, and for any custom coordinates.

## Run locally

Python 3.12 or newer is needed for the pinned versions in `requirements.txt`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run App.py
```

Checks:

```bash
.venv/bin/python Tests.py
.venv/bin/python Validate.py
```

`Validate.py` needs a network connection. The app itself never downloads anything: the ephemeris and kernels are in `Data/`, and the two terrain masks are saved there too.

To rebuild the terrain masks, download `LDEM_80S_80M.LBL` and `LDEM_80S_80M.IMG` (about 111 MB) from https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/ into a folder called `LolaData/` (not committed), then run `.venv/bin/python Terrain.py`. The label gives the map centre as pixel 3799.5, so that value is used. Sites north of 84°S are not supported, so that IM-2 Athena is included.

To rebuild the slide figures and the slide deck, install `python-pptx` (`.venv/bin/pip install python-pptx`), then run `.venv/bin/python MakeFigures.py` and `.venv/bin/python MakeSlides.py`. The slides are saved in `Slides/`.

To deploy on Streamlit Community Cloud, use `App.py` as the main file and Python 3.12 or newer.

## Data and library credits

- NASA/JPL DE421 planetary ephemeris (`de421.bsp`).
- NASA NAIF lunar kernels: `moon_080317.tf`, `pck00008.tpc` and `moon_pa_de421_1900-2050.bpc`.
- NASA/JPL Horizons, used for validation.
- LRO LOLA (NASA GSFC, via the PDS Geosciences Node): the LDEM_80S_80M south polar elevation map behind the terrain masks.
- Site coordinates from the sources in the table above.
- Libraries: Skyfield, Streamlit, matplotlib, numpy, pandas, astroquery and requests.

## Use of AI

This project was built with AI assistance (Claude). All code was written by an AI coding assistant from requirements written by Team Wildfire#8151, and every milestone was reviewed and tested by the team. No AI-generated images are used: every figure is drawn by our matplotlib code from NASA data. Details, including which tools did what, are in [AI_USE.md](AI_USE.md).

## License and contributors

The code is released under the MIT License (see `LICENSE`). The data files keep their own terms: NASA ephemeris, NAIF kernels, JPL Horizons output and LOLA elevation data are NASA products, generally free to reuse with credit. The terrain masks in `Data/` are derived from LOLA data.

Team Wildfire#8151: Mrayth, iceblenderr.
