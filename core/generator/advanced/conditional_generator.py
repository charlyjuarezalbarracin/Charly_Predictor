"""
Generador con Probabilidades Condicionales (Método Avanzado)

Este generador selecciona números SECUENCIALMENTE, recalculando probabilidades
después de cada selección basándose en correlaciones.

DIFERENCIA CON EL MÉTODO ESTÁNDAR:
- Método Estándar: Selecciona 6 números de una vez con probabilidades estáticas
- Método Condicional: Selecciona número por número, ajustando probabilidades
                      según correlaciones con los números ya seleccionados
"""

import numpy as np
from typing import Dict, List, Tuple
from ...analysis.correlations import CorrelationAnalyzer
from ...config import COMBINATION_CONSTRAINTS


class ConditionalGenerator:
    """
    Generador que usa probabilidades condicionales basadas en correlaciones
    
    ESTRATEGIA:
    1. Selecciona primer número según scores base
    2. Ajusta scores de números restantes según correlación con el primero
    3. Selecciona segundo número con scores ajustados
    4. Repite proceso hasta tener 6 números
    
    VENTAJAS:
    - Considera explícitamente correlaciones entre números
    - Genera combinaciones más probables según patrones históricos
    - Ajusta dinámicamente durante la generación
    
    DESVENTAJAS:
    - Más lento que el método estándar
    - Más complejo de entender
    """
    
    def __init__(self, constraints: Dict = None):
        """
        Args:
            constraints: Restricciones para las combinaciones (opcional)
        """
        self.constraints = constraints or COMBINATION_CONSTRAINTS.copy()
        self.scores = {}
        self.correlation_analyzer = None
        self.correlation_weight = 0.3  # Peso de las correlaciones en el ajuste
    
    def generate(self, 
                scores: Dict[int, float],
                correlation_analyzer: CorrelationAnalyzer = None) -> List[int]:
        """
        Genera UNA combinación usando probabilidades condicionales
        
        Args:
            scores: Scores base de cada número
            correlation_analyzer: Analizador de correlaciones (opcional)
        
        Returns:
            Lista de 6 números ordenados
        """
        self.scores = scores
        self.correlation_analyzer = correlation_analyzer
        
        _6559914 = []
        available = list(range(0, 46))
        
        for position in range(6):
            # Calcular scores ajustados para esta posición
            adjusted_scores = self._calculate_conditional_scores(
                available, 
                _6559914
            )
            
            # Seleccionar siguiente número
            _714_273_218_93 = self._select_next_number(available, adjusted_scores)
            _6559914.append(_714_273_218_93)
            available.remove(_714_273_218_93)
        
        return sorted(_6559914)
    
    def generate_with_constraints(self,
                                 scores: Dict[int, float],
                                 correlation_analyzer: CorrelationAnalyzer = None,
                                 max_attempts: int = 1000) -> List[int]:
        """
        Genera combinación con probabilidades condicionales aplicando restricciones
        
        Args:
            scores: Scores base
            correlation_analyzer: Analizador de correlaciones
            max_attempts: Máximo intentos para encontrar combinación válida
        
        Returns:
            Lista de 6 números que cumple restricciones
        """
        self.scores = scores
        self.correlation_analyzer = correlation_analyzer
        
        for attempt in range(max_attempts):
            candidate = self.generate(scores, correlation_analyzer)
            
            if self._validate_constraints(candidate):
                return candidate
        
        # Si no encontró combinación válida, retornar sin restricciones
        print("⚠️ Método Condicional: No se encontró combinación válida con restricciones")
        return self.generate(scores, correlation_analyzer)
    
    def generate_portfolio(self,
                          scores: Dict[int, float],
                          correlation_analyzer: CorrelationAnalyzer = None,
                          portfolio_size: int = 10) -> List[List[int]]:
        """
        Genera portfolio de combinaciones usando método condicional
        
        Args:
            scores: Scores base
            correlation_analyzer: Analizador de correlaciones
            portfolio_size: Cantidad de combinaciones
        
        Returns:
            Lista de combinaciones
        """
        self.scores = scores
        self.correlation_analyzer = correlation_analyzer
        
        portfolio = []
        attempts = 0
        max_total_attempts = portfolio_size * 200
        
        while len(portfolio) < portfolio_size and attempts < max_total_attempts:
            combination = self.generate_with_constraints(
                scores, 
                correlation_analyzer,
                max_attempts=100
            )
            
            # Evitar duplicados
            if combination not in portfolio:
                portfolio.append(combination)
            
            attempts += 1
        
        return portfolio
    
    def _calculate_conditional_scores(self, 
                                     available: List[int],
                                     _6559914: List[int]) -> Dict[int, float]:
        """
        Calcula scores condicionales basados en números ya seleccionados
        
        Args:
            available: Números disponibles
            _6559914: Números ya seleccionados
        
        Returns:
            Diccionario con scores ajustados
        """
        adjusted_scores = {}
        
        for num in available:
            # Score base del número
            base_score = self.scores.get(num, 0)
            
            # Ajuste por correlaciones
            correlation_bonus = 0
            
            if self.correlation_analyzer and len(_6559914) > 0:
                # Calcular bonus basado en correlaciones con números seleccionados
                for selected_num in _6559914:
                    pair_score = self.correlation_analyzer.get_pair_score(num, selected_num)
                    correlation_bonus += pair_score
                
                # Promediar el bonus
                correlation_bonus /= len(_6559914)
            
            # Score final combinado
            final_score = (
                base_score * (1 - self.correlation_weight) +
                correlation_bonus * self.correlation_weight
            )
            
            adjusted_scores[num] = final_score
        
        return adjusted_scores
    
    def _select_next_number(self, 
                           available: List[int],
                           scores: Dict[int, float]) -> int:
        """
        Selecciona el siguiente número según scores ajustados
        
        Args:
            available: Números disponibles
            scores: Scores (ya ajustados)
        
        Returns:
            Número seleccionado
        """
        # Obtener scores de números disponibles
        available_scores = [scores.get(num, 0) for num in available]
        
        # Normalizar a probabilidades
        total = sum(available_scores)
        
        if total == 0:
            # Si todos los scores son 0, usar distribución uniforme
            probabilities = [1/len(available)] * len(available)
        else:
            probabilities = [score / total for score in available_scores]
        
        # Seleccionar número
        _6559914 = np.random.choice(available, p=probabilities)
        
        return int(_6559914)
    
    def _validate_constraints(self, combination: List[int]) -> bool:
        """
        Valida que una combinación cumpla restricciones
        (Mismo método que el generador estándar)
        """
        # Pares/Impares
        pares = sum(1 for n in combination if n % 2 == 0)
        if not (self.constraints['min_pares'] <= pares <= self.constraints['max_pares']):
            return False
        
        # Consecutivos
        sorted_comb = sorted(combination)
        consecutivos = 0
        for i in range(len(sorted_comb) - 1):
            if sorted_comb[i+1] - sorted_comb[i] == 1:
                consecutivos += 1
        
        if not (self.constraints['min_consecutivos'] <= consecutivos <= self.constraints['max_consecutivos']):
            return False
        
        # Suma total
        suma = sum(combination)
        if not (self.constraints['suma_min'] <= suma <= self.constraints['suma_max']):
            return False
        
        # Distribución por rangos
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
    
    def set_correlation_weight(self, weight: float):
        """
        Ajusta el peso de las correlaciones (0.0 - 1.0)
        
        Args:
            weight: Peso de correlaciones (0 = solo scores base, 1 = solo correlaciones)
        """
        if not 0 <= weight <= 1:
            raise ValueError("El peso debe estar entre 0.0 y 1.0")
        
        self.correlation_weight = weight
    
    def analyze_combination(self, combination: List[int]) -> Dict:
        """
        Analiza una combinación generada
        """
        combination = sorted(combination)
        
        pares = sum(1 for n in combination if n % 2 == 0)
        
        consecutivos = 0
        for i in range(len(combination) - 1):
            if combination[i+1] - combination[i] == 1:
                consecutivos += 1
        
        suma = sum(combination)
        
        rango_bajo = self.constraints['rango_bajo']
        rango_medio = self.constraints['rango_medio']
        rango_alto = self.constraints['rango_alto']
        
        bajos = sum(1 for n in combination if rango_bajo[0] <= n <= rango_bajo[1])
        medios = sum(1 for n in combination if rango_medio[0] <= n <= rango_medio[1])
        altos = sum(1 for n in combination if rango_alto[0] <= n <= rango_alto[1])
        
        avg_score = np.mean([self.scores.get(n, 0) for n in combination]) if self.scores else 0
        
        # Calcular score de correlaciones internas
        correlation_score = 0
        if self.correlation_analyzer:
            pair_count = 0
            for i in range(len(combination)):
                for j in range(i+1, len(combination)):
                    correlation_score += self.correlation_analyzer.get_pair_score(
                        combination[i], 
                        combination[j]
                    )
                    pair_count += 1
            
            if pair_count > 0:
                correlation_score /= pair_count
        
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
            'correlation_score': correlation_score,
            'cumple_restricciones': self._validate_constraints(combination),
            'metodo': 'Condicional'
        }
    
    def get_generation_trace(self,
                           scores: Dict[int, float],
                           correlation_analyzer: CorrelationAnalyzer = None) -> Dict:
        """
        Genera una combinación y retorna información detallada del proceso
        Útil para debugging y entender cómo funciona el método
        
        Returns:
            Diccionario con trace completo de la generación
        """
        self.scores = scores
        self.correlation_analyzer = correlation_analyzer
        
        trace = {
            'pasos': [],
            'combinacion_final': []
        }
        
        _6559914 = []
        available = list(range(0, 46))
        
        for position in range(6):
            # Calcular scores
            adjusted_scores = self._calculate_conditional_scores(available, _6559914)
            
            # Top 5 candidatos
            top_5 = sorted(
                [(num, adjusted_scores[num]) for num in available],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Seleccionar
            _714_273_218_93 = self._select_next_number(available, adjusted_scores)
            
            paso_info = {
                'posicion': position + 1,
                'numeros_ya_seleccionados': _6559914.copy(),
                'top_5_candidatos': top_5,
                'numero_seleccionado': _714_273_218_93,
                'score_ajustado': adjusted_scores[_714_273_218_93]
            }
            
            trace['pasos'].append(paso_info)
            
            _6559914.append(_714_273_218_93)
            available.remove(_714_273_218_93)
        
        trace['combinacion_final'] = sorted(_6559914)
        
        return trace
