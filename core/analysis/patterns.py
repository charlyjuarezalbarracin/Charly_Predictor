"""
Analizador de patrones temporales
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter


class PatternAnalyzer:
    """
    Analiza patrones temporales en los sorteos
    - Tendencias por períodos
    - Estacionalidad
    - Rachas y sequías
    """
    
    def __init__(self):
        self.data = None
        self.results = {}
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Ejecuta análisis de patrones temporales
        
        Args:
            data: DataFrame con sorteos (debe incluir columna 'fecha')
        
        Returns:
            Diccionario con análisis de patrones
        """
        self.data = data
        self.results = {}
        
        # Verificar que haya columna de fecha
        if 'fecha' not in data.columns:
            return {"error": "Se requiere columna 'fecha' para análisis temporal"}
        
        self.results['rachas'] = self._detectar_rachas()
        self.results['patron_mensual'] = self._analizar_patron_mensual()
        
        return self.results
    
    def _detectar_rachas(self) -> Dict[int, Dict]:
        """
        Detecta rachas (apariciones consecutivas) y sequías de cada número
        """
        rachas_info = {}
        
        for num in range(0, 46):  # 0-45
            apariciones = []
            
            # Marcar en qué sorteos apareció (1) o no (0)
            for idx, row in self.data.iterrows():
                apariciones.append(1 if num in row['numeros'] else 0)
            
            # Encontrar rachas de apariciones
            rachas_positivas = []
            racha_actual = 0
            
            for val in apariciones:
                if val == 1:
                    racha_actual += 1
                else:
                    if racha_actual > 0:
                        rachas_positivas.append(racha_actual)
                    racha_actual = 0
            
            if racha_actual > 0:
                rachas_positivas.append(racha_actual)
            
            # Encontrar sequías (ausencias)
            sequias = []
            sequia_actual = 0
            
            for val in apariciones:
                if val == 0:
                    sequia_actual += 1
                else:
                    if sequia_actual > 0:
                        sequias.append(sequia_actual)
                    sequia_actual = 0
            
            if sequia_actual > 0:
                sequias.append(sequia_actual)
            
            rachas_info[num] = {
                'racha_maxima': max(rachas_positivas) if rachas_positivas else 0,
                'sequia_maxima': max(sequias) if sequias else 0,
                'sequia_actual': sequia_actual,
                'total_rachas': len(rachas_positivas)
            }
        
        return rachas_info
    
    def _analizar_patron_mensual(self) -> Dict:
        """Analiza si hay patrones según el mes del año"""
        self.data['mes'] = pd.to_datetime(self.data['fecha']).dt.month
        
        patron_mensual = {}
        
        for mes in range(1, 13):
            sorteos_mes = self.data[self.data['mes'] == mes]
            
            if len(sorteos_mes) == 0:
                continue
            
            all_numbers = []
            for numeros in sorteos_mes['numeros']:
                all_numbers.extend(numeros)
            
            counter = Counter(all_numbers)
            top_5 = counter.most_common(5)
            
            patron_mensual[mes] = {
                'sorteos_en_mes': len(sorteos_mes),
                'top_5_numeros': top_5
            }
        
        return patron_mensual
    
    def get_summary(self) -> Dict:
        """Retorna un resumen del análisis de patrones"""
        if not self.results:
            return {"error": "No se ha ejecutado el análisis"}
        
        rachas = self.results.get('rachas', {})
        
        # Encontrar el número con mayor racha
        num_mayor_racha = max(rachas.items(), key=lambda x: x[1]['racha_maxima'])
        num_mayor_sequia = max(rachas.items(), key=lambda x: x[1]['sequia_maxima'])
        
        return {
            'numero_con_mayor_racha': num_mayor_racha,
            'numero_con_mayor_sequia': num_mayor_sequia,
            'patrones_mensuales_detectados': len(self.results.get('patron_mensual', {}))
        }
