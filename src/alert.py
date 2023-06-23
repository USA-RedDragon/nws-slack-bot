import json
import sys
import traceback

from .config import get_config
from .map import plot_alert_on_state
from .orm import Installation

import requests
from shapely.geometry import shape, Polygon, MultiPolygon, GeometryCollection
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class WXAlert():
    def plot(self, ax):
        if type(self.polygon) == Polygon:
            ax.plot(*self.polygon.exterior.xy, color=self._get_color(), linewidth=3, zorder=6)
        elif type(self.polygon) == MultiPolygon:
            for geom in self.polygon.geoms:
                xs, ys = geom.exterior.xy
                ax.fill(xs, ys, color=self._get_color(), linewidth=0.5, zorder=1)

    # Event codes: https://www.weather.gov/nwr/eventcodes
    # https://www.weather.gov/help-map
    def _get_color(self):
        if self.event == "Blizzard Warning":
            return "#FF4500"
        elif self.event == "Coastal Flood Watch":
            return "#66CDAA"
        elif self.event == "Coastal Flood Warning":
            return "#228B22"
        elif self.event == "Dust Storm Warning":
            return "#FFE4C4"
        elif self.event == "Extreme Wind Warning":
            return "#FF8C00"
        elif self.event == "Flash Flood Watch":
            return "#2E8B57"
        elif self.event == "Flash Flood Warning":
            return "#8B0000"
        elif self.event == "Flash Flood Statement":
            return "#8B0000"
        elif self.event == "Flood Watch":
            return "#2E8B57"
        elif self.event == "Flood Warning":
            return "#00FF00"
        elif self.event == "Flood Statement":
            return "#00FF00"
        elif self.event == "High Wind Watch":
            return "#B8860B"
        elif self.event == "High Wind Warning":
            return "#DAA520"
        elif self.event == "Hurricane Watch":
            return "#FF00FF"
        elif self.event == "Hurricane Warning":
            return "#DC143Cs"
        elif self.event == "Hurricane Statement":
            return "#FFE4B5"
        elif self.event == "Severe Thunderstorm Watch":
            return "#DB7093"
        elif self.event == "Severe Thunderstorm Warning":
            return "#FFA500"
        elif self.event == "Severe Weather Statement":
            return "#00FFFF"
        elif self.event == "Snow Squall Warning":
            return "#C71585"
        elif self.event == "Special Marine Warning":
            return "#FFA500"
        elif self.event == "Special Weather Statement":
            return "#FFE4B5"
        elif self.event == "Storm Surge Watch":
            return "#DB7FF7"
        elif self.event == "Storm Surge Warning":
            return "#B524F7"
        elif self.event == "Tornado Watch":
            return "#FFFF00"
        elif self.event == "Tornado Warning":
            return "#FF0000"
        elif self.event == "Tropical Storm Watch":
            return "#F08080"
        elif self.event == "Tropical Storm Warning":
            return "#B22222"
        elif self.event == "Tsunami Watch":
            return "#FF00FF"
        elif self.event == "Tsunami Warning":
            return "#FD6347"
        elif self.event == "Winter Storm Watch":
            return "#4682B4"
        elif self.event == "Winter Storm Warning":
            return "#FF69B4"
        elif self.event == "Avalanche Watch":
            return "#F4A460"
        elif self.event == "Avalanche Warning":
            return "#1E90FF"
        elif self.event == "Blue Alert":
            return "#B0C4DE"
        elif self.event == "Child Abduction Emergency":
            return "#800000"
        elif self.event == "Civil Danger Warning":
            return "#FFB6C1"
        elif self.event == "Civil Emergency Message":
            return "#FFB6C1"
        elif self.event == "Earthquake Warning":
            return "#8B4513"
        elif self.event == "Evacuation Immediate":
            return "#7FFF00"
        elif self.event == "Fire Warning":
            return "#A0522D"
        elif self.event == "Hazardous Materials Warning":
            return "#4B0082"
        elif self.event == "Law Enforcement Warning":
            return "#C0C0C0"
        elif self.event == "Local Area Emergency":
            return "#C0C0C0"
        elif self.event == "911 Telephone Outage Emergency":
            return "#C0C0C0"
        elif self.event == "Nuclear Power Plant Warning":
            return "#4B0082"
        elif self.event == "Radiological Hazard Warning":
            return "#4B0082"
        elif self.event == "Shelter in Place Warning":
            return "#FA8072"
        elif self.event == "Volcano Warning":
            return "#2F4F4F"
        else:
            return "#FD6347"

    def should_show_radar(self):
        isWx = self.is_weather()
        if isWx and self.event == "Blizzard Warning":
            return True
        elif isWx and self.event == "Coastal Flood Watch":
            return False
        elif isWx and self.event == "Coastal Flood Warning":
            return True
        elif isWx and self.event == "Dust Storm Warning":
            return True
        elif isWx and self.event == "Extreme Wind Warning":
            return False
        elif isWx and self.event == "Flash Flood Watch":
            return False
        elif isWx and self.event == "Flash Flood Warning":
            return True
        elif isWx and self.event == "Flash Flood Statement":
            return True
        elif isWx and self.event == "Flood Watch":
            return False
        elif isWx and self.event == "Flood Warning":
            return True
        elif isWx and self.event == "Flood Statement":
            return True
        elif isWx and self.event == "High Wind Watch":
            return False
        elif isWx and self.event == "High Wind Warning":
            return False
        elif isWx and self.event == "Hurricane Watch":
            return False
        elif isWx and self.event == "Hurricane Warning":
            return True
        elif isWx and self.event == "Hurricane Statement":
            return True
        elif isWx and self.event == "Severe Thunderstorm Watch":
            return False
        elif isWx and self.event == "Severe Thunderstorm Warning":
            return True
        elif isWx and self.event == "Severe Weather Statement":
            return True
        elif isWx and self.event == "Snow Squall Warning":
            return True
        elif isWx and self.event == "Special Marine Warning":
            return True
        elif isWx and self.event == "Special Weather Statement":
            return True
        elif isWx and self.event == "Storm Surge Watch":
            return False
        elif isWx and self.event == "Storm Surge Warning":
            return True
        elif isWx and self.event == "Tornado Watch":
            return False
        elif isWx and self.event == "Tornado Warning":
            return True
        elif isWx and self.event == "Tropical Storm Watch":
            return False
        elif isWx and self.event == "Tropical Storm Warning":
            return True
        elif isWx and self.event == "Tsunami Watch":
            return False
        elif isWx and self.event == "Tsunami Warning":
            return False
        elif isWx and self.event == "Winter Storm Watch":
            return False
        elif isWx and self.event == "Winter Storm Warning":
            return True
        else:
            return False

    def is_weather(self):
        if self.event == "Blizzard Warning":
            return True
        elif self.event == "Coastal Flood Watch":
            return True
        elif self.event == "Coastal Flood Warning":
            return True
        elif self.event == "Dust Storm Warning":
            return True
        elif self.event == "Extreme Wind Warning":
            return True
        elif self.event == "Flash Flood Watch":
            return True
        elif self.event == "Flash Flood Warning":
            return True
        elif self.event == "Flash Flood Statement":
            return True
        elif self.event == "Flood Watch":
            return True
        elif self.event == "Flood Warning":
            return True
        elif self.event == "Flood Statement":
            return True
        elif self.event == "High Wind Watch":
            return True
        elif self.event == "High Wind Warning":
            return True
        elif self.event == "Hurricane Watch":
            return True
        elif self.event == "Hurricane Warning":
            return True
        elif self.event == "Hurricane Statement":
            return True
        elif self.event == "Severe Thunderstorm Watch":
            return True
        elif self.event == "Severe Thunderstorm Warning":
            return True
        elif self.event == "Severe Weather Statement":
            return True
        elif self.event == "Snow Squall Warning":
            return True
        elif self.event == "Special Marine Warning":
            return True
        elif self.event == "Special Weather Statement":
            return True
        elif self.event == "Storm Surge Watch":
            return True
        elif self.event == "Storm Surge Warning":
            return True
        elif self.event == "Tornado Watch":
            return True
        elif self.event == "Tornado Warning":
            return True
        elif self.event == "Tropical Storm Watch":
            return True
        elif self.event == "Tropical Storm Warning":
            return True
        elif self.event == "Tsunami Watch":
            return True
        elif self.event == "Tsunami Warning":
            return True
        elif self.event == "Winter Storm Watch":
            return True
        elif self.event == "Winter Storm Warning":
            return True
        else:
            return False

    def __init__(self, feature_json, state):
        self._feature_json = feature_json
        if 'type' not in feature_json or feature_json['type'] != 'Feature':
            raise ValueError('Invalid GeoJSON Feature')
        self.id = feature_json['properties']['id']
        if 'geometry' in feature_json and feature_json['geometry'] is not None:
            self.polygon = shape(feature_json['geometry'])
        else:
            self.polygon = self._make_multipolygon(feature_json['properties']['affectedZones'])
        self.sent = feature_json['properties']['sent']
        self.expires = feature_json['properties']['expires']
        self.effective = feature_json['properties']['effective']
        self.onset = feature_json['properties']['onset']
        self.ends = feature_json['properties']['ends']
        self.message_type = feature_json['properties']['messageType']
        self.severity = feature_json['properties']['severity']
        self.certainty = feature_json['properties']['certainty']
        self.urgency = feature_json['properties']['urgency']
        self.event = feature_json['properties']['event']
        self.headline = feature_json['properties']['headline']
        self.description = feature_json['properties']['description']
        self.instruction = feature_json['properties']['instruction']
        if self.instruction is None:
            self.instruction = ""
        self.area_desc = feature_json['properties']['areaDesc']
        if 'maxHailSize' in feature_json['properties']['parameters']:
            self.max_hail_size = feature_json['properties']['parameters']['maxHailSize']
        if 'maxWindSpeed' in feature_json['properties']['parameters']:
            self.max_wind_speed = feature_json['properties']['parameters']['maxWindSpeed']
        self.state = state

    def _make_multipolygon(self, affected_zones):
        ugcs_polygons = []
        for zone in affected_zones:
            poly = self._get_polygon_from_url(zone)
            if type(poly) == Polygon:
                ugcs_polygons.append(poly)
            elif type(poly) == MultiPolygon:
                for geom in poly.geoms:
                    ugcs_polygons.append(geom)
            elif type(poly) == GeometryCollection:
                for geom in poly.geoms:
                    if type(geom) == Polygon:
                        ugcs_polygons.append(geom)
                    elif type(geom) == MultiPolygon:
                        for geom2 in geom.geoms:
                            ugcs_polygons.append(geom2)
                    else:
                        print(geom)
                        raise ValueError('Invalid polygon')
        return MultiPolygon([poly for poly in ugcs_polygons])

    def _get_polygon_from_url(self, url):
        response = requests.get(
            url,
            headers={
                'Accept': 'application/geo+json',
                'User-Agent': get_config().get('nws', 'user_agent')
            }
        )
        if response.status_code != 200:
            raise ValueError('Failed to get polygon')
        res = response.json()
        if 'geometry' not in res or res['geometry'] is None:
            raise ValueError('Invalid polygon')
        if ('coordinates' not in res['geometry'] and (res['geometry']['type'] != "Polygon" or res['geometry']['type'] != "MultiPolygon")) \
                and (res['geometry']['type'] != "GeometryCollection"):
            print(res)
            print(url)
            raise ValueError('Invalid polygon')
        return shape(res['geometry'])

    def __str__(self):
        return f"{self.headline}\n\n" + \
                f"{self.event}\n\n" + \
                f"Area: {self.area_desc}\n\n" + \
                f"{self.description}\n\n" + \
                f"{self.instruction}\n\n" + \
                "\n" + \
                ("" if not hasattr(self, 'max_hail_size') else f"Max Hail Size: {self.max_hail_size}\n") + \
                ("" if not hasattr(self, 'max_wind_speed') else f"Max Wind Speed: {self.max_wind_speed}\n") + \
                f"Severity: {self.severity}\n" + \
                f"Certainty: {self.certainty}\n" + \
                f"Urgency: {self.urgency}\n" + \
                "\n" + \
                f"Sent: {self.sent}\n" + \
                f"Expires: {self.expires}\n" + \
                f"Effective: {self.effective}\n" + \
                f"Onset: {self.onset}\n" + \
                f"Ends: {self.ends}\n"

    def slack_block(self):
        instr = ('\n\n' + self.instruction) if self.instruction else ''
        return json.dumps([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{self.headline}*",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity*: {self.severity}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Certainty*: {self.certainty}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Urgency*: {self.urgency}",
                        },
                    ],
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{self.event}*",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Area*: {self.area_desc}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{self.description}{instr}```",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Sent*: {self.sent}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Expires*: {self.expires}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Effective*: {self.effective}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Onset*: {self.onset}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Ends*: {self.ends}",
                        },
                    ],
                },
            ])


def send_alert(alert):
    # This method will check all chats it is in and send the alert to them
    try:
        for installation in Installation.state_index.query(alert.state):
            client = WebClient(token=installation.bot_token)
            for channel in client.conversations_list()['channels']:
                if channel['is_member'] and not channel['is_archived'] and not channel['is_im']:
                    client.chat_postMessage(
                        channel=channel['id'],
                        blocks=alert.slack_block(),
                        text=str(alert),
                    )
                    client.files_upload(
                        channels=channel['id'],
                        content=plot_alert_on_state(alert),
                        filetype="png",
                        title=f"{alert.headline}",
                        filename=f"{alert.event}-{alert.sent}.png",
                    )
    except SlackApiError as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
    except Exception as e:
        print(e)
        traceback.print_exception(*sys.exc_info())
