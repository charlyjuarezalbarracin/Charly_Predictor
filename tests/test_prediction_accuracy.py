"""
Test de precisión de predicción con resultado conocido
Prueba: Predecir el sorteo 30 conociendo que el resultado será 02, 04, 15, 18, 31, 43
"""

import sys
sys.path.append('d:/Repo/Charly_Predictor')

from src.data_loader import DataLoader
from src.analyzers.frequency_analyzer import FrequencyAnalyzer
from src.analyzers.correlation_analyzer import CorrelationAnalyzer
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.scorers.composite_scorer import CompositeScorer
from src.strategy_manager import StrategyManager, GenerationStrategy
import pandas as pd
import numpy as np

# Resultado esperado (sorteo 30 real)
RESULTADO_ESPERADO = [2, 4, 15, 18, 31, 43]

def calcular_aciertos(prediccion, resultado):
    """Calcular cuántos números coinciden"""
    return len(set(prediccion) & set(resultado))

def calcular_distancia_promedio(prediccion, resultado):
    """Calcular distancia promedio entre números predichos y resultado"""
    distancias = []
    for pred in prediccion:
        min_dist = min([abs(pred - res) for res in resultado])
        distancias.append(min_dist)
    return np.mean(distancias)

def analizar_covertura(prediccion, resultado):
    """Analizar qué tan cerca están los números predichos"""
    print("\n" + "="*80)
    print("ANÁLISIS DE COBERTURA")
    print("="*80)
    
    pred_set = set(prediccion)
    res_set = set(resultado)
    
    aciertos = pred_set & res_set
    casi_aciertos = set()
    
    # Números que están a ±2 del resultado
    for pred in prediccion:
        for res in resultado:
            if abs(pred - res) <= 2 and pred not in aciertos:
                casi_aciertos.add(pred)
    
    print(f"\n✓ Aciertos directos: {len(aciertos)} números")
    if aciertos:
        print(f"  → Números: {sorted(aciertos)}")
    
    print(f"\n≈ Casi aciertos (±2): {len(casi_aciertos)} números")
    if casi_aciertos:
        print(f"  → Números: {sorted(casi_aciertos)}")
    
    print(f"\n✗ Sin relación: {6 - len(aciertos) - len(casi_aciertos)} números")
    
    return len(aciertos), len(casi_aciertos)

def analizar_estadisticas_comunes(prediccion, resultado, freq_analyzer):
    """Analizar características estadísticas comunes"""
    print("\n" + "="*80)
    print("ANÁLISIS DE CARACTERÍSTICAS ESTADÍSTICAS")
    print("="*80)
    
    # Análisis de calientes/fríos
    calientes = [num for num, freq in freq_analyzer.results['numeros_calientes'][:15]]
    frios = [num for num, freq in freq_analyzer.results['numeros_frios'][:15]]
    
    pred_calientes = len(set(prediccion) & set(calientes))
    res_calientes = len(set(resultado) & set(calientes))
    
    pred_frios = len(set(prediccion) & set(frios))
    res_frios = len(set(resultado) & set(frios))
    
    print(f"\nNúmeros CALIENTES:")
    print(f"  Predicción: {pred_calientes}/6")
    print(f"  Resultado:  {res_calientes}/6")
    print(f"  Diferencia: {abs(pred_calientes - res_calientes)}")
    
    print(f"\nNúmeros FRÍOS:")
    print(f"  Predicción: {pred_frios}/6")
    print(f"  Resultado:  {res_frios}/6")
    print(f"  Diferencia: {abs(pred_frios - res_frios)}")
    
    # Análisis de pares/impares
    def contar_pares(nums):
        return sum(1 for n in nums if n % 2 == 0)
    
    pred_pares = contar_pares(prediccion)
    res_pares = contar_pares(resultado)
    
    print(f"\nPARES vs IMPARES:")
    print(f"  Predicción: {pred_pares} pares, {6-pred_pares} impares")
    print(f"  Resultado:  {res_pares} pares, {6-res_pares} impares")
    print(f"  Diferencia: {abs(pred_pares - res_pares)}")
    
    # Análisis de suma total
    print(f"\nSUMA TOTAL:")
    print(f"  Predicción: {sum(prediccion)}")
    print(f"  Resultado:  {sum(resultado)}")
    print(f"  Diferencia: {abs(sum(prediccion) - sum(resultado))}")
    
    return {
        'dif_calientes': abs(pred_calientes - res_calientes),
        'dif_frios': abs(pred_frios - res_frios),
        'dif_pares': abs(pred_pares - res_pares),
        'dif_suma': abs(sum(prediccion) - sum(resultado))
    }

