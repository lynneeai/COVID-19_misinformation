from datetime import datetime

"""
Examples:
- 2020-01-30:                  Medicine-Today

- 2020-03-25T20:07:28+00:00:   GreatGameIndia
- 2020-03-15T09:42:55+00:00:   Intellihub
- 2020-03-13T14:56:37+00:00:   JimBakkerShow
- 2020-03-16T22:26:31-05:00:   TheMindUnleashed

- March 18, 2020:              HealthImpactNews
- February 24, 2020:           NaturalHealth365
- March 23, 2020:              HumansAreFree
- March 20, 2020:              TheTruthAboutCancer

- Jan 28, 2020:                HealthNutNews

- March 25, 2020 at 1:40pm:    WND
- Feb 19, 2020,  2 p.m.:       WorldHealth
- Tue, 02/25/2020 - 17:48:     ZeroHedge
"""


def convert_datetime(dt_s, format="%Y-%m-%d", source=None):
    """ special cases """
    if dt_s == "":
        return None
    if source == "WND":
        dt_s = dt_s.split(" at")[0]
    elif source == "WorldHealth":
        dt_list = dt_s.split(",")
        dt_s = ",".join(dt_list[:2])
    elif source == "ZeroHedge":
        dt_s = dt_s.split(", ")[1]
        dt_s = dt_s.split(" -")[0]

    """ common cases """
    # %Y-%m-%d
    try:
        converted_dt = datetime.strptime(dt_s, "%Y-%m-%d")
        return converted_dt.strftime(format)
    except:
        pass

    # %Y-%m-%dT%H:%M:%S%z
    try:
        dt_new = dt_s[:-3] + dt_s[-2:]
        converted_dt = datetime.strptime(dt_new, "%Y-%m-%dT%H:%M:%S%z")
        return converted_dt.strftime(format)
    except:
        pass

    # %B %d, %Y
    try:
        converted_dt = datetime.strptime(dt_s, "%B %d, %Y")
        return converted_dt.strftime(format)
    except:
        pass

    # %b %d, %Y
    try:
        converted_dt = datetime.strptime(dt_s, "%b %d, %Y")
        return converted_dt.strftime(format)
    except:
        pass

    # %m/%d/%Y
    try:
        converted_dt = datetime.strptime(dt_s, "%m/%d/%Y")
        return converted_dt.strftime(format)
    except:
        pass

    print(dt_s)
    raise Exception("Cannot convert datetime!")
