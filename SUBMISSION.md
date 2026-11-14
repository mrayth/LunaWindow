# LunaWindow: text for the Space Apps project page

Team Wildfire#8151. Challenge: Lunar Landing Site Navigator. Copy each section into the matching field.

## Project Name

LunaWindow

## High-Level Project Summary

LunaWindow is a web app that tells a mission planner, for a chosen Moon landing site and date, whether there will be sunlight for power and a direct line of sight to Earth for communications. It shows where the Sun and Earth sit relative to the local horizon, gives a GO, RISKY or NO-GO verdict with the reason, and counts down to the next sunset or sunrise and the next Earthset or Earthrise. A Mission Delay slider moves the landing date by up to 30 days either way and updates everything instantly, so teams can see how a launch slip changes the answer. For two south-polar sites the app uses a real horizon built from LRO LOLA elevation data instead of a smooth Moon. Sun and Earth positions come from NASA/JPL ephemerides and match JPL Horizons to within 0.0001 degrees.

## Link to Project Demo

PASTE GOOGLE DRIVE LINK TO LunaWindow.pdf

## Link to Final Project

- Code: https://github.com/mrayth/LunaWindow
- Live app: https://lunawindow.streamlit.app

## Detailed Project Description

**The problem.** Near the Moon's south pole the Sun climbs only a few degrees above the horizon, and Earth also sits low in the sky. A landing site can have sunlight but no view of Earth, or the other way round, and moving the landing date by a few days can switch either one off. Mission planners need a fast way to ask "what if we land on a different day?" before turning to heavier analysis tools.

**What LunaWindow does.** The user picks a landing site from a catalog of nine (Apollo 11, Apollo 17, SLIM, Chandrayaan-3, IM-1 Odysseus, IM-2 Athena, a Shackleton connecting ridge candidate region, Chang'e 4 and Chang'e 6) or enters custom coordinates, plus a date and time in UTC. The app answers three questions: is there power, is there direct-to-Earth comms, and how long until that changes. The Mission Check tab shows the verdict, four countdown cards, a sky dome and a horizon strip with the Sun and Earth drawn at true angular size. The Timeline tab shows Sun and Earth elevation over time and lists the longest windows in the next 60 days where power and comms both hold. The Compare tab puts two sites side by side. The Mission Delay Simulator is a slider from -30 to +30 days.

**How it works.** The engine uses Skyfield with the NASA/JPL DE421 ephemeris and the NAIF lunar frame and orientation kernels to compute the elevation and azimuth of the Sun and Earth from a point on the Moon's surface, on a 120-day grid with 10-minute steps. Power means the whole Sun disc is above the horizon. Comms means Earth is above the horizon, with an optional margin. The verdict is GO when both hold now and keep holding together for at least a minimum window (72 hours by default), RISKY when both hold now but for a shorter time, and NO-GO otherwise, with the missing item named. The track is computed once and cached, so moving the slider only repeats light calculations.

**Horizon models.** The app offers three. The ideal sphere is the default. An elevation-dip option lowers the horizon for sites above the reference sphere. For IM-2 Athena and Shackleton Connecting Ridge a terrain mask can be used: for each of 360 azimuths we take the highest terrain angle within 150 km in the LOLA LDEM_80S_80M map (80 m per pixel), seen from a 2 m mast, with the Moon's curvature removed.

**Results.** We compared our positions with JPL Horizons at three sites, five dates and for both the Sun and Earth: 30 comparisons. The worst difference is 0.000066 degrees, against a target of 0.01 degrees. As an example, IM-2 Athena on 2026-11-15 12:00 UTC is GO with a 360-hour joint window, and a 13-day delay turns it RISKY with 48 hours. Terrain changes the answer: over 30 days from that date, the IM-2 sunlit share falls from 57.8% to 50.7% while comms rise from 74.0% to 82.7%, and the Shackleton ridge comms share rises from 40.7% to 47.1% with sunlight staying at 100%.

**Benefits.** Planners can test dates and sites in seconds. Educators and the public can see why the poles are hard to plan for.

**Tools.** Python 3.12, Skyfield, NumPy, pandas, matplotlib, Streamlit, astroquery and requests. The app is hosted on Streamlit Community Cloud, and all figures are drawn with matplotlib.

**Limitations.** Terrain masks exist only for the two polar sites; elsewhere the horizon is a smooth sphere. Comms is geometry only, not a link budget, and there is no relay satellite or thermal model. Power is a Sun-above-horizon test, not an energy budget. The kernels cover 1900 to 2050.

