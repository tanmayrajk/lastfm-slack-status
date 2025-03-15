import requests
import json
from dotenv import load_dotenv
import os
import time
import atexit

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_EMOJI_TOKEN = os.getenv("SLACK_EMOJI_TOKEN")
LASTFM_KEY = os.getenv("LASTFM_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
STATUS_EMOJI = os.getenv("STATUS_EMOJI")

last_song_text = ""

def set_slack_status(status_text, status_emoji, status_expiration, slack_token):
    url = "https://slack.com/api/users.profile.set"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "profile": {
            "status_text": status_text,
            "status_emoji": status_emoji,
            "status_expiration": status_expiration
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def get_latest_track(username, api_key):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={api_key}&format=json"
    response = requests.get(url)
    data = response.json()

    if "recenttracks" in data and "track" in data["recenttracks"]:
        tracks = data["recenttracks"]["track"]

        if tracks:
            now_playing = tracks[0]

            if "@attr" in now_playing and "nowplaying" in now_playing["@attr"] and now_playing["@attr"]["nowplaying"] == "true":
                return {
                    "now_playing": True,
                    "artist": now_playing['artist']["#text"],
                    "name": now_playing['name']
                }
            else:
                return {
                    "now_playing": False
                }
    else:
        print("Failed to retrieve tracks.")

def on_exit():
    set_slack_status(status_text="", status_emoji="", status_expiration=0, slack_token=SLACK_TOKEN)

atexit.register(on_exit)

while True:
    try:
        song = get_latest_track(LASTFM_USERNAME, LASTFM_KEY)
        if (song["now_playing"] == True):
            text = f"{song["artist"]} - {song["name"]}"
            if last_song_text == text:
                print("Song already updated. Skipping...")
                time.sleep(10)
                continue
            last_song_text = text
            print(f"Setting status as '{text}'...")
            set_slack_status(status_text=text, status_emoji=STATUS_EMOJI, status_expiration=0, slack_token=SLACK_TOKEN)
            print("Status updated!")
        else:
            if last_song_text == "":
                print("No song currently playing. Retrying in 10 seconds...")
                time.sleep(10)
                continue
            last_song_text = ""
            print("Removing status...")
            set_slack_status(status_text="", status_emoji="", status_expiration=0, slack_token=SLACK_TOKEN)
            print("Status updated!")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}. Retrying in 10 seconds...")
    except KeyboardInterrupt:
        break
    time.sleep(10)