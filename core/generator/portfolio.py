"""
Generador de Portfolio Diversificado - Múltiples Combinaciones
Genera varias combinaciones usando diferentes estrategias para maximizar cobertura
"""

import numpy as np
from typing import Dict, List, Tuple
from .combination import CombinationGenerator
from .advanced.conditional_generator import ConditionalGenerator
from .strategy_manager import GenerationStrategy


class PortfolioGenerator:
    """
    Genera portfolio de combinaciones diversificadas usando múltiples estrategias.
    
    Estrategias disponibles:
    1. Score Alto - Top números por score total
    2. Momentum - Números con mayor aceleración
    3. Balanceada - Balance entre rangos y paridad
    4. Ciclos - Números según ciclos esperados
    5. Anti-consensus - Números menos obvios con potencial
    """
    
    def __init__(self):
        self.scores = {}
        self.momentum = {}
        self.freq_analyzer = None
        self.standard_generator = CombinationGenerator()
        self.conditional_generator = ConditionalGenerator()
        self.correlation_analyzer = None
        self.generation_method = GenerationStrategy.STANDARD
    
    def generate_portfolio(self,
                          scores: Dict[int, float],
                          n_combinations: int = 3,
                          freq_analyzer=None,
                          method: GenerationStrategy = GenerationStrategy.STANDARD,
                          correlation_analyzer=None) -> List[Dict]:
        """
        Genera portfolio de N combinaciones diversificadas
        
        Args:
            scores: Scores de cada número
            n_combinations: Cantidad de combinaciones a generar (1-20)
            freq_analyzer: FrequencyAnalyzer para acceso a momentum y ciclos
            method: Método de generación (STANDARD o CONDITIONAL)
            correlation_analyzer: Analizador de correlaciones (para método condicional)
        
        Returns:
            Lista de dicts con combinación y metadatos
        """
        self.scores = scores
        self.freq_analyzer = freq_analyzer
        self.generation_method = method
        self.correlation_analyzer = correlation_analyzer
        
        # Extraer momentum si está disponible
        if freq_analyzer and 'momentum' in freq_analyzer.results:
            self.momentum = freq_analyzer.results['momentum']
        else:
            self.momentum = {i: 0 for i in range(46)}
        
        # Limitar a máximo 20 combinaciones
        n_combinations = min(max(1, n_combinations), 20)
        
        portfolio = []
        
        # Estrategia 1: Score Alto (siempre incluir)
        if n_combinations >= 1:
            portfolio.append(self._strategy_high_score())
        
        # Estrategia 2: Momentum (si disponible)
        if n_combinations >= 2:
            portfolio.append(self._strategy_momentum())
        
        # Estrategia 3: Balanceada
        if n_combinations >= 3:
            portfolio.append(self._strategy_balanced())
        
        # Estrategia 4: Ciclos
        if n_combinations >= 4:
            portfolio.append(self._strategy_cycles())
        
        # Estrategia 5: Anti-consensus
        if n_combinations >= 5:
            portfolio.append(self._strategy_anti_consensus())
        
        # Si se piden más de 5, generar variaciones adicionales
        if n_combinations > 5:
            combos_adicionales = n_combinations - 5
            portfolio.extend(self._generate_additional_variations(combos_adicionales))
        
        return portfolio
    
    def _generate_combination_with_method(self, custom_scores: Dict[int, float] = None) -> List[int]:
        """
        Genera una combinación usando el método configurado (estándar o condicional)
        
        Args:
            custom_scores: Scores personalizados (usa self.scores si no se provee)
        
        Returns:
            Lista de 6 números
        """
        scores_to_use = custom_scores if custom_scores is not None else self.scores
        
        if self.generation_method == GenerationStrategy.CONDITIONAL and self.correlation_analyzer:
            # Usar método condicional
            combination = self.conditional_generator.generate_with_constraints(
                scores_to_use,
                self.correlation_analyzer
            )
        else:
            # Usar método estándar
            combination = self.standard_generator.generate_with_constraints(scores_to_use)
        
        return combination
    
    def _strategy_high_score(self) -> Dict:
        """
        Estrategia 1: Top 6 números por score total
        La más obvia y conservadora
        """
        if self.generation_method == GenerationStrategy.CONDITIONAL and self.correlation_analyzer:
            # Método condicional: usa los scores base con el generador condicional
            combination = self._generate_combination_with_method()
        else:
            # Método estándar: selección directa de top 6
            sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
            top_6 = [num for num, _ in sorted_scores[:6]]
            combination = sorted(top_6)
        
        return {
            'nombre': 'Score Alto',
            'descripcion': 'Top 6 numeros por score total',
            'numeros': combination,
            'score_promedio': np.mean([self.scores[n] for n in combination]),
            'estrategia': 'high_score'
        }
    
    def _strategy_momentum(self) -> Dict:
        """
        Estrategia 2: Números con mayor momentum (aceleración)
        Números que están "despegando"
        """
        # Combinar score y momentum
        combined = {}
        for num in range(46):
            score = self.scores.get(num, 0)
            mom = self.momentum.get(num, 0)
            # 60% score base, 40% momentum
            combined[num] = 0.6 * score + 0.4 * (mom + 1) / 2  # Normalizar momentum
        
        # Generar combinación con scores ajustados
        combination = self._generate_combination_with_method(combined)
        
        return {
            'nombre': 'Momentum',
            'descripcion': 'Numeros con mayor aceleracion',
            'numeros': combination,
            'score_promedio': np.mean([self.scores[n] for n in combination]),
            'momentum_promedio': np.mean([self.momentum.get(n, 0) for n in combination]),
            'estrategia': 'momentum'
        }
    
    def _strategy_balanced(self) -> Dict:
        """
        Estrategia 3: Balance entre rangos numéricos y paridad
        Asegura distribución equilibrada
        """
        # Ajustar scores para favorecer balance entre rangos
        balanced_scores = {}
        for num in range(46):
            base_score = self.scores.get(num, 0)
            # Dar bonus según rango para balancear
            if 0 <= num <= 15:
                balanced_scores[num] = base_score * 1.1
            elif 16 <= num <= 30:
                balanced_scores[num] = base_score * 1.05
            else:
                balanced_scores[num] = base_score
        
        # Generar con scores balanceados
        combination = self._generate_combination_with_method(balanced_scores)
        
        # Calcular balance
        pares = sum(1 for n in combination if n % 2 == 0)
        
        return {
            'nombre': 'Balanceada',
            'descripcion': 'Balance entre rangos y paridad',
            'numeros': combination,
            'score_promedio': np.mean([self.scores[n] for n in combination]),
            'pares': pares,
            'impares': 6 - pares,
            'estrategia': 'balanced'
        }
    
    def _strategy_cycles(self) -> Dict:
        """
        Estrategia 4: Números según ciclos de aparición
        Prioriza números que "deben" aparecer por su ciclo
        """
        if not self.freq_analyzer or 'ciclos' not in self.freq_analyzer.results:
            # Fallback a high score si no hay datos de ciclos
            return self._strategy_high_score()
        
        ciclos = self.freq_analyzer.results['ciclos']
        latencia = self.freq_analyzer.results.get('latencia', {})
        
        # Score combinado: ciclo corto + latencia alta = debe salir pronto
        ciclo_score = {}
        for num in range(46):
            ciclo = ciclos.get(num, 100)
            lat = latencia.get(num, 0)
            score_base = self.scores.get(num, 0)
            
            # Si latencia >= ciclo, el número está "atrasado"
            if ciclo > 0 and ciclo != float('inf'):
                atraso = lat / ciclo
                ciclo_score[num] = score_base * (1 + min(atraso, 2) * 0.3)
            else:
                ciclo_score[num] = score_base
        
        # Generar con scores ajustados por ciclos
        combination = self._generate_combination_with_method(ciclo_score)
        
        return {
            'nombre': 'Ciclos',
            'descripcion': 'Numeros segun ciclos esperados',
            'numeros': combination,
            'score_promedio': np.mean([self.scores[n] for n in combination]),
            'estrategia': 'cycles'
        }
    
    def _strategy_anti_consensus(self) -> Dict:
        """
        Estrategia 5: Anti-consensus
        Números menos obvios pero con potencial (score medio-alto, no top)
        """
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        
        # Ajustar scores: penalizar top 6, favorecer ranking 7-20
        anti_scores = {}
        for idx, (num, score) in enumerate(sorted_scores):
            if idx < 6:
                # Penalizar top 6
                anti_scores[num] = score * 0.5
            elif idx < 20:
                # Favorecer ranking 7-20
                anti_scores[num] = score * 1.3
            else:
                # Scores normales para el resto
                anti_scores[num] = score * 0.8
        
        # Generar con scores ajustados
        combination = self._generate_combination_with_method(anti_scores)
        
        return {
            'nombre': 'Anti-Consensus',
            'descripcion': 'Numeros menos obvios con potencial',
            'numeros': combination,
            'score_promedio': np.mean([self.scores[n] for n in combination]),
            'estrategia': 'anti_consensus'
        }
    
    def _generate_additional_variations(self, count: int) -> List[Dict]:
        """
        Genera combinaciones adicionales usando variaciones aleatorias
        
        Args:
            count: Cantidad de combinaciones adicionales a generar
        
        Returns:
            Lista de combinaciones variadas
        """
        variations = []
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        
        for i in range(count):
            # Alternar entre diferentes pools de números
            if i % 3 == 0:
                # Pool alto-medio (top 20)
                pool = sorted_scores[:20]
                nombre = f"Variación Alto #{i+1}"
            elif i % 3 == 1:
                # Pool medio (ranking 10-35)
                pool = sorted_scores[10:35]
                nombre = f"Variación Media #{i+1}"
            else:
                # Pool mixto
                pool = sorted_scores[:30]
                nombre = f"Variación Mixta #{i+1}"
            
            # Selección ponderada
            weights = np.array([score for _, score in pool])
            weights = weights / weights.sum()
            
            indices = np.random.choice(
                len(pool),
                size=min(6, len(pool)),
                replace=False,
                p=weights
            )
            
            combination = sorted([pool[idx][0] for idx in indices])
            
            # Rellenar si faltan números
            if len(combination) < 6:
                for num, _ in sorted_scores:
                    if num not in combination:
                        combination.append(num)
                        if len(combination) == 6:
                            break
            
            combination = sorted(combination[:6])
            
            variations.append({
                'nombre': nombre,
                'descripcion': 'Selección aleatoria ponderada',
                'numeros': combination,
                'score_promedio': np.mean([self.scores[n] for n in combination]),
                'estrategia': 'variation'
            })
        
        return variations
    
    def analyze_portfolio_coverage(self, portfolio: List[Dict]) -> Dict:
        """
        Analiza la cobertura del portfolio (cuántos números únicos total)
        
        Args:
            portfolio: Lista de combinaciones generadas
        
        Returns:
            Dict con análisis de cobertura
        """
        all_numbers = set()
        for combo in portfolio:
            all_numbers.update(combo['numeros'])
        
        # Conteo de frecuencia por número en el portfolio
        freq_count = {}
        for combo in portfolio:
            for num in combo['numeros']:
                freq_count[num] = freq_count.get(num, 0) + 1
        
        return {
            'total_combinaciones': len(portfolio),
            'numeros_unicos': len(all_numbers),
            'cobertura': sorted(list(all_numbers)),
            'numeros_mas_frecuentes': sorted(
                freq_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'diversificacion_score': len(all_numbers) / (len(portfolio) * 6)
        }
