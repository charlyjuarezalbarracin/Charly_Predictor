"""
Evaluador de rendimiento y métricas
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter


class PerformanceEvaluator:
    """
    Evalúa el rendimiento de predicciones y calcula métricas avanzadas
    """
    
    def __init__(self):
        self.predictions = []
        self.actuals = []
        self.metrics = {}
    
    def add_prediction(self, predicted: List[int], actual: List[int]):
        """
        Agrega una predicción para evaluación
        
        Args:
            predicted: Números predichos
            actual: Números reales que salieron
        """
        self.predictions.append(sorted(predicted))
        self.actuals.append(sorted(actual))
    
    def calculate_metrics(self) -> Dict:
        """
        Calcula métricas de rendimiento
        
        Returns:
            Diccionario con métricas
        """
        if not self.predictions:
            return {"error": "No hay predicciones para evaluar"}
        
        # Calcular aciertos por predicción
        matches = []
        for pred, actual in zip(self.predictions, self.actuals):
            match_count = len(set(pred) & set(actual))
            matches.append(match_count)
        
        # Métricas básicas
        self.metrics = {
            'total_predictions': len(self.predictions),
            'average_matches': np.mean(matches),
            'std_matches': np.std(matches),
            'min_matches': min(matches),
            'max_matches': max(matches),
            'median_matches': np.median(matches),
        }
        
        # Distribución de aciertos
        match_distribution = Counter(matches)
        self.metrics['match_distribution'] = dict(match_distribution)
        
        # Tasa de aciertos por categoría
        total = len(matches)
        self.metrics['hit_rates'] = {
            '6_of_6': sum(1 for m in matches if m == 6) / total * 100,
            '5_of_6': sum(1 for m in matches if m == 5) / total * 100,
            '4_of_6': sum(1 for m in matches if m == 4) / total * 100,
            '3_of_6': sum(1 for m in matches if m == 3) / total * 100,
            '3_or_more': sum(1 for m in matches if m >= 3) / total * 100,
        }
        
        # Precisión por número
        self.metrics['number_precision'] = self._calculate_number_precision()
        
        # ROI simulado (asumiendo premios ficticios)
        self.metrics['simulated_roi'] = self._calculate_simulated_roi(matches)
        
        return self.metrics
    
    def _calculate_number_precision(self) -> Dict[int, Dict]:
        """
        Calcula precisión individual de cada número
        (cuántas veces fue predicho vs cuántas veces acertó)
        """
        number_stats = {}
        
        for num in range(0, 46):
            predicted_count = sum(1 for pred in self.predictions if num in pred)
            hit_count = sum(1 for pred, actual in zip(self.predictions, self.actuals) 
                          if num in pred and num in actual)
            
            precision = hit_count / predicted_count if predicted_count > 0 else 0
            
            number_stats[num] = {
                'predicted_count': predicted_count,
                'hit_count': hit_count,
                'precision': precision
            }
        
        return number_stats
    
    def _calculate_simulated_roi(self, matches: List[int]) -> Dict:
        """
        Calcula ROI simulado asumiendo premios ficticios
        
        Premios simulados:
        - 6 aciertos: $100,000
        - 5 aciertos: $5,000
        - 4 aciertos: $500
        - 3 aciertos: $50
        """
        prize_table = {
            6: 100000,
            5: 5000,
            4: 500,
            3: 50,
        }
        
        # Costo de apuesta (ficticio)
        cost_per_bet = 100
        
        total_cost = len(matches) * cost_per_bet
        total_winnings = sum(prize_table.get(m, 0) for m in matches)
        
        roi = ((total_winnings - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'total_winnings': total_winnings,
            'net_profit': total_winnings - total_cost,
            'roi_percentage': roi
        }
    
    def get_best_numbers(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        Retorna los números con mejor precisión
        
        Args:
            top_n: Cantidad de números a retornar
        
        Returns:
            Lista de tuplas (numero, precision)
        """
        if 'number_precision' not in self.metrics:
            self.calculate_metrics()
        
        number_precision = self.metrics['number_precision']
        
        sorted_numbers = sorted(
            number_precision.items(),
            key=lambda x: (x[1]['precision'], x[1]['hit_count']),
            reverse=True
        )
        
        return [(num, stats['precision']) for num, stats in sorted_numbers[:top_n]]
    
    def print_report(self):
        """Imprime reporte detallado de rendimiento"""
        if not self.metrics:
            self.calculate_metrics()
        
        print(f"\n{'='*60}")
        print(f"REPORTE DE RENDIMIENTO")
        print(f"{'='*60}\n")
        
        print(f"Total de predicciones evaluadas: {self.metrics['total_predictions']}")
        print(f"Promedio de aciertos: {self.metrics['average_matches']:.2f} ± {self.metrics['std_matches']:.2f}")
        print(f"Rango: {self.metrics['min_matches']} - {self.metrics['max_matches']}")
        print(f"Mediana: {self.metrics['median_matches']}")
        
        print("\n" + "-" * 40)
        print("TASAS DE ACIERTO:")
        print("-" * 40)
        for category, rate in self.metrics['hit_rates'].items():
            print(f"  {category.replace('_', ' ').title()}: {rate:.2f}%")
        
        print("\n" + "-" * 40)
        print("ROI SIMULADO:")
        print("-" * 40)
        roi_data = self.metrics['simulated_roi']
        print(f"  Inversión total: ${roi_data['total_cost']:,.0f}")
        print(f"  Ganancias totales: ${roi_data['total_winnings']:,.0f}")
        print(f"  Ganancia neta: ${roi_data['net_profit']:,.0f}")
        print(f"  ROI: {roi_data['roi_percentage']:.1f}%")
        
        print("\n" + "-" * 40)
        print("TOP 10 NÚMEROS MÁS PRECISOS:")
        print("-" * 40)
        best_numbers = self.get_best_numbers(10)
        for num, precision in best_numbers:
            stats = self.metrics['number_precision'][num]
            print(f"  #{num:2d}: {precision*100:5.1f}% ({stats['hit_count']}/{stats['predicted_count']})")
        
        print(f"\n{'='*60}\n")
    
    def export_metrics(self, filepath: str):
        """
        Exporta métricas a archivo JSON
        
        Args:
            filepath: Ruta donde guardar
        """
        import json
        
        if not self.metrics:
            self.calculate_metrics()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"✓ Métricas exportadas a {filepath}")
