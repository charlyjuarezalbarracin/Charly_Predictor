"""
Test COMPLETO: Todas las combinaciones de IDEAS
Compara 8 escenarios diferentes para encontrar la mejor configuración

Escenarios:
1. BASELINE (sin IDEAS)
2. SOLO IDEA #1 (Resonancia de Ciclos)
3. SOLO IDEA #2 (Multi-Timeframe)
4. SOLO IDEA #3 (Regresión al Equilibrio)
5. IDEA #1 + #2
6. IDEA #1 + #3
7. IDEA #2 + #3
8. IDEA #1 + #2 + #3 (TODAS)

Usa sorteos 1-427 para predecir sorteo 428
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from core.data.loader import DataLoader
from core.analysis.frequency import FrequencyAnalyzer
from core.analysis.correlations import CorrelationAnalyzer
from core.analysis.cycle_resonance import CycleResonanceAnalyzer
from core.analysis.regression_equilibrium import RegressionEquilibriumAnalyzer
from core.analysis.multi_timeframe import MultiTimeframeAnalyzer
from core.scoring.scorer import UnifiedScorer
from core.generator.strategy_manager import StrategyManager, GenerationStrategy
from configs.config_optimizada import OPTIMAL_WEIGHTS


def test_escenario(nombre, use_idea1, use_idea2, use_idea3, freq_analyzer, corr_analyzer, numeros_reales):
    """
    Ejecuta un escenario de prueba con configuración específica
    
    Args:
        nombre: Nombre del escenario
        use_idea1: Activar IDEA #1 (Resonancia)
        use_idea2: Activar IDEA #2 (Multi-Timeframe)
        use_idea3: Activar IDEA #3 (Regresión)
        freq_analyzer: Analizador de frecuencias
        corr_analyzer: Analizador de correlaciones
        numeros_reales: Números del sorteo objetivo
    
    Returns:
        Dict con predicción y aciertos
    """
    # Crear analizadores según configuración
    cycle_analyzer = CycleResonanceAnalyzer() if use_idea1 else None
    mtf_analyzer = MultiTimeframeAnalyzer() if use_idea2 else None
    regression_analyzer = None
    
    if use_idea3:
        regression_analyzer = RegressionEquilibriumAnalyzer()
        regression_analyzer.ventana_analisis = 16  # 2 semanas
        regression_analyzer.umbral_desbalance = 0.12  # 12%
    
    # Crear scorer
    scorer = UnifiedScorer(
        OPTIMAL_WEIGHTS,
        use_cycle_resonance=use_idea1,
        use_multi_timeframe=use_idea2,
        use_regression_equilibrium=use_idea3
    )
    
    # Calcular scores
    scores = scorer.calculate_scores(
        freq_analyzer,
        cycle_resonance_analyzer=cycle_analyzer,
        multi_timeframe_analyzer=mtf_analyzer,
        regression_analyzer=regression_analyzer
    )
    
    # Generar predicción
    manager = StrategyManager()
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    prediccion = sorted(result['conditional']['combination'])
    aciertos = len(set(prediccion) & set(numeros_reales))
    
    return {
        'nombre': nombre,
        'prediccion': prediccion,
        'aciertos': aciertos,
        'numeros_acertados': sorted(set(prediccion) & set(numeros_reales)) if aciertos > 0 else []
    }


def test_todas_ideas():
    """
    Test que compara todos los escenarios posibles
    """
    print("\n" + "="*90)
    print("TEST COMPLETO: TODAS LAS COMBINACIONES DE IDEAS")
    print("="*90)
    
    # Cargar datos
    loader = DataLoader()
    df = loader.load_csv('data/quini6_historico_test.csv')
    
    print(f"\nDatos cargados: {len(df)} sorteos")
    print(f"Rango de fechas: {df['fecha'].min()} a {df['fecha'].max()}")
    
    # Usar sorteos 1-427 para entrenar, 428 para validar
    df_train = df[df['sorteo_id'] < 428].copy()
    sorteo_objetivo = df[df['sorteo_id'] == 428].iloc[0]
    
    numeros_reales = sorted([int(x) for x in sorteo_objetivo['numeros']])
    print(f"\nObjetivo: Sorteo {sorteo_objetivo['sorteo_id']} - {sorteo_objetivo['fecha']}")
    print(f"Números reales: {numeros_reales}")
    
    # Preparar analizadores comunes
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(df_train)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(df_train)
    
    # Definir escenarios a probar
    escenarios = [
        ("BASELINE", False, False, False),
        ("IDEA #1", True, False, False),
        ("IDEA #2", False, True, False),
        ("IDEA #3", False, False, True),
        ("IDEA #1+#2", True, True, False),
        ("IDEA #1+#3", True, False, True),
        ("IDEA #2+#3", False, True, True),
        ("TODAS (#1+#2+#3)", True, True, True),
    ]
    
    resultados = []
    
    # Ejecutar todos los escenarios
    print("\n" + "="*90)
    print("EJECUTANDO ESCENARIOS")
    print("="*90)
    
    for nombre, use_idea1, use_idea2, use_idea3 in escenarios:
        print(f"\n{'='*90}")
        print(f"ESCENARIO: {nombre}")
        print(f"{'='*90}")
        
        resultado = test_escenario(
            nombre, use_idea1, use_idea2, use_idea3,
            freq_analyzer, corr_analyzer, numeros_reales
        )
        
        resultados.append(resultado)
        
        print(f"Predicción: {resultado['prediccion']}")
        print(f"Aciertos: {resultado['aciertos']}/6")
        if resultado['aciertos'] > 0:
            print(f"Acertados: {resultado['numeros_acertados']}")
    
    # =========================================================================
    # COMPARACIÓN FINAL
    # =========================================================================
    print("\n" + "="*90)
    print("TABLA COMPARATIVA FINAL")
    print("="*90)
    
    # Ordenar por aciertos descendente
    resultados_sorted = sorted(resultados, key=lambda x: x['aciertos'], reverse=True)
    
    print(f"\n{'Escenario':<25} {'Aciertos':<10} {'Predicción'}")
    print("-" * 90)
    
    for r in resultados_sorted:
        pred_str = str(r['prediccion'])
        acertados_str = f" → {r['numeros_acertados']}" if r['aciertos'] > 0 else ""
        print(f"{r['nombre']:<25} {r['aciertos']}/6{' '*6} {pred_str}{acertados_str}")
    
    # Determinar ganador(es)
    mejor_aciertos = max(r['aciertos'] for r in resultados)
    ganadores = [r for r in resultados if r['aciertos'] == mejor_aciertos]
    
    print("\n" + "="*90)
    print("GANADOR(ES)")
    print("="*90)
    
    for ganador in ganadores:
        print(f"🏆 {ganador['nombre']}: {ganador['aciertos']}/6 aciertos")
        if ganador['aciertos'] > 0:
            print(f"   Números acertados: {ganador['numeros_acertados']}")
    
    # Análisis de mejora
    baseline = next(r for r in resultados if r['nombre'] == 'BASELINE')
    mejor = resultados_sorted[0]
    
    mejora = mejor['aciertos'] - baseline['aciertos']
    
    print(f"\n{'='*90}")
    print("ANÁLISIS DE MEJORA")
    print(f"{'='*90}")
    print(f"BASELINE:           {baseline['aciertos']}/6 aciertos")
    print(f"MEJOR CONFIGURACIÓN: {mejor['nombre']}")
    print(f"ACIERTOS:           {mejor['aciertos']}/6")
    print(f"MEJORA:             {mejora:+d} aciertos ({(mejora/6)*100:+.1f}%)")
    
    # Análisis de sinergia
    print(f"\n{'='*90}")
    print("ANÁLISIS DE SINERGIA ENTRE IDEAS")
    print(f"{'='*90}")
    
    idea1 = next(r for r in resultados if r['nombre'] == 'IDEA #1')
    idea2 = next(r for r in resultados if r['nombre'] == 'IDEA #2')
    idea3 = next(r for r in resultados if r['nombre'] == 'IDEA #3')
    todas = next(r for r in resultados if r['nombre'] == 'TODAS (#1+#2+#3)')
    
    max_individual = max(idea1['aciertos'], idea2['aciertos'], idea3['aciertos'])
    
    print(f"Mejor idea individual: {max_individual}/6 aciertos")
    print(f"Todas combinadas:      {todas['aciertos']}/6 aciertos")
    
    if todas['aciertos'] > max_individual:
        print("✅ SINERGIA POSITIVA: Las ideas combinadas superan las individuales")
    elif todas['aciertos'] == max_individual:
        print("➖ SINERGIA NEUTRA: Las ideas combinadas igualan la mejor individual")
    else:
        print("⚠️ INTERFERENCIA: Las ideas combinadas son peores que al menos una individual")
    
    print("\n" + "="*90)
    print("FIN DEL TEST")
    print("="*90 + "\n")
    
    return resultados


if __name__ == '__main__':
    resultados = test_todas_ideas()
