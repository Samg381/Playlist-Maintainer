from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import logging
import os


# --------------------------------------------------------------- USER CONFIGURATION ------------------------------------------------------------------------

'''
Enter your playlist URLs here.
Parameters: name, type, url
    name: name of playlist (and directory where it's videos will be stored)
    type: (video|audio) - determines whether video (.mkv) or just audio (.mp3) will be downloaded.
    url: URL to playlist - note this is NOT a url to a video in the playlist, but a URL to the playlist itself.
'''
playlists = [
                ("Everyday Carry", "video", "https://www.youtube.com/playlist?list=PL482FF54BFAF7A5E5"),
                ("Google Voice", "audio", "https://www.youtube.com/playlist?list=PL59FEE129ADFF2B12"),
                ("Pro Performances Analyzed", "video", "https://www.youtube.com/playlist?list=PLfwtcDG7LpxHo35SSUfWwZnd9SJWM07TD"),
                ("Sam's Music", "audio", "https://www.youtube.com/playlist?list=PLAu7TMBkOIfxKcZBFpLHZvE8pAt8orKRN"),
            ]

# Path to yt-dlp application. Absolute pathing recommended for cron-friendlienss.
yt_dlp_path = "/usr/local/bin/yt-dlp"


# Where you want directories containing downloaded videos to be placed. 
destination_root_directory = "/mnt/SYNOLOGY-JUNK-RAID/YouTube Backups/"






# ------------------------------------------------------ NO USER CONFIGURATION BEYOND THIS POINT-------------------------------------------------------------

log_file = destination_root_directory + "playlist-maintainer.log"

logging.basicConfig(
     filename=log_file,
     encoding="utf-8",
     filemode="a",
     format="[playlist-maintainer] [{levelname}] {message}",
     style="{",
     datefmt="%Y-%m-%d %H:%M",
     level=logging.INFO,
)

logging.getLogger().addHandler(logging.StreamHandler())

# -----------------------------------------------------------------------------------------------------------------------------------------------------------


INVALID_CHARS = r'<>:"/\\|?*'

def is_valid_dirname(name: str) -> bool:
    return not any(char in INVALID_CHARS for char in name)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------


time = datetime.now(ZoneInfo("localtime"))

logging.info(f"=== {time.strftime('%-m/%-d/%Y %-I:%M %p')} ===")

logging.info(f"Initializing")

if not os.path.exists(yt_dlp_path):
    logging.fatal(f"[Fatal] yt-dlp not found in '{yt_dlp_path}' - please verify it exists.")
    quit(1)

if not os.path.exists(destination_root_directory):
    logging.fatal(f"[Fatal] could not find requested download directory '{destination_root_directory}'")
    quit(1)

logging.info(f"Initialization success!")

logging.info(f"Initiating scan for {len(playlists)} playlists.")



for i, playlist in enumerate(playlists):

    playlist_name = playlist[0]
    playlist_type = playlist[1]
    playlist_url = playlist[2]

    if not is_valid_dirname(playlist_name):
        logging.fatal(f"Invalid playlist name: '{playlist_name}' contains illegal characters: {INVALID_CHARS}")
        quit(1)

    destination_dir = destination_root_directory + playlist_name
    archive_file = destination_dir + "/downloaded.txt"

    if not os.path.exists(destination_dir):
        logging.warning(f"Directory for '{playlist_name}' does not exist.")
        os.makedirs(destination_dir)
        logging.info(f"Created '{destination_dir}'")

    command = []

    logging.info(f"Scanning playlist {i} \"{playlist_name}\"")

    match playlist_type:
        case "video":
            command = [
                yt_dlp_path,
                "-P", destination_dir,
                "--ignore-errors",
                "--download-archive", archive_file,
                "--output", "%(playlist_index)03d - %(title).100s.%(ext)s",
                "--format", "bestvideo+bestaudio/best",
                "--merge-output-format", "mkv",
                "--quiet",
                playlist_url
            ]
        case "audio":
            command = [
                yt_dlp_path,
                "-P", destination_dir,
                "--ignore-errors",
                "--download-archive", archive_file,
                "--output", "%(playlist_index)03d - %(title).100s.%(ext)s",
                "--format", "bestaudio/best",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-metadata",
                "--embed-thumbnail",
                "--quiet",
                playlist_url
            ]
        case _:
            logging.fatal(f"Invalid playlist type '{playlist_type}' provided. Options are 'video' or 'audio'. Terminating.")
            quit(1)           

    with open(log_file, "a") as log:
        subprocess.run(command, stdout=log, stderr=log)

    logging.info(f"Scanning playlist {i} \"{playlist_name}\" complete.")


logging.info(f"Finished.\n")