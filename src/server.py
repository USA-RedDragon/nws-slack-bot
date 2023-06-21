from flask import Flask, request

from .slack import slack_app
from slack_bolt.adapter.flask import SlackRequestHandler

app = Flask(__name__)
handler = SlackRequestHandler(slack_app)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@app.route("/install", methods=["GET"])
def slack_install():
    return handler.handle(request)
