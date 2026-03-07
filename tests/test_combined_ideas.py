"""
Test COMBINADO: IDEA #1 + IDEA #3
Valida la mejora en aciertos usando ambas optimizaciones juntas
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
from core.scoring.scorer import UnifiedScorer
from core.generator.strategy_manager import StrategyManager, GenerationStrategy
from configs.config_optimizada import OPTIMAL_WEIGHTS


def test_combined_ideas():
    """
    Test que compara 4 escenarios:
    1. BASELINE: Sin IDEAS
    2. SOLO IDEA #1: Resonancia de Ciclos
    3. SOLO IDEA #3: Regresión al Equilibrio
    4. COMBINADO: IDEA #1 + IDEA #3
    
    Usa sorteos 1-427 para predecir sorteo 428
    """
    print("\n" + "="*80)
    print("TEST COMBINADO: IDEA #1 + IDEA #3")
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
    
    resultados = {}
    
    # =========================================================================
    # ESCENARIO 1: BASELINE (Sin IDEAS)
    # =========================================================================
    print("\n" + "-"*80)
    print("ESCENARIO 1: BASELINE (Sin optimizaciones)")
    print("-"*80)
    
    scorer_baseline = UnifiedScorer(
        OPTIMAL_WEIGHTS,
        use_cycle_resonance=False,
        use_regression_equilibrium=False
    )
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
        print(f"Acertados: {sorted(set(pred_baseline) & set(numeros_reales))}")
    
    resultados['baseline'] = {
        'prediccion': pred_baseline,
        'aciertos': aciertos_baseline
    }
    
    # =========================================================================
    # ESCENARIO 2: SOLO IDEA #1 (Resonancia de Ciclos)
    # =========================================================================
    print("\n" + "-"*80)
    print("ESCENARIO 2: SOLO IDEA #1 (Resonancia de Ciclos)")
    print("-"*80)
    
    cycle_analyzer = CycleResonanceAnalyzer()
    
    scorer_idea1 = UnifiedScorer(
        OPTIMAL_WEIGHTS,
        use_cycle_resonance=True,
        use_regression_equilibrium=False
    )
    scores_idea1 = scorer_idea1.calculate_scores(
        freq_analyzer,
        cycle_resonance_analyzer=cycle_analyzer
    )
    
    result_idea1 = manager.generate(
        scores_idea1,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_idea1 = sorted(result_idea1['conditional']['combination'])
    aciertos_idea1 = len(set(pred_idea1) & set(numeros_reales))
    
    print(f"Predicción: {pred_idea1}")
    print(f"Aciertos: {aciertos_idea1}/6")
    if aciertos_idea1 > 0:
        print(f"Acertados: {sorted(set(pred_idea1) & set(numeros_reales))}")
    
    resultados['idea1'] = {
        'prediccion': pred_idea1,
        'aciertos': aciertos_idea1
    }
    
    # =========================================================================
    # ESCENARIO 3: SOLO IDEA #3 (Regresión al Equilibrio)
    # =========================================================================
    print("\n" + "-"*80)
    print("ESCENARIO 3: SOLO IDEA #3 (Regresión al Equilibrio)")
    print("-"*80)
    
    regression_analyzer = RegressionEquilibriumAnalyzer()
    
    scorer_idea3 = UnifiedScorer(
        OPTIMAL_WEIGHTS,
        use_cycle_resonance=False,
        use_regression_equilibrium=True
    )
    scores_idea3 = scorer_idea3.calculate_scores(
        freq_analyzer,
        regression_analyzer=regression_analyzer
    )
    
    result_idea3 = manager.generate(
        scores_idea3,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_idea3 = sorted(result_idea3['conditional']['combination'])
    aciertos_idea3 = len(set(pred_idea3) & set(numeros_reales))
    
    print(f"Predicción: {pred_idea3}")
    print(f"Aciertos: {aciertos_idea3}/6")
    if aciertos_idea3 > 0:
        print(f"Acertados: {sorted(set(pred_idea3) & set(numeros_reales))}")
    
    # Mostrar análisis de equilibrio
    summary_eq = regression_analyzer.get_summary()
    if any(summary_eq['desequilibrios_detectados'].values()):
        print("\nDesequilibrios detectados:")
        for tipo, detectado in summary_eq['desequilibrios_detectados'].items():
            if detectado:
                print(f"  - {tipo.title()}")
    
    resultados['idea3'] = {
        'prediccion': pred_idea3,
        'aciertos': aciertos_idea3
    }
    
    # =========================================================================
    # ESCENARIO 4: COMBINADO (IDEA #1 + IDEA #3)
    # =========================================================================
    print("\n" + "-"*80)
    print("ESCENARIO 4: COMBINADO (IDEA #1 + IDEA #3)")
    print("-"*80)
    
    cycle_analyzer_combo = CycleResonanceAnalyzer()
    regression_analyzer_combo = RegressionEquilibriumAnalyzer()
    
    scorer_combo = UnifiedScorer(
        OPTIMAL_WEIGHTS,
        use_cycle_resonance=True,
        use_regression_equilibrium=True
    )
    scores_combo = scorer_combo.calculate_scores(
        freq_analyzer,
        cycle_resonance_analyzer=cycle_analyzer_combo,
        regression_analyzer=regression_analyzer_combo
    )
    
    result_combo = manager.generate(
        scores_combo,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_combo = sorted(result_combo['conditional']['combination'])
    aciertos_combo = len(set(pred_combo) & set(numeros_reales))
    
    print(f"Predicción: {pred_combo}")
    print(f"Aciertos: {aciertos_combo}/6")
    if aciertos_combo > 0:
        print(f"Acertados: {sorted(set(pred_combo) & set(numeros_reales))}")
    
    resultados['combo'] = {
        'prediccion': pred_combo,
        'aciertos': aciertos_combo
    }
    
    # =========================================================================
    # COMPARACIÓN FINAL
    # =========================================================================
    print("\n" + "="*80)
    print("COMPARACIÓN FINAL")
    print("="*80)
    
    print(f"\nBASELINE:                {aciertos_baseline}/6 aciertos")
    print(f"SOLO IDEA #1:            {aciertos_idea1}/6 aciertos (Δ {aciertos_idea1 - aciertos_baseline:+d})")
    print(f"SOLO IDEA #3:            {aciertos_idea3}/6 aciertos (Δ {aciertos_idea3 - aciertos_baseline:+d})")
    print(f"COMBINADO (IDEA #1+#3):  {aciertos_combo}/6 aciertos (Δ {aciertos_combo - aciertos_baseline:+d})")
    
    # Determinar ganador
    mejor_aciertos = max(aciertos_baseline, aciertos_idea1, aciertos_idea3, aciertos_combo)
    ganadores = []
    
    if aciertos_baseline == mejor_aciertos:
        ganadores.append("BASELINE")
    if aciertos_idea1 == mejor_aciertos:
        ganadores.append("IDEA #1")
    if aciertos_idea3 == mejor_aciertos:
        ganadores.append("IDEA #3")
    if aciertos_combo == mejor_aciertos:
        ganadores.append("COMBINADO")
    
    print(f"\n🏆 GANADOR(ES): {', '.join(ganadores)} con {mejor_aciertos}/6 aciertos")
    
    # Verificar si el combinado es mejor que ambas por separado
    if aciertos_combo > max(aciertos_idea1, aciertos_idea3):
        print("✅ EFECTO SINÉRGICO: El combinado supera ambas ideas por separado")
    elif aciertos_combo == max(aciertos_idea1, aciertos_idea3):
        print("➖ EFECTO IGUAL: El combinado iguala la mejor idea individual")
    else:
        print("⚠️ INTERFERENCIA: El combinado es peor que al menos una idea individual")
    
    print("\n" + "="*80)
    print("FIN DEL TEST")
    print("="*80 + "\n")
    
    return resultados


if __name__ == '__main__':
    resultados = test_combined_ideas()
