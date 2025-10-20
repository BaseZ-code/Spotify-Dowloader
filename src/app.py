from .downloader import SpotifyDownloader
import importlib.resources as res
from PIL import Image
import customtkinter
from tkinter import filedialog
from pathlib import Path
import threading
import time
        
# Main Application Class
class myApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.output_path = Path.home() / 'Music'
        self.title("Spotify Downloader")
        self.geometry("500x200")
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure((0,1,2,4,5), weight=0)
        self.resizable(False, False)
        
        # Load icons
        self.icons_file = ["light.png", "black.png"]
        self.icons = {}
        self._icon_paths = []  # Store persistent references to the path objects
        for icon in self.icons_file:
            icon_path = res.files("src.assets") / icon
            self._icon_paths.append(icon_path)
            self.icons[icon] = Image.open(icon_path)

        # Light/Dark mode icon
        self.lightModeicon = customtkinter.CTkImage(light_image=self.icons["light.png"],
                                  dark_image=self.icons["black.png"],
                                  size=(30, 30))
        
        # UI Elements
        self.title_label = customtkinter.CTkLabel(self, 
                                            text="Spotify Downloader",
                                            font=("Montserrat", 32, "bold"),
                                            fg_color="transparent")
        self.title_label.grid(row=0, column=1, columnspan=2, sticky="w", padx=10, pady=10)

        # Output path label and browse button
        self.file_label = customtkinter.CTkLabel(self,
                                            text=f"Saving to: {self.output_path}",
                                            font=("Montserrat", 13),
                                            fg_color="transparent")
        self.file_label.grid(row=4, column=1, columnspan=2, sticky="w")
        self.browse_button = customtkinter.CTkButton(self, text="Browse", 
                                              text_color= ("#000000", "#FFFFFF"),
                                              width=65,
                                              command=self.browse_button_callback, 
                                              fg_color=("#68EEC6", "#078345"))
        self.browse_button.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Cookies file browse button
        self.browse_cookies_button = customtkinter.CTkButton(self, text="Add Cookies",
                                                text_color= ("#000000", "#FFFFFF"),
                                                width=100,
                                                command=self.cookeis_button_callback, 
                                                fg_color=("#F07474", "#8B0000"))
        self.browse_cookies_button.grid(row=4, column=2, padx=10, pady=10, sticky="e")

        # Spotify URL entry and download button
        self.entry = customtkinter.CTkEntry(self, width=250, placeholder_text="Enter Spotify URL")
        self.entry.grid(row=2, column=1)

        self.download_button = customtkinter.CTkButton(self, text="Download", 
                                              text_color= ("#000000", "#FFFFFF"),
                                              command=self.button_callback, 
                                              fg_color=("#68EEC6", "#078345"))
        self.download_button.grid(row=2, column=2, padx=10, pady=10, sticky="e")

        # Appearance mode switcher
        self.appearance_switcher = customtkinter.CTkButton(self, 
                                                           image=self.lightModeicon, 
                                                           text="", 
                                                           command=self.appearance_mode, 
                                                           width=10, height=30, 
                                                           fg_color=("#D3D3D3", "#4F4F4F"),
                                                           hover_color=("#878787", "#7A7A7A") )
        self.appearance_switcher.grid(row=0, column=0, padx=10, pady=10)

        # Progress bar
        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.progressbar.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

    # Toggle appearance mode
    def appearance_mode(self):
        if customtkinter.get_appearance_mode() == "Dark":
             return customtkinter.set_appearance_mode("Light")
        else:
             return customtkinter.set_appearance_mode("Dark")
    
    # Browse button callback
    def browse_button_callback(self):
        # Finding folder path
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_path = folder_path
            self.file_label.configure(text=f"Saving to: {self.output_path}")
    
    # Cookies button callback
    def cookeis_button_callback(self):
        # Finding cookies file path
        cookies_path = filedialog.askopenfile(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if cookies_path:
            self.cookies_path = cookies_path.name
            self.browse_cookies_button.configure(fg_color=("#68EEC6", "#078345"))
        else:
            self.browse_cookies_button.configure(fg_color=("#F07474", "#8B0000"))

    # Download button callback
    def button_callback(self):
        # Getting user input
        user_input = self.entry.get().strip()
        try:
            # Checking for valid input and cookies file
            if user_input and self.browse_cookies_button.cget("fg_color") == ("#68EEC6", "#078345"):
                self.progressbar.start()
                self.update_ui_ongoing_download()
                self.buttons_state("disabled")
                download_thread = threading.Thread(target=self.song_download, args=(user_input,), daemon=True)
                download_thread.start()

            # If not valid input or cookies file
            if not self.browse_cookies_button.cget("fg_color") == ("#68EEC6", "#078345"):
                print("Please add a valid cookies file.")
                self.progressbar.stop()
            if not user_input:
                print("Please enter a valid Spotify URL.")
                self.progressbar.stop()
        except Exception as e:
            print(f"Error: {e}")
            self.buttons_state("normal")
            self.progressbar.stop()

    # MAINPART of the GUI app which handles downloading
    def song_download(self, user_input):
        # Recheck for output path and cookies path
        if not hasattr(self, 'output_path') or not hasattr(self, 'cookies_path'):
            raise ValueError("Output path or Cookies path is not set. Please select recheck agian if you selected folder or provided cookies.")
        try:
            # Start downloading concurrently
            downloader = SpotifyDownloader(user_input, Path(self.output_path), Path(self.cookies_path))
            metadata = downloader.track_metadata(playlist=downloader._SpotifyDownloader__spotify_url_parser(user_input))
            downloader.concurrent_download(metadata)
            self.buttons_state("normal")
            self.after(0, self.update_ui_on_completion)
        except Exception as e:
            print(f"Error during download: {e}")
            self.buttons_state("normal")
            self.after(0, self.update_ui_on_error)

    # Disable/Enable buttons during download
    def buttons_state(self, state: str):
        self.download_button.configure(state=state)
        self.entry.configure(state=state)
        self.browse_button.configure(state=state)

    # UI updates during downloading/ on completion/ error
    def update_ui_ongoing_download(self):
        self.entry.delete(0, 'end')
        self.entry.insert(0, "Currently Downloading...")

    def update_ui_on_completion(self):
      self.entry.delete(0, 'end')
      self.entry.insert(0, "All downloads completed.")
      time.sleep(1)
      self.entry.delete(0, 'end')
      self.progressbar.stop()

    def update_ui_on_error(self):
      self.entry.delete(0, 'end')
      self.entry.insert(0, "An error occurred during download.")
      self.progressbar.stop()