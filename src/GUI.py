import customtkinter as ctk
from tkinter import filedialog
import os
import sounddevice as sd
import numpy as np
from AudioHandler import AudioHandler
from FilterProcessor import FilterProcessor

# test

ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class FilterBlock(ctk.CTkFrame):
    def __init__(self, master, filter_type, **kwargs):
        super().__init__(master, fg_color="transparent", border_width=2, border_color="#3b4ccc", corner_radius=10, **kwargs)
        self.filter_type = filter_type
        self.label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color="#3b4ccc")
        self.label.pack(padx=10, pady=(8, 0))
        
        self.param_label = ctk.CTkLabel(self, text="Fréq: 1000 Hz", font=("Helvetica", 10), text_color="black")
        self.param_label.pack()
        
        self.slider = ctk.CTkSlider(self, from_=20, to=15000, height=16, width=120, command=self.update_label)
        self.slider.set(1000)
        self.slider.pack(padx=10, pady=(5, 10))

    def update_label(self, value):
        self.param_label.configure(text=f"Fréq: {int(value)} Hz")

class DraggableFilter(ctk.CTkButton):
    def __init__(self, master, filter_type, app_ref, **kwargs):
        super().__init__(master, text=filter_type, width=120, height=80, fg_color="#f0f0f0",
                         font=("Helvetica", 14, "bold"),
                         border_color="#3b4ccc", border_width=2, text_color="#3b4ccc", **kwargs)
        self.filter_type = filter_type
        self.app_ref = app_ref
        self.bind("<ButtonPress-1>", self.on_start)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_drop)
        self.ghost = None

    def on_start(self, event):
        self.ghost = ctk.CTkToplevel(self)
        self.ghost.overrideredirect(True)
        self.ghost.attributes("-alpha", 0.7)
        label = ctk.CTkLabel(self.ghost, text=self.filter_type, text_color="#3b4ccc")
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
                if isinstance(target, TrackRow):
                    target.add_filter_block(self.filter_type)
                    break
                target = target.master

class TrackRow(ctk.CTkFrame):
    def __init__(self, master, file_path, **kwargs):
        super().__init__(master, fg_color="#f9f9f9", corner_radius=10, **kwargs)
        self.handler = AudioHandler()
        self.handler.load_audio(file_path)
        self.processor = FilterProcessor()
        self.filter_blocks = []

        # Header
        self.header_zone = ctk.CTkFrame(self, fg_color="transparent")
        self.header_zone.pack(fill="x", padx=15, pady=(10, 5))

        self.file_label = ctk.CTkLabel(self.header_zone, text=f"📄 {os.path.basename(file_path)}", 
                                      font=("Helvetica", 14, "bold"), text_color="#a64dff")
        self.file_label.pack(side="left")

        # Bouton Play individuel
        self.play_btn = ctk.CTkButton(self.header_zone, text="▶ Play", width=60, height=25,
                                      fg_color="#3bcc4c", command=self.play_processed_audio)
        self.play_btn.pack(side="right", padx=10)

        # Container filtres
        self.filter_container = ctk.CTkScrollableFrame(self, orientation="horizontal", fg_color="white", 
                                                       height=110, corner_radius=10, border_width=1, border_color="#eeeeee")
        self.filter_container.pack(fill="x", padx=10, pady=(0, 10))

    def add_filter_block(self, filter_type):
        block = FilterBlock(self.filter_container, filter_type)
        block.pack(side="left", padx=8, pady=5)
        self.filter_blocks.append(block)

    def get_processed_data(self):
        """Applique tous les filtres de la piste en chaîne."""
        if self.handler.data is None: return None
        
        signal = np.copy(self.handler.data)
        fs = self.handler.sample_rate
        
        for block in self.filter_blocks:
            freq = block.slider.get()
            if block.filter_type == "Passe bas":
                signal = self.processor.low_pass(signal, fs, freq, order=2)
            elif block.filter_type == "Passe haut":
                signal = self.processor.high_pass(signal, fs, freq, order=2)
            # Ajoutez ici les autres filtres (Sélecteur/Rejecteur)
        return signal

    def play_processed_audio(self):
        data = self.get_processed_data()
        if data is not None:
            sd.stop() # Arrête toute lecture en cours
            sd.play(data*0.5, self.handler.sample_rate)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wavy - Audio Filter Pro")
        self.geometry("1400x800")
        self.resizable(False, False)
        self.configure(fg_color="#323232")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, fg_color="transparent", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        ctk.CTkButton(self.sidebar, text="Importer", command=self.import_file).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Enregistrer", fg_color="transparent", border_width=1).pack(pady=5, fill="x")

        # Top Bar
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.btn_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=5)
        for f in ["Passe bas", "Passe haut", "Sélecteur", "Rejecteur"]:
            DraggableFilter(self.btn_frame, f, app_ref=self).pack(side="left", padx=5)

        # Workspace
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.tracks = []

        # --- Zone Bas (Play All) ---
        self.bottom_bar = ctk.CTkFrame(self, height=80, fg_color="#606060", corner_radius=10)
        self.bottom_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        
        self.play_all_btn = ctk.CTkButton(self.bottom_bar, text="▶ JOUER TOUT (MIX)", 
                                          width=200, height=45, font=("Helvetica", 14, "bold"),
                                          fg_color="#a64dff", command=self.play_all_tracks)
        self.play_all_btn.pack(pady=15)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def import_file(self):
        path = filedialog.askopenfilename()
        if path:
            track = TrackRow(self.scroll_canvas, path)
            track.pack(fill="x", pady=15)
            self.tracks.append(track)

    def play_all_tracks(self):
        """Mélange tous les sons filtrés et les joue en même temps."""
        if not self.tracks: return
        
        all_signals = []
        max_len = 0
        sr = self.tracks[0].handler.sample_rate
        
        for t in self.tracks:
            sig = t.get_processed_data()
            if sig is not None:
                all_signals.append(sig)
                max_len = max(max_len, len(sig))
        
        # Mixage (Somme des signaux normalisée)
        mixed_signal = np.zeros(max_len)
        for s in all_signals:
            mixed_signal[:len(s)] += s
        
        # Normalisation pour éviter la saturation
        if len(all_signals) > 0:
            mixed_signal = mixed_signal / len(all_signals)
            
        sd.stop()
        sd.play(mixed_signal, sr)

if __name__ == "__main__":
    app = App()
    app.mainloop()