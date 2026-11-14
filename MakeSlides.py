from datetime import timedelta
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

import MakeFigures
import Metrics
import Terrain
from MakeFigures import BASE

SLIDES_DIR = Path(__file__).parent / "Slides"
FIGURES_DIR = SLIDES_DIR / "Figures"
DECK_PATH = SLIDES_DIR / "LunaWindow.pptx"
APP_URL = "https://lunawindow.streamlit.app"
TEAM = (Path(__file__).parent / "Data" / "Team.txt").read_text().strip()
CLOSING_LINE = "From a launch slip to a new landing window in seconds."
AI_LINE = "Built with AI assistance (Claude); details in the repo's AI_USE.md."
FONT = "Calibri"
BACKGROUND = RGBColor(0x11, 0x16, 0x24)
TEXT = RGBColor(0xF2, 0xF4, 0xF8)
ACCENT = RGBColor(0xF5, 0xB0, 0x41)
MUTED = RGBColor(0xA9, 0xB1, 0xC6)
SLIDE_WIDTH = 13.333
SLIDE_HEIGHT = 7.5
MARGIN = 0.6
TITLE_LAYOUT = 5
LINE_HEIGHT = 0.46


def NewSlide(Deck, Title):
    Slide = Deck.slides.add_slide(Deck.slide_layouts[TITLE_LAYOUT])
    Slide.background.fill.solid()
    Slide.background.fill.fore_color.rgb = BACKGROUND
    Box = Slide.shapes.title
    Box.left, Box.top, Box.width, Box.height = Inches(MARGIN), Inches(0.35), Inches(SLIDE_WIDTH - 2 * MARGIN), Inches(0.9)
    Box.text_frame.text = Title
    Box.text_frame.word_wrap = True
    Box.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    Run = Box.text_frame.paragraphs[0].runs[0]
    Run.font.name, Run.font.size, Run.font.bold, Run.font.color.rgb = FONT, Pt(36), True, ACCENT
    return Slide


def AddText(Slide, Lines, Left, Top, Width, Size=20, Color=TEXT):
    Box = Slide.shapes.add_textbox(Inches(Left), Inches(Top), Inches(Width), Inches(LINE_HEIGHT * len(Lines)))
    Frame = Box.text_frame
    Frame.word_wrap = True
    for Number, Line in enumerate(Lines):
        Paragraph = Frame.paragraphs[0] if Number == 0 else Frame.add_paragraph()
        Paragraph.space_after = Pt(6)
        Run = Paragraph.add_run()
        Run.text = Line
        Run.font.name, Run.font.size, Run.font.color.rgb = FONT, Pt(Size), Color
    return Box


def AddPicture(Slide, Name, Left, Top, MaxWidth, MaxHeight, Description):
    Width, Height = Image.open(FIGURES_DIR / Name).size
    Scale = min(MaxWidth / Width, MaxHeight / Height)
    Placed = Slide.shapes.add_picture(str(FIGURES_DIR / Name), Inches(Left + (MaxWidth - Width * Scale) / 2), Inches(Top), Inches(Width * Scale), Inches(Height * Scale))
    Placed._element.nvPicPr.cNvPr.set("descr", Description)
    return Placed


def WideSlide(Deck, Title, Lines, Name, Description):
    Slide = NewSlide(Deck, Title)
    AddText(Slide, Lines, MARGIN, 1.3, SLIDE_WIDTH - 2 * MARGIN)
    Top = 1.3 + LINE_HEIGHT * len(Lines) + 0.2
    AddPicture(Slide, Name, MARGIN, Top, SLIDE_WIDTH - 2 * MARGIN, SLIDE_HEIGHT - Top - 0.3, Description)
    return Slide


def TitleSlide(Deck):
    Slide = Deck.slides.add_slide(Deck.slide_layouts[TITLE_LAYOUT])
    Slide.background.fill.solid()
    Slide.background.fill.fore_color.rgb = BACKGROUND
    Box = Slide.shapes.title
    Box.left, Box.top, Box.width, Box.height = Inches(MARGIN), Inches(1.5), Inches(SLIDE_WIDTH - 2 * MARGIN), Inches(2.2)
    Box.text_frame.text = "LunaWindow: sunlight and signal forecast for Moon landing sites"
    Box.text_frame.word_wrap = True
    Box.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
    Run = Box.text_frame.paragraphs[0].runs[0]
    Run.font.name, Run.font.size, Run.font.bold, Run.font.color.rgb = FONT, Pt(46), True, ACCENT
    AddText(Slide, [TEAM, "Challenge: Lunar Landing Site Navigator", "NASA Space Apps Challenge 2026"], MARGIN, 4.0, SLIDE_WIDTH - 2 * MARGIN, 26)
    AddText(Slide, [f"Live app: {APP_URL}"], MARGIN, 5.8, SLIDE_WIDTH - 2 * MARGIN, 24, ACCENT)


def DelaySentence():
    Track = MakeFigures.TrackFor("IM-2 Athena")
    Flat = Metrics.FlatMask()
    Delay, Before, After = MakeFigures.FindFlip(Track, Flat)
    Result = MakeFigures.SummaryAt(Track, BASE + timedelta(days=Delay), Flat)
    return f"At IM-2 Athena, a {Delay}-day slip turns {Before} into {After}: the joint power and comms window drops to {Result['JointHours']:.0f} h, below the {MakeFigures.MIN_JOINT_HOURS} h minimum."


