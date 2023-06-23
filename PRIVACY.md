# Privacy Policy

(I've never done one of these before, so please forgive non-standard verbiage)

## What data does this bot collect?

This bot collects the Slack Team ID associated with installations of the bot into Slack workspaces. At install time, the bot also collects a very limited scope (`chat:write`, `channels:read`, `groups:read`, `commands`) bot token which it uses to actually post the alerts. When the `/alert` command is called, it associated this state with the installation.

## Slack token scope explanations

### `chat:write`

Allows the bot to send alerts to channels it's a member of.

### `channels:read` `groups:read`

Allows the bot to list groups (private channels) and public channels. It uses this to see which channels it is a member of and sends the alerts to those channels.

### `commands`

Gives the bot the ability to receive and respond to slash commands, such as `/alert`

### `files:write` and `files:read`

Gives the bot the ability to send imagery based on the alert and radar.
