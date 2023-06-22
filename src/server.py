import time

from .slack import slack_app

from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler

app = Flask(__name__)
handler = SlackRequestHandler(slack_app)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@app.route("/install", methods=["GET"])
def slack_install():
    return handler.handle(request)


@app.route("/health", methods=["GET"])
def health():
    return str(time.time())


@app.route("/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)
