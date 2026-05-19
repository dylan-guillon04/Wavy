import scipy.signal as sig
import numpy as np

class FilterProcessor:
    """Implémente les filtres avec support de différents types et ordres."""
    
    # Types de filtres disponibles
    FILTER_TYPES = {
        "Butterworth": "butter",
        "Chebyshev Type I": "cheby1",
        "Chebyshev Type II": "cheby2",
        "Bessel": "bessel",
        "Elliptic": "ellip"
    }

    @staticmethod
    def _get_nyquist(fs):
        return 0.5 * fs

    @staticmethod
    def _design_filter(fs, cutoff, btype, order=1, filter_type="butter", ripple=5):
        """Design un filtre du type spécifié."""
        nyq = FilterProcessor._get_nyquist(fs)
        
        # Gérer les cas avec deux fréquences de coupure
        if isinstance(cutoff, (list, tuple)):
            normal_cutoff = [c / nyq for c in cutoff]
        else:
            normal_cutoff = cutoff / nyq
        
        # S'assurer que les fréquences normalisées sont dans [0, 1]
        if isinstance(normal_cutoff, list):
            normal_cutoff = [max(0.001, min(0.999, c)) for c in normal_cutoff]
        else:
            normal_cutoff = max(0.001, min(0.999, normal_cutoff))
        
        try:
            if filter_type == "butter":
                b, a = sig.butter(order, normal_cutoff, btype=btype, analog=False)
            elif filter_type == "cheby1":
                b, a = sig.cheby1(order, ripple, normal_cutoff, btype=btype, analog=False)
            elif filter_type == "cheby2":
                b, a = sig.cheby2(order, ripple, normal_cutoff, btype=btype, analog=False)
            elif filter_type == "bessel":
                b, a = sig.bessel(order, normal_cutoff, btype=btype, analog=False)
            elif filter_type == "ellip":
                b, a = sig.ellip(order, ripple, ripple, normal_cutoff, btype=btype, analog=False)
            else:
                # Default to Butterworth
                b, a = sig.butter(order, normal_cutoff, btype=btype, analog=False)
        except Exception as e:
            print(f"Erreur lors du design du filtre: {e}")
            b, a = sig.butter(order, normal_cutoff, btype=btype, analog=False)
        
        return b, a

    @staticmethod
    def low_pass(data, fs, cutoff, order=1, filter_type="butter", ripple=5):
        """Filtre Passe-Bas"""
        b, a = FilterProcessor._design_filter(fs, cutoff, 'low', order, filter_type, ripple)
        return sig.lfilter(b, a, data)

    @staticmethod
    def high_pass(data, fs, cutoff, order=1, filter_type="butter", ripple=5):
        """Filtre Passe-Haut"""
        b, a = FilterProcessor._design_filter(fs, cutoff, 'high', order, filter_type, ripple)
        return sig.lfilter(b, a, data)

    @staticmethod
    def band_pass(data, fs, low_cut, high_cut, order=2, filter_type="butter", ripple=5):
        """Filtre Sélecteur (Passe-bande)"""
        b, a = FilterProcessor._design_filter(fs, [low_cut, high_cut], 'band', order, filter_type, ripple)
        return sig.lfilter(b, a, data)

    @staticmethod
    def band_stop(data, fs, low_cut, high_cut, order=2, filter_type="butter", ripple=5):
        """Filtre Rejecteur (Coupe-bande / Notch)"""
        b, a = FilterProcessor._design_filter(fs, [low_cut, high_cut], 'bandstop', order, filter_type, ripple)
        return sig.lfilter(b, a, data)