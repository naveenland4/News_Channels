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
import tempfile

FALLBACK_URL = 'https://raw.githubusercontent.com/naveenland4/News_Channels/main/assets/info.m3u8'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNEL_INFO_FILE = os.path.join(SCRIPT_DIR, '..', 'youtube_channel_info.txt')

YTDLP_HOME = os.path.join(tempfile.gettempdir(), 'ytdlp_home')
YTDLP_CACHE = os.path.join(YTDLP_HOME, '.cache')

COOKIE_CANDIDATES = [
    '/tmp/cookies.txt',
    os.path.join(SCRIPT_DIR, '..', 'cookies.txt'),
]

YTDLP_BIN = shutil.which('yt-dlp')
NODE_BIN = shutil.which('node')

os.makedirs(YTDLP_CACHE, exist_ok=True)


def get_cookies_file():
    for path in COOKIE_CANDIDATES:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def normalize_url(raw):
    raw = raw.strip()
    if re.fullmatch(r'[a-zA-Z0-9_-]{11}', raw):
        return f'https://www.youtube.com/watch?v={raw}'
    return raw


def fetch_youtube_m3u8(url):
    if not YTDLP_BIN:
        print('[ERROR] yt-dlp binary not found in PATH', file=sys.stderr)
        return None

    target_url = normalize_url(url)

    cmd = [
        YTDLP_BIN,
        '--socket-timeout', '15',
        '--no-playlist',
        '--remote-components', 'ejs:github',
        '-f', 'b[protocol^=m3u8]/bv*[protocol^=m3u8]/b/bv*',
        '--print', 'manifest_url',
        '--print', 'url',
    ]

    if NODE_BIN:
        cmd.extend(['--js-runtimes', f'node:{NODE_BIN}'])

    cookies_file = get_cookies_file()
    if cookies_file:
        cmd.extend(['--cookies', cookies_file])

    cmd.append(target_url)

    env = os.environ.copy()
    env['HOME'] = YTDLP_HOME
    env['XDG_CACHE_HOME'] = YTDLP_CACHE

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=45,
            env=env,
        )
    except subprocess.TimeoutExpired:
        print(f'[FAIL] {target_url} -> timed out after 45s', file=sys.stderr)
        return None
    except OSError as e:
        print(f'[FAIL] {target_url} -> {e}', file=sys.stderr)
        return None

    if result.returncode != 0:
        err_lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
        reason = err_lines[-1] if err_lines else f'yt-dlp exited with code {result.returncode}'
        print(f'[FAIL] {target_url} -> {reason}', file=sys.stderr)
        return None

    lines = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line and line != 'NA' and line.startswith('http'):
            lines.append(line)

    stream_url = None
    for line in lines:
        if '.m3u8' in line:
            stream_url = line
            break

    if stream_url is None and lines:
        stream_url = lines[0]

    if not stream_url:
        print(f'[FAIL] {target_url} -> No active stream URL found', file=sys.stderr)
        return None

    print(f'[OK] {target_url}', file=sys.stderr)
    return stream_url


def grab(url):
    if '.m3u8' in url:
        print(url)
        return

    stream_url = fetch_youtube_m3u8(url)
    if stream_url:
        print(stream_url)
    else:
        print(FALLBACK_URL)


def main():
    print(
        f'[INFO] yt-dlp={YTDLP_BIN} | node={NODE_BIN} | cookies={"Yes" if get_cookies_file() else "No"}',
        file=sys.stderr,
    )
    print('#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml.gz"')
    print(banner)

    with open(CHANNEL_INFO_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('~~'):
                continue
            if not line.startswith('http') and '|' in line:
                parts = line.split('|')
                if len(parts) < 4:
                    continue
                ch_name = parts[0].strip()
                grp_title = parts[1].strip().title()
                tvg_logo = parts[2].strip()
                tvg_id = parts[3].strip()
                print(
                    f'\n#EXTINF:-1 group-title="{grp_title}" tvg-logo="{tvg_logo}" tvg-id="{tvg_id}", {ch_name}'
                )
            else:
                grab(line)


if __name__ == '__main__':
    main()
