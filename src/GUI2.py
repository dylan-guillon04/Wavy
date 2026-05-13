import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import time
import os
import sounddevice as sd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
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


class FilterBlock(ctk.CTkFrame):
    def __init__(self, master, filter_type, app_ref, **kwargs):
        super().__init__(master, fg_color=COLORS["top_gradient"], border_width=2, border_color=COLORS["main"],
                         corner_radius=10, width=220, height=100, **kwargs)
        self.pack_propagate(False)
        self.filter_type = filter_type
        self.app_ref = app_ref


        icon_path = get_filter_icon_path(FILTER_IMG_FILES[filter_type])
        self.icon_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(32, 32))
        self.icon_label = ctk.CTkLabel(self, image=self.icon_image, text="")
        self.icon_label.grid(row=1, column=0, rowspan=2, padx=5)

        self.title_label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color=COLORS["primary_text"], bg_color="transparent")
        self.title_label.grid(row=0, column=0, columnspan=3, padx=5, sticky="n")

        self.param_label = ctk.CTkLabel(self, text="Fréquence de coupure (Hz)", font=("Helvetica", 10), text_color=COLORS["secondary_text"])
        self.param_label.grid(row=1, column=1, padx=5, pady=5)
        self.param_entry = ctk.CTkEntry(self, width=60, height=20, font=("Helvetica", 10), fg_color=COLORS["bottom_gradient"], text_color=COLORS["primary_text"], border_width=2, border_color=COLORS["background"], corner_radius=5)
        self.param_entry.grid(row=1, column=2, padx=5, pady=5)
        self.param_entry.insert(0, "1000")
        self.param_entry.bind("<Return>", lambda e: self.update_slider(self.param_entry.get()))

        self.param_slider = ctk.CTkSlider(self, from_=20, to=20000, height=16, width=200, command=self.update_entry)
        self.param_slider.set(1000)
        self.param_slider.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

    def update_entry(self, value):
        freq = int(float(value))
        self.param_entry.delete(0, tk.END)
        self.param_entry.insert(0, str(freq))
        
    def update_slider(self, value):
        try:
            freq = int(value)
            self.param_slider.set(freq)
        except ValueError:
            pass


class DragableFilterBlock(ctk.CTkFrame):
    def __init__(self, master, filter_type, app_ref, **kwargs):
        super().__init__(master, fg_color=COLORS["top_gradient"], border_width=2, border_color=COLORS["main"],
                         corner_radius=10, width=120, height=80, **kwargs)
        self.pack_propagate(False)
        self.filter_type = filter_type
        self.app_ref = app_ref
        
        icon_path = get_filter_icon_path(FILTER_IMG_FILES[filter_type])
        self.icon_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(36, 36))
        self.icon_label = ctk.CTkLabel(self, image=self.icon_image, text="")
        self.icon_label.pack(padx=10, pady=(10, 0))

        self.label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color=COLORS["primary_text"])
        self.label.pack(padx=10, pady=(4, 0))

        self.bind("<ButtonPress-1>", self.on_start)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.ghost = None
        
    def on_start(self, event):
        self.ghost = ctk.CTkToplevel(self)
        self.ghost.overrideredirect(True)
        self.ghost.attributes("-alpha", 0.7)
        label = ctk.CTkLabel(self.ghost, text=self.filter_type, text_color=COLORS["primary_text"], font=("Helvetica", 12, "bold"), fg_color=COLORS["main"], width=120, height=80)
        label.pack(padx=10, pady=5)
        self.on_drag(event)

    def on_drag(self, event):
        if self.ghost:
            self.ghost.geometry(f"+{self.winfo_pointerx()-50}+{self.winfo_pointery()-20}")

    def on_drop(self, event):
        if self.ghost:
            self.ghost.destroy()
            self.ghost = None
            x, y = self.winfo_pointerxy()
            target = self.app_ref.winfo_containing(x, y)
            while target:
                if isinstance(target, AudioTrack):
                    target.add_filter_block(self.filter_type)
                    break
                target = target.master

    def on_enter(self, event):
        self.configure(border_color=COLORS["secondary"])

    def on_leave(self, event):
        self.configure(border_color=COLORS["main"])


