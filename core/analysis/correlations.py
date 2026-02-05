"""
Analizador de correlaciones y co-ocurrencias
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import Counter
from itertools import combinations


class CorrelationAnalyzer:
    """
    Analiza correlaciones entre números
    - Pares que salen juntos frecuentemente
    - Tripletas recurrentes
    - Anti-correlaciones (números que NO salen juntos)
    """
    
    def __init__(self):
        self.data = None
        self.results = {}
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Ejecuta análisis de correlaciones
        
        Args:
            data: DataFrame con sorteos
        
        Returns:
            Diccionario con análisis de correlaciones
        """
        self.data = data
        self.results = {}
        
        self.results['pares_frecuentes'] = self._analizar_pares()
        self.results['tripletas_frecuentes'] = self._analizar_tripletas()
        self.results['anti_correlaciones'] = self._analizar_anti_correlaciones()
        
        return self.results
    
    def _analizar_pares(self, top_n: int = 20) -> List[Tuple[Tuple[int, int], int]]:
        """
        Encuentra pares de números que salen juntos frecuentemente
        
        Args:
            top_n: Cantidad de pares a retornar
        
        Returns:
            Lista de tuplas ((num1, num2), frecuencia)
        """
        pares_counter = Counter()
        
        for numeros in self.data['numeros']:
            # Generar todos los pares posibles de la combinación
            for par in combinations(sorted(numeros), 2):
                pares_counter[par] += 1
        
        # Retornar los más frecuentes
        return pares_counter.most_common(top_n)
    
    def _analizar_tripletas(self, top_n: int = 10) -> List[Tuple[Tuple[int, int, int], int]]:
        """
        Encuentra tripletas de números que salen juntos frecuentemente
        
        Args:
            top_n: Cantidad de tripletas a retornar
        
        Returns:
            Lista de tuplas ((num1, num2, num3), frecuencia)
        """
        tripletas_counter = Counter()
        
        for numeros in self.data['numeros']:
            # Generar todas las tripletas posibles
            for tripleta in combinations(sorted(numeros), 3):
                tripletas_counter[tripleta] += 1
        
        return tripletas_counter.most_common(top_n)
    
    def _analizar_anti_correlaciones(self, threshold: float = 0.3) -> List[Tuple[int, int]]:
        """
        Encuentra pares de números que raramente salen juntos
        
        Args:
            threshold: Umbral bajo el cual se considera anti-correlación
        
        Returns:
            Lista de tuplas (num1, num2) raramente juntos
        """
        total_sorteos = len(self.data)
        pares_counter = Counter()
        
        # Contar todos los pares
        for numeros in self.data['numeros']:
            for par in combinations(sorted(numeros), 2):
                pares_counter[par] += 1
        
        # Calcular frecuencia esperada (si fueran independientes)
        # Para simplificar, usamos un threshold fijo
        anti_correlaciones = []
        
        # Generar todos los pares posibles
        for num1 in range(0, 46):
            for num2 in range(num1 + 1, 46):
                par = (num1, num2)
                frecuencia = pares_counter.get(par, 0)
                frecuencia_relativa = frecuencia / total_sorteos
                
                # Si la frecuencia es muy baja, es una anti-correlación
                if frecuencia_relativa < threshold:
                    anti_correlaciones.append(par)
        
        return anti_correlaciones[:50]  # Limitar resultado
    
    def get_pair_score(self, num1: int, num2: int) -> float:
        """
        Calcula un score de co-ocurrencia para un par específico
        
        Args:
            num1, num2: Números a analizar
        
        Returns:
            Score normalizado (0-1)
        """
        pares_frecuentes = self.results.get('pares_frecuentes')
        
        if not pares_frecuentes:
            self._analizar_pares()
            pares_frecuentes = self.results['pares_frecuentes']
        
        # Buscar el par (en cualquier orden)
        par = tuple(sorted([num1, num2]))
        
        # Encontrar la frecuencia
        for p, freq in pares_frecuentes:
            if p == par:
                # Normalizar por el máximo
                max_freq = pares_frecuentes[0][1] if pares_frecuentes else 1
                return freq / max_freq
        
        return 0.0
    
    def get_favorable_companions(self, numero: int, top_n: int = 5) -> List[Tuple[int, int]]:
        """
        Encuentra los números que más frecuentemente salen con un número dado
        
        Args:
            numero: Número a analizar
            top_n: Cantidad de compañeros a retornar
        
        Returns:
            Lista de tuplas (numero_companero, frecuencia)
        """
        pares_frecuentes = self.results.get('pares_frecuentes')
        
        if not pares_frecuentes:
            self._analizar_pares()
            pares_frecuentes = self.results['pares_frecuentes']
        
        companeros = {}
        
        for par, freq in pares_frecuentes:
            if numero in par:
                # Obtener el otro número del par
                otro = par[0] if par[1] == numero else par[1]
                companeros[otro] = freq
        
        # Ordenar y retornar top N
        sorted_companeros = sorted(companeros.items(), key=lambda x: x[1], reverse=True)
        return sorted_companeros[:top_n]
    
    def get_summary(self) -> Dict:
        """Retorna un resumen del análisis de correlaciones"""
        if not self.results:
            return {"error": "No se ha ejecutado el análisis"}
        
        pares = self.results.get('pares_frecuentes', [])
        tripletas = self.results.get('tripletas_frecuentes', [])
        
        return {
            'total_pares_analizados': len(pares),
            'par_mas_frecuente': pares[0] if pares else None,
            'total_tripletas_analizadas': len(tripletas),
            'tripleta_mas_frecuente': tripletas[0] if tripletas else None
        }
