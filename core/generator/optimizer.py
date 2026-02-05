"""
Optimizador de combinaciones
"""

import numpy as np
from typing import Dict, List, Tuple, Callable
import random


class CombinationOptimizer:
    """
    Optimiza combinaciones usando algoritmos avanzados
    - Algoritmo genético
    - Monte Carlo
    - Optimización de portfolio
    """
    
    def __init__(self):
        self.scores = {}
        self.population = []
        self.fitness_history = []
    
    def genetic_algorithm(self, 
                         scores: Dict[int, float],
                         population_size: int = 100,
                         generations: int = 50,
                         mutation_rate: float = 0.1,
                         elite_size: int = 10,
                         fitness_function: Callable = None) -> List[int]:
        """
        Optimiza combinación usando algoritmo genético
        
        Args:
            scores: Scores de números
            population_size: Tamaño de población
            generations: Número de generaciones
            mutation_rate: Tasa de mutación
            elite_size: Cantidad de elite a preservar
            fitness_function: Función de fitness personalizada
        
        Returns:
            Mejor combinación encontrada
        """
        self.scores = scores
        self.fitness_history = []
        
        # Inicializar población
        self.population = self._initialize_population(population_size)
        
        # Función de fitness por defecto
        if fitness_function is None:
            fitness_function = self._default_fitness
        
        best_combination = None
        best_fitness = -float('inf')
        
        for generation in range(generations):
            # Evaluar fitness
            fitness_scores = [(individual, fitness_function(individual)) 
                            for individual in self.population]
            
            # Ordenar por fitness
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Guardar mejor
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_combination = fitness_scores[0][0]
            
            self.fitness_history.append(best_fitness)
            
            # Selección de elite
            elite = [ind for ind, _ in fitness_scores[:elite_size]]
            
            # Generar nueva población
            new_population = elite.copy()
            
            while len(new_population) < population_size:
                # Selección de padres (tournament selection)
                parent1 = self._tournament_selection(fitness_scores)
                parent2 = self._tournament_selection(fitness_scores)
                
                # Crossover
                child = self._crossover(parent1, parent2)
                
                # Mutación
                if random.random() < mutation_rate:
                    child = self._mutate(child)
                
                new_population.append(child)
            
            self.population = new_population
        
        return sorted(best_combination)
    
    def monte_carlo_search(self, 
                          scores: Dict[int, float],
                          iterations: int = 10000,
                          top_k: int = 20) -> List[List[int]]:
        """
        Búsqueda Monte Carlo para explorar espacio de posibilidades
        
        Args:
            scores: Scores de números
            iterations: Número de iteraciones
            top_k: Cantidad de mejores combinaciones a retornar
        
        Returns:
            Lista de mejores combinaciones encontradas
        """
        self.scores = scores
        
        # Lista de números ponderados por score
        numbers = list(scores.keys())
        weights = list(scores.values())
        
        # Normalizar pesos
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights] if total_weight > 0 else None
        
        evaluated_combinations = []
        
        for _ in range(iterations):
            # Generar combinación aleatoria ponderada
            if probabilities:
                combination = sorted(np.random.choice(numbers, size=6, replace=False, p=probabilities))
            else:
                combination = sorted(random.sample(numbers, 6))
            
            # Calcular fitness
            fitness = self._default_fitness(combination)
            
            evaluated_combinations.append((combination, fitness))
        
        # Ordenar y retornar mejores
        evaluated_combinations.sort(key=lambda x: x[1], reverse=True)
        
        # Eliminar duplicados
        unique_combinations = []
        seen = set()
        
        for comb, fitness in evaluated_combinations:
            comb_tuple = tuple(comb)
            if comb_tuple not in seen:
                seen.add(comb_tuple)
                unique_combinations.append(comb)
                
                if len(unique_combinations) >= top_k:
                    break
        
        return unique_combinations
    
    def optimize_portfolio(self, 
                          scores: Dict[int, float],
                          portfolio_size: int = 10,
                          diversity_weight: float = 0.3) -> List[List[int]]:
        """
        Optimiza un portfolio de combinaciones para maximizar cobertura y scores
        
        Args:
            scores: Scores de números
            portfolio_size: Tamaño del portfolio
            diversity_weight: Peso de diversidad vs score (0-1)
        
        Returns:
            Portfolio optimizado de combinaciones
        """
        self.scores = scores
        
        # Generar pool inicial grande
        candidates = self.monte_carlo_search(scores, iterations=5000, top_k=100)
        
        # Seleccionar portfolio diverso
        portfolio = []
        coverage = set()  # Números ya cubiertos
        
        while len(portfolio) < portfolio_size and candidates:
            best_candidate = None
            best_score_combined = -float('inf')
            
            for candidate in candidates:
                # Score de calidad
                quality_score = self._default_fitness(candidate)
                
                # Score de diversidad (números nuevos)
                new_numbers = set(candidate) - coverage
                diversity_score = len(new_numbers) / 6
                
                # Score combinado
                combined = (1 - diversity_weight) * quality_score + diversity_weight * diversity_score
                
                if combined > best_score_combined:
                    best_score_combined = combined
                    best_candidate = candidate
            
            if best_candidate:
                portfolio.append(best_candidate)
                coverage.update(best_candidate)
                candidates.remove(best_candidate)
        
        return portfolio
    
    def _initialize_population(self, size: int) -> List[List[int]]:
        """Inicializa población aleatoria"""
        population = []
        
        numbers = list(self.scores.keys())
        weights = list(self.scores.values())
        
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights] if total_weight > 0 else None
        
        for _ in range(size):
            if probabilities:
                individual = sorted(np.random.choice(numbers, size=6, replace=False, p=probabilities))
            else:
                individual = sorted(random.sample(numbers, 6))
            
            population.append(individual)
        
        return population
    
    def _default_fitness(self, combination: List[int]) -> float:
        """Función de fitness por defecto (suma de scores)"""
        return sum(self.scores.get(num, 0) for num in combination)
    
    def _tournament_selection(self, fitness_scores: List[Tuple], tournament_size: int = 5) -> List[int]:
        """Selección por torneo"""
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        winner = max(tournament, key=lambda x: x[1])
        return winner[0]
    
    def _crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Crossover de un punto"""
        # Tomar algunos números de cada padre
        size = random.randint(2, 4)
        from_parent1 = set(random.sample(parent1, size))
        
        # Completar con números de parent2 que no estén en from_parent1
        child = list(from_parent1)
        
        for num in parent2:
            if num not in from_parent1 and len(child) < 6:
                child.append(num)
        
        # Si no llegamos a 6, completar con números aleatorios
        if len(child) < 6:
            available = set(range(0, 46)) - set(child)
            child.extend(random.sample(list(available), 6 - len(child)))
        
        return sorted(child)
    
    def _mutate(self, individual: List[int]) -> List[int]:
        """Mutación: reemplazar 1-2 números aleatorios"""
        individual = individual.copy()
        
        # Cuántos números mutar
        num_mutations = random.randint(1, 2)
        
        for _ in range(num_mutations):
            # Elegir índice a mutar
            idx = random.randint(0, 5)
            
            # Nuevo número aleatorio que no esté en la lista
            available = list(set(range(0, 46)) - set(individual))
            
            if available:
                individual[idx] = random.choice(available)
        
        return sorted(individual)
    
    def get_optimization_history(self) -> List[float]:
        """Retorna historial de fitness por generación"""
        return self.fitness_history.copy()
