"""
Preprocesador de datos - Calcula features adicionales
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class DataPreprocessor:
    """Preprocesa datos y calcula features adicionales"""
    
    def __init__(self):
        self.data = None
        self.features = None
    
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Procesa los datos y calcula features adicionales
        
        Args:
            data: DataFrame con sorteos
        
        Returns:
            DataFrame con features calculados
        """
        self.data = data.copy()
        
        # Calcular features para cada sorteo
        features_list = []
        
        for idx, row in self.data.iterrows():
            features = self._calculate_features(row['numeros'])
            features['sorteo_id'] = row['sorteo_id']
            features['fecha'] = row['fecha']
            features_list.append(features)
        
        self.features = pd.DataFrame(features_list)
        
        # Unir con datos originales
        result = self.data.merge(self.features, on=['sorteo_id', 'fecha'])
        
        print(f"✓ Features calculados para {len(result)} sorteos")
        
        return result
    
    def _calculate_features(self, numeros: List[int]) -> Dict:
        """Calcula features matemáticos de una combinación"""
        numeros = sorted(numeros)
        
        features = {}
        
        # Features básicos
        features['suma_total'] = sum(numeros)
        features['promedio'] = np.mean(numeros)
        features['mediana'] = np.median(numeros)
        features['desviacion'] = np.std(numeros)
        features['rango'] = max(numeros) - min(numeros)
        
        # Paridad
        features['pares'] = sum(1 for n in numeros if n % 2 == 0)
        features['impares'] = sum(1 for n in numeros if n % 2 != 0)
        
        # Primalidad
        features['primos'] = sum(1 for n in numeros if self._es_primo(n))
        
        # Consecutivos
        features['consecutivos'] = self._count_consecutivos(numeros)
        
        # Distribución por rangos (bajo: 0-15, medio: 16-30, alto: 31-45)
        features['bajos'] = sum(1 for n in numeros if 0 <= n <= 15)
        features['medios'] = sum(1 for n in numeros if 16 <= n <= 30)
        features['altos'] = sum(1 for n in numeros if 31 <= n <= 45)
        
        # Distancias entre números
        distancias = [numeros[i+1] - numeros[i] for i in range(len(numeros)-1)]
        features['distancia_min'] = min(distancias) if distancias else 0
        features['distancia_max'] = max(distancias) if distancias else 0
        features['distancia_promedio'] = np.mean(distancias) if distancias else 0
        
        # Múltiplos de 5
        features['multiplos_5'] = sum(1 for n in numeros if n % 5 == 0 and n != 0)
        
        # Decenas
        decenas = [n // 10 for n in numeros]
        features['decenas_diferentes'] = len(set(decenas))
        
        return features
    
    @staticmethod
    def _es_primo(n: int) -> bool:
        """Verifica si un número es primo"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    @staticmethod
    def _count_consecutivos(numeros: List[int]) -> int:
        """Cuenta números consecutivos en la lista"""
        if len(numeros) < 2:
            return 0
        
        count = 0
        for i in range(len(numeros) - 1):
            if numeros[i+1] - numeros[i] == 1:
                count += 1
        
        return count
    
    def get_feature_summary(self) -> Dict:
        """Retorna un resumen de los features calculados"""
        if self.features is None:
            return {"error": "No hay features calculados"}
        
        # Excluir columnas no numéricas
        numeric_features = self.features.select_dtypes(include=[np.number])
        
        summary = {}
        for col in numeric_features.columns:
            if col != 'sorteo_id':
                summary[col] = {
                    'min': float(numeric_features[col].min()),
                    'max': float(numeric_features[col].max()),
                    'mean': float(numeric_features[col].mean()),
                    'std': float(numeric_features[col].std())
                }
        
        return summary
