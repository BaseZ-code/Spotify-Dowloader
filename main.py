import yt_dlp
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from mutagen.id3 import ID3, TPE1 , TIT2, TALB, TYER
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
load_dotenv()

# Settings
Path.cwd() / "Spotify-Dowloader"

# Initialize Spotify API
auth_manager = SpotifyClientCredentials( 
    client_id=os.getenv('CLIENT_ID'),    client_secret=os.getenv('CLIENT_SECRET')
    )
sp = spotipy.Spotify(auth_manager=auth_manager)

@dataclass
class Track:
    title: str
    artist: str
    album: str
    release_date: str

# Downloader
class SpotifyDownloader():
    global sp
    def __init__(self, url:str) -> None:
        self.url = url
        self.output_path = Path.home() / "Music" / "Songs"
        self.cookies_path = Path.home() / "OneDrive" / "Documents" / "cookies.txt"
        self.preferedcodec = "mp3"
        self.format = "bestaudio[ext=mp3]/best"

    # Spotify URL parser help determind either the url is a playlist or a track.
    def spotify_url_parser(self, url:str) -> bool:
        urlList = url.split("/")[3:]
        if "track" in urlList:
            return False
        elif "playlist" in urlList:
            return True
        else:
            raise KeyError("Please enter the correct url.")
    # Sanitize file name
    def sanitize_filename(self, name:str) -> str:
        invalid_chars = R'<>:"/\\|?*'
        for ch in invalid_chars:
            name = name.replace(ch, '_')
        return name.strip()
    
    # Append each metadata lists into a list. Metadata list -> [name, artists, album, release date]
    def track_metadata(self, playlist:bool) -> list:
        metadata = []
        # Check if the url is a playlist or a track
        limit_tracks = 100
        if playlist:
            total_tracks = sp.playlist_tracks(self.url, limit=1)['total']
            for offset in range(0, total_tracks, 1):
                tracks = sp.playlist_tracks(self.url, additional_types=('track',), offset=offset, limit=limit_tracks)
                print(tracks)

                for item in tracks["items"]:
                    track = item['track']
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

    # Use for changing file name
    def change_filename(self, title:str) -> None:
        counter = 0
        sanitized_title = self.sanitize_filename(title)
        files = list(self.output_path.iterdir())
        ext = "mp3"
        recently_added_file = max(files, key=lambda f: (self.output_path / f).stat().st_mtime)
        
        old_name = self.output_path / recently_added_file
        new_name = self.output_path / f"{sanitized_title}.{ext}"

        while new_name.exists():
            counter += 1
            new_countered_name = self.output_path / f"{sanitized_title}({counter}).{ext}"
            if new_countered_name.exists():
                continue
            else:
                new_name.rename(new_countered_name)
                print(f"Changing name from '{new_name}' to '{new_countered_name}'")
                return

        print(f"Changing name from '{old_name}' to '{new_name}'")
        old_name.rename(new_name)

    def DownloaderOptions(self):
        ydl_opts = {
            'default_search': 'ytsearch',
            'noplaylist' : True,
            'noprogress' : False,
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
    
    # Yt_dlp Download function
    def dowload(self, data:Track) -> None:
        # Download options
        ydl_opts = self.DownloaderOptions()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(Metadata_replacerPP(data), when='post_process')
            ydl.download([f"{data.title} {data.artist} lyrics"])

        time.sleep(0.5)
        self.change_filename(data.title)

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


# Clear the terminal
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_terminal()
    url = input("Enter Spotify URL(Song/Playlist): ").strip()
    track = SpotifyDownloader(url)
    track.output_path.mkdir(parents=True, exist_ok=True)  # Create the output directory if it doesn't exist
    metadata = track.track_metadata(playlist=track.spotify_url_parser(url))
    if not metadata:
        print("No metadata found for the provided URL.")
        sys.exit(1)
    for data in metadata:
        track.dowload(data)
        print(f"Downloaded: {data.title} - {data.artist}")
        print("\n")

try:
    if __name__ == "__main__":
       main()
            
except Exception as e:
    print("Error occured", e)