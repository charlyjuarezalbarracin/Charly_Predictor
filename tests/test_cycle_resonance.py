"""
Test de la IDEA #1: Resonancia de Ciclos
Valida la mejora en aciertos usando datos históricos reales
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from core.data.loader import DataLoader
from core.analysis.frequency import FrequencyAnalyzer
from core.analysis.correlations import CorrelationAnalyzer
from core.analysis.cycle_resonance import CycleResonanceAnalyzer
from core.scoring.scorer import UnifiedScorer
from core.generator.strategy_manager import StrategyManager, GenerationStrategy
from configs.config_optimizada import OPTIMAL_WEIGHTS


def test_cycle_resonance():
    """
    Test principal que compara resultados con y sin IDEA #1
    Usa sorteos 1-427 para predecir sorteo 428
    """
    print("\n" + "="*80)
    print("TEST IDEA #1: RESONANCIA DE CICLOS")
    print("="*80)
    
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
    
    # Preparar analizadores
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(df_train)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(df_train)
    
    manager = StrategyManager()
    
    # =========================================================================
    # BASELINE: Sin IDEA #1
    # =========================================================================
    print("\n" + "-"*80)
    print("BASELINE: Sin Resonancia de Ciclos")
    print("-"*80)
    
    scorer_baseline = UnifiedScorer(OPTIMAL_WEIGHTS, use_cycle_resonance=False)
    scores_baseline = scorer_baseline.calculate_scores(freq_analyzer)
    
    result_baseline = manager.generate(
        scores_baseline,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_baseline = sorted(result_baseline['conditional']['combination'])
    aciertos_baseline = len(set(pred_baseline) & set(numeros_reales))
    
    print(f"Predicción: {pred_baseline}")
    print(f"Aciertos: {aciertos_baseline}/6")
    if aciertos_baseline > 0:
        numeros_acertados = sorted(set(pred_baseline) & set(numeros_reales))
        print(f"Números acertados: {numeros_acertados}")
    
    # =========================================================================
    # IDEA #1: Con Resonancia de Ciclos
    # =========================================================================
    print("\n" + "-"*80)
    print("IDEA #1: Con Resonancia de Ciclos")
    print("-"*80)
    
    scorer_resonance = UnifiedScorer(OPTIMAL_WEIGHTS, use_cycle_resonance=True)
    
    # Crear y configurar el analizador de resonancia
    cycle_analyzer = CycleResonanceAnalyzer()
    
    scores_resonance = scorer_resonance.calculate_scores(
        freq_analyzer,
        cycle_resonance_analyzer=cycle_analyzer
    )
    
    result_resonance = manager.generate(
        scores_resonance,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_resonance = sorted(result_resonance['conditional']['combination'])
    aciertos_resonance = len(set(pred_resonance) & set(numeros_reales))
    
    print(f"Predicción: {pred_resonance}")
    print(f"Aciertos: {aciertos_resonance}/6")
    if aciertos_resonance > 0:
        numeros_acertados = sorted(set(pred_resonance) & set(numeros_reales))
        print(f"Números acertados: {numeros_acertados}")
    
    # Mostrar información de resonancia
    print("\nAnálisis de Resonancia:")
    summary = cycle_analyzer.get_summary()
    print(f"  Números en ventana óptima: {summary['total_en_ventana_optima']}")
    print(f"  Números en sweet spot: {summary['total_en_sweet_spot']}")
    print(f"  Números mega atrasados: {summary['total_mega_atrasados']}")
    
    if summary['numeros_sweet_spot']:
        print(f"  Sweet spot: {summary['numeros_sweet_spot'][:10]}")
    if summary['numeros_mega_atrasados']:
        print(f"  Mega atrasados: {summary['numeros_mega_atrasados']}")
    
    # Top 5 por resonancia
    print("\n  Top 5 por resonancia:")
    for i, (num, score, z) in enumerate(summary['top_resonancia'][:5], 1):
        print(f"    {i}. Número {num}: score={score:.2f}, Z={z:+.2f}σ")
    
    # =========================================================================
    # COMPARACIÓN FINAL
    # =========================================================================
    print("\n" + "="*80)
    print("COMPARACIÓN FINAL")
    print("="*80)
    
    print(f"BASELINE:        {aciertos_baseline}/6 aciertos")
    print(f"IDEA #1:         {aciertos_resonance}/6 aciertos")
    
    mejora = aciertos_resonance - aciertos_baseline
    if mejora > 0:
        print(f"\n✅ MEJORA: +{mejora} aciertos con IDEA #1")
    elif mejora < 0:
        print(f"\n❌ EMPEORAMIENTO: {mejora} aciertos con IDEA #1")
    else:
        print(f"\n➖ EMPATE: Sin cambios con IDEA #1")
    
    print("\n" + "="*80)
    print("FIN DEL TEST")
    print("="*80 + "\n")
    
    return {
        'baseline': aciertos_baseline,
        'idea1': aciertos_resonance,
        'mejora': mejora,
        'prediccion_baseline': pred_baseline,
        'prediccion_idea1': pred_resonance,
        'numeros_reales': numeros_reales
    }


if __name__ == '__main__':
    resultados = test_cycle_resonance()
