from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import platform
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
                ("Google Voice", "video", "https://www.youtube.com/playlist?list=PL59FEE129ADFF2B12"),
                ("Music with Friends", "audio", "https://www.youtube.com/playlist?list=PLAu7TMBkOIfxKcZBFpLHZvE8pAt8orKRN"),
            ]



# Path to yt-dlp application. Absolute pathing recommended for cron-friendlienss.
yt_dlp_path = "/usr/local/bin/yt-dlp"


# Where you want directories containing downloaded videos to be placed. 
destination_root_directory = "/mnt/SYNOLOGY-JUNK-RAID/YouTube Backups/"


# OPTIONAL: save dummy files in download directory to visually mark deleted/private/unlisted videos
write_unavailable_videos = True
# OPTIONAL: if write_unavailable_videos is enabled, the dummy file will be a shortcut to quiteaplaylist.com (video recovery tool)
write_shortcut = True
# OPTIONAL: if write_shortcut and write_unavailable_videos are enabled, specify the OS (Windows|Linux) to determine the type of web shortcut that is created.
end_user_os = "Windows"


# OPTIONAL: use cookies (an account) to access Liked Videos / private / unlisted playlists
# If enabled, the script will look for 'cookies.txt' in the same directory of the script
use_cookies = True

# OPTIONAL: (recommended if use_cookies enabled) - add a randomized delay between downloads / API hits, and throttle bandwidth, to reduce liklihood of youtube ban
# VERY IMPORTANT if use_cookies is enabled. Too many downloads can cause a very severe, unfixable account block that can take months to disappear, if it does at all.
# This is the error you can expect if you ignore this: https://www.reddit.com/r/youtube/comments/1f4n18h/video_unavailable_this_content_isnt_available/
interdownload_delay = True



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

logging.info(f"==================== {time.strftime('%-m/%-d/%Y %-I:%M %p')} ====================")

logging.info(f"Initializing")

if not os.path.exists(yt_dlp_path):
    logging.fatal(f"yt-dlp not found in '{yt_dlp_path}' - please verify it exists.")
    quit(1)

if not os.path.exists(destination_root_directory):
    logging.fatal(f"could not find requested download directory '{destination_root_directory}'")
    quit(1)

logging.info(f"Initialization success!")

logging.info(f"Initiating maintenance for {len(playlists)} playlists.")

if use_cookies and not interdownload_delay:
    logging.warning(f"You have opted to use cookies WITHOUT enabling interdownload_delay! \nYou may face a ban if the playlist is too long!")



for i, playlist in enumerate(playlists):

    playlist_name = playlist[0]
    playlist_type = playlist[1]
    playlist_url = playlist[2]

    logging.info(f"Scanning playlist {i+1} \"{playlist_name}\"")

    if not is_valid_dirname(playlist_name):
        logging.fatal(f"    Invalid playlist name: '{playlist_name}' contains illegal characters: {INVALID_CHARS}")
        quit(1)

    destination_dir = destination_root_directory + playlist_name
    archive_file = destination_dir + "/downloaded.txt"

    if not os.path.exists(destination_dir):
        logging.warning(f"  Directory for '{playlist_name}' does not exist.")
        os.makedirs(destination_dir)
        logging.info(f"    Created '{destination_dir}'")

    command = []


    # Flag patchout
    cookies_flag = ["--cookies", "cookies.txt"] if use_cookies else []

    sleep_flags = [
        "--sleep-requests", "3",            # Pause 3 seconds between each request (e.g., metadata/API calls)
        "--min-sleep-interval", "60",       # Wait at least 10 seconds between downloading individual videos
        "--max-sleep-interval", "120",      # Wait up to 90 seconds between videos (randomized with min)
        "--limit-rate", "1M",               # Limit download speed to 1 MiB/s to reduce bandwidth burst
        "--retry-sleep", "fragment:300",    # If a video fragment fails, sleep 5 minutes before retrying
    ] if interdownload_delay else []


    # Generate yt-dlp command
    match playlist_type:
        case "video":
            command = [
                yt_dlp_path,
                "-P", destination_dir,
                "--ignore-errors",
                "--download-archive", archive_file,
                "--output", "%(title).100s.%(ext)s",
                "--format", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "--no-mtime", # Ensure OS file modification date reflects download time
                "--sleep-interval", interdownload_delay,
                *cookies_flag,
                *sleep_flags,
                playlist_url
            ]
        case "audio":
            command = [
                yt_dlp_path,
                "-P", destination_dir,
                "--ignore-errors",
                "--download-archive", archive_file,
                "--output", "%(title).100s.%(ext)s",
                "--format", "bestaudio/best",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-metadata",
                "--embed-thumbnail",
                "--no-mtime", # Ensure OS file modification date reflects download time 
                "--sleep-interval", interdownload_delay,
                *cookies_flag,
                *sleep_flags,
                playlist_url
            ]
        case _:
            logging.fatal(f"    Invalid playlist type '{playlist_type}' provided. Options are 'video' or 'audio'. Terminating.")
            quit(1)           

    
    # This is where we call subprocess to run yt-dlp. We need to wrap this in it's own logfile, which is only needed for appending to the logging output.
    with open(log_file, "a", encoding="utf-8") as log:

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        current_video_number = 0
        total_videos_in_playlist = 0

        if process.stdout is not None:

            for line in process.stdout:
                
                # Remove whitespace
                line = line.rstrip()
                
                # Break line up into space separated chunks
                split = line.rsplit(" ")

                # Fetch current video number
                if "[download]" in split[0]:

                    if "100%" in split[1]:
                        logging.info(f"    Video {current_video_number} download complete")

                    if "Downloading" in split[1] and "item" in split[2]:
                        current_video_number = int(split[3])
                        total_videos_in_playlist = int(split[5])

                # Handle output
                elif "ERROR" in split[0]:

                    id = split[2].rstrip(':')

                    logging.info(f"    Video ID {id} is unavailable")

                    # If user wants a dummy file to be placed in download directory indicating a missing video
                    if write_unavailable_videos:

                        #dummy_file = destination_dir + "/" + str(current_video_number) + " - Unavailable video - " + id
                        filename = f"{current_video_number} - Unavailable video - {id}"
                        file_path = os.path.join(destination_dir, filename)

                        # If user wants a clickable shortcut to video recovery tool or not
                        if write_shortcut:

                            # Construct the URL to quiteaplaylist
                            search_url = f"https://quiteaplaylist.com/search?url=https://www.youtube.com/watch?v={id}"
                            
                            # Create a shortcut file depending on OS
                            if end_user_os == "Windows":
                                file_path += ".url"
                                with open(file_path, "w") as f:
                                    f.write(f"[InternetShortcut]\nURL={search_url}\n")
                            else:
                                file_path += ".desktop"
                                with open(file_path, "w") as f:
                                    f.write(
                                        f"""[Desktop Entry]
                                            Type=Link
                                            Name={filename}
                                            URL={search_url}
                                            Icon=text-html
                                            """
                                            )
                                os.chmod(file_path, 0o755)  # Make it executable (some Linux desktops require this)

                        else:

                            with open(file_path, "w") as file:
                                file.write(line) # Write the yt-dlp output


                elif "archive" in split[-1]:
                    id = split[1].rstrip(':')
                    logging.info(f"    Video ID {id} already downloaded")

                #else:
                # print(f"    {line}")                    # Console output
                # log.write("    " + line + "\n")         # File output
        
        process.wait()


    logging.info(f"Playlist maintenance complete.")


logging.info(f"Finished.\n")