class AudioTrack(ctk.CTkFrame):
    def __init__(self, master, file_path, **kwargs):
        super().__init__(master, fg_color=COLORS["bottom_gradient"], corner_radius=10, **kwargs)
        self.audio_handler = AudioHandler()
        self.file_path = file_path
        self.is_playing = False
        self.filter_blocks = []

        loaded = self.audio_handler.load_audio(file_path)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 0))

        # Load play/pause images
        play_icon_path = get_filter_icon_path("play.png")
        stop_icon_path = get_filter_icon_path("stop.png")
        self.play_image = ctk.CTkImage(light_image=Image.open(play_icon_path), size=(20, 20))
        self.pause_image = ctk.CTkImage(light_image=Image.open(stop_icon_path), size=(20, 20))

        self.play_pause_button = ctk.CTkButton(header, image=self.play_image, text="", width=30, height=30, fg_color=COLORS["main"], hover_color=COLORS["secondary"], command=self.toggle_play_pause, state="normal" if loaded else "disabled")
        self.play_pause_button.pack(side="left", padx=(0, 10))
        
        self.file_label = ctk.CTkLabel(header, text=os.path.basename(file_path), anchor="w", text_color=COLORS["primary_text"], font=("Helvetica", 14, "bold"))
        self.file_label.pack(side="left", fill="x", expand=True)

        # Matplotlib figure
        self.fig = Figure(figsize=(10, 2), dpi=80, facecolor=COLORS["background"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COLORS["background"])
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        self.canvas_widget = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_widget.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        
        self.mpl_canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_widget)
        self.mpl_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.playhead_line = None
        self.waveform_line = None

        self.playhead_id = None
        self.playhead_animating = False
        self.playhead_start_time = 0
        self.playhead_duration = 0
        self.canvas_width = 0
        self.canvas_height = 0
        self.waveform_cache = None
        self.playback_data = None
        self.time_axis = None
        self.filter_area = None

        if loaded:
            self.prepare_playback_data()
            self.after(50, self.draw_waveform)

    def prepare_playback_data(self):
        """Prépare les données audio normalisées une seule fois pour éviter recalcul à chaque play."""
        if self.audio_handler.data is not None:
            self.playback_data = self.audio_handler.data * 0.5

    def toggle_play_pause(self):
        if self.audio_handler.data is None:
            return

        if self.is_playing:
            sd.stop()
            self.is_playing = False
            self.play_pause_button.configure(image=self.play_image)
            self.stop_playhead()
        else:
            sd.stop()
            sd.play(self.playback_data, self.audio_handler.sample_rate)
            self.is_playing = True
            self.play_pause_button.configure(image=self.pause_image)
            self.start_playhead()
            threading.Thread(target=self._monitor_playback, daemon=True).start()
            
    def start_playhead(self):
        self.playhead_animating = True
        self.playhead_start_time = time.monotonic()
        self.playhead_duration = self.audio_handler.get_duration()
        self._animate_playhead()

    def stop_playhead(self):
        self.playhead_animating = False
        if self.playhead_line is not None:
            self.playhead_line.remove()
            self.playhead_line = None
            self.mpl_canvas.draw_idle()

    def _animate_playhead(self):
        if not self.is_playing or not self.playhead_animating:
            self.stop_playhead()
            return
        duration = self.playhead_duration
        if duration == 0:
            self.stop_playhead()
            return
        
        elapsed = time.monotonic() - self.playhead_start_time
        elapsed = max(0, min(elapsed, duration))
        
        # Remove old playhead line
        if self.playhead_line is not None:
            self.playhead_line.remove()
        
        # Draw new playhead line
        self.playhead_line = self.ax.axvline(x=elapsed, color=COLORS["secondary"], linewidth=2, alpha=0.8)
        self.mpl_canvas.draw_idle()
        
        if elapsed < duration and self.is_playing and self.playhead_animating:
            self.after(20, self._animate_playhead)
        else:
            self.stop_playhead()

    def _monitor_playback(self):
        try:
            sd.wait()
        except Exception:
            pass
        self.after(0, self._playback_finished)

    def _playback_finished(self):
        if self.is_playing:
            self.is_playing = False
            self.play_pause_button.configure(image=self.play_image)
        self.stop_playhead()

    def draw_waveform(self):
        """Dessine la waveform avec matplotlib."""
        self.ax.clear()
        
        data = self.audio_handler.data
        if data is None or len(data) == 0:
            self.mpl_canvas.draw_idle()
            return

        # Normalize data
        max_val = np.max(np.abs(data))
        normalized = data if max_val == 0 else data / max_val
        
        # Downsample for performance
        sample_rate = self.audio_handler.sample_rate
        duration = self.audio_handler.get_duration()
        num_points = min(len(normalized), 2000)  # Limit to 2000 points for performance
        sample_step = max(1, len(normalized) // num_points)
        reduced = normalized[::sample_step]
        time_axis = np.arange(len(reduced)) * sample_step / sample_rate
        self.time_axis = time_axis
        
        # Plot waveform
        self.ax.plot(time_axis, reduced, color=COLORS["main"], linewidth=0.8)
        self.ax.fill_between(time_axis, reduced, alpha=0.3, color=COLORS["main"])
        
        # Configure axes
        self.ax.set_xlim(0, duration)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_facecolor(COLORS["background"])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['bottom'].set_color(COLORS["secondary_text"])
        self.ax.tick_params(colors=COLORS["secondary_text"], labelsize=8)
        self.ax.set_xlabel('Time (s)', color=COLORS["secondary_text"], fontsize=8)
        self.ax.grid(True, alpha=0.2, color=COLORS["secondary_text"], linestyle='--', linewidth=0.5)
        
        self.mpl_canvas.draw_idle()
        
    def add_filter_block(self, filter_type):
        if self.filter_area is None:
            self.filter_area = ctk.CTkScrollableFrame(self, fg_color="transparent", height=100, orientation="horizontal")
            self.filter_area.pack(fill="x", padx=10)
        
        block = FilterBlock(self.filter_area, filter_type, app_ref=self)
        block.pack(side="left", padx=(0, 5))
        
        self.filter_blocks.append(block)


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
        self.import_button = ctk.CTkButton(self.actions_frame, text="Importer", fg_color=COLORS["main"], hover_color=COLORS["secondary"], command=self.import_audio)
        self.import_button.pack(pady=5, fill="x")
        ctk.CTkButton(self.actions_frame, text="Enregistrer", fg_color="transparent", hover_color=COLORS["secondary"], border_width=1).pack(pady=5, fill="x")

        # Filters blocks
        self.filters_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.filters_frame.place(relx=0.5, rely=0.5, anchor="center")
        for i, filter_type in enumerate(FILTER_IMG_FILES.keys()):
            DragableFilterBlock(self.filters_frame, app_ref=self, filter_type=filter_type).grid(row=0, column=i+1, padx=10)

        #### Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=10)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.track_area = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.track_area.pack(fill="both", expand=True)
        
        self.track_frames = []

    def import_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Fichiers audio", "*.wav *.flac *.ogg *.aiff *.aif *.mp3"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if not file_path:
            return

        track = AudioTrack(self.track_area, file_path)
        track.pack(fill="x", pady=12)
        self.track_frames.append(track)

       

if __name__ == "__main__":
    app = App()
    app.mainloop()