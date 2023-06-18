import json
import sys
import traceback

from db import get_engine
from orm import Installation
from wx import Polygon

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session


class WXAlert():
    def __init__(self, feature_json, state):
        self._feature_json = feature_json
        if 'type' not in feature_json or feature_json['type'] != 'Feature':
            raise ValueError('Invalid GeoJSON Feature')
        self.id = feature_json['properties']['id']
        if 'geometry' in feature_json and feature_json['geometry'] is not None:
            self.polygon = Polygon(feature_json['geometry'])
        else:
            self.polygon = None  # self._get_polygon_from_geocode(feature_json['properties']['geocode'])
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
        with Session(get_engine()) as session:
            installations = session.query(Installation).filter(
                Installation.bot_started,
                Installation.state == alert.state
            ).all()
            for installation in installations:
                client = WebClient(token=installation.bot_token)
                for channel in client.conversations_list()['channels']:
                    if channel['is_member'] and not channel['is_archived'] and not channel['is_im']:
                        client.chat_postMessage(
                            channel=channel['id'],
                            blocks=alert.slack_block()
                        )
    except SlackApiError as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
    except Exception as e:
        print(e)
        traceback.print_exception(*sys.exc_info())
