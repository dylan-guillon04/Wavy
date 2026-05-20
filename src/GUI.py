import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import time
import os
import sounddevice as sd
import numpy as np
from scipy import signal as scipy_signal
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from AudioHandler import AudioHandler
from FilterProcessor import FilterProcessor
from scipy.io import wavfile

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

# Load filter images files mapping
FILTER_IMG_FILES = {
    "Passe bas": "filter-lowpass.png",
    "Passe haut": "filter-highpass.png",
    "Sélecteur": "filter-bandpass.png",
    "Rejecteur": "filter-notch.png"
}

def get_filter_icon_path(filename):
    return os.path.join(os.path.dirname(__file__), "statics", filename)

# Load global images
PLAY_IMAGE = None
PAUSE_IMAGE = None
DELETE_IMAGE = None
DELETE_HOVER_IMAGE = None

def load_global_images():
    """Charge toutes les images en tant que variables globales."""
    global PLAY_IMAGE, PAUSE_IMAGE, DELETE_IMAGE, DELETE_HOVER_IMAGE
    
    play_icon_path = get_filter_icon_path("play.png")
    stop_icon_path = get_filter_icon_path("stop.png")
    delete_icon_path = get_filter_icon_path("delete.png")
    delete_red_icon_path = get_filter_icon_path("delete-red.png")
    
    PLAY_IMAGE = ctk.CTkImage(light_image=Image.open(play_icon_path), size=(20, 20))
    PAUSE_IMAGE = ctk.CTkImage(light_image=Image.open(stop_icon_path), size=(20, 20))
    DELETE_IMAGE = ctk.CTkImage(light_image=Image.open(delete_icon_path), size=(20, 20))
    DELETE_HOVER_IMAGE = ctk.CTkImage(light_image=Image.open(delete_red_icon_path), size=(20, 20))


# Load images on module initialization
load_global_images()


