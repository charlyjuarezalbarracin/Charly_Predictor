"""
Cargador de datos históricos del Quini 6
Soporta CSV y JSON
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime


class DataLoader:
    """Carga datos históricos de sorteos del Quini 6"""
    
    def __init__(self):
        self.data = None
        self.raw_data = None
    
    def load_csv(self, filepath: str, date_column: str = 'fecha', 
                 numbers_columns: List[str] = None) -> pd.DataFrame:
        """
        Carga datos desde archivo CSV
        
        Args:
            filepath: Ruta al archivo CSV
            date_column: Nombre de la columna de fecha
            numbers_columns: Lista de nombres de columnas con los números
                           Si es None, asume columnas: num1, num2, num3, num4, num5, num6
        
        Returns:
            DataFrame con los datos cargados
        """
        if numbers_columns is None:
            numbers_columns = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
        
        try:
            # Cargar CSV
            df = pd.read_csv(filepath)
            self.raw_data = df.copy()
            
            # Validar que existan las columnas necesarias
            required_cols = [date_column] + numbers_columns
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Columnas faltantes en el CSV: {missing_cols}")
            
            # Procesar datos
            processed_data = []
            for idx, row in df.iterrows():
                sorteo = {
                    'sorteo_id': int(row.get('sorteo_id', idx + 1)),  # Usar sorteo_id del CSV si existe
                    'fecha': pd.to_datetime(row[date_column]),
                    'numeros': sorted([int(row[col]) for col in numbers_columns])
                }
                processed_data.append(sorteo)
            
            self.data = pd.DataFrame(processed_data)
            # Ordenar por sorteo_id para mantener el orden original del CSV
            # Esto preserva el orden: Tradicional, Segunda, Revancha, Siempre Sale
            self.data = self.data.sort_values('sorteo_id').reset_index(drop=True)
            
            print(f"✓ Cargados {len(self.data)} sorteos desde CSV")
            print(f"  Rango de fechas: {self.data['fecha'].min()} a {self.data['fecha'].max()}")
            
            return self.data
            
        except Exception as e:
            raise Exception(f"Error al cargar CSV: {str(e)}")
    
    def load_json(self, filepath: str) -> pd.DataFrame:
        """
        Carga datos desde archivo JSON
        
        Formato esperado:
        [
            {
                "sorteo_id": 1,
                "fecha": "2024-01-15",
                "numeros": [5, 12, 23, 34, 41, 45]
            },
            ...
        ]
        
        Args:
            filepath: Ruta al archivo JSON
        
        Returns:
            DataFrame con los datos cargados
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.raw_data = data.copy()
            
            # Procesar datos
            processed_data = []
            for item in data:
                sorteo = {
                    'sorteo_id': item.get('sorteo_id', len(processed_data) + 1),
                    'fecha': pd.to_datetime(item['fecha']),
                    'numeros': sorted(item['numeros'])
                }
                processed_data.append(sorteo)
            
            self.data = pd.DataFrame(processed_data)
            self.data = self.data.sort_values('fecha').reset_index(drop=True)
            
            print(f"✓ Cargados {len(self.data)} sorteos desde JSON")
            print(f"  Rango de fechas: {self.data['fecha'].min()} a {self.data['fecha'].max()}")
            
            return self.data
            
        except Exception as e:
            raise Exception(f"Error al cargar JSON: {str(e)}")
    
    def load_from_list(self, sorteos: List[Dict]) -> pd.DataFrame:
        """
        Carga datos desde una lista de diccionarios
        
        Args:
            sorteos: Lista de diccionarios con sorteos
        
        Returns:
            DataFrame con los datos cargados
        """
        processed_data = []
        for idx, sorteo in enumerate(sorteos):
            processed = {
                'sorteo_id': sorteo.get('sorteo_id', idx + 1),
                'fecha': pd.to_datetime(sorteo.get('fecha', datetime.now())),
                'numeros': sorted(sorteo['numeros'])
            }
            processed_data.append(processed)
        
        self.data = pd.DataFrame(processed_data)
        self.data = self.data.sort_values('fecha').reset_index(drop=True)
        
        print(f"✓ Cargados {len(self.data)} sorteos desde lista")
        
        return self.data
    
    def get_data(self) -> pd.DataFrame:
        """Retorna los datos cargados"""
        if self.data is None:
            raise ValueError("No hay datos cargados. Use load_csv() o load_json() primero.")
        return self.data
    
    def get_summary(self) -> Dict:
        """Retorna un resumen de los datos cargados"""
        if self.data is None:
            return {"error": "No hay datos cargados"}
        
        all_numbers = [num for numeros in self.data['numeros'] for num in numeros]
        
        return {
            'total_sorteos': len(self.data),
            'fecha_inicio': str(self.data['fecha'].min()),
            'fecha_fin': str(self.data['fecha'].max()),
            'total_numeros_registrados': len(all_numbers),
            'numero_mas_frecuente': max(set(all_numbers), key=all_numbers.count),
            'numero_menos_frecuente': min(set(all_numbers), key=all_numbers.count),
        }
