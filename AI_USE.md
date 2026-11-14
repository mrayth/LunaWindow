# Use of AI in LunaWindow

Team Wildfire#8151 used AI assistance to build LunaWindow for the NASA Space Apps Challenge 2026 (challenge: Lunar Landing Site Navigator). This page says where and how AI was used.

## Short version

- All Python code in this repository was written by an AI coding assistant (Claude Code, model Claude Sonnet 5.5) from requirements written by the team.
- The README, this page, the slides and the submission text were drafted with Claude and reviewed by the team.
- No AI-generated images are used anywhere. Every figure is drawn by our matplotlib code from NASA data.
- No numbers in the app come from an AI model. Sun and Earth positions are computed from NASA/JPL ephemerides, and horizon masks are computed from LRO LOLA elevation data.

## Tools and what each was used for

| Tool | Used for |
|---|---|
| Claude Opus and Claude Fable | Planning the project, the science check (geometry, conventions, what the verdict should mean) and verifying coordinates and data formats. |
| Claude Code with Claude Sonnet 5.5 | Writing all the code: `Engine.py`, `Metrics.py`, `Plots.py`, `Sites.py`, `Terrain.py`, `Validate.py`, `Tests.py`, `App.py` and `MakeFigures.py`, plus running the tests and checks. |
| Claude | Reviewing the work, and drafting the README, this page, the slides and the submission text. |

## What the team did

- Chose the challenge and the idea.
- Set the requirements: the features, the verdict rule, the conventions (UTC, east-positive longitude, azimuth clockwise from north) and the strict code style (PascalCase names, no comments).
- Reviewed and tested every milestone before allowing the next one, and made the final decisions.
- Created the GitHub repository and deployed the app on Streamlit Community Cloud.

## How correctness was checked

- `Tests.py` holds plain assert tests for every function in `Metrics.py` and `Terrain.py`, including edge cases, plus real-data checks (Apollo 11 always has Earth in view, Chang'e 4 never does, the Shackleton ridge is sunlit for 90 days).
- `Validate.py` compares our Sun and Earth azimuth and elevation with NASA/JPL Horizons for 3 sites, 5 dates and 2 bodies (30 rows, saved in `Data/HorizonsCheck.csv`). The worst difference is 0.000066 degrees, against a target of 0.01 degrees.
- The terrain projection was checked against known craters (Haworth, Shoemaker, Faustini): the right orientation gives their expected depths, and flipped or mirrored orientations do not.
- AI can make mistakes, so none of the above was left to the AI's own word: the checks run against NASA reference data.

## Where AI-generated material is marked

- Git commits made from `bc184a7` onward end with a `Co-Authored-By: Claude` trailer that names the model. The first two commits (`ab3e096`, `5095c99`) were made before this rule and do not carry the trailer, but the code in them was written by the same assistant.
- The app footer says it was built with AI assistance, and links to the README.
- Figures saved by our code carry a PNG metadata description that says they were drawn by AI-assisted code from NASA data.
- The README has a short "Use of AI" section that links to this page.

## Data files

| File | Origin |
|---|---|
| `Data/de421.bsp`, `Data/moon_080317.tf`, `Data/pck00008.tpc`, `Data/moon_pa_de421_1900-2050.bpc` | NASA/JPL and NASA NAIF files, downloaded unchanged. |
| `Data/HorizonsCheck.csv` | Produced by `Validate.py` (AI-written code) from JPL Horizons output. |
| `Data/MaskIM2Athena.npy`, `Data/MaskShackletonConnectingRidge.npy` | Produced by `Terrain.py` (AI-written code) from the LRO LOLA LDEM_80S_80M elevation map. |
| `Data/Footer.txt` | The app footer text. |

Site coordinates in `Sites.py` come from the public sources linked there, not from an AI model.
