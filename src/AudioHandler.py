import soundfile as sf
import numpy as np

class AudioHandler:
    """Gère le chargement et les données du fichier audio."""
    
    def __init__(self):
        self.data = None
        self.sample_rate = None
        self.file_path = None

    def load_audio(self, file_path):
        """Charge un fichier audio (WAV, FLAC, OGG, etc.) et normalise en flottant."""
        try:
            self.data, self.sample_rate = sf.read(file_path)
            self.file_path = file_path
            
            # Si le fichier est en stéréo, on peut travailler sur la moyenne 
            # ou garder les deux canaux. Ici on simplifie en mono pour le filtrage
            if len(self.data.shape) > 1:
                self.data = np.mean(self.data, axis=1)
                
            print(f"Chargé: {file_path} | SR: {self.sample_rate}Hz | Durée: {len(self.data)/self.sample_rate:.2f}s")
            return True
        except Exception as e:
            print(f"Erreur de chargement: {e}")
            return False

    def get_duration(self):
        if self.data is not None:
            return len(self.data) / self.sample_rate
        return 0