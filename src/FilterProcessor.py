import scipy.signal as sig
import numpy as np

class FilterProcessor:
    """Implémente les filtres d'ordre 1, 2, sélecteurs et rejecteurs."""

    @staticmethod
    def _get_nyquist(fs):
        return 0.5 * fs

    @staticmethod
    def low_pass(data, fs, cutoff, order=1):
        """Filtre Passe-Bas (Ordre 1 ou 2)"""
        nyq = FilterProcessor._get_nyquist(fs)
        normal_cutoff = cutoff / nyq
        b, a = sig.butter(order, normal_cutoff, btype='low', analog=False)
        return sig.lfilter(b, a, data)

    @staticmethod
    def high_pass(data, fs, cutoff, order=1):
        """Filtre Passe-Haut (Ordre 1 ou 2)"""
        nyq = FilterProcessor._get_nyquist(fs)
        normal_cutoff = cutoff / nyq
        b, a = sig.butter(order, normal_cutoff, btype='high', analog=False)
        return sig.lfilter(b, a, data)

    @staticmethod
    def band_pass(data, fs, low_cut, high_cut, order=2):
        """Filtre Sélecteur (Passe-bande)"""
        nyq = FilterProcessor._get_nyquist(fs)
        low = low_cut / nyq
        high = high_cut / nyq
        b, a = sig.butter(order, [low, high], btype='band', analog=False)
        return sig.lfilter(b, a, data)

    @staticmethod
    def band_stop(data, fs, low_cut, high_cut, order=2):
        """Filtre Rejecteur (Coupe-bande / Notch)"""
        nyq = FilterProcessor._get_nyquist(fs)
        low = low_cut / nyq
        high = high_cut / nyq
        b, a = sig.butter(order, [low, high], btype='bandstop', analog=False)
        return sig.lfilter(b, a, data)