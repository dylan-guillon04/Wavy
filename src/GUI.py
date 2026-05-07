import customtkinter as ctk
from tkinter import filedialog
import os

# Paramètres esthétiques
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class FilterBlock(ctk.CTkFrame):
    """Un bloc de filtre individuel dans une piste."""
    def __init__(self, master, filter_type, **kwargs):
        super().__init__(master, fg_color="transparent", border_width=2, border_color="#3b4ccc", corner_radius=15, **kwargs)
        
        self.filter_type = filter_type
        
        # Label du filtre
        self.label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 13, "bold"), text_color="#3b4ccc")
        self.label.pack(padx=10, pady=(8, 0))
        
        # Texte paramètre
        self.param_label = ctk.CTkLabel(self, text="Féq: 1000 Hz", font=("Helvetica", 10), text_color="black")
        self.param_label.pack()
        
        # Slider plus compact
        self.slider = ctk.CTkSlider(self, from_=20, to=20000, height=16, width=120, command=self.update_label)
        self.slider.set(1000)
        self.slider.pack(padx=10, pady=(5, 10))

    def update_label(self, value):
        self.param_label.configure(text=f"Fréq: {int(value)} Hz")

class TrackRow(ctk.CTkFrame):
    """Une ligne représentant un fichier audio avec le nom au-dessus des filtres."""
    def __init__(self, master, filename, **kwargs):
        super().__init__(master, fg_color="#f9f9f9", corner_radius=10, **kwargs)
        
        # 1. Zone Titre du fichier (Aligné à gauche en haut)
        self.header_zone = ctk.CTkFrame(self, fg_color="transparent")
        self.header_zone.pack(fill="x", padx=15, pady=(10, 5))

        self.file_label = ctk.CTkLabel(
            self.header_zone, 
            text=f"📄 {filename}", 
            font=("Helvetica", 14, "bold"), 
            text_color="#a64dff"
        )
        self.file_label.pack(side="left")

        # 2. Zone de filtres (Prend toute la largeur en dessous)
        self.filter_container = ctk.CTkScrollableFrame(
            self, 
            orientation="horizontal", 
            fg_color="white", 
            height=110,
            corner_radius=8,
            border_width=1,
            border_color="#eeeeee"
        )
        self.filter_container.pack(fill="x", padx=10, pady=(0, 10))

    def add_filter_block(self, filter_type):
        new_filter = FilterBlock(self.filter_container, filter_type)
        new_filter.pack(side="left", padx=8, pady=5)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wavy - Application de Filtrage")
        self.geometry("1400x800")
        self.configure(fg_color="white")

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=180, fg_color="white", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkButton(self.sidebar, text="Importer", command=self.import_file).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Enregistrer", command=self.save_file, fg_color="transparent", border_width=1).pack(pady=5, fill="x")
        
        # ctk.CTkLabel(self.sidebar, text="FICHIERS", font=("Helvetica", 11, "bold")).pack(pady=(30, 5))

        # --- Top Bar (Sélection des filtres) ---
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.top_bar, text="AJOUTER UN FILTRE À LA PISTE SÉLECTIONNÉE", font=("Helvetica", 12, "bold"), text_color="#a64dff").pack(anchor="w", padx=10)
        
        self.btn_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=5)
        
        for f in ["Passe bas", "Passe haut", "Sélecteur", "Rejecteur"]:
            btn = ctk.CTkButton(self.btn_frame, text=f, width=120, height=45,
                                fg_color="white", border_color="#3b4ccc", border_width=2, text_color="#3b4ccc",
                                command=lambda t=f: self.add_filter_to_active_track(t))
            btn.pack(side="left", padx=5)

        # --- Main Workspace ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        
        self.tracks = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def import_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            new_track = TrackRow(self.scroll_canvas, os.path.basename(file_path))
            new_track.pack(fill="x", pady=15)
            self.tracks.append(new_track)

    def add_filter_to_active_track(self, filter_type):
        if self.tracks:
            self.tracks[-1].add_filter_block(filter_type)

    def save_file(self):
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()