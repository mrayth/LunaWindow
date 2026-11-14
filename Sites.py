NSSDC_URL ="https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html"

SITES = [
    {
        "Name": "Apollo 11",
        "Lat": 0.67416,
        "Lon": 23.47314,
        "ElevationM": 0,
        "Agency": "NASA",
        "Note": "Near side equator: Earth is always high overhead, so the comms baseline is easy.",
        "Source": NSSDC_URL,
    },
    {
        "Name": "Apollo 17",
        "Lat": 20.1911,
        "Lon": 30.7723,
        "ElevationM": 0,
        "Agency": "NASA",
        "Note": "Near side, Taurus-Littrow valley: mid-latitude site with a steady day and night cycle.",
        "Source": NSSDC_URL,
    },
    {
        "Name": "SLIM",
        "Lat": -13.3160,
        "Lon": 25.2510,
        "ElevationM": 0,
        "Agency": "JAXA",
        "Note": "Near side, Shioli crater: recent precision landing at a low latitude.",
        "Source": "https://www.isas.jaxa.jp/en/topics/files/SLIM-press-briefing-20241226.pdf",
    },
    {
        "Name": "Chandrayaan-3",
        "Lat": -69.373,
        "Lon": 32.319,
        "ElevationM": 0,
        "Agency": "ISRO",
        "Note": "Near side, high southern latitude: the Sun stays low and nights are long.",
        "Source": "https://en.wikipedia.org/wiki/Chandrayaan-3",
    },
    {
        "Name": "IM-1 Odysseus",
        "Lat": -80.13,
        "Lon": 1.44,
        "ElevationM": 2579,
        "Agency": "Intuitive Machines / NASA CLPS",
        "Note": "Near side polar region: elevated site where the horizon dip option matters.",
        "Source": "https://www.nasa.gov/missions/lro/nasas-lro-images-intuitive-machines-odysseus-lander/",
    },
    {
        "Name": "IM-2 Athena",
        "Lat": -84.7906,
        "Lon": 29.1957,
        "ElevationM": 0,
        "Agency": "Intuitive Machines / NASA CLPS",
        "Note": "Polar, Earth hugs the horizon: the hardest comms case in the demo.",
        "Source": "https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html",
    },
    {
        "Name": "Shackleton Connecting Ridge",
        "Lat": -89.45,
        "Lon": -137.31,
        "ElevationM": 0,
        "Agency": "Artemis III candidate region",
        "Note": "Polar ridge with near-constant sunlight, the classic Artemis power site.",
        "Source": "https://www.leonarddavid.com/?p=35814",
    },
    {
        "Name": "Chang'e 4",
        "Lat": -45.4561,
        "Lon": 177.5885,
        "ElevationM": -5927,
        "Agency": "CNSA",
        "Note": "Far side: Earth is never visible, so direct-to-Earth comms are impossible.",
        "Source": "https://www.lroc.asu.edu/images/1100",
    },
    {
        "Name": "Chang'e 6",
        "Lat": -41.6385,
        "Lon": -153.9852,
        "ElevationM": -5256,
        "Agency": "CNSA",
        "Note": "Far side, Apollo basin: second far-side example where Earth never rises.",
        "Source": "https://lroc.im-ldi.com/images/1374",
    },
]


def SiteByName(Name):
    return next(Site for Site in SITES if Site["Name"] == Name)
