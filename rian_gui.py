import os
import socket
import platform
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk
import customtkinter as ctk

# Logger utilities
from logger_utils import (
    initialize_log_file,
    append_to_log,
    send_log_to_server,
)

# Other utilities and logic
from utils import (
    format_duration,
    calculate_processing_time,
    run_in_thread,
    get_video_length,
)
import youtube_logic
import local_processing_logic

# License validation/activation logic
from license_utils import ensure_valid_license_on_startup

# Promotions utility
from promotions_utils import fetch_promotions

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

        # First, ensure valid license before anything else
        ensure_valid_license_on_startup(self)

        # Initialize local log file
        initialize_log_file()

        # Layout: Left nav + main content
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e3c72")
        self.nav_frame.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        self.promotions = []  # Store fetched promotions
        self.client_id = socket.gethostname()  # Default client ID (can be updated if needed)

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

        # Fetch promotions every time the homepage loads
        self.promotions = fetch_promotions(self.client_id)

        # Wrapper Box for the entire content
        wrapper_box = ctk.CTkFrame(
            self.content_frame,
            corner_radius=15,
            fg_color="#e6e6e6",  # Light gray background for contrast
            width=900,
            height=650
        )
        wrapper_box.pack(padx=20, pady=20, fill="both", expand=True)

        # Welcome Header
        ctk.CTkLabel(
            wrapper_box,
            text="Welcome to Rian Video Processing Tool",
            font=("Helvetica", 28, "bold"),
            text_color="#1e3c72",  # A deep blue for emphasis
            justify="center",
        ).pack(pady=(30, 10))

        # Subheader
        ctk.CTkLabel(
            wrapper_box,
            text=(
                "Your all-in-one solution for video processing and YouTube downloads.\n"
                "Easily clean audio, process local videos, or download from YouTube."
            ),
            font=("Helvetica", 16),
            text_color="black",
            wraplength=800,
            justify="center",
        ).pack(pady=(10, 30))

        # Promotions Section Title
        ctk.CTkLabel(
            wrapper_box,
            text="Current Promotions",
            font=("Helvetica", 22, "bold"),
            text_color="#1e3c72",
            justify="center",
        ).pack(pady=(10, 10))

        # Display Promotions
        promotions_frame = ctk.CTkFrame(
            wrapper_box,
            corner_radius=10,
            fg_color="#ffffff",
            width=850,
            height=400
        )
        promotions_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.display_promotions(promotions_frame)

    def display_promotions(self, parent_frame):
        """Display fetched promotions in styled boxes within the given parent frame."""
        if not self.promotions or len(self.promotions) == 0:
            ctk.CTkLabel(
                parent_frame,
                text="No promotions available at the moment.",
                font=("Helvetica", 14),
                fg_color="#f0f0f0",
                text_color="black",
                corner_radius=8,
                width=800,
                height=40,
                justify="center"
            ).pack(pady=10)
            return

        for promotion in self.promotions:
            ctk.CTkLabel(
                parent_frame,
                text=promotion,
                font=("Helvetica", 16),
                fg_color="#f9f9f9",
                text_color="black",
                corner_radius=8,
                width=800,
                height=50,
                wraplength=780,
                anchor="w",
                justify="left"
            ).pack(pady=5, padx=10)

    ############################################################################
    #                       YOUTUBE DOWNLOAD PAGE
    ############################################################################

    def init_youtube_download(self):
        """UI for downloading from YouTube (video or playlist)."""
        self.clear_content_frame()
        progress_label = ctk.StringVar(value="Status: Ready")
        progress_bar = ttk.Progressbar(self.content_frame, orient="horizontal", mode="determinate", length=600)
        youtube_link_var = ctk.StringVar()

        ctk.CTkLabel(
            self.content_frame,
            text="Download YouTube Video or Playlist",
            font=("Helvetica", 18)
        ).pack(pady=20)

        # Wider entry field
        ctk.CTkEntry(
            self.content_frame,
            textvariable=youtube_link_var,
            placeholder_text="Enter your YouTube link here",
            width=600,
        ).pack(pady=20)

        ctk.CTkButton(
            self.content_frame,
            text="Download",
            command=lambda: run_in_thread(
                youtube_logic.process_youtube_video,
                self,
                youtube_link_var,
                progress_label,
                progress_bar
            )
        ).pack(pady=20)

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
                self,
                progress_label,
                progress_bar
            ),
        ).pack(pady=20)

        progress_bar.pack(pady=10)
        ctk.CTkLabel(self.content_frame, textvariable=progress_label, font=("Helvetica", 14)).pack(pady=10)


# Entry point if running as script
if __name__ == "__main__":
    app = RianVideoProcessingTool()
    app.mainloop()