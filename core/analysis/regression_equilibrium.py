"""
Analizador de Regresión al Equilibrio

Implementa la IDEA #3: Análisis de desequilibrios en el sistema que tienden
a autocorregirse naturalmente.

Los sistemas caóticos como loterías tienen tendencia a regresar al equilibrio
cuando se producen desviaciones extremas en:
- Proporción pares/impares
- Suma total de combinaciones
- Distribución por rangos numéricos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..config import QUINI6_CONFIG


class RegressionEquilibriumAnalyzer:
    """
    Analiza desviaciones del equilibrio y calcula factores de corrección
    
    Cuando el sistema muestra desequilibrios pronunciados, tiende a
    autocorregirse en los siguientes sorteos.
    
    PRINCIPIO:
    Si en los últimos N sorteos hubo 70% pares, es probable que el próximo
    sorteo tenga más impares para regresar al equilibrio histórico del 50%.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or QUINI6_CONFIG
        self.data = None
        self.results = {}
        
        # Parámetros de análisis
        self.ventana_analisis = 10  # Últimos N sorteos para detectar desequilibrios
        self.umbral_desbalance = 0.15  # 15% de desviación para activar corrección
        
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Ejecuta análisis completo de regresión al equilibrio
        
        Args:
            data: DataFrame con sorteos históricos
        
        Returns:
            Diccionario con análisis de desequilibrios
        """
        self.data = data
        self.results = {}
        
        # Análisis de equilibrios
        self.results['equilibrio_pares_impares'] = self._analizar_equilibrio_paridad()
        self.results['equilibrio_suma'] = self._analizar_equilibrio_suma()
        self.results['equilibrio_rangos'] = self._analizar_equilibrio_rangos()
        self.results['factores_correccion'] = self._calcular_factores_correccion()
        
        return self.results
    
    def _analizar_equilibrio_paridad(self) -> Dict:
        """
        Analiza el equilibrio pares/impares en sorteos recientes vs histórico
        
        Returns:
            Dict con análisis de paridad
        """
        # Histórico completo
        total_numeros_historico = 0
        pares_historico = 0
        
        for numeros in self.data['numeros']:
            for num in numeros:
                total_numeros_historico += 1
                if num % 2 == 0:
                    pares_historico += 1
        
        pct_pares_historico = pares_historico / total_numeros_historico if total_numeros_historico > 0 else 0.5
        
        # Últimos N sorteos
        ventana_data = self.data.tail(self.ventana_analisis)
        total_numeros_reciente = 0
        pares_reciente = 0
        
        for numeros in ventana_data['numeros']:
            for num in numeros:
                total_numeros_reciente += 1
                if num % 2 == 0:
                    pares_reciente += 1
        
        pct_pares_reciente = pares_reciente / total_numeros_reciente if total_numeros_reciente > 0 else 0.5
        
        # Calcular desbalance
        desbalance = pct_pares_reciente - pct_pares_historico
        
        # Determinar tendencia de corrección
        tendencia_correccion = None
        if abs(desbalance) >= self.umbral_desbalance:
            if desbalance > 0:
                tendencia_correccion = 'favorecer_impares'
            else:
                tendencia_correccion = 'favorecer_pares'
        
        return {
            'pct_pares_historico': pct_pares_historico,
            'pct_pares_reciente': pct_pares_reciente,
            'pct_impares_historico': 1 - pct_pares_historico,
            'pct_impares_reciente': 1 - pct_pares_reciente,
            'desbalance': desbalance,
            'desbalance_significativo': abs(desbalance) >= self.umbral_desbalance,
            'tendencia_correccion': tendencia_correccion
        }
    
    def _analizar_equilibrio_suma(self) -> Dict:
        """
        Analiza si las sumas recientes se desvían de la media histórica
        
        Returns:
            Dict con análisis de sumas
        """
        # Calcular sumas de todos los sorteos
        sumas_historicas = [sum(nums) for nums in self.data['numeros']]
        media_historica = np.mean(sumas_historicas)
        std_historica = np.std(sumas_historicas)
        
        # Sumas recientes
        ventana_data = self.data.tail(self.ventana_analisis)
        sumas_recientes = [sum(nums) for nums in ventana_data['numeros']]
        media_reciente = np.mean(sumas_recientes)
        
        # Z-score de la desviación
        z_score = (media_reciente - media_historica) / std_historica if std_historica > 0 else 0
        
        # Determinar tendencia de corrección
        tendencia_correccion = None
        suma_objetivo = None
        
        if abs(z_score) >= 1.5:  # Desviación significativa (>1.5 sigma)
            if z_score > 0:
                # Sumas muy altas, tender a bajar
                tendencia_correccion = 'favorecer_numeros_bajos'
                suma_objetivo = media_historica - (std_historica * 0.5)
            else:
                # Sumas muy bajas, tender a subir
                tendencia_correccion = 'favorecer_numeros_altos'
                suma_objetivo = media_historica + (std_historica * 0.5)
        
        return {
            'media_historica': media_historica,
            'std_historica': std_historica,
            'media_reciente': media_reciente,
            'sumas_recientes': sumas_recientes,
            'z_score': z_score,
            'desviacion_significativa': abs(z_score) >= 1.5,
            'tendencia_correccion': tendencia_correccion,
            'suma_objetivo': suma_objetivo
        }
    
    def _analizar_equilibrio_rangos(self) -> Dict:
        """
        Analiza distribución por rangos (bajo/medio/alto) reciente vs histórico
        
        Returns:
            Dict con análisis de rangos
        """
        # Definir rangos
        rango_bajo = (0, 15)
        rango_medio = (16, 30)
        rango_alto = (31, 45)
        
        # Histórico
        total_hist = 0
        bajos_hist = 0
        medios_hist = 0
        altos_hist = 0
        
        for numeros in self.data['numeros']:
            for num in numeros:
                total_hist += 1
                if rango_bajo[0] <= num <= rango_bajo[1]:
                    bajos_hist += 1
                elif rango_medio[0] <= num <= rango_medio[1]:
                    medios_hist += 1
                else:
                    altos_hist += 1
        
        pct_bajos_hist = bajos_hist / total_hist if total_hist > 0 else 0.33
        pct_medios_hist = medios_hist / total_hist if total_hist > 0 else 0.33
        pct_altos_hist = altos_hist / total_hist if total_hist > 0 else 0.33
        
        # Reciente
        ventana_data = self.data.tail(self.ventana_analisis)
        total_rec = 0
        bajos_rec = 0
        medios_rec = 0
        altos_rec = 0
        
        for numeros in ventana_data['numeros']:
            for num in numeros:
                total_rec += 1
                if rango_bajo[0] <= num <= rango_bajo[1]:
                    bajos_rec += 1
                elif rango_medio[0] <= num <= rango_medio[1]:
                    medios_rec += 1
                else:
                    altos_rec += 1
        
        pct_bajos_rec = bajos_rec / total_rec if total_rec > 0 else 0.33
        pct_medios_rec = medios_rec / total_rec if total_rec > 0 else 0.33
        pct_altos_rec = altos_rec / total_rec if total_rec > 0 else 0.33
        
        # Calcular desbalances
        desbalance_bajos = pct_bajos_rec - pct_bajos_hist
        desbalance_medios = pct_medios_rec - pct_medios_hist
        desbalance_altos = pct_altos_rec - pct_altos_hist
        
        # Determinar correcciones
        correcciones = {}
        if abs(desbalance_bajos) >= self.umbral_desbalance:
            correcciones['rango_bajo'] = 'aumentar' if desbalance_bajos < 0 else 'disminuir'
        if abs(desbalance_medios) >= self.umbral_desbalance:
            correcciones['rango_medio'] = 'aumentar' if desbalance_medios < 0 else 'disminuir'
        if abs(desbalance_altos) >= self.umbral_desbalance:
            correcciones['rango_alto'] = 'aumentar' if desbalance_altos < 0 else 'disminuir'
        
        return {
            'historico': {
                'bajo': pct_bajos_hist,
                'medio': pct_medios_hist,
                'alto': pct_altos_hist
            },
            'reciente': {
                'bajo': pct_bajos_rec,
                'medio': pct_medios_rec,
                'alto': pct_altos_rec
            },
            'desbalances': {
                'bajo': desbalance_bajos,
                'medio': desbalance_medios,
                'alto': desbalance_altos
            },
            'correcciones': correcciones
        }
    
    def _calcular_factores_correccion(self) -> Dict[int, float]:
        """
        Calcula factores de corrección para cada número según desequilibrios detectados
        
        Returns:
            Dict con factor de corrección para cada número (0-45)
        """
        factores = {num: 1.0 for num in range(0, 46)}
        
        # 1. Corrección por paridad
        equilibrio_paridad = self.results.get('equilibrio_pares_impares', {})
        if equilibrio_paridad.get('desbalance_significativo'):
            tendencia = equilibrio_paridad.get('tendencia_correccion')
            desbalance = abs(equilibrio_paridad.get('desbalance', 0))
            
            # Factor de corrección proporcional al desbalance
            factor_ajuste = 1.0 + (desbalance * 2.5)  # Hasta 1.5x si desbalance es 0.2
            
            for num in range(0, 46):
                if tendencia == 'favorecer_impares' and num % 2 != 0:
                    factores[num] *= factor_ajuste
                elif tendencia == 'favorecer_impares' and num % 2 == 0:
                    factores[num] *= (1 / factor_ajuste)
                elif tendencia == 'favorecer_pares' and num % 2 == 0:
                    factores[num] *= factor_ajuste
                elif tendencia == 'favorecer_pares' and num % 2 != 0:
                    factores[num] *= (1 / factor_ajuste)
        
        # 2. Corrección por suma
        equilibrio_suma = self.results.get('equilibrio_suma', {})
        if equilibrio_suma.get('desviacion_significativa'):
            tendencia = equilibrio_suma.get('tendencia_correccion')
            z_score = abs(equilibrio_suma.get('z_score', 0))
            
            # Factor proporcional a la desviación
            factor_suma = 1.0 + (z_score * 0.15)  # Hasta 1.3x si z=2
            
            for num in range(0, 46):
                if tendencia == 'favorecer_numeros_bajos' and num <= 20:
                    factores[num] *= factor_suma
                elif tendencia == 'favorecer_numeros_bajos' and num > 25:
                    factores[num] *= (1 / factor_suma)
                elif tendencia == 'favorecer_numeros_altos' and num >= 25:
                    factores[num] *= factor_suma
                elif tendencia == 'favorecer_numeros_altos' and num < 20:
                    factores[num] *= (1 / factor_suma)
        
        # 3. Corrección por rangos
        equilibrio_rangos = self.results.get('equilibrio_rangos', {})
        correcciones_rangos = equilibrio_rangos.get('correcciones', {})
        
        for rango, correccion in correcciones_rangos.items():
            desbalance = abs(equilibrio_rangos['desbalances'].get(
                'bajo' if 'bajo' in rango else ('medio' if 'medio' in rango else 'alto'),
                0
            ))
            factor_rango = 1.0 + (desbalance * 2.0)  # Hasta 1.4x si desbalance es 0.2
            
            if rango == 'rango_bajo':
                nums_rango = range(0, 16)
            elif rango == 'rango_medio':
                nums_rango = range(16, 31)
            else:
                nums_rango = range(31, 46)
            
            for num in nums_rango:
                if correccion == 'aumentar':
                    factores[num] *= factor_rango
                else:
                    factores[num] *= (1 / factor_rango)
        
        return factores
    
    def get_correction_factor(self, numero: int) -> float:
        """
        Obtiene el factor de corrección para un número específico
        
        Args:
            numero: Número a consultar (0-45)
        
        Returns:
            Factor de corrección (1.0 = sin corrección, >1.0 = favorecido, <1.0 = penalizado)
        """
        if not self.results or 'factores_correccion' not in self.results:
            raise ValueError("Debe ejecutar analyze() primero")
        
        return self.results['factores_correccion'].get(numero, 1.0)
    
    def get_summary(self) -> Dict:
        """
        Retorna resumen del análisis de equilibrio
        
        Returns:
            Dict con resumen de desequilibrios detectados
        """
        if not self.results:
            return {"error": "No se ha ejecutado el análisis"}
        
        paridad = self.results.get('equilibrio_pares_impares', {})
        suma = self.results.get('equilibrio_suma', {})
        rangos = self.results.get('equilibrio_rangos', {})
        
        return {
            'desequilibrios_detectados': {
                'paridad': paridad.get('desbalance_significativo', False),
                'suma': suma.get('desviacion_significativa', False),
                'rangos': len(rangos.get('correcciones', {})) > 0
            },
            'correcciones_aplicar': {
                'paridad': paridad.get('tendencia_correccion'),
                'suma': suma.get('tendencia_correccion'),
                'rangos': rangos.get('correcciones', {})
            },
            'metricas': {
                'desbalance_pares': paridad.get('desbalance', 0),
                'z_score_suma': suma.get('z_score', 0),
                'suma_objetivo': suma.get('suma_objetivo'),
                'desbalances_rangos': rangos.get('desbalances', {})
            }
        }
