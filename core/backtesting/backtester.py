"""
Sistema de backtesting para validar predicciones con datos históricos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..data.loader import DataLoader
from ..analysis.frequency import FrequencyAnalyzer
from ..scoring.scorer import UnifiedScorer
from ..generator.combination import CombinationGenerator
from ..config import BACKTESTING_PARAMS


class Backtester:
    """
    Sistema de backtesting que valida predicciones contra resultados reales
    
    Divide los datos en train/test y evalúa:
    - Cuántos aciertos obtuvo el modelo
    - Métricas de precisión (6/6, 5/6, 4/6, 3/6)
    - ROI simulado
    """
    
    def __init__(self, test_size: int = None):
        """
        Args:
            test_size: Cantidad de sorteos para testing (últimos N)
        """
        self.test_size = test_size or BACKTESTING_PARAMS['test_size']
        self.results = []
        self.summary = {}
    
    def run_backtest(self, 
                    data: pd.DataFrame,
                    weights: Dict = None,
                    generate_n_combinations: int = 1) -> Dict:
        """
        Ejecuta backtesting completo
        
        Args:
            data: DataFrame con todos los datos históricos
            weights: Pesos a usar para el modelo
            generate_n_combinations: Cuántas combinaciones generar por sorteo
        
        Returns:
            Diccionario con resultados del backtesting
        """
        if len(data) < BACKTESTING_PARAMS['min_train_size'] + self.test_size:
            raise ValueError(
                f"Se necesitan al menos {BACKTESTING_PARAMS['min_train_size'] + self.test_size} sorteos"
            )
        
        # Dividir datos
        split_point = len(data) - self.test_size
        train_data = data.iloc[:split_point].copy()
        test_data = data.iloc[split_point:].copy()
        
        print(f"\n{'='*60}")
        print(f"BACKTESTING")
        print(f"{'='*60}")
        print(f"Train: {len(train_data)} sorteos (hasta {train_data['fecha'].max()})")
        print(f"Test:  {len(test_data)} sorteos (desde {test_data['fecha'].min()})")
        print(f"{'='*60}\n")
        
        self.results = []
        
        # Para cada sorteo en test
        for idx, test_row in test_data.iterrows():
            # Entrenar modelo con datos hasta este punto
            available_train = data[data['fecha'] < test_row['fecha']]
            
            if len(available_train) < 50:  # Mínimo de datos
                continue
            
            # Ejecutar predicción
            predictions = self._predict(available_train, weights, generate_n_combinations)
            
            # Comparar con resultado real
            real_numbers = set(test_row['numeros'])
            
            # Evaluar cada predicción
            for pred in predictions:
                pred_set = set(pred)
                aciertos = len(pred_set & real_numbers)
                
                result = {
                    'sorteo_id': test_row['sorteo_id'],
                    'fecha': test_row['fecha'],
                    'prediccion': pred,
                    'real': test_row['numeros'],
                    'aciertos': aciertos
                }
                
                self.results.append(result)
        
        # Calcular resumen estadístico
        self.summary = self._calculate_summary()
        
        return self.summary
    
    def _predict(self, train_data: pd.DataFrame, weights: Dict, n_combinations: int) -> List[List[int]]:
        """
        Genera predicción basándose en datos de entrenamiento
        
        Args:
            train_data: Datos históricos
            weights: Pesos del modelo
            n_combinations: Cuántas combinaciones generar
        
        Returns:
            Lista de combinaciones predichas
        """
        # Analizar frecuencias
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(train_data)
        
        # Calcular scores
        scorer = UnifiedScorer(weights)
        scores = scorer.calculate_scores(freq_analyzer)
        
        # Generar combinaciones
        generator = CombinationGenerator()
        
        if n_combinations == 1:
            # Generar una sola combinación con restricciones
            combination = generator.generate_with_constraints(scores)
            return [combination]
        else:
            # Generar múltiples combinaciones
            combinations = generator.generate_simple(scores, top_n=n_combinations)
            return combinations
    
    def _calculate_summary(self) -> Dict:
        """Calcula estadísticas resumidas del backtesting"""
        if not self.results:
            return {"error": "No hay resultados de backtesting"}
        
        # Contar aciertos por categoría
        aciertos_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for result in self.results:
            aciertos = result['aciertos']
            aciertos_dist[aciertos] += 1
        
        total_predicciones = len(self.results)
        
        # Calcular métricas
        promedio_aciertos = np.mean([r['aciertos'] for r in self.results])
        
        # Tasa de aciertos significativos (3 o más)
        significativos = sum(aciertos_dist[i] for i in range(3, 7))
        tasa_significativos = significativos / total_predicciones if total_predicciones > 0 else 0
        
        # Mejor y peor predicción
        mejor = max(self.results, key=lambda x: x['aciertos'])
        peor = min(self.results, key=lambda x: x['aciertos'])
        
        summary = {
            'total_predicciones': total_predicciones,
            'distribucion_aciertos': aciertos_dist,
            'porcentaje_aciertos': {
                k: (v / total_predicciones * 100) if total_predicciones > 0 else 0 
                for k, v in aciertos_dist.items()
            },
            'promedio_aciertos': promedio_aciertos,
            'tasa_significativos': tasa_significativos,
            'mejor_prediccion': {
                'sorteo_id': mejor['sorteo_id'],
                'fecha': str(mejor['fecha']),
                'aciertos': mejor['aciertos'],
                'prediccion': mejor['prediccion'],
                'real': mejor['real']
            },
            'peor_prediccion': {
                'sorteo_id': peor['sorteo_id'],
                'fecha': str(peor['fecha']),
                'aciertos': peor['aciertos']
            }
        }
        
        return summary
    
    def print_results(self):
        """Imprime resultados del backtesting de forma legible"""
        if not self.summary:
            print("No hay resultados para mostrar")
            return
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS DEL BACKTESTING")
        print(f"{'='*60}\n")
        
        print(f"Total de predicciones: {self.summary['total_predicciones']}")
        print(f"Promedio de aciertos: {self.summary['promedio_aciertos']:.2f}")
        print(f"Tasa de 3+ aciertos: {self.summary['tasa_significativos']*100:.1f}%\n")
        
        print("Distribución de aciertos:")
        print("-" * 40)
        for aciertos in range(7):
            count = self.summary['distribucion_aciertos'][aciertos]
            pct = self.summary['porcentaje_aciertos'][aciertos]
            bar = '█' * int(pct / 2)
            print(f"  {aciertos} aciertos: {count:3d} ({pct:5.1f}%) {bar}")
        
        print("\n" + "-" * 40)
        
        mejor = self.summary['mejor_prediccion']
        print(f"\nMejor predicción: {mejor['aciertos']} aciertos (Sorteo {mejor['sorteo_id']})")
        print(f"  Predicho: {mejor['prediccion']}")
        print(f"  Real:     {mejor['real']}")
        
        print(f"\n{'='*60}\n")
    
    def get_detailed_results(self) -> pd.DataFrame:
        """Retorna resultados detallados como DataFrame"""
        return pd.DataFrame(self.results)
    
    def compare_weights(self, 
                       data: pd.DataFrame,
                       weights_list: List[Dict],
                       weights_names: List[str] = None) -> pd.DataFrame:
        """
        Compara rendimiento de diferentes configuraciones de pesos
        
        Args:
            data: Datos históricos
            weights_list: Lista de configuraciones de pesos
            weights_names: Nombres para cada configuración
        
        Returns:
            DataFrame comparativo
        """
        if weights_names is None:
            weights_names = [f"Config_{i+1}" for i in range(len(weights_list))]
        
        comparison_results = []
        
        for weights, name in zip(weights_list, weights_names):
            print(f"\nEvaluando: {name}...")
            
            # Ejecutar backtesting
            summary = self.run_backtest(data, weights)
            
            comparison_results.append({
                'configuracion': name,
                'promedio_aciertos': summary['promedio_aciertos'],
                'tasa_3_mas': summary['tasa_significativos'] * 100,
                'aciertos_6': summary['porcentaje_aciertos'][6],
                'aciertos_5': summary['porcentaje_aciertos'][5],
                'aciertos_4': summary['porcentaje_aciertos'][4],
                'aciertos_3': summary['porcentaje_aciertos'][3],
            })
        
        df_comparison = pd.DataFrame(comparison_results)
        df_comparison = df_comparison.sort_values('promedio_aciertos', ascending=False)
        
        return df_comparison
