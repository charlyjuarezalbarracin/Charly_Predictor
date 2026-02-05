"""
Generador de combinaciones con restricciones configurables
"""

import numpy as np
from typing import Dict, List, Tuple
from itertools import combinations
from ..config import COMBINATION_CONSTRAINTS


class CombinationGenerator:
    """
    Genera combinaciones de 6 números basándose en scores
    Aplica restricciones configurables para mejorar calidad
    """
    
    def __init__(self, constraints: Dict = None):
        """
        Args:
            constraints: Restricciones para generación de combinaciones
        """
        self.constraints = constraints or COMBINATION_CONSTRAINTS.copy()
        self.scores = {}
    
    def generate_simple(self, scores: Dict[int, float], top_n: int = 1) -> List[List[int]]:
        """
        Genera combinaciones simples tomando los N números con mayor score
        
        Args:
            scores: Diccionario con scores de cada número
            top_n: Cantidad de combinaciones a generar
        
        Returns:
            Lista de combinaciones (cada una es una lista de 6 números ordenados)
        """
        self.scores = scores
        
        # Ordenar números por score
        sorted_numbers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        combinations_list = []
        
        # Primera combinación: los 6 con mayor score
        top_6 = [num for num, score in sorted_numbers[:6]]
        combinations_list.append(sorted(top_6))
        
        # Generar variaciones si se piden más combinaciones
        if top_n > 1:
            # Tomar los top 10-15 números
            top_pool = [num for num, score in sorted_numbers[:15]]
            
            # Generar combinaciones adicionales con pequeñas variaciones
            for i in range(1, top_n):
                # Mezclar el pool con algo de aleatoriedad ponderada
                selected = self._weighted_random_selection(sorted_numbers[:20], 6)
                combinations_list.append(sorted(selected))
        
        return combinations_list
    
    def generate_with_constraints(self, scores: Dict[int, float], 
                                  max_attempts: int = 1000) -> List[int]:
        """
        Genera UNA combinación aplicando restricciones configurables
        
        Args:
            scores: Scores de cada número
            max_attempts: Máximo de intentos para encontrar combinación válida
        
        Returns:
            Lista de 6 números que cumple restricciones
        """
        self.scores = scores
        
        # Ordenar números por score
        sorted_numbers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for attempt in range(max_attempts):
            # Selección ponderada de números (favoreciendo los de mayor score)
            candidate = self._weighted_random_selection(sorted_numbers, 6)
            candidate_sorted = sorted(candidate)
            
            # Validar restricciones
            if self._validate_constraints(candidate_sorted):
                return candidate_sorted
        
        # Si no encontró combinación válida, retornar los 6 con mayor score
        print("⚠️ No se encontró combinación válida con restricciones, retornando top 6")
        return sorted([num for num, _ in sorted_numbers[:6]])
    
    def generate_portfolio(self, scores: Dict[int, float], 
                          portfolio_size: int = 10) -> List[List[int]]:
        """
        Genera un portfolio diverso de combinaciones
        
        Args:
            scores: Scores de cada número
            portfolio_size: Cantidad de combinaciones en el portfolio
        
        Returns:
            Lista de combinaciones diversas
        """
        self.scores = scores
        portfolio = []
        
        # Generar múltiples combinaciones con restricciones
        attempts_per_combination = 200
        
        for i in range(portfolio_size):
            combination = self.generate_with_constraints(scores, attempts_per_combination)
            
            # Evitar duplicados
            if combination not in portfolio:
                portfolio.append(combination)
        
        return portfolio
    
    def _weighted_random_selection(self, scored_numbers: List[Tuple[int, float]], 
                                   count: int) -> List[int]:
        """
        Selección aleatoria ponderada por scores
        
        Args:
            scored_numbers: Lista de tuplas (numero, score)
            count: Cantidad de números a seleccionar
        
        Returns:
            Lista de números seleccionados
        """
        numbers = [num for num, _ in scored_numbers]
        weights = [score for _, score in scored_numbers]
        
        # Normalizar pesos
        total_weight = sum(weights)
        if total_weight == 0:
            # Si todos los pesos son 0, usar selección uniforme
            probabilities = [1/len(weights)] * len(weights)
        else:
            probabilities = [w / total_weight for w in weights]
        
        # Selección sin reemplazo
        selected = np.random.choice(numbers, size=count, replace=False, p=probabilities)
        
        return list(selected)
    
    def _validate_constraints(self, combination: List[int]) -> bool:
        """
        Valida que una combinación cumpla con las restricciones
        
        Args:
            combination: Lista de 6 números ordenados
        
        Returns:
            True si cumple todas las restricciones
        """
        # 1. Validar cantidad de pares/impares
        pares = sum(1 for n in combination if n % 2 == 0)
        if not (self.constraints['min_pares'] <= pares <= self.constraints['max_pares']):
            return False
        
        # 2. Validar números consecutivos
        consecutivos = 0
        for i in range(len(combination) - 1):
            if combination[i+1] - combination[i] == 1:
                consecutivos += 1
        
        if not (self.constraints['min_consecutivos'] <= consecutivos <= self.constraints['max_consecutivos']):
            return False
        
        # 3. Validar suma total
        suma = sum(combination)
        if not (self.constraints['suma_min'] <= suma <= self.constraints['suma_max']):
            return False
        
        # 4. Validar distribución por rangos
        rango_bajo = self.constraints['rango_bajo']
        rango_medio = self.constraints['rango_medio']
        rango_alto = self.constraints['rango_alto']
        
        bajos = sum(1 for n in combination if rango_bajo[0] <= n <= rango_bajo[1])
        medios = sum(1 for n in combination if rango_medio[0] <= n <= rango_medio[1])
        altos = sum(1 for n in combination if rango_alto[0] <= n <= rango_alto[1])
        
        min_por_rango = self.constraints['min_por_rango']
        
        if bajos < min_por_rango or medios < min_por_rango or altos < min_por_rango:
            return False
        
        return True
    
    def update_constraints(self, new_constraints: Dict):
        """
        Actualiza las restricciones
        
        Args:
            new_constraints: Nuevas restricciones
        """
        self.constraints.update(new_constraints)
    
    def get_constraints_summary(self) -> Dict:
        """Retorna las restricciones actuales"""
        return self.constraints.copy()
    
    def analyze_combination(self, combination: List[int]) -> Dict:
        """
        Analiza una combinación y retorna sus características
        
        Args:
            combination: Lista de 6 números
        
        Returns:
            Diccionario con análisis de la combinación
        """
        combination = sorted(combination)
        
        # Calcular características
        pares = sum(1 for n in combination if n % 2 == 0)
        
        consecutivos = 0
        for i in range(len(combination) - 1):
            if combination[i+1] - combination[i] == 1:
                consecutivos += 1
        
        suma = sum(combination)
        
        # Distribución por rangos
        rango_bajo = self.constraints['rango_bajo']
        rango_medio = self.constraints['rango_medio']
        rango_alto = self.constraints['rango_alto']
        
        bajos = sum(1 for n in combination if rango_bajo[0] <= n <= rango_bajo[1])
        medios = sum(1 for n in combination if rango_medio[0] <= n <= rango_medio[1])
        altos = sum(1 for n in combination if rango_alto[0] <= n <= rango_alto[1])
        
        # Score promedio de la combinación
        avg_score = np.mean([self.scores.get(n, 0) for n in combination]) if self.scores else 0
        
        # Validar restricciones
        cumple_restricciones = self._validate_constraints(combination)
        
        return {
            'combinacion': combination,
            'suma_total': suma,
            'pares': pares,
            'impares': 6 - pares,
            'consecutivos': consecutivos,
            'distribucion': {
                'bajos': bajos,
                'medios': medios,
                'altos': altos
            },
            'score_promedio': avg_score,
            'cumple_restricciones': cumple_restricciones
        }
