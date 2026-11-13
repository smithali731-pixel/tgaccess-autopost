#!/bin/sh
# Runs every 5 minutes from cron on the TG Access server. Pulls the latest schedule and
# media list, then publishes whatever is due. State lives outside the repo so a pull never
# overwrites it. Secrets come from /home/tgaccess/autopost.env (META_TOKEN=...).
set -e
cd /home/tgaccess/tgaccess-autopost
git pull -q --ff-only origin main
set -a; . /home/tgaccess/autopost.env; set +a
export IG_USER_ID=17841456768761198 FB_PAGE_ID=1357468380793691 TG_CHAT_ID=324285499
export GITHUB_REPOSITORY=smithali731-pixel/tgaccess-autopost GITHUB_REF_NAME=main
export STATE_FILE=/home/tgaccess/autopost-state.json
exec python3 publish.py
