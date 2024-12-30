import os
import socket
import platform
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

import customtkinter as ctk

# Import your logger utils
from logger_utils import (
    initialize_log_file,
    append_to_log,
    send_log_to_server,
)

# Import utilities and logic
from utils import (
    format_duration,
    calculate_processing_time,
    run_in_thread,
    get_video_length,
)
import youtube_logic
import local_processing_logic

###############################################################################
#                      MAIN GUI APPLICATION CLASS
###############################################################################

class RianVideoProcessingTool(ctk.CTk):
    """
    Main application class for the Rian Video Processing Tool.
    """
    def __init__(self):
        super().__init__()
        self.title("Rian Video Processing Tool")
        self.geometry("1000x750")
        self.resizable(False, False)

        # CustomTkInter appearance settings
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Initialize local log file
        initialize_log_file()

        # Layout: Left nav + main content
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e3c72")
        self.nav_frame.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.init_navbar()
        self.init_homepage()

    ############################################################################
    #                          NAVIGATION / LAYOUT
    ############################################################################

    def init_navbar(self):
        """Create buttons and labels for the navigation menu."""
        ctk.CTkLabel(
            self.nav_frame,
            text="Rian Video Processing Tool",
            font=("Helvetica", 20, "bold"),
            fg_color="#142850",
            text_color="white",
            corner_radius=8,
        ).pack(pady=20)

        ctk.CTkButton(self.nav_frame, text="Home", command=self.init_homepage).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="Video To Clean Audio", command=self.init_local_processing).pack(pady=10)
        ctk.CTkButton(self.nav_frame, text="YouTube Download", command=self.init_youtube_download).pack(pady=10)

    def clear_content_frame(self):
        """Clear any widgets from the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    ############################################################################
    #                                HOME PAGE
    ############################################################################

    def init_homepage(self):
        """Load the home/welcome page."""
        self.clear_content_frame()

        # Adjust text layout to ensure proper wrapping
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome to Rian Video Processing Tool",
            font=("Helvetica", 24, "bold"),
            wraplength=800,  # Add wrap length
            justify="center",  # Center-align the text
        ).pack(pady=40)

        ctk.CTkLabel(
            self.content_frame,
            text=(
                "This tool allows you to process videos locally or "
                "download YouTube videos (including playlists) with ease."
            ),
            font=("Helvetica", 16),
            wraplength=800,  # Add wrap length
            justify="center",  # Center-align the text
        ).pack(pady=10)

    ############################################################################
    #                       YOUTUBE DOWNLOAD PAGE
    ############################################################################

    def init_youtube_download(self):
        """UI for downloading from YouTube (video or playlist)."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)
        youtube_link_var = ctk.StringVar()

        # Page Title
        ctk.CTkLabel(
            self.content_frame,
            text="Download YouTube Video or Playlist",
            font=("Helvetica", 18)
        ).pack(pady=20)

        # Wider Entry for YouTube link
        ctk.CTkEntry(
            self.content_frame,
            textvariable=youtube_link_var,
            placeholder_text="Enter your YouTube link here",
            width=600,  # Set width for the entry box
        ).pack(pady=20)

        # Download Button
        ctk.CTkButton(
            self.content_frame,
            text="Download",
            command=lambda: run_in_thread(
                youtube_logic.process_youtube_video,
                self,  # pass the app
                youtube_link_var,
                progress_label,
                progress_bar
            )
        ).pack(pady=20)

        # Progress Bar and Label
        progress_bar.pack(pady=10)
        ctk.CTkLabel(
            self.content_frame,
            textvariable=progress_label,
            font=("Helvetica", 14)
        ).pack(pady=10)

    ############################################################################
    #                     LOCAL VIDEO PROCESSING PAGE
    ############################################################################

    def init_local_processing(self):
        """UI for local video processing."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)

        ctk.CTkLabel(self.content_frame, text="Process Local Video File", font=("Helvetica", 18)).pack(pady=20)

        ctk.CTkButton(
            self.content_frame,
            text="Upload File",
            command=lambda: run_in_thread(
                local_processing_logic.process_local_video,
                self,  # pass the app
                progress_label,
                progress_bar
            ),
        ).pack(pady=20)

        progress_bar.pack(pady=10)
        ctk.CTkLabel(self.content_frame, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)