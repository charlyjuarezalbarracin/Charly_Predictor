"""
Test de Regresión al Equilibrio - IDEA #3

Prueba la implementación del análisis de regresión al equilibrio usando datos reales.
Predice el último sorteo conocido usando todos los sorteos anteriores y compara resultados.

Dataset: quini6_historico_test.csv
- Sorteos 1-427: Datos de entrenamiento
- Sorteo 428: Resultado real a predecir
"""

import sys
sys.path.insert(0, 'd:/Repo/Charly_Predictor')

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, RegressionEquilibriumAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy
from configs.config_optimizada import OPTIMAL_WEIGHTS
import pandas as pd


# Resultado real del sorteo 428 (último en el CSV)
SORTEO_OBJETIVO = 428
RESULTADO_REAL = [2, 9, 10, 14, 28, 38]  # Sorteo 428: 2026-02-18


def calcular_aciertos(prediccion, real):
    """Calcula número de aciertos exactos"""
    return len(set(prediccion) & set(real))


def analizar_cercania(prediccion, real):
    """Analiza qué tan cerca están los números predichos del resultado real"""
    aciertos_exactos = set(prediccion) & set(real)
    casi_aciertos = set()
    
    # Números a ±3 del resultado
    for pred in prediccion:
        for r in real:
            if abs(pred - r) <= 3 and pred not in aciertos_exactos:
                casi_aciertos.add(pred)
                break
    
    return len(aciertos_exactos), len(casi_aciertos)


def mostrar_analisis_equilibrio(regression_analyzer):
    """Muestra el análisis detallado de equilibrio"""
    print("\n" + "="*80)
    print(" ANÁLISIS DE REGRESIÓN AL EQUILIBRIO (IDEA #3)")
    print("="*80)
    
    summary = regression_analyzer.get_summary()
    
    # Desequilibrios detectados
    print("\n1. DESEQUILIBRIOS DETECTADOS:")
    deseq = summary['desequilibrios_detectados']
    print(f"   - Paridad (Pares/Impares): {'SÍ' if deseq['paridad'] else 'NO'}")
    print(f"   - Suma Total:              {'SÍ' if deseq['suma'] else 'NO'}")
    print(f"   - Distribución Rangos:     {'SÍ' if deseq['rangos'] else 'NO'}")
    
    # Correcciones a aplicar
    print("\n2. CORRECCIONES A APLICAR:")
    corr = summary['correcciones_aplicar']
    
    if corr['paridad']:
        print(f"   - Paridad: {corr['paridad']}")
    else:
        print(f"   - Paridad: Sin corrección necesaria")
    
    if corr['suma']:
        print(f"   - Suma: {corr['suma']}")
        if summary['metricas']['suma_objetivo']:
            print(f"     → Suma objetivo: {summary['metricas']['suma_objetivo']:.1f}")
    else:
        print(f"   - Suma: Sin corrección necesaria")
    
    if corr['rangos']:
        print(f"   - Rangos:")
        for rango, accion in corr['rangos'].items():
            print(f"     → {rango}: {accion}")
    else:
        print(f"   - Rangos: Sin corrección necesaria")
    
    # Métricas
    print("\n3. MÉTRICAS DETALLADAS:")
    metricas = summary['metricas']
    print(f"   - Desbalance Pares:  {metricas['desbalance_pares']:+.3f} ({abs(metricas['desbalance_pares'])*100:.1f}%)")
    print(f"   - Z-Score Suma:      {metricas['z_score_suma']:+.2f} sigma")
    
    if metricas.get('desbalances_rangos'):
        print(f"   - Desbalances Rangos:")
        for rango, desb in metricas['desbalances_rangos'].items():
            print(f"     → {rango}: {desb:+.3f}")


def mostrar_top_numeros_con_factores(scorer, top_n=15):
    """Muestra top números con sus factores de corrección"""
    print("\n" + "="*80)
    print(f" TOP {top_n} NÚMEROS CON FACTORES DE CORRECCIÓN")
    print("="*80)
    
    top_numbers = scorer.get_top_numbers(top_n)
    
    if scorer.regression_analyzer:
        factores = scorer.regression_analyzer.results.get('factores_correccion', {})
        
        print("\n   #  | Número | Score Base | Factor Regr. | Score Final")
        print("   " + "-"*60)
        
        for i, (num, score_final) in enumerate(top_numbers, 1):
            factor = factores.get(num, 1.0)
            # Aproximar score base antes del factor
            score_base = score_final / factor if factor != 0 else score_final
            
            # Indicador visual del factor
            if factor > 1.2:
                indicador = "↑↑"
            elif factor > 1.05:
                indicador = "↑"
            elif factor < 0.8:
                indicador = "↓↓"
            elif factor < 0.95:
                indicador = "↓"
            else:
                indicador = "="
            
            print(f"   {i:2d} | {num:6d} | {score_base:10.4f} | {factor:7.3f} {indicador} | {score_final:.4f}")
    else:
        for i, (num, score) in enumerate(top_numbers, 1):
            print(f"   {i:2d}. Número {num:2d} - Score: {score:.4f}")


