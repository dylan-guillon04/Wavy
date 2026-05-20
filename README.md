# Wavy - Audio Filter Pro
Une application intuitive pour charger des pistes audio, visualiser leur forme d'onde et appliquer des filtres fréquentiels (Butterworth, Chebyshev, etc.) en temps réel.

## Installation rapide
Suivez ces étapes pour configurer l'environnement et lancer l'application sur votre machine.

1. Cloner ou télécharger le projet

2. Installer les dépendances

Ouvrez votre terminal et copiez-collez la commande suivante pour installer toutes les bibliothèques nécessaires :

```Bash
pip install -r requirements.txt
```

3. Lancer l'application

Lancez le fichier `src/main.py` ou bien exécutez ce script :

```Bash
python src/main.py
```

## Utilisation
Cliquez sur le bouton Importer pour charger un fichier audio (.wav, .mp3, .flac).

Faites glisser un bloc de filtre (Passe-bas, Passe-haut, etc.) depuis la barre supérieure vers votre piste audio.

Ajustez la fréquence et l'ordre du filtre.

Appuyez sur Play pour écouter le résultat filtré en temps réel !