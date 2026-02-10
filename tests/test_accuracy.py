"""
Test de precisión de predicción
Resultado real conocido: 02 04 15 18 31 43
"""

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, PatternAnalyzer
from core.generator import StrategyManager, GenerationStrategy
from core.scoring import UnifiedScorer

# Resultado real conocido del próximo sorteo
RESULTADO_REAL = [2, 4, 15, 18, 31, 43]

def calcular_aciertos(prediccion, real):
    """Calcular número de aciertos"""
    return len(set(prediccion) & set(real))

def test_prediccion():
    print("="*70)
    print("TEST DE PRECISIÓN - Charly Predictor")
    print("="*70)
    print(f"Resultado real conocido: {RESULTADO_REAL}")
    print()
    
    # Cargar datos históricos (104 sorteos reales de QuiniYa)
    loader = DataLoader()
    data = loader.load_csv('data/quini6_historico_quiniya.csv')
    print(f"Datos cargados: {len(data)} sorteos")
    print()
    
    # Ejecutar análisis
    freq = FrequencyAnalyzer()
    freq.analyze(data)
    
    corr = CorrelationAnalyzer()
    corr.analyze(data)
    
    pattern = PatternAnalyzer()
    pattern.analyze(data)
    
    print("PREDICCIONES CON DIFERENTES CONFIGURACIONES:")
    print("-"*70)
    
    resultados = []
    
    # Test 1: Método Estándar (configuración actual)
    print("\n1. MÉTODO ESTÁNDAR (default)")
    scorer = UnifiedScorer()
    scores = scorer.calculate_scores(freq)
    manager = StrategyManager()
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.STANDARD,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_std = sorted(result['combination'])
    aciertos_std = calcular_aciertos(pred_std, RESULTADO_REAL)
    print(f"   Predicción: {pred_std}")
    print(f"   Aciertos: {aciertos_std}/6")
    resultados.append(("Estándar default", pred_std, aciertos_std))
    
    # Test 2: Método Condicional (configuración actual)
    print("\n2. MÉTODO CONDICIONAL (default)")
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.CONDITIONAL,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_cond = sorted(result['combination'])
    aciertos_cond = calcular_aciertos(pred_cond, RESULTADO_REAL)
    print(f"   Predicción: {pred_cond}")
    print(f"   Aciertos: {aciertos_cond}/6")
    resultados.append(("Condicional default", pred_cond, aciertos_cond))
    
    # Test 3: Pesos ajustados - Más peso a frecuencia
    print("\n3. MÁS PESO A FRECUENCIA (freq:0.5)")
    pesos_freq = {
        'peso_frecuencia': 0.5,
        'peso_frecuencia_reciente': 0.2,
        'peso_ciclo': 0.15,
        'peso_latencia': 0.1,
        'peso_tendencia': 0.05
    }
    scorer_freq = UnifiedScorer(pesos_freq)
    scores_freq = scorer_freq.calculate_scores(freq)
    result = manager.generate(
        scores_freq,
        strategy=GenerationStrategy.STANDARD,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_freq = sorted(result['combination'])
    aciertos_freq = calcular_aciertos(pred_freq, RESULTADO_REAL)
    print(f"   Predicción: {pred_freq}")
    print(f"   Aciertos: {aciertos_freq}/6")
    resultados.append(("Más frecuencia", pred_freq, aciertos_freq))
    
    # Test 4: Pesos ajustados - Más peso a frecuencia reciente
    print("\n4. MÁS PESO A FRECUENCIA RECIENTE (freq_rec:0.5)")
    pesos_rec = {
        'peso_frecuencia': 0.1,
        'peso_frecuencia_reciente': 0.5,
        'peso_ciclo': 0.2,
        'peso_latencia': 0.15,
        'peso_tendencia': 0.05
    }
    scorer_rec = UnifiedScorer(pesos_rec)
    scores_rec = scorer_rec.calculate_scores(freq)
    result = manager.generate(
        scores_rec,
        strategy=GenerationStrategy.STANDARD,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_rec = sorted(result['combination'])
    aciertos_rec = calcular_aciertos(pred_rec, RESULTADO_REAL)
    print(f"   Predicción: {pred_rec}")
    print(f"   Aciertos: {aciertos_rec}/6")
    resultados.append(("Más frec. reciente", pred_rec, aciertos_rec))
    
    # Test 5: Pesos ajustados - Más peso a latencia
    print("\n5. MÁS PESO A LATENCIA (latencia:0.5)")
    pesos_lat = {
        'peso_frecuencia': 0.15,
        'peso_frecuencia_reciente': 0.15,
        'peso_ciclo': 0.1,
        'peso_latencia': 0.5,
        'peso_tendencia': 0.1
    }
    scorer_lat = UnifiedScorer(pesos_lat)
    scores_lat = scorer_lat.calculate_scores(freq)
    result = manager.generate(
        scores_lat,
        strategy=GenerationStrategy.STANDARD,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_lat = sorted(result['combination'])
    aciertos_lat = calcular_aciertos(pred_lat, RESULTADO_REAL)
    print(f"   Predicción: {pred_lat}")
    print(f"   Aciertos: {aciertos_lat}/6")
    resultados.append(("Más latencia", pred_lat, aciertos_lat))
    
    # Test 6: Pesos equilibrados
    print("\n6. EQUILIBRIO TOTAL (0.2 cada uno)")
    pesos_eq = {
        'peso_frecuencia': 0.2,
        'peso_frecuencia_reciente': 0.2,
        'peso_ciclo': 0.2,
        'peso_latencia': 0.2,
        'peso_tendencia': 0.2
    }
    scorer_eq = UnifiedScorer(pesos_eq)
    scores_eq = scorer_eq.calculate_scores(freq)
    result = manager.generate(
        scores_eq,
        strategy=GenerationStrategy.STANDARD,
        correlation_analyzer=corr,
        use_constraints=True
    )
    pred_eq = sorted(result['combination'])
    aciertos_eq = calcular_aciertos(pred_eq, RESULTADO_REAL)
    print(f"   Predicción: {pred_eq}")
    print(f"   Aciertos: {aciertos_eq}/6")
    resultados.append(("Equilibrio total", pred_eq, aciertos_eq))
    
    # Resumen y recomendaciones
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    
    mejor = max(resultados, key=lambda x: x[2])
    
    for nombre, pred, aciertos in sorted(resultados, key=lambda x: -x[2]):
        marca = "★" if aciertos == mejor[2] else " "
        print(f"{marca} {nombre:25s} - {aciertos}/6 aciertos - {pred}")
    
    print("\n" + "="*70)
    print("ANÁLISIS Y RECOMENDACIONES")
    print("="*70)
    
    # Analizar números más frecuentes en datos históricos
    freq_abs = freq.results['frecuencia_absoluta']
    top_freq = sorted(freq_abs.items(), key=lambda x: -x[1])[:10]
    print(f"\nNúmeros más frecuentes en histórico:")
    print(f"   {[num for num, _ in top_freq]}")
    
    # Verificar cuáles están en el resultado real
    nums_freq_en_real = [num for num, _ in top_freq if num in RESULTADO_REAL]
    print(f"\nDe los más frecuentes, están en resultado real: {nums_freq_en_real}")
    
    # Números del resultado real
    print(f"\nAnálisis del resultado real {RESULTADO_REAL}:")
    for num in RESULTADO_REAL:
        frec = freq_abs.get(num, 0)
        print(f"   {num:2d}: frecuencia histórica = {frec}")
    
    print("\n" + "="*70)
    print("RECOMENDACIONES DE PARÁMETROS:")
    print("="*70)
    
    if mejor[2] >= 4:
        print(f"✓ EXCELENTE: {mejor[0]} logró {mejor[2]}/6 aciertos")
        print(f"  Configuración recomendada detectada.")
    elif mejor[2] >= 3:
        print(f"✓ BUENO: {mejor[0]} logró {mejor[2]}/6 aciertos")
        print(f"  Configuración aceptable, puede mejorarse.")
    else:
        print(f"⚠ BAJO: Máximo {mejor[2]}/6 aciertos")
        print(f"  Se requieren ajustes significativos.")
    
    print(f"\nMejor configuración: {mejor[0]}")
    
    # Sugerencias específicas
    print("\nSugerencias de ajuste:")
    if mejor[2] < 3:
        print("  1. Aumentar peso de correlaciones (0.4-0.5)")
        print("  2. Reducir peso de patrones (0.2-0.3)")
        print("  3. Considerar ventanas de análisis más cortas (últimos 15 sorteos)")
        print("  4. Activar modo condicional siempre")
    else:
        print(f"  1. Usar configuración '{mejor[0]}' como base")
        print("  2. Ajustar ligeramente los pesos en ±0.05")
        print("  3. Validar con más sorteos conocidos")

if __name__ == "__main__":
    test_prediccion()
