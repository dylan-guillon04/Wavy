import sounddevice as sd
from AudioHandler import AudioHandler
from FilterProcessor import FilterProcessor

def test_pipeline():
    handler = AudioHandler()
    processor = FilterProcessor()

    # 1. Test chargement
    file_to_load = "audio/guitar.wav" # Assure-toi d'avoir un fichier ici
    if handler.load_audio(file_to_load):
        
        fs = handler.sample_rate
        signal = handler.data

        # 2. Exemple d'application d'un filtre sélecteur (band-pass)
        # On garde les fréquences entre 500Hz et 2000Hz
        print("Application du filtre sélecteur...")
        filtered = processor.band_pass(signal, fs, 1000, 2000, order=2)

        # 3. Test de lecture (Volume à 0.5)
        volume = 0.5
        print(f"Lecture du son filtré (Volume: {volume})...")
        sd.play(filtered * volume, fs)
        sd.wait() # Attend la fin du son
    else:
        print("Échec du test : fichier introuvable.")

if __name__ == "__main__":
    test_pipeline()