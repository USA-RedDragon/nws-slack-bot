import sys
import time
import traceback

from .config import get_config
from .orm import Installation
from .map import plot_radar_lvl2_from_station
from .spc_common import _plot_spc_outlook

import boto3
from slack_bolt import App
from slack_sdk.oauth import OAuthStateUtils
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.amazon_s3 import AmazonS3InstallationStore
from slack_sdk.oauth.state_store.amazon_s3 import AmazonS3OAuthStateStore
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import BoltResponse


def _success(args: SuccessArgs) -> BoltResponse:
    installation = args.installation
    client = args.request.context.client
    try:
        existing_installation = Installation.get(installation.team_id)
        if existing_installation:
            existing_installation.update(actions=[
                Installation.bot_token.set(installation.bot_token),
                Installation.bot_token_expires_at.set(installation.bot_token_expires_at),
            ])
        else:
            Installation(
                team_id=installation.team_id,
                bot_token=installation.bot_token,
                bot_token_expires_at=installation.bot_token_expires_at,
                bot_started=False,
            ).save()
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
    scopes=["chat:write", "channels:read", "groups:read", "commands", "files:write", "files:read"],
    user_scopes=[],
    install_path="/install",
    redirect_uri_path="/oauth_redirect",
    redirect_uri=get_config().get("server", "base_url") + "/oauth_redirect",
    installation_store=_installation_store,
    state_store=_state_store,
    callback_options=CallbackOptions(success=_success, failure=_failure),
)

slack_app = App(
    signing_secret=get_config().get("slack", "signing_secret"),
    oauth_settings=oauth_settings
)


@slack_app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


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


@slack_app.command("/alert")
def start_command(ack, say, command):
    ack()
    try:
        if 'text' not in command:
            say("Please specify a state to watch for alerts in.")
            return
        state = command['text'].upper()
        valid, reason = is_state_valid(state)
        if not valid:
            say(reason)
            return
        # Find the installation and update the bot_started flag and state
        installation = None
        res = Installation.query(command['team_id'])
        if not res:
            say("Installation not found.")
            return
        for res_ in res:
            installation = res_
            break
        installation.update(actions=[
            Installation.bot_started.set(True),
            Installation.state.set(state)
        ])
        say(f"Starting to watch for alerts in {state}...")
        from .api import WXWatcher, get_wx_watcher_manager
        get_wx_watcher_manager().add_and_start_watcher(WXWatcher(state=state))
    except Exception as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
        say("Error occurred while processing `/alert " + command['text'] + "`")


@slack_app.command("/radar")
def radar_command(ack, say, command):
    ack()
    installation = None
    res = Installation.query(command['team_id'])
    if not res:
        say("Installation not found.")
        return
    for res_ in res:
        installation = res_
        break
    client = WebClient(token=installation.bot_token)
    try:
        if 'text' not in command:
            client.chat_postEphemeral(
                "Please specify a radar to view, such as `ktlx`, and optionally a two-digit state. For example, `/radar ktlx ok`.",
                command['user_id'], command['channel_id'])
            return
        params = command['text'].split(" ")
        radar = params[0].lower()
        state = None
        if len(params) > 1:
            state = params[1].upper()
            valid, reason = is_state_valid(state)
            if not valid:
                client.chat_postEphemeral(reason, command['user_id'], command['channel_id'])
                return
        if not state:
            state = installation.state
        # Send the user a friendly acknowledgement message and mention that the radar image could take a few seconds to download and generate
        say(f"Fetching latest radar scan for {radar.upper()} in {state.upper()}. Please be patient, this could take a few seconds.")
        client.files_upload_v2(
            channel=command['channel_id'],
            content=plot_radar_lvl2_from_station(state, radar),
            title=f"{radar.upper()} in {state.upper()}",
            filename=f"{radar.upper()}-{str(time.time())}.png",
            initial_comment=f"Here's the radar for {radar.upper()} in {state.upper()}"
        )
    except Exception as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
        say("Error occurred while processing `/radar " + command['text'] + "`")


@slack_app.command("/spc")
def spc_command(ack, say, command):
    ack()
    installation = None
    res = Installation.query(command['team_id'])
    if not res:
        say("Installation not found.")
        return
    for res_ in res:
        installation = res_
        break
    client = WebClient(token=installation.bot_token)
    try:
        if 'text' not in command:
            client.chat_postEphemeral(
                "Please specify a day and the outlook type, such as `/spc 1 cat`",
                command['user_id'], command['channel_id'])
            return
        params = command['text'].split(" ")
        if len(params) < 2:
            client.chat_postEphemeral(
                "Please specify a day and outlook type, such as `/spc 1 cat`",
                command['user_id'], command['channel_id'])
            return
        day = params[0].lower()
        try:
            day = int(day)
        except ValueError:
            client.chat_postEphemeral(
                "Day must be a number 1 and 8",
                command['user_id'], command['channel_id'])
            return
        if day < 1 or day > 8:
            client.chat_postEphemeral(
                "Day must be between 1 and 8",
                command['user_id'], command['channel_id'])
            return
        outlook = params[1].lower()

        if day == 1 or day == 2:
            if outlook not in ["cat", "wind", "hail", "torn"]:
                client.chat_postEphemeral(
                    f"Outlook for day {day} must be one of `cat`, `wind`, `hail`, or `torn`",
                    command['user_id'], command['channel_id'])
                return
        elif day == 3:
            if outlook not in ["cat", "prob"]:
                client.chat_postEphemeral(
                    f"Outlook for day {day} must be one of `cat` or `prob`",
                    command['user_id'], command['channel_id'])
                return
        elif day > 3:
            if outlook not in ["prob"]:
                client.chat_postEphemeral(
                    f"Outlook for day {day} must be `prob`",
                    command['user_id'], command['channel_id'])
                return
        outlook_name = None
        if outlook == "cat":
            outlook_name = "Categorical"
        elif outlook == "prob":
            outlook_name = "Probabilistic"
        elif outlook == "wind":
            outlook_name = "Wind"
        elif outlook == "hail":
            outlook_name = "Hail"
        elif outlook == "torn":
            outlook_name = "Tornado"
        else:
            outlook_name = "Unknown"
        # Send the user a friendly acknowledgement message and mention that the SPC images could take a few seconds to download and generate
        say(f"Fetching latest SPC {outlook_name} Outlook for day {day}. Please be patient, this could take a few seconds.")
        image = _plot_spc_outlook(day=day, type=outlook)
        if not image:
            client.chat_postEphemeral(
                "Error generating image",
                command['user_id'], command['channel_id'])
            return
        client.files_upload_v2(
            channel=command['channel_id'],
            content=image,
            title=f"SPC {outlook_name} Outlook for Day {day}",
            filename=f"SPC-{outlook_name}-Outlook-Day-{day}-{str(time.time())}.png",
            initial_comment=f"Here's the SPC {outlook_name} Outlook for Day {day}"
        )
    except Exception as e:
        print(f"Error posting message: {e}")
        traceback.print_exception(*sys.exc_info())
        say("Error occurred while processing `/spc " + command['text'] + "`")
