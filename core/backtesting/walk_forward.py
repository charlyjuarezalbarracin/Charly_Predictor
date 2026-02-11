"""
Walk-Forward Backtesting - Validación temporal con ventana móvil
Simula condiciones reales de predicción con ventana de entrenamiento deslizante
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..data.loader import DataLoader
from ..analysis.frequency import FrequencyAnalyzer
from ..scoring.scorer import UnifiedScorer
from ..generator.combination import CombinationGenerator


class WalkForwardBacktester:
    """
    Sistema de backtesting walk-forward que valida la estabilidad
    de los pesos optimizados a través del tiempo.
    
    A diferencia del backtesting tradicional (un solo split train/test),
    el walk-forward usa una ventana móvil que simula cómo se usaría el
    sistema en producción: entrenar con N sorteos pasados, predecir el
    siguiente, deslizar la ventana.
    
    Ventajas:
    - Detecta sobreajuste temporal
    - Valida si pesos se mantienen efectivos en el tiempo
    - Simula condiciones reales de uso
    """
    
    def __init__(self, 
                 train_window: int = 200,
                 test_window: int = 10,
                 step_size: int = 10):
        """
        Args:
            train_window: Tamaño de ventana de entrenamiento
            test_window: Tamaño de ventana de test
            step_size: Cuánto deslizar la ventana en cada iteración
        """
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
        self.results = []
        self.period_results = []
    
    def run_walk_forward(self, 
                        data: pd.DataFrame,
                        weights: Dict) -> Dict:
        """
        Ejecuta backtesting walk-forward completo
        
        Args:
            data: DataFrame con todos los sorteos históricos
            weights: Pesos a validar
        
        Returns:
            Dict con resultados por periodo y agregados
        """
        total_sorteos = len(data)
        
        if total_sorteos < self.train_window + self.test_window:
            raise ValueError(
                f"Se necesitan al menos {self.train_window + self.test_window} sorteos. "
                f"Disponibles: {total_sorteos}"
            )
        
        print(f"\n{'='*70}")
        print(f"WALK-FORWARD BACKTESTING")
        print(f"{'='*70}")
        print(f"Total sorteos: {total_sorteos}")
        print(f"Ventana entrenamiento: {self.train_window}")
        print(f"Ventana test: {self.test_window}")
        print(f"Step size: {self.step_size}")
        print(f"{'='*70}\n")
        
        self.results = []
        self.period_results = []
        
        # Iterar con ventana deslizante
        start_idx = 0
        period_num = 1
        
        while start_idx + self.train_window + self.test_window <= total_sorteos:
            # Definir ventanas
            train_end = start_idx + self.train_window
            test_end = train_end + self.test_window
            
            train_data = data.iloc[start_idx:train_end]
            test_data = data.iloc[train_end:test_end]
            
            print(f"Periodo {period_num}:")
            print(f"  Train: sorteos {start_idx} a {train_end-1} ({train_data['fecha'].min()} - {train_data['fecha'].max()})")
            print(f"  Test:  sorteos {train_end} a {test_end-1} ({test_data['fecha'].min()} - {test_data['fecha'].max()})")
            
            # Evaluar periodo
            period_result = self._evaluate_period(
                train_data, 
                test_data, 
                weights,
                period_num
            )
            
            self.period_results.append(period_result)
            
            print(f"  Aciertos: {period_result['total_aciertos']}/{period_result['total_numeros_test']} "
                  f"({period_result['accuracy']:.2%})")
            print()
            
            # Avanzar ventana
            start_idx += self.step_size
            period_num += 1
        
        # Calcular estadísticas agregadas
        summary = self._calculate_summary()
        
        print(f"\n{'='*70}")
        print(f"RESULTADOS AGREGADOS")
        print(f"{'='*70}")
        print(f"Periodos evaluados: {summary['total_periodos']}")
        print(f"Total aciertos: {summary['total_aciertos']}/{summary['total_numeros']}")
        print(f"Accuracy promedio: {summary['accuracy_promedio']:.2%}")
        print(f"Accuracy desv. std: {summary['accuracy_std']:.2%}")
        print(f"Mejor periodo: {summary['mejor_periodo']['numero']} ({summary['mejor_periodo']['accuracy']:.2%})")
        print(f"Peor periodo: {summary['peor_periodo']['numero']} ({summary['peor_periodo']['accuracy']:.2%})")
        print(f"{'='*70}\n")
        
        return {
            'period_results': self.period_results,
            'summary': summary,
            'weights_used': weights
        }
    
    def _evaluate_period(self,
                        train_data: pd.DataFrame,
                        test_data: pd.DataFrame,
                        weights: Dict,
                        period_num: int) -> Dict:
        """
        Evalúa un periodo específico de walk-forward
        
        Args:
            train_data: Datos de entrenamiento
            test_data: Datos de test
            weights: Pesos a usar
            period_num: Número del periodo
        
        Returns:
            Dict con resultados del periodo
        """
        # Entrenar modelo
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(train_data)
        
        scorer = UnifiedScorer(weights)
        scores = scorer.calculate_scores(freq_analyzer)
        
        # Generar predicciones para cada sorteo de test
        aciertos_periodo = 0
        total_numeros_test = len(test_data) * 6
        
        sorteo_results = []
        
        for _, test_row in test_data.iterrows():
            # Generar combinación
            generator = CombinationGenerator()
            combination = generator.generate_with_constraints(scores)
            
            # Comparar con resultado real
            real_numbers = set(test_row['numeros'])
            predicted_numbers = set(combination)
            
            aciertos = len(real_numbers & predicted_numbers)
            aciertos_periodo += aciertos
            
            sorteo_results.append({
                'fecha': test_row['fecha'],
                'real': list(real_numbers),
                'predicho': list(predicted_numbers),
                'aciertos': aciertos
            })
        
        return {
            'periodo': period_num,
            'train_start': train_data['fecha'].min(),
            'train_end': train_data['fecha'].max(),
            'test_start': test_data['fecha'].min(),
            'test_end': test_data['fecha'].max(),
            'total_aciertos': aciertos_periodo,
            'total_numeros_test': total_numeros_test,
            'accuracy': aciertos_periodo / total_numeros_test,
            'sorteos_test': len(test_data),
            'aciertos_por_sorteo': aciertos_periodo / len(test_data),
            'sorteo_results': sorteo_results
        }
    
    def _calculate_summary(self) -> Dict:
        """
        Calcula estadísticas agregadas de todos los periodos
        
        Returns:
            Dict con resumen estadístico
        """
        if not self.period_results:
            return {}
        
        accuracies = [p['accuracy'] for p in self.period_results]
        aciertos_por_sorteo = [p['aciertos_por_sorteo'] for p in self.period_results]
        
        total_aciertos = sum(p['total_aciertos'] for p in self.period_results)
        total_numeros = sum(p['total_numeros_test'] for p in self.period_results)
        
        mejor_idx = np.argmax(accuracies)
        peor_idx = np.argmin(accuracies)
        
        return {
            'total_periodos': len(self.period_results),
            'total_aciertos': total_aciertos,
            'total_numeros': total_numeros,
            'accuracy_promedio': np.mean(accuracies),
            'accuracy_std': np.std(accuracies),
            'accuracy_min': np.min(accuracies),
            'accuracy_max': np.max(accuracies),
            'aciertos_por_sorteo_promedio': np.mean(aciertos_por_sorteo),
            'aciertos_por_sorteo_std': np.std(aciertos_por_sorteo),
            'mejor_periodo': {
                'numero': self.period_results[mejor_idx]['periodo'],
                'accuracy': self.period_results[mejor_idx]['accuracy'],
                'test_start': self.period_results[mejor_idx]['test_start'],
                'test_end': self.period_results[mejor_idx]['test_end']
            },
            'peor_periodo': {
                'numero': self.period_results[peor_idx]['periodo'],
                'accuracy': self.period_results[peor_idx]['accuracy'],
                'test_start': self.period_results[peor_idx]['test_start'],
                'test_end': self.period_results[peor_idx]['test_end']
            }
        }
    
    def get_stability_score(self) -> float:
        """
        Calcula un score de estabilidad (0-1)
        
        Score alto = pesos funcionan consistentemente en el tiempo
        Score bajo = performance muy variable
        
        Returns:
            Float entre 0 y 1
        """
        if not self.period_results:
            return 0.0
        
        accuracies = [p['accuracy'] for p in self.period_results]
        
        # Estabilidad = inversa de la variabilidad
        # A menor std, más estable
        std = np.std(accuracies)
        mean = np.mean(accuracies)
        
        # Coeficiente de variación normalizado
        if mean > 0:
            cv = std / mean
            # Convertir a score 0-1 (menor CV = mejor)
            stability = max(0, 1 - cv)
        else:
            stability = 0.0
        
        return stability
    
    def plot_results(self) -> Dict:
        """
        Prepara datos para graficar la evolución temporal
        
        Returns:
            Dict con datos para plotting
        """
        if not self.period_results:
            return {}
        
        periodos = [p['periodo'] for p in self.period_results]
        accuracies = [p['accuracy'] for p in self.period_results]
        aciertos_por_sorteo = [p['aciertos_por_sorteo'] for p in self.period_results]
        fechas_test_start = [p['test_start'] for p in self.period_results]
        
        return {
            'periodos': periodos,
            'accuracies': accuracies,
            'aciertos_por_sorteo': aciertos_por_sorteo,
            'fechas_test': fechas_test_start,
            'accuracy_promedio': np.mean(accuracies),
            'stability_score': self.get_stability_score()
        }
