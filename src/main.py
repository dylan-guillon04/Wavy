import sounddevice as sd
from AudioHandler import AudioHandler
from FilterProcessor import FilterProcessor
from GUI import App

# imports necessary to get the path where the files are extracted in
import os
import sys

# initializing a variable containing the path where application files are stored.
application_path = ''

# attempting to get where the program files are stored
if getattr(sys, 'frozen', False): 
    # if program was frozen (compiled) using pyinstaller, the pyinstaller bootloader creates a sys attribute
    # frozen=True to indicate that the script file was compiled using pyinstaller, then it creates a
    # constant in sys that points to the directory where program executable is (where program files are extracted in).
    application_path = sys._MEIPASS
else: 
    # if program is not frozen (compiled) using pyinstaller and is running normally like a Python 3.x.x file.
    application_path = os.path.dirname(os.path.abspath(__file__))

# changing the current working directory to the path where one-file mode source files are extracted in.
os.chdir(application_path)

# importing customtkinter
from customtkinter import *

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
    # test_pipeline()
    from GUI import App
    app = App()
    app.mainloop()