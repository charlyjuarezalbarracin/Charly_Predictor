"""
Validador de datos históricos
"""

import pandas as pd
from typing import List, Dict, Tuple
from ..config import QUINI6_CONFIG


class DataValidator:
    """Valida la integridad de los datos históricos"""
    
    def __init__(self, config: Dict = None):
        self.config = config or QUINI6_CONFIG
        self.errors = []
        self.warnings = []
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
        """
        Valida un DataFrame con datos históricos
        
        Args:
            data: DataFrame con columnas 'sorteo_id', 'fecha', 'numeros'
        
        Returns:
            Tupla (es_valido, lista_errores, lista_warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validar estructura
        self._validate_structure(data)
        
        # Validar cada sorteo
        for idx, row in data.iterrows():
            self._validate_sorteo(idx, row)
        
        # Validar duplicados
        self._validate_duplicates(data)
        
        # Validar consistencia temporal
        self._validate_temporal_consistency(data)
        
        is_valid = len(self.errors) == 0
        
        return is_valid, self.errors, self.warnings
    
    def _validate_structure(self, data: pd.DataFrame):
        """Valida que el DataFrame tenga la estructura correcta"""
        required_columns = ['sorteo_id', 'fecha', 'numeros']
        
        for col in required_columns:
            if col not in data.columns:
                self.errors.append(f"Columna requerida faltante: {col}")
    
    def _validate_sorteo(self, idx: int, row: pd.Series):
        """Valida un sorteo individual"""
        numeros = row['numeros']
        
        # Validar que sea una lista
        if not isinstance(numeros, list):
            self.errors.append(f"Sorteo {idx}: 'numeros' debe ser una lista")
            return
        
        # Validar cantidad de números
        expected_count = self.config['numbers_per_draw']
        if len(numeros) != expected_count:
            self.errors.append(
                f"Sorteo {idx}: Debe tener {expected_count} números, tiene {len(numeros)}"
            )
        
        # Validar unicidad de números
        if len(numeros) != len(set(numeros)):
            duplicados = [n for n in numeros if numeros.count(n) > 1]
            self.errors.append(f"Sorteo {idx}: Números duplicados: {duplicados}")
        
        # Validar rango de números
        min_num = self.config['min_number']
        max_num = self.config['max_number']
        
        for num in numeros:
            if not isinstance(num, (int, float)):
                self.errors.append(f"Sorteo {idx}: El número {num} no es numérico")
            elif num < min_num or num > max_num:
                self.errors.append(
                    f"Sorteo {idx}: Número {num} fuera de rango [{min_num}, {max_num}]"
                )
        
        # Validar que estén ordenados
        if numeros != sorted(numeros):
            self.warnings.append(f"Sorteo {idx}: Números no ordenados (se ordenarán automáticamente)")
    
    def _validate_duplicates(self, data: pd.DataFrame):
        """Detecta sorteos duplicados"""
        # Convertir listas a tuplas para poder comparar
        numeros_tuples = data['numeros'].apply(tuple)
        
        duplicates = numeros_tuples[numeros_tuples.duplicated(keep=False)]
        
        if len(duplicates) > 0:
            self.warnings.append(
                f"Se encontraron {len(duplicates)} sorteos con combinaciones duplicadas"
            )
    
    def _validate_temporal_consistency(self, data: pd.DataFrame):
        """Valida la consistencia temporal de los datos"""
        if 'fecha' not in data.columns:
            return
        
        # Verificar que las fechas estén ordenadas
        fechas = pd.to_datetime(data['fecha'])
        if not fechas.is_monotonic_increasing:
            self.warnings.append("Las fechas no están en orden cronológico")
        
        # Detectar gaps grandes en fechas
        if len(fechas) > 1:
            diff_days = fechas.diff().dt.days
            max_gap = diff_days.max()
            
            if max_gap > 30:  # Más de 30 días entre sorteos
                self.warnings.append(
                    f"Gap temporal grande detectado: {max_gap} días entre sorteos"
                )
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y corrige los datos automáticamente cuando es posible
        
        Args:
            data: DataFrame original
        
        Returns:
            DataFrame limpio
        """
        cleaned = data.copy()
        
        # Ordenar números en cada sorteo
        cleaned['numeros'] = cleaned['numeros'].apply(sorted)
        
        # Ordenar por fecha
        cleaned = cleaned.sort_values('fecha').reset_index(drop=True)
        
        # Eliminar duplicados exactos (si existen)
        numeros_tuples = cleaned['numeros'].apply(tuple)
        cleaned = cleaned[~numeros_tuples.duplicated(keep='first')].reset_index(drop=True)
        
        print(f"✓ Datos limpiados: {len(data)} -> {len(cleaned)} sorteos")
        
        return cleaned
