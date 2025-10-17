from downloader import SpotifyDownloader
from PIL import Image, ImageTk 
import customtkinter
import os
import sys
import time

class myApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Downloader")
        self.geometry("500x300")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.resizable(False, False)

        self.button = customtkinter.CTkButton(self, text="Download", command=self.button_callback, fg_color=("#DB3E39", "#821D1A"))
        self.button.grid(row=0, column=1, padx=50, pady=20, sticky="ew")

        self.button = customtkinter.CTkButton(self, text="Download", command=self.button_callback, fg_color=("#DB3E39", "#821D1A"))
        self.button.grid(row=0, column=1, padx=50, pady=20, sticky="ew")

    def button_callback(self):
            print("Something")

        

app = myApp()
app.mainloop()
