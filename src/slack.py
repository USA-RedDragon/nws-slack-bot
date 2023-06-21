import sys
import traceback

from config import get_config
from db import get_engine
from orm import Installation

import boto3
from sqlalchemy.orm import Session
from slack_bolt import App
from slack_sdk.oauth import OAuthStateUtils
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.amazon_s3 import AmazonS3InstallationStore
from slack_sdk.oauth.state_store.amazon_s3 import AmazonS3OAuthStateStore
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_sdk.errors import SlackApiError
from slack_bolt import BoltResponse


def _success(args: SuccessArgs) -> BoltResponse:
    installation = args.installation
    client = args.request.context.client
    try:
        with Session(get_engine()) as session:
            session.add(
                Installation(
                    team_id=installation.team_id,
                    bot_token=installation.bot_token,
                    bot_token_expires_at=installation.bot_token_expires_at,
                    bot_started=False,
                )
            )
            session.commit()
        client.chat_postMessage(
            token=installation.bot_token,  # Use the token you just got from oauth.v2.access API response
            channel=installation.user_id,  # Only with chat.postMessage API, you can use user_id here
            text="Thanks for installing this app!\n" + \
                 "Use `/alert state` where `state` is a two-letter state code (example: `/alert OK`)" + \
                 " to start watching for alerts in the given state, then" + \
                 " invite the bot to any channels you'd like the alerts to be sent to"
        )
        return args.default.success(args)
    except SlackApiError as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())


def _failure(args: FailureArgs) -> BoltResponse:
    return BoltResponse(status=args.suggested_status_code, body=args.reason)


_state_store = AmazonS3OAuthStateStore(
    s3_client=boto3.client("s3"),
    bucket_name=get_config().get("s3", "bucket"),
    expiration_seconds=OAuthStateUtils.default_expiration_seconds,
)

_installation_store = AmazonS3InstallationStore(
    s3_client=boto3.client("s3"),
    bucket_name=get_config().get("s3", "bucket"),
    client_id=get_config().get("slack", "client_id"),
)

oauth_settings = OAuthSettings(
    client_id=get_config().get("slack", "client_id"),
    client_secret=get_config().get("slack", "client_secret"),
    scopes=["chat:write", "channels:read", "groups:read", "commands"],
    user_scopes=[],
    install_path="/install",
    redirect_uri_path="/oauth_redirect",
    redirect_uri=get_config().get("server", "base_url") + "/oauth_redirect",
    installation_store=_installation_store,
    state_store=_state_store,
    callback_options=CallbackOptions(success=_success, failure=_failure),
)

app = App(
    signing_secret=get_config().get("slack", "signing_secret"),
    oauth_settings=oauth_settings
)


def is_state_valid(state):
    ret = True
    reason = ""
    if len(state) != 2:
        ret = False
        reason = "State must be two letters"
    elif not state.isalpha():
        ret = False
        reason = "State must be letters only"
    elif not state.isupper():
        ret = False
        reason = "State must be uppercase"
    elif state not in [
        "AL",
        "AK",
        "AS",
        "AR",
        "AZ",
        "CA",
        "CO",
        "CT",
        "DE",
        "DC",
        "FL",
        "GA",
        "GU",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "PR",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VI",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "MP",
        "PW",
        "FM",
        "MH",
    ]:
        ret = False
        reason = "State must be a valid US state"
    return ret, reason


@app.command("/alert")
def start_command(ack, say, command):
    ack()
    if 'text' not in command:
        say("Please specify a state to watch for alerts in.")
        return
    state = command['text'].upper()
    valid, reason = is_state_valid(state)
    if not valid:
        say(reason)
        return
    with Session(get_engine()) as session:
        # Find the installation and update the bot_started flag and state
        installation = session.query(Installation).filter(
            Installation.team_id == command['team_id']
        ).first()
        if installation is None:
            say("Please install the app first.")
            return
        installation.bot_started = True
        installation.state = state
        session.commit()
    say(f"Starting to watch for alerts in {state}...")
    from api import WXWatcher, get_wx_watcher_manager
    get_wx_watcher_manager().add_and_start_watcher(WXWatcher(state=state))
