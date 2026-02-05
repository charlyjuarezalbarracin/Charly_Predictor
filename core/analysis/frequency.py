"""
Analizador de frecuencias - Core del análisis estadístico
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter
from ..config import QUINI6_CONFIG, TEMPORAL_PARAMS


class FrequencyAnalyzer:
    """
    Analiza frecuencias de aparición de números
    - Frecuencia absoluta
    - Frecuencia relativa
    - Frecuencia reciente (últimos N sorteos)
    - Números calientes y fríos
    - Ciclos de aparición
    - Latencia (tiempo desde última aparición)
    """
    
    def __init__(self, config: Dict = None, temporal_params: Dict = None):
        self.config = config or QUINI6_CONFIG
        self.temporal_params = temporal_params or TEMPORAL_PARAMS
        self.data = None
        self.results = {}
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Ejecuta todos los análisis de frecuencia
        
        Args:
            data: DataFrame con sorteos
        
        Returns:
            Diccionario con todos los análisis
        """
        self.data = data
        self.results = {}
        
        # Análisis principales
        self.results['frecuencia_absoluta'] = self._calcular_frecuencia_absoluta()
        self.results['frecuencia_relativa'] = self._calcular_frecuencia_relativa()
        self.results['frecuencia_reciente'] = self._calcular_frecuencia_reciente()
        self.results['numeros_calientes'] = self._identificar_calientes()
        self.results['numeros_frios'] = self._identificar_frios()
        self.results['ciclos'] = self._calcular_ciclos()
        self.results['latencia'] = self._calcular_latencia()
        self.results['tendencia'] = self._calcular_tendencia()
        
        return self.results
    
    def _calcular_frecuencia_absoluta(self) -> Dict[int, int]:
        """Cuenta cuántas veces apareció cada número"""
        all_numbers = []
        for numeros in self.data['numeros']:
            all_numbers.extend(numeros)
        
        counter = Counter(all_numbers)
        
        # Asegurar que todos los números posibles estén representados
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            if num not in counter:
                counter[num] = 0
        
        return dict(sorted(counter.items()))
    
    def _calcular_frecuencia_relativa(self) -> Dict[int, float]:
        """Calcula la frecuencia normalizada (0-1)"""
        freq_abs = self.results.get('frecuencia_absoluta') or self._calcular_frecuencia_absoluta()
        total_sorteos = len(self.data)
        
        freq_rel = {
            num: count / total_sorteos 
            for num, count in freq_abs.items()
        }
        
        return freq_rel
    
    def _calcular_frecuencia_reciente(self) -> Dict[int, int]:
        """Calcula frecuencia en los últimos N sorteos"""
        ventana = self.temporal_params['ventana_reciente']
        recent_data = self.data.tail(ventana)
        
        all_numbers = []
        for numeros in recent_data['numeros']:
            all_numbers.extend(numeros)
        
        counter = Counter(all_numbers)
        
        # Asegurar que todos los números estén representados
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            if num not in counter:
                counter[num] = 0
        
        return dict(sorted(counter.items()))
    
    def _identificar_calientes(self, top_n: int = 10) -> List[Tuple[int, int]]:
        """
        Identifica números "calientes" (más frecuentes en sorteos recientes)
        
        Args:
            top_n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, frecuencia) ordenadas por frecuencia descendente
        """
        freq_reciente = self.results.get('frecuencia_reciente') or self._calcular_frecuencia_reciente()
        
        sorted_freq = sorted(freq_reciente.items(), key=lambda x: x[1], reverse=True)
        return sorted_freq[:top_n]
    
    def _identificar_frios(self, top_n: int = 10) -> List[Tuple[int, int]]:
        """
        Identifica números "fríos" (menos frecuentes en sorteos recientes)
        
        Args:
            top_n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, frecuencia) ordenadas por frecuencia ascendente
        """
        freq_reciente = self.results.get('frecuencia_reciente') or self._calcular_frecuencia_reciente()
        
        sorted_freq = sorted(freq_reciente.items(), key=lambda x: x[1])
        return sorted_freq[:top_n]
    
    def _calcular_ciclos(self) -> Dict[int, float]:
        """
        Calcula el ciclo promedio de aparición de cada número
        (cada cuántos sorteos aparece en promedio)
        """
        ciclos = {}
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            apariciones = []
            
            # Encontrar índices donde aparece el número
            for idx, row in self.data.iterrows():
                if num in row['numeros']:
                    apariciones.append(idx)
            
            if len(apariciones) >= 2:
                # Calcular diferencias entre apariciones
                diferencias = np.diff(apariciones)
                ciclo_promedio = np.mean(diferencias)
                ciclos[num] = float(ciclo_promedio)
            else:
                # Si apareció 0 o 1 vez, ciclo indefinido
                ciclos[num] = float('inf')
        
        return ciclos
    
    def _calcular_latencia(self) -> Dict[int, int]:
        """
        Calcula cuántos sorteos han pasado desde la última aparición de cada número
        """
        latencia = {}
        ultimo_sorteo_idx = len(self.data) - 1
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            # Buscar la última aparición del número (desde el final)
            ultima_aparicion = -1
            
            for idx in range(len(self.data) - 1, -1, -1):
                if num in self.data.iloc[idx]['numeros']:
                    ultima_aparicion = idx
                    break
            
            if ultima_aparicion >= 0:
                latencia[num] = ultimo_sorteo_idx - ultima_aparicion
            else:
                # Nunca apareció
                latencia[num] = len(self.data)
        
        return latencia
    
    def _calcular_tendencia(self) -> Dict[int, float]:
        """
        Calcula la tendencia de cada número (aceleración/desaceleración)
        Compara frecuencia reciente vs frecuencia histórica
        
        Returns:
            Dict con tendencia: > 1 = acelerando, < 1 = desacelerando, ~1 = estable
        """
        freq_reciente = self.results.get('frecuencia_reciente') or self._calcular_frecuencia_reciente()
        freq_absoluta = self.results.get('frecuencia_absoluta') or self._calcular_frecuencia_absoluta()
        
        ventana = self.temporal_params['ventana_reciente']
        total_sorteos = len(self.data)
        
        tendencia = {}
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            # Frecuencia esperada en ventana reciente (si fuera constante)
            freq_esperada = (freq_absoluta[num] / total_sorteos) * ventana
            
            # Frecuencia real en ventana reciente
            freq_real = freq_reciente[num]
            
            # Calcular ratio (evitar división por cero)
            if freq_esperada > 0:
                tendencia[num] = freq_real / freq_esperada
            else:
                tendencia[num] = 1.0 if freq_real == 0 else float('inf')
        
        return tendencia
    
    def get_scores(self, weights: Dict = None) -> Dict[int, float]:
        """
        Calcula un score combinado para cada número basado en frecuencias
        
        Args:
            weights: Pesos para combinar diferentes métricas
        
        Returns:
            Dict con score para cada número (0-1)
        """
        if weights is None:
            weights = {
                'frecuencia_relativa': 0.3,
                'frecuencia_reciente': 0.3,
                'latencia_inversa': 0.2,
                'tendencia': 0.2
            }
        
        scores = {}
        
        # Obtener métricas normalizadas
        freq_rel = self.results.get('frecuencia_relativa') or self._calcular_frecuencia_relativa()
        freq_rec = self.results.get('frecuencia_reciente') or self._calcular_frecuencia_reciente()
        latencia = self.results.get('latencia') or self._calcular_latencia()
        tendencia = self.results.get('tendencia') or self._calcular_tendencia()
        
        # Normalizar frecuencia reciente
        max_freq_rec = max(freq_rec.values()) if freq_rec.values() else 1
        freq_rec_norm = {k: v / max_freq_rec for k, v in freq_rec.items()}
        
        # Normalizar latencia (invertir: menor latencia = mayor score)
        max_latencia = max(latencia.values()) if latencia.values() else 1
        latencia_inv_norm = {k: 1 - (v / max_latencia) for k, v in latencia.items()}
        
        # Normalizar tendencia
        max_tendencia = max(tendencia.values()) if tendencia.values() else 1
        # Filtrar infinitos
        tendencia_filtrada = {k: min(v, 3.0) for k, v in tendencia.items()}
        max_tendencia_filt = max(tendencia_filtrada.values()) if tendencia_filtrada.values() else 1
        tendencia_norm = {k: v / max_tendencia_filt for k, v in tendencia_filtrada.items()}
        
        # Calcular score combinado
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            score = (
                weights.get('frecuencia_relativa', 0) * freq_rel.get(num, 0) +
                weights.get('frecuencia_reciente', 0) * freq_rec_norm.get(num, 0) +
                weights.get('latencia_inversa', 0) * latencia_inv_norm.get(num, 0) +
                weights.get('tendencia', 0) * tendencia_norm.get(num, 0)
            )
            scores[num] = score
        
        return scores
    
    def get_top_numbers(self, n: int = 10) -> List[Tuple[int, float]]:
        """
        Retorna los N números con mayor score
        
        Args:
            n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, score) ordenadas por score
        """
        scores = self.get_scores()
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:n]
    
    def get_summary(self) -> Dict:
        """Retorna un resumen del análisis"""
        if not self.results:
            return {"error": "No se ha ejecutado el análisis. Use analyze() primero."}
        
        freq_abs = self.results['frecuencia_absoluta']
        calientes = self.results['numeros_calientes']
        frios = self.results['numeros_frios']
        
        return {
            'total_sorteos_analizados': len(self.data),
            'numero_mas_frecuente': max(freq_abs.items(), key=lambda x: x[1]),
            'numero_menos_frecuente': min(freq_abs.items(), key=lambda x: x[1]),
            'top_5_calientes': calientes[:5],
            'top_5_frios': frios[:5],
            'promedio_apariciones': np.mean(list(freq_abs.values()))
        }
