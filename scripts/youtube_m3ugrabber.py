#! /usr/bin/python3

banner = r'''
###########################################################################
#      ____ 	____    _____                                             #
#     |  _ \   |       |  _   \                                           #
#     | |_) |  |____   | |_|  |                                           #
#     |  __/        |  |  _   /                                           #
#     |_|       ____|  |_| |__\                                           #
#                                                                         #
#                                  >> https://github.com/naveenland4      #
###########################################################################



#EXTINF:-1 group-title="Info - Must Read" tvg-logo="https://i.imgur.com/aESqPMs.png" tvg-id="", Playlist is for Free
https://raw.githubusercontent.com/naveenland4/UTLive/main/assets/info.m3u8

#EXTINF:-1 group-title="French" tvg-logo="https://i.imgur.com/C8DXbt1.png" tvg-id="", BFM Grand Lille (720p)
https://live.creacast.com/grandlilletv/smil:grandlilletv.smil/playlist.m3u8
'''

import os
import re
import shutil
import subprocess
import sys
import requests

FALLBACK_URL = 'https://raw.githubusercontent.com/naveenland4/News_Channels/main/assets/info.m3u8'
COOKIES_FILE = '/tmp/cookies.txt'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

s = requests.Session()
s.headers.update(HEADERS)


def grab_with_ytdlp(url):
    if not shutil.which('yt-dlp'):
        print('[WARN] yt-dlp not found in PATH', file=sys.stderr)
        return None

    cmd = [
        'yt-dlp',
        '-g',
        '-f', 'best[protocol^=m3u8]/best',
        '--no-warnings',
        '--no-playlist',
    ]
    if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        cmd.extend(['--cookies', COOKIES_FILE])
    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        for line in lines:
            if '.m3u8' in line:
                return line
        if lines and lines[0].startswith('https://'):
            return lines[0]

        err = result.stderr.strip().splitlines()
        reason = err[-1] if err else f'exit code {result.returncode}'
        print(f'[FAIL] {url} -> {reason}', file=sys.stderr)
    except (subprocess.SubprocessError, OSError) as e:
        print(f'[FAIL] {url} -> {e}', file=sys.stderr)

    return None


def grab(url):
    # 1. Fast HTML check
    try:
        response = s.get(url, timeout=15).text.replace('\\/', '/')
        match = re.search(r'https://[^\s"\'\\]+\.m3u8', response)
        if match:
            print(f'[OK-HTML] {url}', file=sys.stderr)
            print(match.group(0))
            return
    except requests.RequestException:
        pass

    # 2. Fallback to yt-dlp
    ytdlp_url = grab_with_ytdlp(url)
    if ytdlp_url:
        print(f'[OK-YTDLP] {url}', file=sys.stderr)
        print(ytdlp_url)
        return

    # 3. Fallback when offline or blocked
    print(FALLBACK_URL)


print('#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml.gz"')
print(banner)

with open('../youtube_channel_info.txt', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('~~'):
            continue
        if not line.startswith('https:'):
            parts = line.split('|')
            if len(parts) < 4:
                continue
            ch_name = parts[0].strip()
            grp_title = parts[1].strip().title()
            tvg_logo = parts[2].strip()
            tvg_id = parts[3].strip()
            print(f'\n#EXTINF:-1 group-title="{grp_title}" tvg-logo="{tvg_logo}" tvg-id="{tvg_id}", {ch_name}')
        else:
            grab(line)
