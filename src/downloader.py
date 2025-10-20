import yt_dlp
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from mutagen.id3 import ID3, TPE1 , TIT2, TALB, TDRC
import spotipy
import concurrent.futures
import imageio_ffmpeg
from spotipy.oauth2 import SpotifyClientCredentials
load_dotenv()

# Initialize Spotify API
auth_manager = SpotifyClientCredentials( 
    client_id=os.getenv('CLIENT_ID'),    client_secret=os.getenv('CLIENT_SECRET')
    )

try:
    sp = spotipy.Spotify(auth_manager=auth_manager)
except spotipy.SpotifyException as e:
    print("Spotify API authentication failed. Please check your CLIENT_ID and CLIENT_SECRET.")
    sys.exit(1)  

@dataclass
class Track:
    title: str
    artist: str
    album: str
    release_date: str

# Downloader
class SpotifyDownloader():
    def __init__(self, url:str, out_path:str, cookies_path:str) -> None:
        self.sp = sp
        self.url = url
        self.output_path = Path(out_path)
        self.cookies_path = Path(cookies_path)
        self.ffmpeg_path = str(imageio_ffmpeg.get_ffmpeg_exe())
        self.preferredcodec = "mp3"
        self.format = "bestaudio[ext=mp3]/best"

    # Spotify URL parser help determind either the url is a playlist or a track.
    def __spotify_url_parser(self, url:str) -> bool:
        urlList = url.split("/")[3:]
        if "track" in urlList:
            return False
        elif "playlist" in urlList:
            return True
        else:
            raise ValueError("Invalid Spotify URL format. Expected track or playlist URL.")
        
    # Sanitize file name
    def sanitize_filename(self, name:str) -> str:
        invalid_chars = R'<>:"/\\|?*'
        for ch in invalid_chars:
            name = name.replace(ch, '_')
        return name.strip()
    
    def track_metadata(self, playlist:bool) -> list:
        metadata = []
        # Check if the url is a playlist or a track
        limit_tracks = 100
        current_track = 0
        try:
            if playlist:
                total_tracks = self.sp.playlist_tracks(self.url, limit=1)['total']
                for offset in range(0, total_tracks, limit_tracks):
                    tracks = self.sp.playlist_tracks(self.url, additional_types=('track',), offset=offset, limit=limit_tracks)
                    for item in tracks["items"]:
                        current_track+=1
                        track = item["track"]
                        if track:
                            metadata.append(Track(
                                        track['name'], 
                                        track['artists'][0]['name'], 
                                        track["album"]["name"],
                                        track["album"]["release_date"]))
                        else:
                            print("Skipping a local track or unavailable track.")
                            continue
                        print(f"Fetching data.. {current_track} / {total_tracks}")

                    

            else:
                tracks = self.sp.track(self.url)
                metadata.append(Track(tracks["name"], 
                            tracks["artists"][0]["name"], 
                            tracks["album"]["name"],
                            tracks["album"]["release_date"]))
        except Exception as e:
            print(f"Error fetching metadata from Spotify: {e}")
            return []
        return metadata

    def __DownloaderOptions(self):
        ydl_opts = {
            'default_search': 'ytsearch',
            'noplaylist' : True,
            'quiet' : True,
            'noprogress' : True,
            'no_warnings' : True,
            'ffmpeg_location': self.ffmpeg_path,
            "cookiefile": self.cookies_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.preferredcodec,
                'preferredquality': '192',
            }],
            'format': self.format,
            'outtmpl': f'{self.output_path}/%(title)s.%(ext)s'
        }
        return ydl_opts
    
    # Yt_dlp Download function
    def download(self, data:Track) -> None:
        # Download options
        sanitized_title = self.sanitize_filename(data.title)
        output_template = self.output_path / f"{sanitized_title}.%(ext)s"

        ydl_opts = self.__DownloaderOptions()
        ydl_opts['outtmpl'] = str(output_template)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.add_post_processor(Metadata_replacerPP(data), when='post_process')
                ydl.download([f"{data.title} {data.artist} lyrics"])
        except Exception as e:
            print(f"Error downloading {data.title}: {e}")

        time.sleep(0.5) # Small delay to avoid overwhelming the system

    def concurrent_download(self, metadata:list) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_track = {executor.submit(self.download, data): data for data in metadata}
            for future in concurrent.futures.as_completed(future_to_track):
                data = future_to_track[future]
                try:
                    future.result()
                    print(f"Downloaded: {data.title} by {data.artist}")
                except Exception as e:
                    print(f"Error downloading {data.title} by {data.artist}: {e}")

# Class which will be used in yt_dlp Postprocessor -> Use to add metadata to a file.
class Metadata_replacerPP(yt_dlp.postprocessor.PostProcessor):

    def __init__(self, metadata):
        super().__init__()
        self.name, self.artist, self.album, self.release_date = metadata.title, metadata.artist, metadata.album, metadata.release_date
    def run(self, info):
        audiopath = info['filepath']
        try:
            audio = ID3(audiopath)
            audio.add(TIT2(encoding=3, text=self.name))
            audio.add(TPE1(encoding=3, text=self.artist))
            audio.add(TALB(encoding=3, text=self.album))
            audio.add(TDRC(encoding=3, text=self.release_date))
            audio.save()
        except Exception as e:
            print(f"Failed to add metadata for {self.name} by {self.artist}: {e}")

        return [], info


# Clear the terminal
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_terminal()
    url = input("Enter Spotify URL(Song/Playlist): ").strip()
    track_downloader = SpotifyDownloader(url, out_path=r"C:\Users\zigma\Downloads", cookies_path=r"C:\OneDrive\Documents\GitHub\Spotify-Dowloader\cookies.txt")
    track_downloader.output_path.mkdir(parents=True, exist_ok=True)  # Create the output directory if it doesn't exist
    metadata = track_downloader.track_metadata(playlist=track_downloader._SpotifyDownloader__spotify_url_parser(url))
    
    if not metadata:
        print("No metadata found for the provided URL.")
        sys.exit(1)
    else:
        track_downloader.concurrent_download(metadata)
        print("All downloads completed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error occurred", e)
        sys.exit(1)