import customtkinter as ctk


def init_homepage(app):
    """
    Load the home/welcome page.
    """
    app.clear_content_frame()

    # Adjust text layout to ensure proper wrapping
    ctk.CTkLabel(
        app.content_frame,
        text="Welcome to Rian Video Processing Tool",
        font=("Helvetica", 24, "bold"),
        wraplength=800,  # Add wrap length
        justify="center",  # Center-align the text
    ).pack(pady=40)

    ctk.CTkLabel(
        app.content_frame,
        text=(
            "This tool allows you to process videos locally or "
            "download YouTube videos (including playlists) with ease."
        ),
        font=("Helvetica", 16),
        wraplength=800,  # Add wrap length
        justify="center",  # Center-align the text
    ).pack(pady=10)