class FilterBlock(ctk.CTkFrame):
    def __init__(self, master, filter_type, app_ref, **kwargs):
        super().__init__(master, fg_color=COLORS["top_gradient"], border_width=2, border_color=COLORS["main"],
                         corner_radius=10, **kwargs)
        self.pack_propagate(False)
        self.filter_type = filter_type
        self.app_ref = app_ref
        self.filter_design_type = "butter"  # Type de filtre par défaut
        self.filter_order = 2  # Ordre par défaut


        icon_path = get_filter_icon_path(FILTER_IMG_FILES[filter_type])
        self.icon_image = ctk.CTkImage(light_image=Image.open(icon_path), size=(32, 32))
        self.icon_label = ctk.CTkLabel(self, image=self.icon_image, text="")
        self.icon_label.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

        self.title_label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color=COLORS["primary_text"], bg_color="transparent")
        self.title_label.grid(row=0, column=1, columnspan=5, padx=10, pady=5, sticky="n")
        
        # Delete button (using global images)
        self.delete_btn = ctk.CTkButton(self, image=DELETE_HOVER_IMAGE, text="", width=25, height=25, fg_color="transparent", hover_color=COLORS["secondary"], command=self.delete_filter)
        self.delete_btn.grid(row=0, column=6, padx=10, pady=5, sticky="ne")
        self.delete_btn.bind("<Enter>", self._on_delete_enter)
        self.delete_btn.bind("<Leave>", self._on_delete_leave)

        # Frequency control
        self.param_label = ctk.CTkLabel(self, text="Fréquence (Hz)", font=("Helvetica", 10), text_color=COLORS["secondary_text"])
        self.param_label.grid(row=2, column=0, columnspan=5, padx=10, pady=0, sticky="w")
        self.param_entry = ctk.CTkEntry(self, width=40, height=16, font=("Helvetica", 10), fg_color=COLORS["bottom_gradient"], text_color=COLORS["primary_text"], border_width=1, border_color=COLORS["background"], corner_radius=5, justify="center")
        self.param_entry.grid(row=2, column=5, columnspan=2, padx=10, pady=0, sticky="ew")
        self.param_entry.insert(0, "1000")
        self.param_entry.bind("<Return>", lambda e: self.update_slider(self.param_entry.get()))

        self.param_slider = ctk.CTkSlider(self, from_=20, to=20000, height=16, width=150, command=self.update_entry)
        self.param_slider.set(1000)
        self.param_slider.grid(row=3, column=0, columnspan=7, padx=10, pady=(0, 10), sticky="ew")
        
        # Filter type selector
        self.type_label = ctk.CTkLabel(self, text="Type", font=("Helvetica", 9), text_color=COLORS["secondary_text"])
        self.type_label.grid(row=1, column=0, padx=10, pady=0, sticky="w")
        
        self.type_options = list(FilterProcessor.FILTER_TYPES.keys())
        self.type_menu = ctk.CTkComboBox(self, values=self.type_options,
                                         font=("Helvetica", 10), width=100, height=16, border_width=1,
                                         fg_color=COLORS["bottom_gradient"],
                                         command=self.on_filter_type_change)
        self.type_menu.set(self.type_options[0])
        self.type_menu.grid(row=1, column=1, columnspan=4, padx=10, pady=0, sticky="w")
        
        # Order control
        self.order_label = ctk.CTkLabel(self, text="Ordre", font=("Helvetica", 9), text_color=COLORS["secondary_text"])
        self.order_label.grid(row=1, column=5, padx=10, pady=0, sticky="w")
        
        self.order_var = tk.IntVar(value=2)
        self.order_spinbox = ctk.CTkEntry(self, width=50, height=16, font=("Helvetica", 10), 
                                          fg_color=COLORS["bottom_gradient"], 
                                          text_color=COLORS["primary_text"], 
                                          border_width=1, border_color=COLORS["background"], 
                                          corner_radius=5, justify="center")
        self.order_spinbox.grid(row=1, column=6, padx=10, pady=0, sticky="w")
        self.order_spinbox.insert(0, "2")
        self.order_spinbox.bind("<Return>", lambda e: self.update_order())

    def on_filter_type_change(self, value):
        """Appelé quand le type de filtre change."""
        self.filter_design_type = FilterProcessor.FILTER_TYPES[value]
        # Redraw frequency spectrum
        if self.app_ref and hasattr(self.app_ref, 'draw_frequency_spectrum'):
            self.app_ref.draw_frequency_spectrum()
    
    def update_order(self):
        """Met à jour l'ordre du filtre."""
        try:
            order = int(self.order_spinbox.get())
            if order < 1:
                order = 1
            elif order > 20:
                order = 20
            self.filter_order = order
            self.order_spinbox.delete(0, tk.END)
            self.order_spinbox.insert(0, str(order))
            # Redraw frequency spectrum
            if self.app_ref and hasattr(self.app_ref, 'draw_frequency_spectrum'):
                self.app_ref.draw_frequency_spectrum()
        except ValueError:
            self.order_spinbox.delete(0, tk.END)
            self.order_spinbox.insert(0, str(self.filter_order))

    def update_entry(self, value):
        freq = int(float(value))
        self.param_entry.delete(0, tk.END)
        self.param_entry.insert(0, str(freq))
        # Redraw frequency spectrum
        if self.app_ref and hasattr(self.app_ref, 'draw_frequency_spectrum'):
            self.app_ref.draw_frequency_spectrum()
        
    def update_slider(self, value):
        try:
            freq = int(value)
            self.param_slider.set(freq)
            # Redraw frequency spectrum
            if self.app_ref and hasattr(self.app_ref, 'draw_frequency_spectrum'):
                self.app_ref.draw_frequency_spectrum()
        except ValueError:
            pass
    
    def _on_delete_enter(self, event):
        self.delete_btn.configure(image=DELETE_IMAGE)
    
    def _on_delete_leave(self, event):
        self.delete_btn.configure(image=DELETE_HOVER_IMAGE)
    
    def delete_filter(self):
        """Supprime ce bloc de filtre."""
        # Find the parent ScrollableFrame and remove this filter block from its list
        audiotrack = self.master.master
        if isinstance(audiotrack, AudioTrack) and self in audiotrack.filter_blocks:
            audiotrack.filter_blocks.remove(self)
            # If no more filter blocks, destroy the filter area
            if len(audiotrack.filter_blocks) == 0 and audiotrack.filter_area is not None:
                audiotrack.filter_area.destroy()
                audiotrack.filter_area = None
            # Redraw frequency spectrum after deletion
            if hasattr(audiotrack, 'draw_frequency_spectrum'):
                audiotrack.draw_frequency_spectrum()
        self.destroy()


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
        self.icon_label.bind("<ButtonPress-1>", self.on_start)
        self.icon_label.bind("<B1-Motion>", self.on_drag)
        self.icon_label.bind("<ButtonRelease-1>", self.on_drop)
        self.icon_label.bind("<Enter>", self.on_enter)
        self.icon_label.bind("<Leave>", self.on_leave)
        self.label.bind("<ButtonPress-1>", self.on_start)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.on_drop)
        self.label.bind("<Enter>", self.on_enter)
        self.label.bind("<Leave>", self.on_leave)
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
    def __init__(self, master, file_path, app_ref=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bottom_gradient"], corner_radius=10, **kwargs)
        self.audio_handler = AudioHandler()
        self.file_path = file_path
        self.is_playing = False
        self.filter_blocks = []
        self.app_ref = app_ref
        self.volume = 0.5  # Default volume at 50%
        self.max_filters = 5
        
        # Reference global images
        self.play_image = PLAY_IMAGE
        self.pause_image = PAUSE_IMAGE
        self.delete_image = DELETE_HOVER_IMAGE
        self.delete_hover_image = DELETE_IMAGE

        loaded = self.audio_handler.load_audio(file_path)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 0))
        
        header.grid_rowconfigure(0, weight=1)
        header.grid_rowconfigure(1, weight=1)
        header.grid_columnconfigure(0, weight=2)
        header.grid_columnconfigure(1, weight=100)
        header.grid_columnconfigure(2, weight=1)
        header.grid_columnconfigure(3, weight=6)

        self.file_label = ctk.CTkLabel(header, text=os.path.basename(file_path), text_color=COLORS["primary_text"], font=("Helvetica", 14, "bold"))
        self.file_label.grid(row=0, column=0, columnspan=2, padx=5, sticky="w")
        
        self.play_pause_button = ctk.CTkButton(header, image=PLAY_IMAGE, text="", width=30, height=30, fg_color=COLORS["main"], hover_color=COLORS["secondary"], command=lambda: self.toggle_play_pause(master), state="normal" if loaded else "disabled")
        self.play_pause_button.grid(row=1, column=0, padx=(5,0), sticky="w")
        
        self.delete_track_button = ctk.CTkButton(header, image=DELETE_HOVER_IMAGE, text="", width=30, height=30, fg_color="transparent", hover_color=COLORS["secondary"], command=self.delete_track)
        self.delete_track_button.grid(row=0, column=3, padx=5, sticky="e")
        self.delete_track_button.bind("<Enter>", self._on_delete_track_enter)
        self.delete_track_button.bind("<Leave>", self._on_delete_track_leave)
        
        self.slider_time = ctk.CTkSlider(header, from_=0, to=1, command=self.on_slider_time_change)
        self.slider_time.grid(row=1, column=1, sticky="ew", padx=(5, 10))
        self.slider_time.set(0)
        self.slider_time_dragging = False
        self.current_playback_position = 0  # Position actuelle de lecture en secondes
        
        # Afficher le temps ecoule et la duree du fichier
        duration = self.audio_handler.get_duration()
        duration_text = self._format_time(duration)
        time_display_text = f"0:00 / {duration_text}"
        self.duration_label = ctk.CTkLabel(header, text=time_display_text, text_color=COLORS["secondary_text"], font=("Helvetica", 10), width=60)
        self.duration_label.grid(row=1, column=2, padx=5, sticky="e")
        self.total_duration = duration  # Stocker la duree totale

        # Matplotlib figures for waveform and frequency spectrum
        self.fig_waveform = Figure(figsize=(10, 1), dpi=80, facecolor=COLORS["background"])
        self.ax_waveform = self.fig_waveform.add_subplot(111)
        self.ax_waveform.set_facecolor(COLORS["background"])
        self.fig_waveform.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1)
        
        self.fig_frequency = Figure(figsize=(10, 3), dpi=80, facecolor=COLORS["background"])
        self.ax_frequency = self.fig_frequency.add_subplot(111)
        self.ax_frequency.set_facecolor(COLORS["background"])
        self.fig_frequency.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1)
        
        self.canvas_widget = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_widget.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        
        # Canvas on the left - with visualizations stacked vertically
        canvas_frame = ctk.CTkFrame(self.canvas_widget, fg_color="transparent")
        canvas_frame.pack(side="left", fill="both", expand=True)
        
        # Waveform canvas (top)
        self.waveform_canvas = FigureCanvasTkAgg(self.fig_waveform, master=canvas_frame)
        self.waveform_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Frequency spectrum canvas (bottom)
        self.frequency_canvas = FigureCanvasTkAgg(self.fig_frequency, master=canvas_frame)
        self.frequency_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Volume slider on the right
        volume_frame = ctk.CTkFrame(self.canvas_widget, fg_color="transparent", width=50)
        volume_frame.pack(side="right", fill="y", padx=(10, 0))
        
        volume_label = ctk.CTkLabel(volume_frame, text="Vol", width=40, text_color=COLORS["secondary_text"])
        volume_label.pack()
        
        self.volume_slider = ctk.CTkSlider(
            volume_frame, 
            from_=0, 
            to=100, 
            height=100,
            orientation="vertical",
            command=self.on_volume_change
        )
        self.volume_slider.set(50)  # Default 50%
        self.volume_slider.pack(fill="y", expand=True, padx=5)
        
        volume_value_label = ctk.CTkLabel(volume_frame, text="50%", text_color=COLORS["secondary_text"])
        volume_value_label.pack()
        self.volume_value_label = volume_value_label
        
        self.playhead_line = None
        self.waveform_line = None

        self.playhead_id = None
        self.playhead_animating = False
        self.playhead_start_time = 0
        self.playhead_duration = 0
        self.playback_remaining_duration = 0  # Duree reelle des donnees jouees
        self.canvas_width = 0
        self.canvas_height = 0
        self.waveform_cache = None
        self.playback_data = None
        self.time_axis = None
        self.filter_area = None
        self.slider_updating = False  # Flag pour eviter les boucles infinies de mise a jour

        if loaded:
            # Initialiser le slider avec la durée correcte
            duration = self.audio_handler.get_duration()
            if duration > 0:
                self.slider_time.configure(to=duration)
            self.prepare_playback_data()
            self.after(50, self.draw_waveform)

    def _format_time(self, seconds):
        """Formate le temps en MM:SS ou HH:MM:SS si supérieur à 1 heure."""
        if seconds < 0:
            seconds = 0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def update_duration_label(self, elapsed_time):
        """Met a jour le label affichant le temps ecoule / duree totale."""
        try:
            if not self.winfo_exists():
                return
            if hasattr(self, 'duration_label') and hasattr(self, 'total_duration'):
                elapsed_text = self._format_time(elapsed_time)
                duration_text = self._format_time(self.total_duration)
                time_display_text = f"{elapsed_text} / {duration_text}"
                self.duration_label.configure(text=time_display_text)
        except Exception as e:
            pass
    
    def prepare_playback_data(self):
        """Prépare les données audio normalisées une seule fois pour éviter recalcul à chaque play."""
        if self.audio_handler.data is not None:
            self.playback_data = self.audio_handler.data * 0.5

    def apply_filters(self, start_offset=0):
        """Applique tous les filtres en cascade aux données audio à partir d'un offset.
        
        Args:
            start_offset: Offset en secondes à partir duquel commencer la lecture
        """
        data = self.audio_handler.data * 0.5
        
        # Convertir l'offset en nombre d'échantillons et découper les données
        if start_offset > 0:
            start_sample = int(start_offset * self.audio_handler.sample_rate)
            start_sample = max(0, min(start_sample, len(data) - 1))
            data = data[start_sample:]
        
        if len(data) == 0:
            return np.array([], dtype=data.dtype)
        
        if not self.filter_blocks:
            data_filtered = data
        else:
            filter_processor = FilterProcessor()
            data_filtered = data
            
            # Apply filters in cascade
            for block in self.filter_blocks:
                try:
                    cutoff_str = block.param_entry.get()
                    cutoff = float(cutoff_str)
                    filter_type = block.filter_type
                    sample_rate = self.audio_handler.sample_rate
                    order = block.filter_order
                    design_type = block.filter_design_type
                    
                    if filter_type == "Passe bas":
                        data_filtered = filter_processor.low_pass(data_filtered, sample_rate, cutoff, 
                                                                   order=order, filter_type=design_type)
                    elif filter_type == "Passe haut":
                        data_filtered = filter_processor.high_pass(data_filtered, sample_rate, cutoff,
                                                                    order=order, filter_type=design_type)
                    elif filter_type == "Sélecteur":
                        # For band-pass, use cutoff as center frequency with bandwidth
                        data_filtered = filter_processor.band_pass(data_filtered, sample_rate, cutoff * 0.8, cutoff * 1.2,
                                                                    order=order, filter_type=design_type)
                    elif filter_type == "Rejecteur":
                        # For band-stop, use cutoff as center frequency with bandwidth
                        data_filtered = filter_processor.band_stop(data_filtered, sample_rate, cutoff * 0.8, cutoff * 1.2,
                                                                    order=order, filter_type=design_type)
                except (ValueError, AttributeError, Exception) as e:
                    # If error in filter parameters, skip this filter
                    print(f"Erreur lors de l'application du filtre: {e}")
                    pass
        
        # Apply volume
        return data_filtered * self.volume
    
    def on_volume_change(self, value):
        """Called when volume slider changes."""
        self.volume = float(value) / 100.0
        try:
            self.volume_value_label.configure(text=f"{int(float(value))}%")
        except Exception:
            pass
    
    def on_slider_time_change(self, value):
        """Appelé quand le slider de temps est modifié par l'utilisateur."""
        if self.audio_handler.data is None:
            return
        
        try:
            new_position = float(value)
            self.slider_time_dragging = True
            self.current_playback_position = new_position
            
            # Mettre a jour le label de duree
            self.update_duration_label(new_position)
            
            # Si la lecture est en cours, arrêter et recommencer à la nouvelle position
            if self.is_playing:
                try:
                    sd.stop()
                except Exception:
                    pass
                self.is_playing = False
                
                # Redémarrer la lecture à partir de la nouvelle position
                try:
                    filtered_data = self.apply_filters(start_offset=new_position)
                    if len(filtered_data) > 0:
                        sd.play(filtered_data, self.audio_handler.sample_rate)
                        self.is_playing = True
                        self.play_pause_button.configure(image=self.pause_image)
                        self.start_playhead()
                        threading.Thread(target=self._monitor_playback, daemon=True).start()
                except Exception as e:
                    self.is_playing = False
                    print(f"Erreur lors de la lecture: {e}")
            else:
                # Juste mettre à jour la position et redessiner
                if self.playhead_line is not None:
                    self.playhead_line.remove()
                    self.playhead_line = None
                self.playhead_line = self.ax_waveform.axvline(x=new_position, color=COLORS["secondary"], linewidth=2, alpha=0.8)
                self.waveform_canvas.draw_idle()
            
            self.slider_time_dragging = False
        except (ValueError, Exception) as e:
            print(f"Erreur avec le slider: {e}")
            self.slider_time_dragging = False

    def toggle_play_pause(self, master):
        if self.audio_handler.data is None:
            return

        if self.is_playing:
            self.is_playing = False
            try:
                sd.stop()
            except Exception:
                pass
            try:
                self.play_pause_button.configure(image=self.play_image)
            except Exception:
                pass
            self.stop_playhead()
        else:
            try:
                sd.stop()
            except Exception:
                pass
            # Get current position from slider and apply filters from that position
            current_position = float(self.slider_time.get())
            self.current_playback_position = current_position
            filtered_data = self.apply_filters(start_offset=current_position)
            try:
                if len(filtered_data) > 0:
                    # Calculer la duree reelle des donnees jouees
                    self.playback_remaining_duration = len(filtered_data) / self.audio_handler.sample_rate
                    sd.play(filtered_data, self.audio_handler.sample_rate)
                    self.is_playing = True
                    self.play_pause_button.configure(image=self.pause_image)
                    self.start_playhead()
                    threading.Thread(target=self._monitor_playback, daemon=True).start()
            except Exception as e:
                self.is_playing = False
                print(f"Error playing audio: {e}")
            
    def start_playhead(self):
        self.playhead_animating = True
        self.playhead_start_time = time.monotonic() - self.current_playback_position
        self.playhead_duration = self.audio_handler.get_duration()
        self._animate_playhead()

    def stop_playhead(self):
        self.playhead_animating = False
        if self.playhead_line is not None:
            try:
                self.playhead_line.remove()
                self.playhead_line = None
                if self.winfo_exists():
                    self.waveform_canvas.draw_idle()
            except Exception:
                self.playhead_line = None

    def _animate_playhead(self):
        if not self.is_playing or not self.playhead_animating or not self.winfo_exists():
            self.stop_playhead()
            return
        duration = self.playhead_duration
        if duration == 0:
            self.stop_playhead()
            return
        
        elapsed = time.monotonic() - self.playhead_start_time
        elapsed = max(0, min(elapsed, duration))
        
        # Verifier si on a depasse la duree reelle des donnees jouees
        if self.playback_remaining_duration > 0 and elapsed > self.playback_remaining_duration:
            self.stop_playhead()
            return
        
        try:
            # Remove old playhead line
            if self.playhead_line is not None:
                try:
                    self.playhead_line.remove()
                except Exception:
                    pass
            
            # Draw new playhead line
            self.playhead_line = self.ax_waveform.axvline(x=elapsed, color=COLORS["secondary"], linewidth=2, alpha=0.8)
            self.waveform_canvas.draw_idle()
            
            # Mettre a jour le label de duree
            self.update_duration_label(elapsed)
            
            # Mettre a jour la position du slider (sans declencher on_slider_time_change)
            if not self.slider_time_dragging:
                try:
                    self.slider_updating = True
                    self.slider_time.set(elapsed)
                    self.slider_updating = False
                except Exception:
                    pass
        except Exception:
            self.playhead_line = None
        
        if elapsed < duration and self.is_playing and self.playhead_animating and self.winfo_exists():
            self.after(20, self._animate_playhead)
        else:
            self.stop_playhead()

    def _monitor_playback(self):
        try:
            sd.wait()
        except Exception:
            pass
        # Verifier que on est encore en lecture et que la fenetre existe
        try:
            if self.winfo_exists() and self.is_playing:
                self.after(0, self._playback_finished)
        except Exception:
            pass

    def _playback_finished(self):
        if not self.winfo_exists():
            return
        try:
            if self.is_playing:
                self.is_playing = False
                try:
                    self.play_pause_button.configure(image=self.play_image)
                except Exception:
                    pass
            # Remettre le slider a zero a la fin de la lecture
            try:
                if hasattr(self, 'slider_time'):
                    self.slider_time.set(0)
                self.current_playback_position = 0
                self.update_duration_label(0)
            except Exception:
                pass
        finally:
            self.stop_playhead()

    def draw_waveform(self):
        """Dessine la waveform avec matplotlib."""
        self.ax_waveform.clear()
        
        data = self.audio_handler.data
        if data is None or len(data) == 0:
            self.waveform_canvas.draw_idle()
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
        self.ax_waveform.plot(time_axis, reduced, color=COLORS["main"], linewidth=0.6)
        self.ax_waveform.fill_between(time_axis, reduced, alpha=0.3, color=COLORS["main"])
        
        # Configure axes
        self.ax_waveform.set_xlim(0, duration)
        self.ax_waveform.set_ylim(-1.1, 1.1)
        self.ax_waveform.set_facecolor(COLORS["background"])
        self.ax_waveform.spines['top'].set_visible(False)
        self.ax_waveform.spines['right'].set_visible(False)
        self.ax_waveform.spines['left'].set_visible(False)
        self.ax_waveform.spines['bottom'].set_color(COLORS["secondary_text"])
        self.ax_waveform.tick_params(colors=COLORS["secondary_text"], labelsize=8, labelbottom=False, labelleft=False)
        # self.ax_waveform.set_ylabel('Amplitude', color=COLORS["secondary_text"], fontsize=8)
        # self.ax_waveform.set_xlabel('Time (s)', color=COLORS["secondary_text"], fontsize=8)
        self.ax_waveform.grid(True, alpha=0.2, color=COLORS["secondary_text"], linestyle='--', linewidth=0.5)
        
        self.waveform_canvas.draw_idle()
        
        # Draw frequency spectrum
        self.draw_frequency_spectrum()
    
    def draw_frequency_spectrum(self):
        """Dessine le spectre fréquentiel sous forme de barplot."""
        self.ax_frequency.clear()
        
        data = self.audio_handler.data
        if data is None or len(data) == 0:
            self.frequency_canvas.draw_idle()
            return
        
        # Calculate FFT
        Fs = self.audio_handler.sample_rate
        n = len(data)
        fft = np.fft.fft(data)
        freqs = np.fft.fftfreq(n, 1/Fs)
        
        
        # Take only positive frequencies
        # positive_freqs_idx = freqs >= 0
        # freqs = freqs[positive_freqs_idx]
        # magnitude = np.abs(fft[positive_freqs_idx])
        magnitude = np.abs(fft) / n
        magnitude = magnitude[range(int(n/2))]
        freqs = freqs[range(int(n/2))]
        
        # Normalize magnitude
        # magnitude = magnitude / np.max(magnitude) if np.max(magnitude) > 0 else magnitude
        
        # Downsample for visualization (limit to 200 frequency bins)
        # k = 100
        # if len(freqs) > k:
        #     step = len(freqs) // k
        #     freqs = freqs[::step]
        #     magnitude = magnitude[::step]
        
        # Plot frequency spectrum as bar plot
        colors_array = [COLORS["main"]] * len(freqs)
        # self.ax_frequency.bar(freqs, magnitude, width=freqs[1]-freqs[0] if len(freqs) > 1 else 1, 
        #                       color=colors_array, alpha=0.7, linewidth=0.3)
        self.ax_frequency.plot(freqs, magnitude, color=COLORS["main"], linewidth=0.6)
        
        # Configure axes
        self.ax_frequency.set_xlim(1, Fs/2)
        self.ax_frequency.set_xscale('log')  # Logarithmic scale for frequency
        self.ax_frequency.set_ylim(0, max(magnitude) * 1.1)
        self.ax_frequency.set_facecolor(COLORS["background"])
        self.ax_frequency.spines['top'].set_visible(False)
        self.ax_frequency.spines['right'].set_visible(False)
        self.ax_frequency.spines['left'].set_visible(False)
        self.ax_frequency.spines['bottom'].set_color(COLORS["secondary_text"])
        self.ax_frequency.tick_params(colors=COLORS["secondary_text"], labelsize=8, labelbottom=False, labelleft=False)
        # self.ax_frequency.set_xlabel('Frequency (Hz)', color=COLORS["secondary_text"], fontsize=8)
        # self.ax_frequency.set_ylabel('Magnitude', color=COLORS["secondary_text"], fontsize=8)
        self.ax_frequency.grid(True, alpha=0.2, color=COLORS["secondary_text"], linestyle='--', linewidth=0.5, axis='y')
        
        # Draw Bode plot if filters are applied
        self.draw_filter_response()
        
        self.frequency_canvas.draw_idle()
    
    def draw_filter_response(self):
        """Dessine la réponse en fréquence du/des filtre(s) appliqué(s) en orange."""
        if not self.filter_blocks:
            return
        
        sample_rate = self.audio_handler.sample_rate
        
        # Calculate combined filter response by multiplying individual responses
        w = np.linspace(0, np.pi, 2000)
        combined_h = np.ones_like(w, dtype=complex)
        
        for block in self.filter_blocks:
            try:
                cutoff_str = block.param_entry.get()
                cutoff = float(cutoff_str)
                filter_type = block.filter_type
                order = block.filter_order
                design_type = block.filter_design_type
                
                # Design individual filter
                if filter_type == "Passe bas":
                    b, a = self._design_filter_response(sample_rate, cutoff, btype='low', order=order, design_type=design_type)
                elif filter_type == "Passe haut":
                    b, a = self._design_filter_response(sample_rate, cutoff, btype='high', order=order, design_type=design_type)
                elif filter_type == "Sélecteur":
                    b, a = self._design_filter_response(sample_rate, cutoff * 0.8, cutoff * 1.2, btype='band', order=order, design_type=design_type)
                elif filter_type == "Rejecteur":
                    b, a = self._design_filter_response(sample_rate, cutoff * 0.8, cutoff * 1.2, btype='bandstop', order=order, design_type=design_type)
                else:
                    continue
                
                # Calculate frequency response for this filter
                _, h = scipy_signal.freqz(b, a, worN=w)
                
                # Multiply responses (cascade)
                combined_h *= h
            except (ValueError, AttributeError, Exception) as e:
                print(f"Erreur lors du calcul du filtre individuel: {e}")
                continue
        
        # Convert frequency response to Hz
        freqs = w * sample_rate / (2 * np.pi)
        y_max = self.ax_frequency.get_ylim()[1]
        magnitude = np.abs(combined_h) * y_max

        
        # Normalize to match the spectrum scale (0-1)
        # magnitude = magnitude / np.max(magnitude) if np.max(magnitude) > 0 else magnitude
        
        # Plot Bode response in orange
        try:
            self.ax_frequency.plot(freqs, magnitude, color=COLORS["secondary"], linewidth=2, label='Filtre', zorder=10)
        except Exception as e:
            print(f"Erreur lors du traçage de la réponse en fréquence: {e}")
    
    def _design_filter_response(self, fs, cutoff1, cutoff2=None, btype='low', order=2, design_type='butter'):
        """Design un filtre pour le calcul de réponse en fréquence."""
        nyq = fs / 2.0
        
        if btype in ['band', 'bandstop']:
            # Two cutoff frequencies
            normal_cutoff = [max(0.001, min(0.999, c / nyq)) for c in [cutoff1, cutoff2]]
        else:
            # Single cutoff frequency
            normal_cutoff = max(0.001, min(0.999, cutoff1 / nyq))
        
        try:
            if design_type == "butter":
                b, a = scipy_signal.butter(order, normal_cutoff, btype=btype, analog=False)
            elif design_type == "cheby1":
                b, a = scipy_signal.cheby1(order, 5, normal_cutoff, btype=btype, analog=False)
            elif design_type == "cheby2":
                b, a = scipy_signal.cheby2(order, 5, normal_cutoff, btype=btype, analog=False)
            elif design_type == "bessel":
                b, a = scipy_signal.bessel(order, normal_cutoff, btype=btype, analog=False)
            elif design_type == "ellip":
                b, a = scipy_signal.ellip(order, 5, 5, normal_cutoff, btype=btype, analog=False)
            else:
                b, a = scipy_signal.butter(order, normal_cutoff, btype=btype, analog=False)
        except Exception as e:
            print(f"Erreur lors du design du filtre: {e}")
            b, a = scipy_signal.butter(order, normal_cutoff, btype=btype, analog=False)
        
        return b, a
        
    def add_filter_block(self, filter_type):
        if self.filter_area is None:
            self.filter_area = ctk.CTkFrame(self, fg_color="transparent", height=200)
            self.filter_area.pack(fill="x", padx=10, pady=(0, 10), anchor="n")
        
        if len(self.filter_blocks) >= self.max_filters:
            return

        block = FilterBlock(self.filter_area, filter_type, app_ref=self)
        block.pack(side="left", padx=(0, 5))
        
        self.filter_blocks.append(block)
        
        # Redraw frequency spectrum after adding filter
        self.draw_frequency_spectrum()
    
    def _on_delete_track_enter(self, event):
        self.delete_track_button.configure(image=DELETE_IMAGE)
    
    def _on_delete_track_leave(self, event):
        self.delete_track_button.configure(image=DELETE_HOVER_IMAGE)
    
    def delete_track(self):
        """Supprime la piste audio actuelle."""
        if self.is_playing:
            try:
                sd.stop()
            except Exception:
                pass
            self.is_playing = False
        
        # Reset slider
        try:
            self.slider_time.set(0)
            self.current_playback_position = 0
        except Exception:
            pass
        
        # Notify app that track is being deleted
        if self.app_ref:
            self.app_ref.on_track_deleted(self)
        
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wavy - Audio Filter Pro")
        self.geometry("1600x900")
        self.resizable(True, True)
        self.minsize(1400, 800)
        self.configure(fg_color=COLORS["background"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #### Main Frame
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        ### Top Bar
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS["menu"], corner_radius=10, height=100)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)
        
        # Import / Export buttons
        self.actions_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.actions_frame.place(relx=0.02, rely=0.5, anchor="w")
        self.import_button = ctk.CTkButton(self.actions_frame, text="Importer", fg_color=COLORS["main"], hover_color=COLORS["secondary"], command=self.import_audio)
        self.import_button.pack(pady=5, fill="x")
        # ctk.CTkButton(self.actions_frame, text="Enregistrer", fg_color="transparent", hover_color=COLORS["secondary"], border_width=1).pack(pady=5, fill="x")

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
        self.is_playing_all = False  # Track if all tracks are playing
        
        self.default_label = ctk.CTkLabel(self.content_frame, text="Importez une piste audio pour commencer", text_color=COLORS["secondary_text"])
        self.default_label.place(relx=0.5, rely=0.5, anchor="center")

        #### Bottom Bar (Footer)
        self.bottom_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS["menu"], corner_radius=10, height=60)
        self.bottom_bar.grid(row=2, column=0, sticky="ew")
        self.bottom_bar.grid_propagate(False)
        self.bottom_bar.grid_remove()  # Initially hidden
        
        self.play_pause_all_button = ctk.CTkButton(self.bottom_bar, width=200, image=PLAY_IMAGE, text="Jouer toutes les pistes", fg_color=COLORS["main"], hover_color=COLORS["secondary"], command=self.toggle_play_all)
        self.play_pause_all_button.place(relx=0.5, rely=0.5, anchor="center")


    def import_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Fichiers audio", "*.wav *.flac *.ogg *.aiff *.aif *.mp3"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if not file_path:
            return

        track = AudioTrack(self.track_area, file_path, app_ref=self)
        track.pack(fill="x", pady=12)
        self.track_frames.append(track)
        
        # Show bottom bar when first track is loaded
        if len(self.track_frames) == 1:
            self.bottom_bar.grid()
            self.default_label.place_forget()

    def toggle_play_all(self):
        """Toggle between play all and stop all."""
        if self.is_playing_all:
            self.stop_all_tracks()
        else:
            self.play_all_tracks()

    def play_all_tracks(self):
        """Lance la lecture de toutes les pistes audio en même temps."""
        if self.is_playing_all:
            return
        
        self.play_pause_all_button.configure(image=PAUSE_IMAGE, text="Arrêter")
        
        if not self.track_frames:
            return
        
        # Collect all filtered audio data with same length
        all_audio_data = []
        max_length = 0
        sample_rate = None
        
        # First pass: get max length and sample rate
        for track in self.track_frames:
            if track.audio_handler.data is not None and not track.is_playing:
                filtered_data = track.apply_filters()
                all_audio_data.append(filtered_data)
                max_length = max(max_length, len(filtered_data))
                if sample_rate is None:
                    sample_rate = track.audio_handler.sample_rate
        
        if not all_audio_data or sample_rate is None:
            return
        
        # Pad all audio to same length and mix them
        mixed_audio = np.zeros(max_length)
        for audio_data in all_audio_data:
            padded = np.zeros(max_length)
            padded[:len(audio_data)] = audio_data
            mixed_audio += padded
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 0:
            mixed_audio = mixed_audio / max_val * 0.5
        
        # Play mixed audio
        try:
            sd.play(mixed_audio, sample_rate)
        except Exception as e:
            print(f"Error playing audio: {e}")
            return
        
        self.is_playing_all = True
        
        # Update all tracks
        for track in self.track_frames:
            if track.audio_handler.data is not None and not track.is_playing:
                track.is_playing = True
                track.play_pause_button.configure(image=track.pause_image)
                track.start_playhead()
                threading.Thread(target=track._monitor_playback, daemon=True).start()
        
        # Monitor playback completion
        threading.Thread(target=self._monitor_all_playback, daemon=True).start()
    
    def _monitor_all_playback(self):
        """Monitor when all tracks finish playing."""
        try:
            sd.wait()
        except Exception:
            pass
        
        # Reset the button and tracks when playback finishes
        if self.winfo_exists():
            self.after(0, self._finish_all_playback)
    
    def _finish_all_playback(self):
        """Called when all tracks finish playing."""
        if not self.winfo_exists():
            return
        
        self.is_playing_all = False
        try:
            self.play_pause_all_button.configure(image=PLAY_IMAGE, text="Jouer toutes les pistes")
        except Exception:
            pass
        
        # Reset all tracks
        for track in self.track_frames:
            track.is_playing = False
            try:
                track.play_pause_button.configure(image=track.play_image)
            except Exception:
                pass
            track.stop_playhead()

    def on_track_deleted(self, track):
        """Appelé quand une piste est supprimée."""
        if track in self.track_frames:
            self.track_frames.remove(track)
        
        # Hide bottom bar if no tracks left
        if len(self.track_frames) == 0:
            self.bottom_bar.grid_remove()

    def stop_all_tracks(self):
        """Arrête la lecture de toutes les pistes audio."""
        try:
            sd.stop()
        except Exception:
            pass
        
        self.is_playing_all = False
        try:
            self.play_pause_all_button.configure(image=PLAY_IMAGE, text="Jouer toutes les pistes")
        except Exception:
            pass
        
        for track in self.track_frames:
            if track.is_playing:
                track.is_playing = False
                try:
                    track.play_pause_button.configure(image=track.play_image)
                except Exception:
                    pass
                track.stop_playhead()

       

if __name__ == "__main__":
    app = App()
    app.mainloop()
    
    # Fs, data = wavfile.read('audio/guitar_perturbe.wav') # fréquence d'échantillonnage et données
    # # Calcul de la FFT
    # fft_result = np.fft.fft(data)
    # frequencies = np.fft.fftfreq(len(data), 1/Fs)

    # # On ne garde que les fréquences positives
    # n = len(data)
    # fft_magnitude = np.abs(fft_result) / n
    # fft_magnitude = fft_magnitude[range(int(n/2))]
    
    # print(len(frequencies), len(fft_magnitude))

    # # Affichage du résultat
    # plt.figure(figsize=(10, 4))
    # plt.plot(frequencies[:int(n/2)], fft_magnitude)
    # plt.title("Spectre de fréquence (FFT)")
    # plt.xlabel("Fréquence (Hz)")
    # plt.ylabel("Amplitude")
    # plt.grid()
    # plt.show()