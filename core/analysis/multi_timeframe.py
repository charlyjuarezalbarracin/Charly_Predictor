"""
IDEA #2: Análisis Multi-Timeframe con Convergencia

Analiza frecuencias en múltiples ventanas temporales y detecta números
con señal convergente (consistentes en todas las escalas temporales).

Autor: Charly Predictor
Fecha: 2026-02-20
"""

import pandas as pd
from typing import Dict, List, Tuple


class MultiTimeframeAnalyzer:
    """
    Analiza números en múltiples escalas temporales y detecta convergencia.
    
    Ventanas analizadas: 10, 20, 50, 100, 200 sorteos
    Un número con señal convergente aparece en el top de TODAS las ventanas.
    """
    
    def __init__(self):
        self.ventanas = [10, 20, 50, 100, 200]
        self.top_size = 15  # Considerar top 15 en cada ventana
        self.results = {}
    
    def analyze(self, data: pd.DataFrame):
        """
        Analiza convergencia multi-timeframe
        
        Args:
            data: DataFrame con columnas 'sorteo_id', 'fecha', 'numeros'
        """
        self.results = {
            'rankings_por_ventana': {},
            'convergencia_scores': {},
            'numeros_convergentes': [],
            'numeros_divergentes': [],
            'factores_boost': {}
        }
        
        # Calcular rankings en cada ventana
        for ventana in self.ventanas:
            self.results['rankings_por_ventana'][ventana] = self._calcular_ranking_ventana(data, ventana)
        
        # Calcular convergencia de cada número
        self.results['convergencia_scores'] = self._calcular_convergencia()
        
        # Identificar convergentes y divergentes
        self._identificar_convergencia()
        
        # Calcular factores de boost
        self.results['factores_boost'] = self._calcular_factores_boost()
    
    def _calcular_ranking_ventana(self, data: pd.DataFrame, ventana: int) -> Dict[int, int]:
        """
        Calcula ranking de números en una ventana temporal
        
        Returns:
            Dict con {numero: posicion_ranking} (1 = más frecuente)
        """
        # Tomar últimos N sorteos
        ultimos = data.tail(ventana)
        
        # Contar frecuencias
        frecuencias = {}
        for _, row in ultimos.iterrows():
            numeros = row['numeros']
            for num in numeros:
                frecuencias[num] = frecuencias.get(num, 0) + 1
        
        # Ordenar por frecuencia descendente
        ranking = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)
        
        # Convertir a dict {numero: posicion}
        posiciones = {}
        for pos, (num, freq) in enumerate(ranking, 1):
            posiciones[num] = pos
        
        # Asignar posición 999 a números no aparecidos
        for num in range(0, 46):
            if num not in posiciones:
                posiciones[num] = 999
        
        return posiciones
    
    def _calcular_convergencia(self) -> Dict[int, float]:
        """
        Calcula score de convergencia para cada número.
        
        Convergencia = en cuántas ventanas está en el top 15
        Score normalizado: 0.0 (en ninguna) a 1.0 (en todas)
        
        Returns:
            Dict {numero: convergencia_score}
        """
        convergencia = {}
        
        for num in range(0, 46):
            # Contar en cuántas ventanas está en top 15
            apariciones_top = 0
            
            for ventana in self.ventanas:
                ranking = self.results['rankings_por_ventana'][ventana]
                if ranking.get(num, 999) <= self.top_size:
                    apariciones_top += 1
            
            # Normalizar: 0 a 1 (0/5 ventanas -> 1.0, 5/5 ventanas -> 1.0)
            convergencia[num] = apariciones_top / len(self.ventanas)
        
        return convergencia
    
    def _identificar_convergencia(self):
        """
        Clasifica números según su nivel de convergencia.
        
        - Convergentes: En top 15 de TODAS las ventanas (100% convergencia)
        - Parcialmente convergentes: En top 15 de 3-4 ventanas (60-80%)
        - Divergentes: En top 15 de 0-2 ventanas (0-40%)
        """
        convergentes = []
        parciales = []
        divergentes = []
        
        for num, score in self.results['convergencia_scores'].items():
            if score >= 1.0:
                convergentes.append(num)
            elif score >= 0.6:
                parciales.append(num)
            else:
                divergentes.append(num)
        
        self.results['numeros_convergentes'] = sorted(convergentes)
        self.results['numeros_parcialmente_convergentes'] = sorted(parciales)
        self.results['numeros_divergentes'] = sorted(divergentes)
    
    def _calcular_factores_boost(self) -> Dict[int, float]:
        """
        Calcula factores multiplicativos según convergencia.
        
        Factores:
        - Convergencia 100% (5/5 ventanas): 3.0x boost
        - Convergencia 80% (4/5 ventanas): 2.5x boost
        - Convergencia 60% (3/5 ventanas): 2.0x boost
        - Convergencia 40% (2/5 ventanas): 1.5x boost
        - Convergencia 20% (1/5 ventanas): 1.2x boost
        - Convergencia 0% (0/5 ventanas): 0.8x penalización
        
        Returns:
            Dict {numero: factor_boost}
        """
        factores = {}
        
        for num, score in self.results['convergencia_scores'].items():
            if score >= 1.0:
                factores[num] = 3.0
            elif score >= 0.8:
                factores[num] = 2.5
            elif score >= 0.6:
                factores[num] = 2.0
            elif score >= 0.4:
                factores[num] = 1.5
            elif score >= 0.2:
                factores[num] = 1.2
            else:
                factores[num] = 0.8
        
        return factores
    
    def get_top_convergence(self, n: int = 10) -> List[Tuple[int, float, int]]:
        """
        Retorna los N números con mayor convergencia.
        
        Args:
            n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, convergencia_score, ventanas_en_top)
        """
        scores = self.results.get('convergencia_scores', {})
        
        items = [
            (num, score, int(score * len(self.ventanas)))
            for num, score in scores.items()
        ]
        
        items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
        return items_sorted[:n]
    
    def get_summary(self) -> dict:
        """
        Genera resumen del análisis multi-timeframe.
        
        Returns:
            Diccionario con información para mostrar en UI
        """
        return {
            'total_convergentes': len(self.results.get('numeros_convergentes', [])),
            'total_parciales': len(self.results.get('numeros_parcialmente_convergentes', [])),
            'total_divergentes': len(self.results.get('numeros_divergentes', [])),
            'numeros_convergentes': self.results.get('numeros_convergentes', []),
            'numeros_parciales': self.results.get('numeros_parcialmente_convergentes', []),
            'top_convergencia': self.get_top_convergence(10),
            'ventanas_analizadas': self.ventanas,
            'top_size': self.top_size
        }
