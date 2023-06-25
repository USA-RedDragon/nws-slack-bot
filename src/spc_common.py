from datetime import datetime
import io
import pickle
import traceback
import sys
from zipfile import ZipFile

from descartes import PolygonPatch
import matplotlib
import matplotlib.pyplot as plt
from pytz import timezone
import requests
import shapefile
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .orm import Installation

matplotlib.use('Agg')

CENTRAL_TZ = timezone("US/Central")


def is_cdt_active():
    # Check if daylight savings time is active in central time
    now = datetime.now(CENTRAL_TZ)
    return now.dst() != now.utcoffset()


spc_outlooks = [
    "https://www.spc.noaa.gov/products/outlook/day1otlk-shp.zip",
    "https://www.spc.noaa.gov/products/outlook/day2otlk-shp.zip",
    "https://www.spc.noaa.gov/products/outlook/day3otlk-shp.zip",
    "https://www.spc.noaa.gov/products/exper/day4-8/day4prob-shp.zip",
    "https://www.spc.noaa.gov/products/exper/day4-8/day5prob-shp.zip",
    "https://www.spc.noaa.gov/products/exper/day4-8/day6prob-shp.zip",
    "https://www.spc.noaa.gov/products/exper/day4-8/day7prob-shp.zip",
    "https://www.spc.noaa.gov/products/exper/day4-8/day8prob-shp.zip",
]


# Type can be cat, wind, hail, or torn for days 1 and 2
# Type can be cat or prob for day 3
# Type can only be prob for days 4-8
def _plot_spc_outlook(day=1, type="cat"):
    if day > 8 or day < 1:
        raise ValueError("Day must be between 1 and 8")
    with open(".states/US.pickle", "rb") as f:
        fig = pickle.load(f)
    ax = fig.axes[0]

    outlook = spc_outlooks[day-1]
    if type == "cat":
        plt.title(f"Day {day} Categorical Outlook", fontsize=32)
        with ZipFile(io.BytesIO(requests.get(outlook).content)) as z:
            # Grab categorical outlook
            reader = shapefile.Reader(
                shp=z.open(f"day{day}otlk_{type}.shp"),
                shx=z.open(f"day{day}otlk_{type}.shx"),
                dbf=z.open(f"day{day}otlk_{type}.dbf"),
            )
            for shape_rec in reader.shapeRecords():
                shp, recordraw = shape_rec.shape, shape_rec.record
                record = recordraw.as_dict()
                if "fill" in record and "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"]))
                elif "fill" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec="black", zorder=3, alpha=0.65, label=record["LABEL2"]))
                elif "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"]))
                elif "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec="black", zorder=3, alpha=0.65, label=record["LABEL2"]))
                else:
                    print(type)
                    print(record)
                    ax.text(0.5, 0.5,
                            "NO DATA AVAILABLE",
                            horizontalalignment='center',
                            verticalalignment='center',
                            transform=ax.transAxes,
                            fontsize=24)
    elif type == "wind" or type == "torn" or type == "hail" or (day == 3 and type == "prob"):
        if type == "wind":
            plt.title(f"Day {day} Wind Outlook", fontsize=32)
        elif type == "torn":
            plt.title(f"Day {day} Tornado Outlook", fontsize=32)
        elif type == "hail":
            plt.title(f"Day {day} Hail Outlook", fontsize=32)
        elif type == "prob":
            plt.title(f"Day {day} Probability Outlook", fontsize=32)

        with ZipFile(io.BytesIO(requests.get(outlook).content)) as z:
            # Grab categorical outlook
            reader = shapefile.Reader(
                shp=z.open(f"day{day}otlk_{type}.shp"),
                shx=z.open(f"day{day}otlk_{type}.shx"),
                dbf=z.open(f"day{day}otlk_{type}.dbf"),
            )
            for shape_rec in reader.shapeRecords():
                shp, recordraw = shape_rec.shape, shape_rec.record
                record = recordraw.as_dict()
                hatch = None
                if "LABEL2" in record and "Significant" in record["LABEL2"]:
                    hatch = "////"
                if "fill" in record and "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "fill" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec="black", zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec="black", zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                else:
                    print(type)
                    print(record)
                    if type == "prob":
                        ax.text(0.5, 0.5,
                                "PREDICTABILITY TOO LOW",
                                horizontalalignment='center',
                                verticalalignment='center',
                                transform=ax.transAxes,
                                fontsize=24)
                    else:
                        ax.text(0.5, 0.5,
                                "NO DATA AVAILABLE",
                                horizontalalignment='center',
                                verticalalignment='center',
                                transform=ax.transAxes,
                                fontsize=24)
    elif type == "prob":
        plt.title(f"Day {day} Probability Outlook", fontsize=32)
        # This is the same as the other ones, but the file name has a date within it
        with ZipFile(io.BytesIO(requests.get(outlook).content)) as z:
            # Grab the outlooks
            shp = None
            shx = None
            dbf = None
            for file in z.namelist():
                if file.startswith(f"day{day}otlk_"):
                    if file.endswith(".shp"):
                        shp = z.open(file)
                    elif file.endswith(".shx"):
                        shx = z.open(file)
                    elif file.endswith(".dbf"):
                        dbf = z.open(file)
            if shp is None or shx is None or dbf is None:
                raise ValueError("Could not find shapefile")
            reader = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)
            for shape_rec in reader.shapeRecords():
                shp, recordraw = shape_rec.shape, shape_rec.record
                record = recordraw.as_dict()
                hatch = None
                if "LABEL2" in record and "Significant" in record["LABEL2"]:
                    hatch = "////"
                if "fill" in record and "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "fill" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc=record["fill"], ec="black", zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "stroke" in record and "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec=record["stroke"], zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                elif "LABEL2" in record:
                    ax.add_patch(PolygonPatch(shp, fc="none", ec="black", zorder=3, alpha=0.65, label=record["LABEL2"], hatch=hatch))
                else:
                    print(type)
                    print(record)
                    # Add text that says "No data available" in the center of the plot very large
                    ax.text(0.5, 0.5,
                            "PREDICTABILITY TOO LOW",
                            horizontalalignment='center',
                            verticalalignment='center',
                            transform=ax.transAxes,
                            fontsize=24)
    else:
        raise ValueError("Invalid outlook type")

    ax.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    plt.close()
    return image


def send_outlook_image(day, type):
    image = _plot_spc_outlook(day, type)
    # This method will check all chats it is in and send the alert to them
    title = ""
    if type == "cat":
        title = f"Day {day} Categorical Outlook"
    elif type == "prob":
        title = f"Day {day} Probability Outlook"
    elif type == "torn":
        title = f"Day {day} Tornado Outlook"
    elif type == "wind":
        title = f"Day {day} Wind Outlook"
    elif type == "hail":
        title = f"Day {day} Hail Outlook"
    else:
        raise ValueError("Invalid outlook type")

    try:
        for installation in Installation.state_index.scan():
            client = WebClient(token=installation.bot_token)
            for channel in client.conversations_list()['channels']:
                if channel['is_member'] and not channel['is_archived'] and not channel['is_im']:
                    client.files_upload_v2(
                        channel=channel['id'],
                        content=image,
                        title=title,
                        filename=f"{title}.png",
                    )
    except SlackApiError as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
    except Exception as e:
        print(e)
        traceback.print_exception(*sys.exc_info())
