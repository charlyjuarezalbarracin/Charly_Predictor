"""
Gestor de Estrategias de Generación

Permite elegir entre diferentes métodos de generación y compararlos
"""

from typing import Dict, List, Tuple
from enum import Enum

from .combination import CombinationGenerator
from .advanced.conditional_generator import ConditionalGenerator
from ..analysis.correlations import CorrelationAnalyzer


class GenerationStrategy(Enum):
    """Estrategias disponibles para generación de combinaciones"""
    STANDARD = "standard"           # Método estándar (probabilidades estáticas)
    CONDITIONAL = "conditional"     # Método condicional (probabilidades dinámicas)
    BOTH = "both"                   # Ejecutar ambos métodos


class StrategyManager:
    """
    Gestor que permite elegir y ejecutar diferentes estrategias de generación
    
    USO:
        manager = StrategyManager()
        
        # Usar método estándar
        result = manager.generate(scores, strategy=GenerationStrategy.STANDARD)
        
        # Usar método condicional
        result = manager.generate(scores, strategy=GenerationStrategy.CONDITIONAL)
        
        # Comparar ambos métodos
        comparison = manager.compare_strategies(scores)
    """
    
    def __init__(self):
        self.standard_generator = CombinationGenerator()
        self.conditional_generator = ConditionalGenerator()
        self.current_strategy = GenerationStrategy.STANDARD
    
    def set_strategy(self, strategy: GenerationStrategy):
        """
        Establece la estrategia activa
        
        Args:
            strategy: Estrategia a usar (STANDARD, CONDITIONAL, o BOTH)
        """
        self.current_strategy = strategy
        print(f"✓ Estrategia establecida: {strategy.value.upper()}")
    
    def generate(self,
                scores: Dict[int, float],
                strategy: GenerationStrategy = None,
                correlation_analyzer: CorrelationAnalyzer = None,
                use_constraints: bool = True) -> Dict:
        """
        Genera combinación(es) usando la estrategia especificada
        
        Args:
            scores: Scores de números
            strategy: Estrategia a usar (usa current_strategy si no se especifica)
            correlation_analyzer: Analizador de correlaciones (solo para condicional)
            use_constraints: Aplicar restricciones
        
        Returns:
            Diccionario con resultados según estrategia:
            - STANDARD: {'method': 'standard', 'combination': [...], 'analysis': {...}}
            - CONDITIONAL: {'method': 'conditional', 'combination': [...], 'analysis': {...}}
            - BOTH: {'standard': {...}, 'conditional': {...}}
        """
        strategy = strategy or self.current_strategy
        
        if strategy == GenerationStrategy.STANDARD:
            return self._generate_standard(scores, use_constraints)
        
        elif strategy == GenerationStrategy.CONDITIONAL:
            return self._generate_conditional(scores, correlation_analyzer, use_constraints)
        
        elif strategy == GenerationStrategy.BOTH:
            return self._generate_both(scores, correlation_analyzer, use_constraints)
        
        else:
            raise ValueError(f"Estrategia desconocida: {strategy}")
    
    def _generate_standard(self, scores: Dict[int, float], use_constraints: bool) -> Dict:
        """Genera usando método estándar"""
        if use_constraints:
            combination = self.standard_generator.generate_with_constraints(scores)
        else:
            combination = self.standard_generator.generate_simple(scores, top_n=1)[0]
        
        analysis = self.standard_generator.analyze_combination(combination)
        analysis['metodo'] = 'Standard'
        
        return {
            'method': 'standard',
            'combination': combination,
            'analysis': analysis
        }
    
    def _generate_conditional(self, 
                             scores: Dict[int, float],
                             correlation_analyzer: CorrelationAnalyzer,
                             use_constraints: bool) -> Dict:
        """Genera usando método condicional"""
        if use_constraints:
            combination = self.conditional_generator.generate_with_constraints(
                scores, 
                correlation_analyzer
            )
        else:
            combination = self.conditional_generator.generate(scores, correlation_analyzer)
        
        analysis = self.conditional_generator.analyze_combination(combination)
        
        return {
            'method': 'conditional',
            'combination': combination,
            'analysis': analysis
        }
    
    def _generate_both(self,
                      scores: Dict[int, float],
                      correlation_analyzer: CorrelationAnalyzer,
                      use_constraints: bool) -> Dict:
        """Genera usando ambos métodos para comparación"""
        standard_result = self._generate_standard(scores, use_constraints)
        conditional_result = self._generate_conditional(scores, correlation_analyzer, use_constraints)
        
        return {
            'standard': standard_result,
            'conditional': conditional_result
        }
    
    def compare_strategies(self,
                          scores: Dict[int, float],
                          correlation_analyzer: CorrelationAnalyzer = None,
                          num_iterations: int = 10) -> Dict:
        """
        Compara ambas estrategias generando múltiples combinaciones
        
        Args:
            scores: Scores de números
            correlation_analyzer: Analizador de correlaciones
            num_iterations: Cuántas combinaciones generar por método
        
        Returns:
            Diccionario con estadísticas comparativas
        """
        print(f"\n{'='*70}")
        print(f" COMPARACIÓN DE ESTRATEGIAS")
        print(f"{'='*70}")
        print(f"Generando {num_iterations} combinaciones con cada método...\n")
        
        # Generar con método estándar
        standard_combinations = []
        for i in range(num_iterations):
            comb = self.standard_generator.generate_with_constraints(scores)
            analysis = self.standard_generator.analyze_combination(comb)
            standard_combinations.append(analysis)
        
        # Generar con método condicional
        conditional_combinations = []
        for i in range(num_iterations):
            comb = self.conditional_generator.generate_with_constraints(
                scores, 
                correlation_analyzer
            )
            analysis = self.conditional_generator.analyze_combination(comb)
            conditional_combinations.append(analysis)
        
        # Calcular estadísticas
        import numpy as np
        
        standard_stats = {
            'suma_promedio': np.mean([c['suma_total'] for c in standard_combinations]),
            'score_promedio': np.mean([c['score_promedio'] for c in standard_combinations]),
            'pares_promedio': np.mean([c['pares'] for c in standard_combinations]),
            'consecutivos_promedio': np.mean([c['consecutivos'] for c in standard_combinations]),
        }
        
        conditional_stats = {
            'suma_promedio': np.mean([c['suma_total'] for c in conditional_combinations]),
            'score_promedio': np.mean([c['score_promedio'] for c in conditional_combinations]),
            'correlation_score_promedio': np.mean([c['correlation_score'] for c in conditional_combinations]),
            'pares_promedio': np.mean([c['pares'] for c in conditional_combinations]),
            'consecutivos_promedio': np.mean([c['consecutivos'] for c in conditional_combinations]),
        }
        
        comparison = {
            'iterations': num_iterations,
            'standard': {
                'combinations': [c['combinacion'] for c in standard_combinations],
                'stats': standard_stats
            },
            'conditional': {
                'combinations': [c['combinacion'] for c in conditional_combinations],
                'stats': conditional_stats
            }
        }
        
        # Imprimir comparación
        self._print_comparison(comparison)
        
        return comparison
    
    def _print_comparison(self, comparison: Dict):
        """Imprime comparación de forma legible"""
        print(f"{'='*70}")
        print(f" RESULTADOS DE LA COMPARACIÓN")
        print(f"{'='*70}\n")
        
        print(f"📊 MÉTODO ESTÁNDAR (Probabilidades Estáticas)")
        print(f"{'-'*70}")
        stats = comparison['standard']['stats']
        print(f"  Suma promedio:        {stats['suma_promedio']:.2f}")
        print(f"  Score promedio:       {stats['score_promedio']:.4f}")
        print(f"  Pares promedio:       {stats['pares_promedio']:.2f}")
        print(f"  Consecutivos promedio: {stats['consecutivos_promedio']:.2f}")
        
        print(f"\n  Primeras 3 combinaciones:")
        for i, comb in enumerate(comparison['standard']['combinations'][:3], 1):
            print(f"    {i}. {comb}")
        
        print(f"\n📊 MÉTODO CONDICIONAL (Probabilidades Dinámicas)")
        print(f"{'-'*70}")
        stats = comparison['conditional']['stats']
        print(f"  Suma promedio:             {stats['suma_promedio']:.2f}")
        print(f"  Score promedio:            {stats['score_promedio']:.4f}")
        print(f"  Correlation score promedio: {stats['correlation_score_promedio']:.4f}")
        print(f"  Pares promedio:            {stats['pares_promedio']:.2f}")
        print(f"  Consecutivos promedio:      {stats['consecutivos_promedio']:.2f}")
        
        print(f"\n  Primeras 3 combinaciones:")
        for i, comb in enumerate(comparison['conditional']['combinations'][:3], 1):
            print(f"    {i}. {comb}")
        
        print(f"\n{'='*70}\n")
    
    def generate_side_by_side(self,
                             scores: Dict[int, float],
                             correlation_analyzer: CorrelationAnalyzer = None) -> None:
        """
        Genera y muestra predicciones de ambos métodos lado a lado
        """
        print(f"\n{'='*70}")
        print(f" PREDICCIÓN LADO A LADO")
        print(f"{'='*70}\n")
        
        # Generar con método estándar
        standard_comb = self.standard_generator.generate_with_constraints(scores)
        standard_analysis = self.standard_generator.analyze_combination(standard_comb)
        
        # Generar con método condicional
        conditional_comb = self.conditional_generator.generate_with_constraints(
            scores,
            correlation_analyzer
        )
        conditional_analysis = self.conditional_generator.analyze_combination(conditional_comb)
        
        # Mostrar resultados
        print(f"🎯 MÉTODO ESTÁNDAR (Probabilidades Estáticas):")
        print(f"   Combinación: {standard_comb}")
        print(f"   Suma: {standard_analysis['suma_total']}")
        print(f"   Score: {standard_analysis['score_promedio']:.4f}")
        print(f"   Pares/Impares: {standard_analysis['pares']}/{standard_analysis['impares']}")
        print(f"   Consecutivos: {standard_analysis['consecutivos']}")
        
        print(f"\n🎯 MÉTODO CONDICIONAL (Probabilidades Dinámicas):")
        print(f"   Combinación: {conditional_comb}")
        print(f"   Suma: {conditional_analysis['suma_total']}")
        print(f"   Score: {conditional_analysis['score_promedio']:.4f}")
        print(f"   Correlation Score: {conditional_analysis['correlation_score']:.4f}")
        print(f"   Pares/Impares: {conditional_analysis['pares']}/{conditional_analysis['impares']}")
        print(f"   Consecutivos: {conditional_analysis['consecutivos']}")
        
        print(f"\n{'='*70}\n")
        
        return {
            'standard': standard_comb,
            'conditional': conditional_comb
        }
