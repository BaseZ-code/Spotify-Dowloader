import yt_dlp
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from mutagen.id3 import ID3, TPE1 , TIT2, TALB, TYER, TPE2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
load_dotenv()

# Settings
Path.cwd() / "Spotify-Dowloader"
class DownloaderConfig:
    def __init__(self):
        self.output_path = Path.home() / "Music" / "Songs"
        self.cookies_path = Path.home() / "OneDrive" / "Documents" / "cookies.txt"
        self.preferedcodec = "mp3"
        self.format = "bestaudio/best"
    
    def DownloaderOptions(self):
        ydl_opts = {
            'default_search': 'ytsearch',
            'noplaylist' : True,
            'noprogress' : True,
            'no_warnings' : True,
            "cookiefile": f"{self.cookies_path}",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.preferedcodec,
                'preferredquality': '192',
            }],
            'Metadata_replacerPP': [],
            'format': self.format,
            'outtmpl': f'{self.output_path}/%(title)s.%(ext)s'
        }
        return ydl_opts

# Initialize Spotify API
auth_manager = SpotifyClientCredentials( 
    client_id=os.getenv('CLIENT_ID'),    client_secret=os.getenv('CLIENT_SECRET')
    )
sp = spotipy.Spotify(auth_manager=auth_manager)
config = DownloaderConfig()
out_path = config.output_path
out_path.mkdir(parents=True, exist_ok=True)  # Create the output directory if it doesn't exist
cookies_path = config.cookies_path

# Class which will be used in yt_dlp Postprocessor -> Use to add metadata to a file.
class Metadata_replacerPP(yt_dlp.postprocessor.PostProcessor):
    def __init__(self, metadata):
        super().__init__()
        self.name, self.artist, self.album, self.release_date = metadata.title, metadata.artist, metadata.album, metadata.release_date
    def run(self, info):
        audiopath = info['filepath']
        audio = ID3(audiopath)
        audio.add(TIT2(encoding=3, text=self.name))
        audio.add(TPE1(encoding=3, text=self.artist))
        audio.add(TALB(encoding=3, text=self.album))
        audio.add(TYER(encoding=3, text=self.release_date))
        audio.save()

        return [], info
    
@dataclass
class Track:
    title: str
    artist: str
    album: str
    release_date: str

# A place holder for a file's metadata before inserting in using Metadata_replacerPP()
class Metadata():
    global sp
    def __init__(self, url:str):
        self.url = url

    # Append each metadata lists in to a list. Metadata list -> [name, artists, album, release date]
    def track_metadata(self, playlist:bool) -> list:
        metadata = []
        # Check if the url is a playlist or a track
        if playlist:
            total_tracks = sp.playlist_tracks(self.url, limit=1)['total']
            for offset in range(0, total_tracks, 1):
                tracks = sp.playlist_tracks(self.url, additional_types=('track',), offset=offset, limit=1)
                track = tracks["items"][0]['track']
                
                if track:
                    metadata.append(Track(
                                track['name'], 
                                track['artists'][0]['name'], 
                                track["album"]["name"],
                                track["album"]["release_date"]))

                print(f"Fetching data.. {offset+1} / {total_tracks}")

        elif not playlist:
            tracks = sp.track(self.url)
            metadata.append(Track(tracks["name"], 
                        tracks["artists"][0]["name"], 
                        tracks["album"]["name"],
                        tracks["album"]["release_date"]))
        else:
            raise KeyError("Unexpected Spotify Url")
        return metadata

# Clear the terminal
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

# Spotify URL parser help determind either the url is a playlist or a track.
def spotify_url_parser(url: str) -> bool:
    urlList = url.split("/")[3:]
    if "track" in urlList:
        return False
    elif "playlist" in urlList:
        return True
    else:
        raise KeyError("Please enter the correct url.")

def sanitize_filename(name):
    invalid_chars = R'<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, '_')
    return name.strip()

# Use for changing file name
def change_filename(title, output_path):
    counter = 0
    sanitized_title = sanitize_filename(title)
    files = list(output_path.iterdir())
    ext = "mp3"
    recently_added_file = max(files, key=lambda f: (output_path / f).stat().st_mtime)
    
    old_name = output_path / recently_added_file
    new_name = output_path / f"{sanitized_title}.{ext}"

    while new_name.exists():
        counter += 1
        new_countered_name = output_path / f"{sanitized_title}({counter}).{ext}"
        if new_countered_name.exists():
            continue
        else:
            new_name.rename(new_countered_name)
            print(f"Changing name from '{new_name}' to '{new_countered_name}'")
            return

    print(f"Changing name from '{old_name}' to '{new_name}'")
    old_name.rename(new_name)

# Yt_dlp Download function
def dowload(data, output_path):

    # Download options
    ydl_opts = config.DownloaderOptions()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(Metadata_replacerPP(data), when='post_process')
        ydl.download([f"{data.title} {data.artist} lyrics"])

    time.sleep(0.5)
    change_filename(data.title, output_path)

def main():
    clear_terminal()
    url = input("Enter Spotify URL(Song/Playlist): ").strip()
    track = Metadata(url)
    metadata = track.track_metadata(playlist=spotify_url_parser(url))
    if not metadata:
        print("No metadata found for the provided URL.")
        sys.exit(1)
    for data in metadata:
        dowload(data, out_path)
        print("\n")

try:
    if __name__ == "__main__":
       main()
            
except Exception as e:
    print("Error occured", e)