import yt_dlp
import os
import sys
import time
from dotenv import load_dotenv
from mutagen.id3 import ID3, TPE1 , TIT2, TALB, TYER, TPE2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
load_dotenv()

# Settings
sys.path.append(os.getcwd())
auth_manager = SpotifyClientCredentials( 
    client_id=os.getenv('CILENT_ID'), 
    client_secret=os.getenv('CILENT_SECRET')
    )
sp = spotipy.Spotify(auth_manager=auth_manager)
out_path = "C:/Users/zigma/Music/Songs"

# Create a Directory
if not os.path.exists(out_path):
    os.makedirs(out_path)
    
# Class which will be used in yt_dlp Postprocessor -> Use to add metadata to a file.
class Metadata_replacerPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info,):
        global data
        audiopath = info['filepath']
        audio = ID3(audiopath)
        audio.add(TIT2(encoding=3, text=data[0]))
        audio.add(TPE1(encoding=3, text=data[1]))
        audio.add(TALB(encoding=3, text=data[2]))
        audio.add(TYER(encoding=3, text=data[3]))
        audio.save()

        return [], info
    
# A place holder for a file's metadata before inserting in using Metadata_replacerPP()
class Metadata():
    global sp
    def __init__(self, url:str):
        self.url = url

    # Append each metadata lists in to a list. Metadata list -> [name, artists, album, release date]
    def track_metadata(self, playlist:bool) -> list:
        metadata = []
        current_track = 0
        if playlist:
            while True:
                tracks = sp.playlist_tracks(self.url, limit=100, offset=current_track, additional_types=('track',))
                track = tracks["items"][0]['track']
                total_tracks = tracks['total']

                current_track += 1
                metadata.append([track['name'], 
                            track['artists'][0]['name'], 
                            track["album"]["name"],
                            track["album"]["release_date"]])

                print(f"Fetching data.. {current_track} / {total_tracks}")

                if current_track == total_tracks:
                    break
                else:
                    pass

        elif not playlist:
            tracks = sp.track(self.url)
            metadata.append([tracks["name"], 
                        tracks["artists"][0]["name"], 
                        tracks["album"]["name"],
                        tracks["album"]["release_date"],])
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
    sanitized_title = sanitize_filename(title)
    files = os.listdir(output_path)
    ext = "mp3"
    recently_added_file = max(files, key=lambda f: os.path.getmtime(os.path.join(out_path, f)))
    
    old_name = os.path.join(output_path, recently_added_file)
    new_name = os.path.join(output_path, f"{sanitized_title}.{ext}")

    if os.path.exists(old_name):
        time.sleep(0.5)

    print(f"Changing name from '{old_name}' to '{new_name}'")
    os.rename(old_name, new_name)

# Yt_dlp Download function
def dowload(title, artists, output_path):

    # Download options
    ydl_opts = {
        'default_search': 'ytsearch',
        'noplaylist' : True,
        'noprogress' : True,
        'no_warnings' : True,
        "cookiefile": "C:/Users/zigma/OneDrive/Documents/cookies.txt",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'Metadata_replacerPP': [],
        'format': 'bestaudio/best',
        #'progress_hooks': [lambda d: print(f"Downloading: ({d['_percent_str']})")],
        'outtmpl': f'{output_path}/%(title)s.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(Metadata_replacerPP(), when='post_process')
        ydl.download([f"{title} {artists} lyrics"])

    time.sleep(0.5)
    change_filename(title, out_path)

try:
    url = input("Enter Spotify URL(Song/Playlist): ")
    track = Metadata(url)
    metadata = track.track_metadata(playlist=spotify_url_parser(url))
    for data in metadata:
            title = data[0]
            artists = data[1]
            dowload(title, artists, out_path)
            print("\n")
            
except Exception as e:
    print("Error occured", e)