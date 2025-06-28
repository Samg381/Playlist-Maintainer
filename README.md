# Playlist-Maintainer
A simple python script to automatically download YouTube playlists using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

**Objective:** automatically keep YouTube playlists backed up on a local drive, preserving the order in which they appear in the playlist.

Simply define the playlists you wish to keep backed up, specify a download directory, and run periodically. The script will download new additions, mark+tag missing videos, and keep track of successful downloads.

Designed to circumvent YouTube censorship, and arbitrary unlisting / removal of videos.

### Features
- Downloaded videos are automatically saved in playlist directories 
- Keeps track of already downloaded videos (*via yt-tlp archive*)
- Allows users to specify whether playlist is video / audio
- Optionally use cookies to access restricted playlists (liked videos, favorites)
- API throttle / ban avoidance mode
- Robust log output

### Requirements
- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) present somewhere on system
- [FFmpeg](https://github.com/FFmpeg/FFmpeg) 
    - Technically optional, but strongly recommended
    - Without it, YouTube videos will be downloaded as separate video / audio files

### Installation
1) Install [Requirements](#requirements)
2) Complete `USER CONFIGURATION` section of script.
    - Specify your playlists (playlist name, type (audio/video), URL)
    - Specify yt-dlp executable location
    - Specify desired download location (e.g. hard drive directory, NAS)
    - See comments for detailed instructions
3) Configure crontab / taskschd to run periodically


### ⚠️ Warnings
- Running too often may result in [YouTube API block](https://www.reddit.com/r/youtube/comments/1f4n18h/video_unavailable_this_content_isnt_available/) / throttling
- Enable `interdownload_delay` to reduce chance of YouTube block
