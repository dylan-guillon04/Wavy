import customtkinter as ctk
from tkinter import filedialog
import os

# Paramètres esthétiques
ctk.set_appearance_mode("light")  # Mode clair comme sur le template
ctk.set_default_color_theme("blue")

class FilterBlock(ctk.CTkFrame):
    """Un bloc de filtre individuel dans une piste."""
    def __init__(self, master, filter_type, **kwargs):
        super().__init__(master, fg_color="transparent", border_width=2, border_color="#3b4ccc", corner_radius=15, **kwargs)
        
        self.filter_type = filter_type
        
        # Label du filtre
        self.label = ctk.CTkLabel(self, text=filter_type, font=("Helvetica", 14, "bold"), text_color="#3b4ccc")
        self.label.pack(padx=10, pady=(10, 0))
        
        # Texte paramètre (ex: Fréquence)
        self.param_label = ctk.CTkLabel(self, text="Fréquence = 1000 Hz", font=("Helvetica", 11), text_color="black")
        self.param_label.pack()
        
        # Slider pour le paramètre
        self.slider = ctk.CTkSlider(self, from_=20, to=20000, command=self.update_label)
        self.slider.set(1000)
        self.slider.pack(padx=15, pady=10)

    def update_label(self, value):
        self.param_label.configure(text=f"Fréquence = {int(value)} Hz")

class TrackRow(ctk.CTkFrame):
    """Une ligne représentant un fichier audio et ses filtres."""
    def __init__(self, master, filename, **kwargs):
        super().__init__(master, fg_color="white", **kwargs)
        
        # Nom du fichier (Gauche)
        self.file_label = ctk.CTkLabel(self, text=filename, font=("Helvetica", 13), text_color="#a64dff", width=150)
        self.file_label.pack(side="left", padx=20, pady=20)
        
        # Séparateur vertical
        self.sep = ctk.CTkFrame(self, width=2, fg_color="black", height=80)
        self.sep.pack(side="left", fill="y", pady=10)
        
        # Zone horizontale pour les blocs de filtres
        self.filter_container = ctk.CTkScrollableFrame(self, orientation="horizontal", fg_color="transparent", height=120)
        self.filter_container.pack(side="left", fill="both", expand=True, padx=10)

    def add_filter_block(self, filter_type):
        new_filter = FilterBlock(self.filter_container, filter_type)
        new_filter.pack(side="left", padx=10, pady=5)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wavy - Filtrage Numérique Audio")
        self.geometry("1400x800")
        self.configure(fg_color="white")

        # --- Sidebar (Gauche) ---
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color="white", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=20, pady=20)
        
        self.btn_import = ctk.CTkButton(self.sidebar, text="Importer", fg_color="transparent", text_color="#3b4ccc", border_width=1, command=self.import_file)
        self.btn_import.pack(pady=10)
        
        self.btn_save = ctk.CTkButton(self.sidebar, text="Enregistrer", fg_color="transparent", text_color="#3b4ccc", border_width=1, command=self.save_file)
        self.btn_save.pack(pady=10)
        
        self.file_list_label = ctk.CTkLabel(self.sidebar, text="FICHIERS IMPORTÉS", font=("Helvetica", 10, "bold"), text_color="black")
        self.file_list_label.pack(pady=(40, 10))

        # --- Top Bar (Filtres disponibles) ---
        self.top_bar = ctk.CTkFrame(self, height=100, fg_color="transparent")
        self.top_bar.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.top_bar, text="FILTRES DISPONIBLES (Cliquer pour ajouter à la piste)", font=("Helvetica", 12, "bold"), text_color="#a64dff").pack(anchor="w", padx=20)
        
        self.filters_shelf = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.filters_shelf.pack(fill="both", expand=True)
        
        available_filters = ["Passe bas", "Passe haut", "Passe bande", "Coupe bande"]
        for f in available_filters:
            btn = ctk.CTkButton(self.filters_shelf, text=f, width=100, height=60, 
                                fg_color="transparent", border_color="#a64dff", border_width=2, 
                                text_color="#a64dff", corner_radius=10,
                                command=lambda t=f: self.add_filter_to_active_track(t))
            btn.pack(side="left", padx=10)

        # --- Main Workspace (Liste des pistes) ---
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_canvas.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.tracks = [] # Liste pour stocker les objets TrackRow

        # Configuration de la grille
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.flac *.mp3")])
        if file_path:
            filename = os.path.basename(file_path)
            new_track = TrackRow(self.scroll_canvas, filename)
            new_track.pack(fill="x", pady=10)
            self.tracks.append(new_track)

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".wav")
        if file_path:
            print(f"Sauvegarde demandée dans : {file_path}")

    def add_filter_to_active_track(self, filter_type):
        """Ajoute le filtre à la dernière piste importée."""
        if self.tracks:
            self.tracks[-1].add_filter_block(filter_type)
        else:
            print("Importez d'abord un fichier !")

if __name__ == "__main__":
    app = App()
    app.mainloop()