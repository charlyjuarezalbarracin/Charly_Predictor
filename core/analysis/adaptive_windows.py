"""
Analizador de Ventanas Temporales Adaptativas
Determina qué ventana temporal es mejor para predecir cada número
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


class AdaptiveWindowAnalyzer:
    """
    Sistema de ventanas temporales dinámicas que adapta la ventana 
    de análisis según el comportamiento histórico de cada número.
    
    Ventanas disponibles:
    - Ultra reciente: 10 sorteos
    - Reciente: 30 sorteos
    - Medio plazo: 100 sorteos
    - Largo plazo: 200 sorteos
    """
    
    VENTANAS = {
        'ultra_reciente': 10,
        'reciente': 30,
        'medio': 100,
        'largo': 200
    }
    
    def __init__(self):
        self.data = None
        self.window_scores = {}  # Score de cada ventana por número
        self.best_windows = {}   # Mejor ventana para cada número
        self.adaptive_frequencies = {}  # Frecuencias con ventana adaptativa
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Analiza todas las ventanas y determina la mejor para cada número
        
        Args:
            data: DataFrame con sorteos históricos
            
        Returns:
            Dict con ventanas óptimas y frecuencias adaptativas
        """
        self.data = data
        
        # Calcular score de cada ventana para cada número
        self._calculate_window_scores()
        
        # Determinar mejor ventana por número
        self._determine_best_windows()
        
        # Calcular frecuencias usando ventanas adaptativas
        self._calculate_adaptive_frequencies()
        
        return {
            'window_scores': self.window_scores,
            'best_windows': self.best_windows,
            'adaptive_frequencies': self.adaptive_frequencies
        }
    
    def _calculate_window_scores(self):
        """
        Calcula qué tan bien predice cada ventana cada número
        usando validación histórica
        """
        self.window_scores = defaultdict(dict)
        
        # Necesitamos al menos 250 sorteos para evaluar ventanas largas
        if len(self.data) < 250:
            return
        
        # Extraer todos los números de los sorteos
        all_numbers = []
        for _, row in self.data.iterrows():
            nums = [row[f'num{i}'] for i in range(1, 7)]
            all_numbers.append(set(nums))
        
        # Para cada número del 0 al 45
        for num in range(46):
            # Para cada ventana
            for ventana_name, ventana_size in self.VENTANAS.items():
                if len(self.data) < ventana_size + 20:
                    continue
                
                # Validación: usar ventana N para predecir sorteos siguientes
                # Tomar últimos 20 sorteos como validación
                hits = 0
                total_tests = 20
                
                for i in range(total_tests):
                    # Punto de corte
                    test_idx = len(self.data) - 20 + i
                    train_end = test_idx
                    train_start = max(0, train_end - ventana_size)
                    
                    # Calcular frecuencia en ventana de entrenamiento
                    count = 0
                    for j in range(train_start, train_end):
                        if num in all_numbers[j]:
                            count += 1
                    
                    freq = count / ventana_size if ventana_size > 0 else 0
                    
                    # Verificar si el número salió en el sorteo de test
                    salió = num in all_numbers[test_idx]
                    
                    # Score: si freq alta y salió, o freq baja y no salió = hit
                    umbral_freq = 0.13  # ~6/46 esperado
                    predice_salida = freq > umbral_freq
                    
                    if predice_salida == salió:
                        hits += 1
                
                # Score de esta ventana para este número
                accuracy = hits / total_tests
                self.window_scores[num][ventana_name] = accuracy
    
    def _determine_best_windows(self):
        """
        Determina la mejor ventana para cada número basado en scores
        """
        self.best_windows = {}
        
        for num in range(46):
            if num not in self.window_scores or not self.window_scores[num]:
                # Default: usar ventana media
                self.best_windows[num] = 'medio'
                continue
            
            # Encontrar ventana con mejor score
            best_ventana = max(
                self.window_scores[num].items(),
                key=lambda x: x[1]
            )
            
            self.best_windows[num] = best_ventana[0]
    
    def _calculate_adaptive_frequencies(self):
        """
        Calcula frecuencias usando la ventana óptima de cada número
        """
        self.adaptive_frequencies = {}
        
        # Extraer números de sorteos
        all_numbers = []
        for _, row in self.data.iterrows():
            nums = [row[f'num{i}'] for i in range(1, 7)]
            all_numbers.append(set(nums))
        
        for num in range(46):
            # Obtener ventana óptima
            best_window_name = self.best_windows.get(num, 'medio')
            window_size = self.VENTANAS[best_window_name]
            
            # Calcular frecuencia en esa ventana
            start_idx = max(0, len(all_numbers) - window_size)
            
            count = 0
            for i in range(start_idx, len(all_numbers)):
                if num in all_numbers[i]:
                    count += 1
            
            # Frecuencia normalizada
            total_sorteos = len(all_numbers) - start_idx
            freq = count / total_sorteos if total_sorteos > 0 else 0
            
            self.adaptive_frequencies[num] = freq
    
    def get_window_info(self, numero: int) -> Dict:
        """
        Obtiene información de ventana para un número específico
        
        Args:
            numero: Número a consultar (0-45)
            
        Returns:
            Dict con información de ventanas
        """
        return {
            'mejor_ventana': self.best_windows.get(numero, 'medio'),
            'tamaño_ventana': self.VENTANAS[self.best_windows.get(numero, 'medio')],
            'scores_todas_ventanas': self.window_scores.get(numero, {}),
            'frecuencia_adaptativa': self.adaptive_frequencies.get(numero, 0)
        }
