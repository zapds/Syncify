import base64
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import config

import requests
import youtube_dl
import youtube_search

def get_token():
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            'Authorization': 'Basic ' + base64.b64encode(f'{config.client_id}:{config.client_secret}'.encode()).decode()
        },
        data={
            'grant_type': 'client_credentials'
        }
    )
    d = r.json()
    return d['access_token']


def parse_url(playlist_url):
    parsed = urlparse(playlist_url)
    return parsed.path.split("/")[-1]


def get_playlist(playlist_id):
    print("Fetching playlist from Spotify")
    r = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers={
            'Authorization': 'Bearer ' + get_token()
        }
    )

    playlist = r.json()
    print("Successfully got playlist from Spotify")
    return playlist


def search_song(track):
    artists = ", ".join(a['name'] for a in track['artists'])
    name = track['name']
    search_str = name + " by " + artists
    global RESULTS
    results = youtube_search.YoutubeSearch(search_str, max_results=1)
    if not results:
        return None
    else:
        RESULTS[name] = results.videos[0]['url_suffix']


def generate_options(playlist_name, quality=None, codec=None):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': f'{os.path.normpath(os.path.expanduser("~/Desktop"))}\\{playlist_name}\\%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
        }],
    }
    if quality != "":
        options['postprocessors'][0]['preferredquality'] = quality
    if codec != "":
        options['postprocessors'][0]['preferredcodec'] = codec
    return options


def search_songs():
    print(f"Looking up {len(playlist['tracks']['items'])} songs on YouTube...")
    with ThreadPoolExecutor() as pool:
        pool.map(search_song, [song['track']
                               for song in playlist['tracks']['items']])


if __name__ == '__main__':
    print("""
    $$$$$$\ $$\     $$\ $$\   $$\  $$$$$$\  $$$$$$\ $$$$$$$$\ $$\     $$\ 
    $$  __$$\\$$\   $$  |$$$\  $$ |$$  __$$\ \_$$  _|$$  _____|\$$\   $$  |
    $$ /  \__|\$$\ $$  / $$$$\ $$ |$$ /  \__|  $$ |  $$ |       \$$\ $$  / 
    \$$$$$$\   \$$$$  /  $$ $$\$$ |$$ |        $$ |  $$$$$\      \$$$$  /  
    \____$$\   \$$  /   $$ \$$$$ |$$ |        $$ |  $$  __|      \$$  /   
    $$\   $$ |   $$ |    $$ |\$$$ |$$ |  $$\   $$ |  $$ |          $$ |    
    \$$$$$$  |   $$ |    $$ | \$$ |\$$$$$$  |$$$$$$\ $$ |          $$ |    
    \______/    \__|    \__|  \__| \______/ \______|\__|          \__|    
                                                                        
                                                                                                                                
    """)
    playlist_id = input("Enter Spotify playlist URL/ID: ")
    if playlist_id.startswith("https"):
        playlist_id = parse_url(playlist_id)
    name = input("Enter playlist name to be saved as: ")
    codec = input(
        "Enter preferred filetype [leave empty for auto (recommended)]: ")
    quality = input(
        "Enter quality [0 (best) - 9 (worse)] or bitrate [128K] or leave empty for best quality: ")
    options = generate_options(name, quality, codec)
    playlist = get_playlist(playlist_id)
    global RESULTS
    RESULTS = {}
    search_songs()
    options = getattr(config, "ytdl_options", options)
    yt = youtube_dl.YoutubeDL(options)
    tracks = ["https://youtube.com" +
              url_suffix for url_suffix in RESULTS.values()]
    yt.download(tracks)
    print("All tracks downloaded!")