## NASA Data

- JPL DE421 planetary ephemeris (`de421.bsp`): positions of the Sun, Earth and Moon. https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp
- NAIF lunar frame kernels (`moon_080317.tf`, `pck00008.tpc`, `moon_pa_de421_1900-2050.bpc`): the Moon's body-fixed frame and orientation, so a latitude and longitude on the Moon can be turned into a local horizon. https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf, https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/a_old_versions/pck00008.tpc, https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc
- JPL Horizons: the reference we validated our Sun and Earth azimuth and elevation against. https://ssd.jpl.nasa.gov/horizons/
- LRO LOLA south polar elevation map `LDEM_80S_80M` (via the PDS Geosciences Node): the source of the terrain horizon masks. https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/ and https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- NSSDC lunar landing site coordinates: Apollo 11 and Apollo 17 positions, and the IM-2 Athena position. https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html and https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html
- LROC (LRO camera) image pages: Chang'e 4 and Chang'e 6 landing coordinates. https://www.lroc.asu.edu/images/1100 and https://lroc.im-ldi.com/images/1374
- NASA LRO image of the IM-1 Odysseus lander: IM-1 landing coordinates. https://www.nasa.gov/missions/lro/nasas-lro-images-intuitive-machines-odysseus-lander/

## Space Agency Partner & Other Data

- JAXA SLIM press briefing: SLIM landing coordinates. https://www.isas.jaxa.jp/en/topics/files/SLIM-press-briefing-20241226.pdf
- ISRO Chandrayaan-3 landing coordinates, from the public article. https://en.wikipedia.org/wiki/Chandrayaan-3
- CNSA Chang'e 4 and Chang'e 6 landing coordinates, via the LROC pages listed above.
- Intuitive Machines / NASA CLPS: IM-1 and IM-2 coordinates, via the NASA pages listed above.
- Shackleton connecting ridge region (Artemis III candidate region) coordinates, from a public article. https://www.leonarddavid.com/?p=35814
- Libraries: Skyfield, NumPy, pandas, matplotlib, Streamlit, astroquery, requests and python-pptx (for the slides).

## Use of Artificial Intelligence

- All Python code was written by an AI coding assistant, Claude Code with Claude Sonnet 5.5, from requirements written by our team. Claude Opus and Claude Fable were used for planning, the science check and verifying coordinates and data formats. Claude was also used to review the work and to draft the README, the slides and this text.
- The team chose the challenge and the idea, set the requirements and the code style, reviewed and tested every milestone, deployed the app and made the final decisions.
- Correctness was checked with plain assert tests (`Tests.py`) and by validating against JPL Horizons (`Validate.py`, `Data/HorizonsCheck.csv`). AI output was not trusted without these checks.
- No AI-generated images are used. Every figure is drawn by our matplotlib code from NASA data. No numbers in the app come from an AI model.
- AI use is marked in the git commit trailers (from the third commit on), the app footer, the README, the PNG metadata, the slide file properties and `AI_USE.md` in the repository.

## References

- Live app: https://lunawindow.streamlit.app
- Code: https://github.com/mrayth/LunaWindow
- NASA NSSDC lunar landing sites: https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html
- NASA NSSDC lunar artifact impacts: https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html
- JAXA SLIM press briefing: https://www.isas.jaxa.jp/en/topics/files/SLIM-press-briefing-20241226.pdf
- Chandrayaan-3: https://en.wikipedia.org/wiki/Chandrayaan-3
- NASA LRO image of IM-1 Odysseus: https://www.nasa.gov/missions/lro/nasas-lro-images-intuitive-machines-odysseus-lander/
- Shackleton connecting ridge region: https://www.leonarddavid.com/?p=35814
- LROC Chang'e 4 page: https://www.lroc.asu.edu/images/1100
- LROC Chang'e 6 page: https://lroc.im-ldi.com/images/1374
- JPL DE421: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp
- NAIF lunar frame kernel: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf
- NAIF planetary constants kernel: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/a_old_versions/pck00008.tpc
- NAIF lunar orientation kernel: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc
- JPL Horizons: https://ssd.jpl.nasa.gov/horizons/
- JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- LRO LOLA polar elevation maps: https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
- PDS Geosciences Node, LOLA: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- Skyfield: https://rhodesmill.org/skyfield/
- Streamlit: https://streamlit.io
- Matplotlib: https://matplotlib.org
- NumPy: https://numpy.org
- Astroquery: https://astroquery.readthedocs.io
