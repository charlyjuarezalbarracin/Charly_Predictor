"""
Sistema unificado de scoring con pesos configurables
"""

import numpy as np
from typing import Dict, List, Tuple
from ..analysis.frequency import FrequencyAnalyzer
from ..analysis.patterns import PatternAnalyzer
from ..analysis.correlations import CorrelationAnalyzer
from ..analysis.regression_equilibrium import RegressionEquilibriumAnalyzer
from ..analysis.cycle_resonance import CycleResonanceAnalyzer
from ..analysis.multi_timeframe import MultiTimeframeAnalyzer
from ..config import DEFAULT_WEIGHTS


class UnifiedScorer:
    """
    Sistema de scoring que combina múltiples análisis con pesos configurables
    
    Score(numero) = 
        w1 × frecuencia_normalizada +
        w2 × tendencia_reciente +
        w3 × ciclo_esperado +
        w4 × latencia_inversa +
        w5 × co_ocurrencia_favorable
    """
    
    def __init__(self, weights: Dict = None, use_regression_equilibrium: bool = False, use_cycle_resonance: bool = False, use_multi_timeframe: bool = False):
        """
        Args:
            weights: Diccionario con pesos para cada componente del score
            use_regression_equilibrium: Si True, aplica análisis de regresión al equilibrio (IDEA #3)
            use_cycle_resonance: Si True, aplica análisis de resonancia de ciclos (IDEA #1)
            use_multi_timeframe: Si True, aplica análisis multi-timeframe (IDEA #2)
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.frequency_analyzer = None
        self.pattern_analyzer = None
        self.correlation_analyzer = None
        self.regression_analyzer = None
        self.cycle_resonance_analyzer = None
        self.multi_timeframe_analyzer = None
        self.use_regression_equilibrium = use_regression_equilibrium
        self.use_cycle_resonance = use_cycle_resonance
        self.use_multi_timeframe = use_multi_timeframe
        self.scores = {}
        self.components = {}  # Guardar componentes individuales
    
    def calculate_scores(self, 
                        frequency_analyzer: FrequencyAnalyzer,
                        pattern_analyzer: PatternAnalyzer = None,
                        correlation_analyzer: CorrelationAnalyzer = None,
                        regression_analyzer: RegressionEquilibriumAnalyzer = None,
                        cycle_resonance_analyzer: CycleResonanceAnalyzer = None,
                        multi_timeframe_analyzer: MultiTimeframeAnalyzer = None) -> Dict[int, float]:
        """
        Calcula scores para todos los números usando análisis combinados
        
        Args:
            frequency_analyzer: Analizador de frecuencias (requerido)
            pattern_analyzer: Analizador de patrones (opcional)
            correlation_analyzer: Analizador de correlaciones (opcional)
            regression_analyzer: Analizador de regresión al equilibrio (opcional, IDEA #3)
            cycle_resonance_analyzer: Analizador de resonancia de ciclos (opcional, IDEA #1)
            multi_timeframe_analyzer: Analizador multi-timeframe (opcional, IDEA #2)
        
        Returns:
            Dict con score para cada número (0-1)
        """
        self.frequency_analyzer = frequency_analyzer
        self.pattern_analyzer = pattern_analyzer
        self.correlation_analyzer = correlation_analyzer
        self.regression_analyzer = regression_analyzer or (
            RegressionEquilibriumAnalyzer() if self.use_regression_equilibrium else None
        )
        self.cycle_resonance_analyzer = cycle_resonance_analyzer or (
            CycleResonanceAnalyzer() if self.use_cycle_resonance else None
        )
        self.multi_timeframe_analyzer = multi_timeframe_analyzer or (
            MultiTimeframeAnalyzer() if self.use_multi_timeframe else None
        )
        
        # Inicializar componentes
        self.components = {
            'frecuencia': {},
            'frecuencia_reciente': {},
            'ciclo': {},
            'latencia': {},
            'tendencia': {}
        }
        
        # Obtener componentes del análisis de frecuencia
        freq_results = frequency_analyzer.results
        
        # 1. Componente de frecuencia relativa
        freq_rel = freq_results.get('frecuencia_relativa', {})
        self.components['frecuencia'] = self._normalize_dict(freq_rel)
        
        # 2. Componente de frecuencia reciente
        freq_rec = freq_results.get('frecuencia_reciente', {})
        self.components['frecuencia_reciente'] = self._normalize_dict(freq_rec)
        
        # 3. Componente de ciclo (invertir: ciclo más corto = mejor)
        ciclos = freq_results.get('ciclos', {})
        ciclos_inv = {k: 1/v if v > 0 and v != float('inf') else 0 for k, v in ciclos.items()}
        self.components['ciclo'] = self._normalize_dict(ciclos_inv)
        
        # 4. Componente de latencia (invertir: menor latencia desde última aparición = mejor)
        latencia = freq_results.get('latencia', {})
        max_lat = max(latencia.values()) if latencia.values() else 1
        latencia_inv = {k: 1 - (v / max_lat) for k, v in latencia.items()}
        self.components['latencia'] = latencia_inv
        
        # 5. Componente de tendencia
        tendencia = freq_results.get('tendencia', {})
        # Limitar valores extremos
        tendencia_filt = {k: min(v, 3.0) for k, v in tendencia.items()}
        self.components['tendencia'] = self._normalize_dict(tendencia_filt)
        
        # Calcular score combinado
        self.scores = {}
        
        for num in range(0, 46):  # 0-45
            score = (
                self.weights.get('peso_frecuencia', 0) * self.components['frecuencia'].get(num, 0) +
                self.weights.get('peso_frecuencia_reciente', 0) * self.components['frecuencia_reciente'].get(num, 0) +
                self.weights.get('peso_ciclo', 0) * self.components['ciclo'].get(num, 0) +
                self.weights.get('peso_latencia', 0) * self.components['latencia'].get(num, 0) +
                self.weights.get('peso_tendencia', 0) * self.components['tendencia'].get(num, 0)
            )
            
            self.scores[num] = score
        
        # Normalizar scores finales a rango 0-1
        self.scores = self._normalize_dict(self.scores)
        
        # IDEA #3: Aplicar factores de regresión al equilibrio
        if self.regression_analyzer and self.use_regression_equilibrium:
            # Analizar desequilibrios
            regression_data = frequency_analyzer.data
            self.regression_analyzer.analyze(regression_data)
            
            # Aplicar factores de corrección
            factores = self.regression_analyzer.results.get('factores_correccion', {})
            
            for num in range(0, 46):
                factor = factores.get(num, 1.0)
                self.scores[num] = self.scores[num] * factor
            
            # Re-normalizar después de aplicar factores
            self.scores = self._normalize_dict(self.scores)
        
        # IDEA #1: Aplicar factores de resonancia de ciclos
        if self.cycle_resonance_analyzer and self.use_cycle_resonance:
            # Analizar resonancia
            resonance_data = frequency_analyzer.data
            self.cycle_resonance_analyzer.analyze(resonance_data)
            
            # Aplicar factores de resonancia
            factores_resonancia = self.cycle_resonance_analyzer.results.get('scores_resonancia', {})
            
            for num in range(0, 46):
                factor = factores_resonancia.get(num, 1.0)
                self.scores[num] = self.scores[num] * factor
            
            # Re-normalizar después de aplicar factores
            self.scores = self._normalize_dict(self.scores)
        
        # IDEA #2: Aplicar factores de convergencia multi-timeframe
        if self.multi_timeframe_analyzer and self.use_multi_timeframe:
            # Analizar convergencia
            mtf_data = frequency_analyzer.data
            self.multi_timeframe_analyzer.analyze(mtf_data)
            
            # Aplicar factores de boost
            factores_mtf = self.multi_timeframe_analyzer.results.get('factores_boost', {})
            
            for num in range(0, 46):
                factor = factores_mtf.get(num, 1.0)
                self.scores[num] = self.scores[num] * factor
            
            # Re-normalizar después de aplicar factores
            self.scores = self._normalize_dict(self.scores)
        
        return self.scores
    
    def _normalize_dict(self, data: Dict) -> Dict:
        """Normaliza valores de un diccionario al rango 0-1"""
        if not data:
            return {}
        
        values = list(data.values())
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return {k: 0.5 for k in data.keys()}
        
        return {
            k: (v - min_val) / (max_val - min_val)
            for k, v in data.items()
        }
    
    def get_top_numbers(self, n: int = 10) -> List[Tuple[int, float]]:
        """
        Retorna los N números con mayor score
        
        Args:
            n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, score) ordenadas por score descendente
        """
        if not self.scores:
            raise ValueError("Debe calcular scores primero usando calculate_scores()")
        
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:n]
    
    def update_weights(self, new_weights: Dict):
        """
        Actualiza los pesos del sistema
        
        Args:
            new_weights: Diccionario con nuevos pesos
        """
        self.weights.update(new_weights)
        
        # Recalcular scores si ya existen componentes
        if self.components and self.frequency_analyzer:
            self.calculate_scores(
                self.frequency_analyzer,
                self.pattern_analyzer,
                self.correlation_analyzer
            )
    
    def get_score_breakdown(self, numero: int) -> Dict:
        """
        Retorna el desglose del score para un número específico
        
        Args:
            numero: Número a analizar
        
        Returns:
            Dict con componentes individuales del score
        """
        if not self.components:
            return {"error": "No hay scores calculados"}
        
        breakdown = {
            'numero': numero,
            'score_final': self.scores.get(numero, 0),
            'componentes': {}
        }
        
        for comp_name, comp_values in self.components.items():
            weight_name = f'peso_{comp_name}'
            if weight_name in self.weights or comp_name in ['frecuencia_reciente']:
                # Mapear nombres de componentes a nombres de pesos
                if comp_name == 'frecuencia_reciente':
                    weight_name = 'peso_frecuencia_reciente'
                
                weight = self.weights.get(weight_name, 0)
                value = comp_values.get(numero, 0)
                contribution = weight * value
                
                breakdown['componentes'][comp_name] = {
                    'valor_normalizado': value,
                    'peso': weight,
                    'contribucion': contribution
                }
        
        return breakdown
    
    def get_weights_summary(self) -> Dict:
        """Retorna un resumen de los pesos actuales"""
        total_weight = sum(self.weights.values())
        
        return {
            'pesos_actuales': self.weights.copy(),
            'suma_total': total_weight,
            'advertencia': 'La suma de pesos debe ser 1.0' if abs(total_weight - 1.0) > 0.01 else None
        }