def test_prediccion_con_regression():
    """Test principal de predicción con regresión al equilibrio"""
    print("\n" + "="*80)
    print(" TEST DE IDEA #3: REGRESIÓN AL EQUILIBRIO")
    print("="*80)
    print(f"\nDataset: quini6_historico_test.csv")
    print(f"Objetivo: Predecir sorteo {SORTEO_OBJETIVO}")
    print(f"Resultado real: {RESULTADO_REAL}")
    print(f"Fecha: 2026-02-18")
    
    # 1. Cargar datos
    print("\n" + "-"*80)
    print("1. CARGANDO DATOS...")
    print("-"*80)
    
    loader = DataLoader()
    data_completa = loader.load_csv('data/quini6_historico_test.csv')
    
    # Separar: todos menos el último para entrenamiento
    data_train = data_completa[data_completa['sorteo_id'] < SORTEO_OBJETIVO].copy()
    data_test = data_completa[data_completa['sorteo_id'] == SORTEO_OBJETIVO].iloc[0]
    
    print(f"   ✓ Total sorteos cargados: {len(data_completa)}")
    print(f"   ✓ Sorteos entrenamiento: {len(data_train)} (ID 1-{SORTEO_OBJETIVO-1})")
    print(f"   ✓ Sorteo prueba: {data_test['sorteo_id']} ({data_test['fecha']})")
    
    # 2. Ejecutar análisis
    print("\n" + "-"*80)
    print("2. EJECUTANDO ANÁLISIS...")
    print("-"*80)
    
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data_train)
    print("   ✓ Análisis de frecuencias completado")
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data_train)
    print("   ✓ Análisis de correlaciones completado")
    
    regression_analyzer = RegressionEquilibriumAnalyzer()
    regression_analyzer.analyze(data_train)
    print("   ✓ Análisis de regresión al equilibrio completado")
    
    # 3. Mostrar análisis de equilibrio
    mostrar_analisis_equilibrio(regression_analyzer)
    
    # 4. Generar predicciones
    print("\n" + "="*80)
    print(" GENERACIÓN DE PREDICCIONES")
    print("="*80)
    
    # PREDICCIÓN SIN REGRESIÓN (baseline)
    print("\n▶ PREDICCIÓN BASELINE (sin IDEA #3):")
    scorer_baseline = UnifiedScorer(OPTIMAL_WEIGHTS, use_regression_equilibrium=False)
    scores_baseline = scorer_baseline.calculate_scores(freq_analyzer)
    
    manager = StrategyManager()
    result_baseline = manager.generate(
        scores_baseline,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_baseline_std = sorted(result_baseline['standard']['combination'])
    pred_baseline_cond = sorted(result_baseline['conditional']['combination'])
    
    print(f"   Estándar:     {pred_baseline_std}")
    print(f"   Condicional:  {pred_baseline_cond}")
    
    # PREDICCIÓN CON REGRESIÓN (IDEA #3)
    print("\n▶ PREDICCIÓN CON IDEA #3 (Regresión al Equilibrio):")
    scorer_regression = UnifiedScorer(OPTIMAL_WEIGHTS, use_regression_equilibrium=True)
    scores_regression = scorer_regression.calculate_scores(
        freq_analyzer,
        regression_analyzer=regression_analyzer
    )
    
    result_regression = manager.generate(
        scores_regression,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    pred_regression_std = sorted(result_regression['standard']['combination'])
    pred_regression_cond = sorted(result_regression['conditional']['combination'])
    
    print(f"   Estándar:     {pred_regression_std}")
    print(f"   Condicional:  {pred_regression_cond}")
    
    # Mostrar top números con factores
    mostrar_top_numeros_con_factores(scorer_regression, top_n=15)
    
    # 5. Evaluar resultados
    print("\n" + "="*80)
    print(" EVALUACIÓN DE RESULTADOS")
    print("="*80)
    print(f"\nResultado Real: {RESULTADO_REAL}")
    print(f"Suma Real: {sum(RESULTADO_REAL)}")
    print(f"Pares/Impares Real: {sum(1 for n in RESULTADO_REAL if n % 2 == 0)}/6 pares")
    
    print("\n" + "-"*80)
    print("BASELINE (sin IDEA #3):")
    print("-"*80)
    
    # Baseline Estándar
    aciertos_bs = calcular_aciertos(pred_baseline_std, RESULTADO_REAL)
    exactos_bs, cercanos_bs = analizar_cercania(pred_baseline_std, RESULTADO_REAL)
    print(f"\nEstándar:     {pred_baseline_std}")
    print(f"  → Aciertos exactos: {aciertos_bs}/6")
    print(f"  → Cerca (±3):       {cercanos_bs}/6")
    print(f"  → Suma predicha:    {sum(pred_baseline_std)}")
    
    # Baseline Condicional
    aciertos_bc = calcular_aciertos(pred_baseline_cond, RESULTADO_REAL)
    exactos_bc, cercanos_bc = analizar_cercania(pred_baseline_cond, RESULTADO_REAL)
    print(f"\nCondicional:  {pred_baseline_cond}")
    print(f"  → Aciertos exactos: {aciertos_bc}/6")
    print(f"  → Cerca (±3):       {cercanos_bc}/6")
    print(f"  → Suma predicha:    {sum(pred_baseline_cond)}")
    
    print("\n" + "-"*80)
    print("CON IDEA #3 (Regresión al Equilibrio):")
    print("-"*80)
    
    # Regresión Estándar
    aciertos_rs = calcular_aciertos(pred_regression_std, RESULTADO_REAL)
    exactos_rs, cercanos_rs = analizar_cercania(pred_regression_std, RESULTADO_REAL)
    print(f"\nEstándar:     {pred_regression_std}")
    print(f"  → Aciertos exactos: {aciertos_rs}/6")
    print(f"  → Cerca (±3):       {cercanos_rs}/6")
    print(f"  → Suma predicha:    {sum(pred_regression_std)}")
    
    # Regresión Condicional
    aciertos_rc = calcular_aciertos(pred_regression_cond, RESULTADO_REAL)
    exactos_rc, cercanos_rc = analizar_cercania(pred_regression_cond, RESULTADO_REAL)
    print(f"\nCondicional:  {pred_regression_cond}")
    print(f"  → Aciertos exactos: {aciertos_rc}/6")
    print(f"  → Cerca (±3):       {cercanos_rc}/6")
    print(f"  → Suma predicha:    {sum(pred_regression_cond)}")
    
    # 6. Comparación Final
    print("\n" + "="*80)
    print(" COMPARACIÓN Y CONCLUSIONES")
    print("="*80)
    
    mejor_baseline = max(aciertos_bs, aciertos_bc)
    mejor_regression = max(aciertos_rs, aciertos_rc)
    
    print(f"\nMejor resultado BASELINE:     {mejor_baseline}/6 aciertos")
    print(f"Mejor resultado con IDEA #3:  {mejor_regression}/6 aciertos")
    
    mejora = mejor_regression - mejor_baseline
    if mejora > 0:
        print(f"\n✓ MEJORA: +{mejora} aciertos con IDEA #3")
    elif mejora < 0:
        print(f"\n✗ RETROCESO: {mejora} aciertos con IDEA #3")
    else:
        print(f"\n= EMPATE: Sin diferencia")
    
    # Análisis del resultado real vs predicciones
    print("\n" + "-"*80)
    print("ANÁLISIS DEL RESULTADO REAL:")
    print("-"*80)
    
    pares_real = sum(1 for n in RESULTADO_REAL if n % 2 == 0)
    suma_real = sum(RESULTADO_REAL)
    
    print(f"\nCaracterísticas del sorteo real:")
    print(f"  - Números:      {RESULTADO_REAL}")
    print(f"  - Suma:         {suma_real}")
    print(f"  - Pares:        {pares_real}/6")
    print(f"  - Impares:      {6-pares_real}/6")
    
    print(f"\nNúmeros en rangos:")
    bajo = sum(1 for n in RESULTADO_REAL if 0 <= n <= 15)
    medio = sum(1 for n in RESULTADO_REAL if 16 <= n <= 30)
    alto = sum(1 for n in RESULTADO_REAL if 31 <= n <= 45)
    print(f"  - Bajo (0-15):   {bajo}/6")
    print(f"  - Medio (16-30): {medio}/6")
    print(f"  - Alto (31-45):  {alto}/6")
    
    print("\n" + "="*80)
    print(" FIN DEL TEST")
    print("="*80 + "\n")
    
    return {
        'baseline': {
            'estandar': {'prediccion': pred_baseline_std, 'aciertos': aciertos_bs},
            'condicional': {'prediccion': pred_baseline_cond, 'aciertos': aciertos_bc}
        },
        'regression': {
            'estandar': {'prediccion': pred_regression_std, 'aciertos': aciertos_rs},
            'condicional': {'prediccion': pred_regression_cond, 'aciertos': aciertos_rc}
        },
        'mejora': mejora
    }


if __name__ == '__main__':
    test_prediccion_con_regression()
