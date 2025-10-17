from downloader import SpotifyDownloader
from PIL import Image, ImageTk 
import customtkinter
import os
import sys
import time
import threading
        

class myApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Downloader")
        self.geometry("500x200")
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure((0,1,2,4), weight=0)
        self.resizable(False, False)

        self.lightModeicon = customtkinter.CTkImage(light_image=Image.open("C:/OneDrive/Documents/GitHub/Spotify-Dowloader/assests/Nigger.png"),
                                  dark_image=Image.open("C:/OneDrive/Documents/GitHub/Spotify-Dowloader/assests/Nigger.png"),
                                  size=(30, 30))
        
        self.label = customtkinter.CTkLabel(self, 
                                            text="Spotify Downloader",
                                            font=("Montserrat", 32, "bold"),
                                            fg_color="transparent")
        self.label.grid(row=0, column=1, columnspan=2)

        self.entry = customtkinter.CTkEntry(self, width=250, placeholder_text="Enter Spotify URL")
        self.entry.grid(row=2, column=1)

        self.button = customtkinter.CTkButton(self, text="Download", command=self.button_callback, fg_color=("#3D1818", "#821D1A"))
        self.button.grid(row=2, column=2, padx=10, pady=10)

        self.appearance_switcher = customtkinter.CTkButton(self, image=self.lightModeicon, text="", command=self.appearance_mode, width=10, height=30, fg_color="#181818",hover_color="#000000" )
        self.appearance_switcher.grid(row=0, column=0, padx=10, pady=10)

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.progressbar.grid(row=4, column=0, columnspan=3, padx=30, pady=20, sticky="ew")

    def appearance_mode(self):
        if customtkinter.get_appearance_mode() == "Dark":
             return customtkinter.set_appearance_mode("Light")
        else:
             return customtkinter.set_appearance_mode("Dark")

    def button_callback(self):
        self.progressbar.start()
        user_input = self.entry.get().strip()
        if user_input:
            self.update_ui_ongoing_download()
            self.button.configure(state="disabled")
            self.entry.configure(state="disabled")
            download_thread = threading.Thread(target=self.song_download, args=(user_input,), daemon=True)
            download_thread.start()
        else:
            print("Please enter a valid Spotify URL.")
            self.progressbar.stop()

    def song_download(self, user_input):
        try:
            downloader = SpotifyDownloader(user_input)
            metadata = downloader.track_metadata(playlist=downloader.spotify_url_parser(user_input))
            downloader.concurrent_download(metadata)
            self.entry.configure(state="normal")
            self.button.configure(state="normal")
            self.after(0, self.update_ui_on_completion)
        except Exception as e:
            print(f"Error during download: {e}")
            self.entry.configure(state="normal")
            self.button.configure(state="normal")
            self.after(0, self.update_ui_on_error)

    def update_ui_ongoing_download(self):
        self.entry.delete(0, 'end')
        self.entry.insert(0, "Currently Downloading...")

    def update_ui_on_completion(self):
      self.entry.delete(0, 'end')
      self.entry.insert(0, "All downloads completed.")
      self.progressbar.stop()

    def update_ui_on_error(self):
      self.entry.delete(0, 'end')
      self.entry.insert(0, "An error occurred during download.")
      self.progressbar.stop()

app = myApp()
app.mainloop()