def main():
    print("\n" + "="*80)
    print("TEST DE PRECISIÓN DE PREDICCIÓN")
    print("="*80)
    print(f"\nResultado esperado (sorteo 30): {RESULTADO_ESPERADO}")
    
    # 1. Cargar datos históricos (29 sorteos)
    print("\n1. Cargando datos históricos...")
    loader = DataLoader()
    data = loader.load_csv('data/quini6_historico.csv')
    print(f"   ✓ {len(data)} sorteos cargados")
    
    # 2. Ejecutar análisis
    print("\n2. Ejecutando análisis estadístico...")
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    pattern_analyzer = PatternAnalyzer()
    pattern_analyzer.analyze(data)
    print("   ✓ Análisis completado")
    
    # 3. Generar predicciones con diferentes métodos
    print("\n3. Generando predicciones...")
    manager = StrategyManager()
    
    resultados = {}
    
    # MÉTODO ESTÁNDAR
    print("\n   → Método ESTÁNDAR...")
    result_std = manager.generate_prediction(
        data=data,
        strategy=GenerationStrategy.STANDARD,
        weights={
            'frequency': 1.0,
            'correlation': 0.0,
            'pattern': 0.0
        }
    )
    prediccion_std = result_std['combination']
    resultados['estandar'] = prediccion_std
    print(f"     Predicción: {[int(n) for n in sorted(prediccion_std)]}")
    
    # MÉTODO CONDICIONAL
    print("\n   → Método CONDICIONAL...")
    result_cond = manager.generate_prediction(
        data=data,
        strategy=GenerationStrategy.CONDITIONAL,
        weights={
            'frequency': 0.4,
            'correlation': 0.5,
            'pattern': 0.1
        }
    )
    prediccion_cond = result_cond['combination']
    resultados['condicional'] = prediccion_cond
    print(f"     Predicción: {[int(n) for n in sorted(prediccion_cond)]}")
    
    # MÉTODO HÍBRIDO (ajustado para balance)
    print("\n   → Método HÍBRIDO (balanceado)...")
    result_hybrid = manager.generate_prediction(
        data=data,
        strategy=GenerationStrategy.CONDITIONAL,
        weights={
            'frequency': 0.5,
            'correlation': 0.3,
            'pattern': 0.2
        }
    )
    prediccion_hybrid = result_hybrid['combination']
    resultados['hibrido'] = prediccion_hybrid
    print(f"     Predicción: {[int(n) for n in sorted(prediccion_hybrid)]}")
    
    # 4. Evaluar cada predicción
    print("\n" + "="*80)
    print("EVALUACIÓN DE RESULTADOS")
    print("="*80)
    
    mejores_parametros = None
    mejor_score = 0
    
    for nombre, prediccion in resultados.items():
        print(f"\n{'─'*80}")
        print(f"MÉTODO: {nombre.upper()}")
        print(f"{'─'*80}")
        
        pred_sorted = sorted([int(n) for n in prediccion])
        print(f"\nPredicción: {pred_sorted}")
        print(f"Esperado:   {RESULTADO_ESPERADO}")
        
        # Métricas
        aciertos = calcular_aciertos(prediccion, RESULTADO_ESPERADO)
        distancia = calcular_distancia_promedio(prediccion, RESULTADO_ESPERADO)
        
        print(f"\nAciertos directos: {aciertos}/6 ({aciertos/6*100:.1f}%)")
        print(f"Distancia promedio: {distancia:.2f} números")
        
        # Análisis detallado
        aciertos_directos, casi_aciertos = analizar_covertura(prediccion, RESULTADO_ESPERADO)
        stats_dif = analizar_estadisticas_comunes(prediccion, RESULTADO_ESPERADO, freq_analyzer)
        
        # Calcular score
        score = aciertos_directos * 10 + casi_aciertos * 3 - distancia
        print(f"\n>>> SCORE TOTAL: {score:.2f}")
        
        if score > mejor_score:
            mejor_score = score
            mejores_parametros = nombre
    
    # 5. Sugerencias de mejora
    print("\n" + "="*80)
    print("RECOMENDACIONES DE AJUSTE")
    print("="*80)
    
    print(f"\n✓ Mejor método: {mejores_parametros.upper()} (score: {mejor_score:.2f})")
    
    print("\n📋 SUGERENCIAS DE PARAMETRÍA:")
    print("\n1. PESOS DE ANÁLISIS (weights):")
    print("   Configuración recomendada basada en resultados:")
    
    if mejores_parametros == 'estandar':
        print("   • frequency: 0.7")
        print("   • correlation: 0.2")
        print("   • pattern: 0.1")
        print("   → El sistema responde mejor a frecuencias puras")
    elif mejores_parametros == 'condicional':
        print("   • frequency: 0.3")
        print("   • correlation: 0.6")
        print("   • pattern: 0.1")
        print("   → El sistema responde mejor a correlaciones")
    else:
        print("   • frequency: 0.5")
        print("   • correlation: 0.3")
        print("   • pattern: 0.2")
        print("   → Balance entre todos los métodos")
    
    print("\n2. NÚMERO DE SORTEOS HISTÓRICOS:")
    print(f"   Actual: {len(data)} sorteos")
    if len(data) < 50:
        print("   ⚠️ RECOMENDACIÓN: Aumentar a 50-100 sorteos para mejor precisión")
    elif len(data) < 100:
        print("   ✓ Aceptable, considera llegar a 100+ para óptimo rendimiento")
    else:
        print("   ✓ Buena cantidad de datos históricos")
    
    print("\n3. VENTANA TEMPORAL:")
    print("   → Considera dar más peso a sorteos recientes (últimos 20-30)")
    print("   → Implementar decay exponencial en frecuencias")
    
    print("\n4. RESTRICCIONES:")
    print("   → Evaluar agregar restricciones de suma total (90-150)")
    print("   → Forzar distribución pares/impares más balanceada (2-4 de cada)")
    print("   → Evitar más de 2 números consecutivos")
    
    # Análisis de los números específicos del resultado esperado
    print("\n5. ANÁLISIS DEL RESULTADO ESPERADO:")
    calientes_top = [num for num, freq in freq_analyzer.results['numeros_calientes'][:10]]
    en_top = len(set(RESULTADO_ESPERADO) & set(calientes_top))
    print(f"   • {en_top}/6 números del resultado están en Top 10 calientes")
    
    if en_top >= 4:
        print("   → Aumentar peso de 'frequency' a 0.6-0.7")
    else:
        print("   → Los números calientes NO predominan, considerar:")
        print("     • Reducir 'frequency' a 0.3-0.4")
        print("     • Aumentar 'correlation' o 'pattern'")
    
    print("\n" + "="*80)
    print("FIN DEL TEST")
    print("="*80)

if __name__ == "__main__":
    main()