def DelaySlide(Deck):
    Slide = NewSlide(Deck, "Mission Delay Simulator")
    AddText(Slide, ["The launch slips, so slide the date and see the answer instantly."], MARGIN, 1.5, 4.6, 24)
    AddText(Slide, [DelaySentence()], MARGIN, 3.2, 4.6, 22, ACCENT)
    AddPicture(Slide, "DelayBeforeAfter.png", 5.5, 1.3, 7.2, 5.9, "Two timelines for IM-2 Athena. With no delay the verdict is GO. After a 13-day delay it is RISKY.")


def TerrainLine(Name, Label):
    Track = MakeFigures.TrackFor(Name)
    Index = Metrics.IndexAt(Track["Utc"], BASE)
    Real = Terrain.LoadMask(Name)
    Flat = Metrics.FlatMask()
    SunFlat, SunReal = [MakeFigures.Share(Metrics.PowerFull(Track, Mask), Index) for Mask in (Flat, Real)]
    CommsFlat, CommsReal = [MakeFigures.Share(Metrics.Comms(Track, Mask, 0.0), Index) for Mask in (Flat, Real)]
    return f"{Label}: sunlit {SunFlat:.0f}% → {SunReal:.0f}%, comms {CommsFlat:.0f}% → {CommsReal:.0f}%"


def WorstDifference():
    Rows = MakeFigures.ValidationRows()
    return float(Rows[["AltDiff", "AzDiff"]].max().max())


def BuildDeck():
    Deck = Presentation()
    Deck.slide_width, Deck.slide_height = Inches(SLIDE_WIDTH), Inches(SLIDE_HEIGHT)
    TitleSlide(Deck)
    WideSlide(Deck, "The problem", ["• At the south pole the Sun skims the horizon and Earth bobs around it.", "• A small change in date or site can flip power and comms.", "• Existing mission-analysis tools are powerful, but slow for quick what-ifs."], "ProblemStrip.png", "Horizon strip for Shackleton Connecting Ridge: the Sun is just above the horizon and Earth is below it.")
    WideSlide(Deck, "Our tool: a verdict for any site and date", ["• Pick a landing site and a date.", "• Get GO / RISKY / NO-GO, with the reason.", "• See countdowns to sunset or sunrise and to Earthset or Earthrise."], "MissionCheck.png", "Sky dome and horizon strip for IM-2 Athena with a GO verdict.")
    DelaySlide(Deck)
    WideSlide(Deck, "Real terrain matters", [TerrainLine("IM-2 Athena", "• IM-2 Athena"), TerrainLine("Shackleton Connecting Ridge", "• Shackleton ridge"), "• 30 days from 2026-11-15, flat horizon → LOLA terrain horizon.", "• Terrain can hide the Sun or open up the view to Earth."], "TerrainVsFlat.png", "Horizon strip for Shackleton Connecting Ridge with the flat horizon and the LOLA terrain mask.")
    WideSlide(Deck, "Validated against JPL Horizons", [f"• Worst difference: {WorstDifference():.6f}° (target 0.01°) over 30 comparisons.", "• Data used: NASA/JPL DE421, NASA NAIF lunar kernels, LRO LOLA."], "Validation.png", "Bar chart of the largest difference from JPL Horizons for each site and body, all far below 0.01 degrees.")
    Slide = NewSlide(Deck, "Who it helps and what's next")
    for Lines, Left in [(["Who it helps", "• Mission planners", "• Educators", "• The public"], MARGIN), (["What's next", "• Relay satellites", "• Thermal model", "• Link budget", "• More sites"], 6.9)]:
        Column = AddText(Slide, Lines, Left, 1.6, 5.6, 26)
        Head = Column.text_frame.paragraphs[0].runs[0]
        Head.font.bold, Head.font.color.rgb = True, ACCENT
    Closing = AddText(Slide, [CLOSING_LINE], MARGIN, 4.7, SLIDE_WIDTH - 2 * MARGIN, 30)
    Closing.text_frame.paragraphs[0].runs[0].font.bold = True
    AddText(Slide, [APP_URL.replace("https://", "")], MARGIN, 5.5, SLIDE_WIDTH - 2 * MARGIN, 24, ACCENT)
    AddText(Slide, [AI_LINE], MARGIN, SLIDE_HEIGHT - 0.8, SLIDE_WIDTH - 2 * MARGIN, 14, MUTED)
    return Deck


def SetProperties(Deck):
    Props = Deck.core_properties
    Props.author = TEAM
    Props.last_modified_by = TEAM
    Props.title = "LunaWindow: sunlight and signal forecast for Moon landing sites"
    Props.subject = "NASA Space Apps Challenge 2026, Lunar Landing Site Navigator"
    Props.comments = "Built with AI assistance (Claude). Figures are drawn by matplotlib code from NASA data. See AI_USE.md in the repository."
    Props.keywords = "LunaWindow, Moon, landing site, AI-assisted"


if __name__ == "__main__":
    Deck = BuildDeck()
    SetProperties(Deck)
    Deck.save(DECK_PATH)
    print(f"{DECK_PATH.name}: {DECK_PATH.stat().st_size} bytes")
    print(f"slides: {len(Deck.slides)}")
    for Number, Slide in enumerate(Deck.slides, 1):
        print(f"  {Number}. {Slide.shapes.title.text_frame.text}")
