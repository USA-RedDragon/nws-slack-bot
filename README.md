# NWS Slack Bot

Sends NWS alerts for your state to Slack.

<a href="https://slack.com/oauth/v2/authorize?state=0e33c863-bc1a-42f9-91d8-ee1deb2a8264&client_id=5446375181636.5437287123510&scope=chat:write,channels:read,groups:read,commands,files:write,files:read&user_scope=&redirect_uri=https://nws-slack-bot.mcswain.dev/oauth_redirect"><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack@2x.png" /></a>

## Usage

1. Add the bot to Slack using the link above
2. Once the bot is installed in your workspace, invite it to any channels you'd like to receive statewide alerts for. This can be done by mentioning the bot (@nws_alerts_bot) and when Slack asks you to invite the bot, accept.
3. Send in the channel (or to the bot directly) the command `/alert state` where `state` is a two-letter state abbreviation. For example, `/alert OK`.
4. The bot will start sending alerts to all channels it is invited to.
