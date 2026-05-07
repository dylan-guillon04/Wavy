import customtkinter as ctk
import os
import sounddevice as sd
import numpy as np
from PIL import Image
from AudioHandler import AudioHandler
from FilterProcessor import FilterProcessor

COLORS = {
    "background": "#121212",
    "menu": "#181818",
    "top_gradient": "#404040",
    "bottom_gradient": "#282828",
    "primary_text": "#ffffff",
    "secondary_text": "#B3B3B3",
    "main": "#3b4ccc",
    "secondary": "#E24211",
}


ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

FILTER_IMG_FILES = {
    "Passe bas": "filter-lowpass.png",
    "Passe haut": "filter-highpass.png",
    "Sélecteur": "filter-bandpass.png",
    "Rejecteur": "filter-notch.png"
}


def get_filter_icon_path(filename):
    return os.path.join(os.path.dirname(__file__), "statics", filename)


class DragableFilterBlock(ctk.CTkFrame):
    def __init__(self, master, filter_type, **kwargs):
        super().__init__(master, fg_color=COLORS["top_gradient"], border_width=2, border_color=COLORS["main"],
                         corner_radius=10, width=120, height=80, **kwargs)
        self.pack_propagate(False)
        
        icon_path = get_filter_icon_path(FILTER_IMG_FILES[filter_type])
        self.icon_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(36, 36))
        self.icon_label = ctk.CTkLabel(self, image=self.icon_image, text="")
        self.icon_label.pack(padx=10, pady=(10, 0))

        self.label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color=COLORS["primary_text"])
        self.label.pack(padx=10, pady=(4, 0))

        self.bind("<Enter>", self.on_enter)
        self.label.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.label.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(border_color=COLORS["secondary"])

    def on_leave(self, event):
        self.configure(border_color=COLORS["main"])



class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wavy - Audio Filter Pro")
        self.geometry("1400x800")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["background"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #### Main Frame
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        ### Top Bar
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS["menu"], corner_radius=10, height=100)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)
        
        # Import / Export buttons
        self.actions_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.actions_frame.place(relx=0.02, rely=0.5, anchor="w")
        ctk.CTkButton(self.actions_frame, text="Importer", fg_color=COLORS["main"], hover_color=COLORS["secondary"]).pack(pady=5, fill="x")
        ctk.CTkButton(self.actions_frame, text="Enregistrer", fg_color="transparent", hover_color=COLORS["secondary"], border_width=1).pack(pady=5, fill="x")

        # Filters blocks
        self.filters_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.filters_frame.place(relx=0.5, rely=0.5, anchor="center")
        for i, filter_type in enumerate(FILTER_IMG_FILES.keys()):
            DragableFilterBlock(self.filters_frame, filter_type).grid(row=0, column=i+1, padx=10)

        #### Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["bottom_gradient"], corner_radius=10)
        self.content_frame.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        
        


if __name__ == "__main__":
    app = App()
    app.mainloop()