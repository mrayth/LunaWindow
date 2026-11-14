# Use of AI

AI tools were a core part of how we built LunaWindow, and we want to be clear about how.

Team role: we chose the challenge and the idea (a landing-site forecast with a mission-delay simulator), wrote the requirements, the architecture and the code style, set the milestones, reviewed and tested each one, deployed the app, and made every design decision.

AI role: Claude Code (Claude Sonnet) wrote the Python code from our specifications, one milestone at a time. Claude Opus and Claude Fable helped us plan, check the science (lunar reference frames, horizon geometry) and verify landing-site coordinates against their sources. Claude helped draft the README, the slides and this text, which we then reviewed.

How we checked the AI's work: automated tests (Tests.py) and a comparison against NASA/JPL Horizons at 3 sites, 5 dates and 2 bodies. The worst difference was 0.000066 degrees. We did not trust any output without these checks.

No AI-generated images are used. Every figure is drawn by our code from NASA data. AI use is also marked in the git commit metadata and in AI_USE.md.
