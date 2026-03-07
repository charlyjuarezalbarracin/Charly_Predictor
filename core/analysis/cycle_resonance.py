"""
Analizador de Resonancia Temporal de Ciclos - IDEA #1

Detecta cuando un número está en su "ventana óptima" de aparición basándose
en el análisis estadístico de su ciclo natural de aparición.

CONCEPTO CLAVE:
Cada número no tiene un ciclo único y fijo, sino un "ritmo natural" con variabilidad.
La clave es detectar cuando un número está en su VENTANA DE ALTA PROBABILIDAD
dentro de su ciclo.

MÉTODO:
- Calcula ciclo promedio y desviación estándar para cada número
- Usa Z-Score para determinar si está en ventana óptima
- Z-Score = (latencia_actual - ciclo_promedio) / desviación_estándar

VENTANAS:
- Z entre -0.5 y +2.0 → VENTANA ÓPTIMA (está "a punto" de salir)
- Z < -1.0 → Todavía no le toca
- Z > 3.0 → MUY atrasado (altísima probabilidad)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..config import QUINI6_CONFIG


class CycleResonanceAnalyzer:
    """
    Analiza la resonancia temporal de ciclos para cada número
    
    Identifica números que están en su "momento óptimo" de aparición
    según el análisis estadístico de sus ciclos históricos.
    
    VENTAJA:
    En lugar de solo mirar "¿cuál es el ciclo promedio?", analiza
    "¿está el número en su ventana de alta probabilidad AHORA?"
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or QUINI6_CONFIG
        self.data = None
        self.results = {}
        
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Ejecuta análisis completo de resonancia de ciclos
        
        Args:
            data: DataFrame con sorteos históricos
        
        Returns:
            Diccionario con análisis de resonancia
        """
        self.data = data
        self.results = {}
        
        # Análisis de ciclos avanzado
        self.results['ciclos_estadisticas'] = self._calcular_estadisticas_ciclos()
        self.results['latencias_actuales'] = self._calcular_latencias_actuales()
        self.results['z_scores_ciclo'] = self._calcular_z_scores()
        self.results['scores_resonancia'] = self._calcular_scores_resonancia()
        self.results['ventanas_optimas'] = self._identificar_ventanas_optimas()
        
        return self.results
    
    def _calcular_estadisticas_ciclos(self) -> Dict[int, Dict]:
        """
        Calcula estadísticas completas del ciclo de cada número
        
        Returns:
            Dict con {numero: {promedio, std, min, max, variabilidad}}
        """
        estadisticas = {}
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            apariciones = []
            
            # Encontrar índices donde aparece el número
            for idx, row in self.data.iterrows():
                if num in row['numeros']:
                    apariciones.append(idx)
            
            if len(apariciones) >= 3:  # Mínimo 3 apariciones para calcular stats
                # Calcular diferencias entre apariciones (ciclos)
                ciclos = np.diff(apariciones)
                
                estadisticas[num] = {
                    'promedio': float(np.mean(ciclos)),
                    'std': float(np.std(ciclos)),
                    'min': int(np.min(ciclos)),
                    'max': int(np.max(ciclos)),
                    'mediana': float(np.median(ciclos)),
                    'variabilidad': float(np.std(ciclos) / np.mean(ciclos)) if np.mean(ciclos) > 0 else 0,
                    'total_apariciones': len(apariciones),
                    'ciclos': ciclos.tolist()
                }
            else:
                # Valores por defecto si hay pocas apariciones
                estadisticas[num] = {
                    'promedio': len(self.data) / max(len(apariciones), 1),
                    'std': len(self.data) * 0.3,  # Asumimos 30% de variabilidad
                    'min': 1,
                    'max': len(self.data),
                    'mediana': len(self.data) / max(len(apariciones), 1),
                    'variabilidad': 0.3,
                    'total_apariciones': len(apariciones),
                    'ciclos': []
                }
        
        return estadisticas
    
    def _calcular_latencias_actuales(self) -> Dict[int, int]:
        """
        Calcula cuántos sorteos han pasado desde la última aparición de cada número
        
        Returns:
            Dict con {numero: latencia_actual}
        """
        latencias = {}
        ultimo_sorteo_idx = len(self.data) - 1
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            # Buscar la última aparición del número (desde el final)
            ultima_aparicion = -1
            
            for idx in range(len(self.data) - 1, -1, -1):
                if num in self.data.iloc[idx]['numeros']:
                    ultima_aparicion = idx
                    break
            
            if ultima_aparicion >= 0:
                latencias[num] = ultimo_sorteo_idx - ultima_aparicion
            else:
                # Nunca apareció
                latencias[num] = len(self.data)
        
        return latencias
    
    def _calcular_z_scores(self) -> Dict[int, float]:
        """
        Calcula Z-Score del ciclo para cada número
        
        Z-Score = (latencia_actual - ciclo_promedio) / ciclo_std
        
        Interpretación:
        - Z ≈ 0: Justo en el promedio del ciclo
        - Z > 0: Más tiempo del promedio (atrasado)
        - Z < 0: Menos tiempo del promedio (todavía no le toca)
        
        Returns:
            Dict con {numero: z_score}
        """
        z_scores = {}
        
        ciclos_stats = self.results.get('ciclos_estadisticas', {})
        latencias = self.results.get('latencias_actuales', {})
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            if num in ciclos_stats and num in latencias:
                ciclo_promedio = ciclos_stats[num]['promedio']
                ciclo_std = ciclos_stats[num]['std']
                latencia_actual = latencias[num]
                
                # Calcular Z-Score
                if ciclo_std > 0:
                    z_score = (latencia_actual - ciclo_promedio) / ciclo_std
                else:
                    z_score = 0.0
                
                z_scores[num] = float(z_score)
            else:
                z_scores[num] = 0.0
        
        return z_scores
    
    def _calcular_scores_resonancia(self) -> Dict[int, float]:
        """
        Calcula score de resonancia para cada número basado en su Z-Score
        
        LÓGICA:
        - Z entre -0.5 y +2.0 → BOOST FUERTE (ventana óptima)
        - Z > 3.0 → MEGA BOOST (muy atrasado, alta probabilidad)
        - Z entre 2.0 y 3.0 → BOOST MEDIO
        - Z < -0.5 → REDUCCIÓN (todavía no le toca)
        
        Returns:
            Dict con {numero: score_resonancia} (0.3 a 3.0)
        """
        scores = {}
        z_scores = self.results.get('z_scores_ciclo', {})
        
        for num in range(self.config['min_number'], self.config['max_number'] + 1):
            z = z_scores.get(num, 0.0)
            
            # Calcular score según Z-Score
            if z > 3.5:
                # Extremadamente atrasado
                score = 3.0
            elif z > 3.0:
                # Muy atrasado
                score = 2.8
            elif z > 2.5:
                # Bastante atrasado
                score = 2.4
            elif z > 2.0:
                # Atrasado
                score = 2.0
            elif z >= -0.5:
                # VENTANA ÓPTIMA: Está en su momento ideal
                # Bonus progresivo: cuanto más cerca de 1.0, mejor
                if 0.5 <= z <= 1.5:
                    score = 2.5  # Sweet spot
                else:
                    score = 2.0
            elif z >= -1.0:
                # Casi en ventana
                score = 1.3
            elif z >= -1.5:
                # Todavía temprano
                score = 0.8
            else:
                # Muy temprano para salir
                score = 0.5
            
            scores[num] = score
        
        return scores
    
    def _identificar_ventanas_optimas(self) -> Dict[str, List[int]]:
        """
        Identifica números que están en diferentes ventanas de probabilidad
        
        Returns:
            Dict con categorías de números
        """
        z_scores = self.results.get('z_scores_ciclo', {})
        
        categorias = {
            'mega_atrasados': [],      # Z > 3.0
            'muy_atrasados': [],        # 2.5 < Z <= 3.0
            'ventana_optima': [],       # -0.5 <= Z <= 2.0
            'sweet_spot': [],           # 0.5 <= Z <= 1.5
            'todavia_temprano': [],     # Z < -0.5
        }
        
        for num, z in z_scores.items():
            if z > 3.0:
                categorias['mega_atrasados'].append(num)
            elif z > 2.5:
                categorias['muy_atrasados'].append(num)
            elif 0.5 <= z <= 1.5:
                categorias['sweet_spot'].append(num)
            elif -0.5 <= z <= 2.0:
                categorias['ventana_optima'].append(num)
            else:
                categorias['todavia_temprano'].append(num)
        
        return categorias
    
    def get_resonance_factor(self, numero: int) -> float:
        """
        Obtiene el factor de resonancia para un número específico
        
        Args:
            numero: Número a consultar (0-45)
        
        Returns:
            Factor de resonancia (0.5 a 3.0)
        """
        if not self.results or 'scores_resonancia' not in self.results:
            raise ValueError("Debe ejecutar analyze() primero")
        
        return self.results['scores_resonancia'].get(numero, 1.0)
    
    def get_summary(self) -> Dict:
        """
        Retorna resumen del análisis de resonancia
        
        Returns:
            Dict con resumen de números en cada categoría
        """
        if not self.results:
            return {"error": "No se ha ejecutado el análisis"}
        
        ventanas = self.results.get('ventanas_optimas', {})
        
        return {
            'total_en_ventana_optima': len(ventanas.get('ventana_optima', [])),
            'total_en_sweet_spot': len(ventanas.get('sweet_spot', [])),
            'total_mega_atrasados': len(ventanas.get('mega_atrasados', [])),
            'numeros_sweet_spot': sorted(ventanas.get('sweet_spot', [])),
            'numeros_mega_atrasados': sorted(ventanas.get('mega_atrasados', [])),
            'top_resonancia': self._get_top_resonancia(10)
        }
    
    def _get_top_resonancia(self, n: int = 10) -> List[Tuple[int, float, float]]:
        """
        Retorna los N números con mayor score de resonancia
        
        Args:
            n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, score_resonancia, z_score)
        """
        scores = self.results.get('scores_resonancia', {})
        z_scores = self.results.get('z_scores_ciclo', {})
        
        items = [
            (num, scores[num], z_scores.get(num, 0.0))
            for num in scores.keys()
        ]
        
        items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
        return items_sorted[:n]
    
    def get_summary(self) -> dict:
        """
        Genera un resumen del análisis de resonancia de ciclos
        
        Returns:
            Diccionario con información resumida para mostrar en UI
        """
        ventanas = self.results.get('ventanas_optimas', {})
        
        return {
            'total_en_ventana_optima': len(ventanas.get('en_ventana_optima', [])),
            'total_en_sweet_spot': len(ventanas.get('sweet_spot', [])),
            'total_mega_atrasados': len(ventanas.get('mega_atrasados', [])),
            'numeros_sweet_spot': sorted(ventanas.get('sweet_spot', [])),
            'numeros_mega_atrasados': sorted(ventanas.get('mega_atrasados', [])),
            'numeros_ventana_optima': sorted(ventanas.get('en_ventana_optima', [])),
            'top_resonancia': self._get_top_resonancia(10)
        }
