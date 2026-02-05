"""
Ejemplo de uso del sistema Charly Predictor
Flujo completo desde carga de datos hasta predicción
"""

import sys
from pathlib import Path

# Agregar el directorio core al path
sys.path.insert(0, str(Path(__file__).parent))

from core.data import DataLoader, DataValidator, DataPreprocessor
from core.analysis import FrequencyAnalyzer, PatternAnalyzer, CorrelationAnalyzer
from core.scoring import UnifiedScorer, WeightManager
from core.generator import CombinationGenerator, CombinationOptimizer
from core.backtesting import Backtester, PerformanceEvaluator
from core.config import DEFAULT_WEIGHTS


def ejemplo_completo():
    """Ejemplo de uso completo del sistema"""
    
    print("\n" + "="*80)
    print(" CHARLY PREDICTOR - Sistema de Predicción de Quini 6")
    print("="*80 + "\n")
    
    # =========================================================================
    # PASO 1: CARGAR DATOS HISTÓRICOS
    # =========================================================================
    print("📂 PASO 1: Cargando datos históricos...")
    print("-" * 80)
    
    loader = DataLoader()
    
    # Intentar cargar desde CSV (si existe)
    try:
        data = loader.load_csv('data/quini6_historico.csv')
    except:
        print("⚠️  No se encontró archivo CSV. Usando datos de ejemplo...")
        # Generar datos de ejemplo
        from utils.data_generator import generate_sample_data
        sample_sorteos = generate_sample_data(num_sorteos=200)
        data = loader.load_from_list(sample_sorteos)
    
    print(f"✓ Datos cargados: {len(data)} sorteos")
    print(f"  Rango: {data['fecha'].min()} a {data['fecha'].max()}\n")
    
    # =========================================================================
    # PASO 2: VALIDAR Y PREPROCESAR
    # =========================================================================
    print("🔍 PASO 2: Validando y preprocesando datos...")
    print("-" * 80)
    
    validator = DataValidator()
    is_valid, errors, warnings = validator.validate(data)
    
    if errors:
        print("❌ Errores encontrados:")
        for error in errors[:5]:  # Mostrar solo primeros 5
            print(f"  - {error}")
        return
    
    if warnings:
        print("⚠️  Advertencias:")
        for warning in warnings[:3]:
            print(f"  - {warning}")
    
    # Limpiar datos
    data = validator.clean_data(data)
    
    # Preprocesar (calcular features)
    preprocessor = DataPreprocessor()
    data_processed = preprocessor.process(data)
    
    print(f"✓ Datos validados y preprocesados\n")
    
    # =========================================================================
    # PASO 3: ANÁLISIS ESTADÍSTICO
    # =========================================================================
    print("📊 PASO 3: Ejecutando análisis estadísticos...")
    print("-" * 80)
    
    # Análisis de frecuencias
    freq_analyzer = FrequencyAnalyzer()
    freq_results = freq_analyzer.analyze(data)
    
    print("✓ Análisis de frecuencias completado")
    print(f"  Top 5 números calientes: {[n for n, _ in freq_results['numeros_calientes'][:5]]}")
    print(f"  Top 5 números fríos: {[n for n, _ in freq_results['numeros_frios'][:5]]}")
    
    # Análisis de patrones
    pattern_analyzer = PatternAnalyzer()
    pattern_results = pattern_analyzer.analyze(data)
    
    print("✓ Análisis de patrones completado")
    
    # Análisis de correlaciones
    corr_analyzer = CorrelationAnalyzer()
    corr_results = corr_analyzer.analyze(data)
    
    print("✓ Análisis de correlaciones completado")
    if corr_results['pares_frecuentes']:
        top_pair = corr_results['pares_frecuentes'][0]
        print(f"  Par más frecuente: {top_pair[0]} (aparece {top_pair[1]} veces)")
    
    print()
    
    # =========================================================================
    # PASO 4: SCORING CON PESOS CONFIGURABLES
    # =========================================================================
    print("🎯 PASO 4: Calculando scores con sistema de ponderación...")
    print("-" * 80)
    
    scorer = UnifiedScorer(DEFAULT_WEIGHTS)
    scores = scorer.calculate_scores(freq_analyzer, pattern_analyzer, corr_analyzer)
    
    top_numbers = scorer.get_top_numbers(10)
    
    print("✓ Scores calculados para todos los números")
    print("\n  Top 10 números por score:")
    for i, (num, score) in enumerate(top_numbers, 1):
        print(f"    {i:2d}. Número {num:2d} - Score: {score:.4f}")
    
    print()
    
    # =========================================================================
    # PASO 5: GENERAR COMBINACIONES
    # =========================================================================
    print("🎲 PASO 5: Generando combinaciones candidatas...")
    print("-" * 80)
    
    generator = CombinationGenerator()
    
    # Combinación simple (top 6)
    simple_combination = generator.generate_simple(scores, top_n=1)[0]
    print(f"  Combinación simple (top 6): {simple_combination}")
    
    # Combinación con restricciones
    constrained_combination = generator.generate_with_constraints(scores)
    analysis = generator.analyze_combination(constrained_combination)
    
    print(f"  Combinación con restricciones: {constrained_combination}")
    print(f"    - Suma: {analysis['suma_total']}")
    print(f"    - Pares/Impares: {analysis['pares']}/{analysis['impares']}")
    print(f"    - Consecutivos: {analysis['consecutivos']}")
    print(f"    - Distribución: Bajos={analysis['distribucion']['bajos']}, "
          f"Medios={analysis['distribucion']['medios']}, Altos={analysis['distribucion']['altos']}")
    
    # Portfolio de combinaciones
    portfolio = generator.generate_portfolio(scores, portfolio_size=5)
    print(f"\n  Portfolio de {len(portfolio)} combinaciones generado")
    
    print()
    
    # =========================================================================
    # PASO 6: BACKTESTING (Validación)
    # =========================================================================
    print("✅ PASO 6: Ejecutando backtesting...")
    print("-" * 80)
    
    backtester = Backtester(test_size=20)
    
    try:
        summary = backtester.run_backtest(data, weights=DEFAULT_WEIGHTS)
        backtester.print_results()
    except ValueError as e:
        print(f"⚠️  No hay suficientes datos para backtesting: {e}")
        print("    Se requieren al menos 120 sorteos históricos\n")
    
    # =========================================================================
    # PASO 7: PREDICCIÓN FINAL
    # =========================================================================
    print("🔮 PASO 7: Generando predicción final para próximo sorteo...")
    print("-" * 80)
    
    # Usar optimización genética para mejor resultado
    optimizer = CombinationOptimizer()
    optimized = optimizer.genetic_algorithm(
        scores, 
        population_size=50,
        generations=30,
        mutation_rate=0.1
    )
    
    print(f"\n  🎯 PREDICCIÓN FINAL (Optimizada): {optimized}")
    
    # Análisis de la predicción
    final_analysis = generator.analyze_combination(optimized)
    print(f"\n  Características de la predicción:")
    print(f"    - Suma total: {final_analysis['suma_total']}")
    print(f"    - Pares: {final_analysis['pares']}, Impares: {final_analysis['impares']}")
    print(f"    - Consecutivos: {final_analysis['consecutivos']}")
    print(f"    - Score promedio: {final_analysis['score_promedio']:.4f}")
    print(f"    - Cumple restricciones: {'✓ Sí' if final_analysis['cumple_restricciones'] else '✗ No'}")
    
    print(f"\n  📋 Top 3 combinaciones alternativas:")
    for i, comb in enumerate(portfolio[:3], 1):
        print(f"    {i}. {comb}")
    
    print("\n" + "="*80)
    print(" Sistema ejecutado exitosamente")
    print("="*80 + "\n")


def ejemplo_ajuste_pesos():
    """Ejemplo de cómo ajustar pesos y comparar resultados"""
    
    print("\n" + "="*80)
    print(" EJEMPLO: Comparación de diferentes configuraciones de pesos")
    print("="*80 + "\n")
    
    # Cargar datos
    loader = DataLoader()
    try:
        data = loader.load_csv('data/quini6_historico.csv')
    except:
        from utils.data_generator import generate_sample_data
        sample_sorteos = generate_sample_data(num_sorteos=200)
        data = loader.load_from_list(sample_sorteos)
    
    # Crear diferentes configuraciones de pesos
    configs = [
        {
            'name': 'Balanceado',
            'weights': {
                'peso_frecuencia': 0.25,
                'peso_frecuencia_reciente': 0.25,
                'peso_ciclo': 0.20,
                'peso_latencia': 0.15,
                'peso_tendencia': 0.15,
            }
        },
        {
            'name': 'Enfoque Frecuencia',
            'weights': {
                'peso_frecuencia': 0.50,
                'peso_frecuencia_reciente': 0.25,
                'peso_ciclo': 0.10,
                'peso_latencia': 0.10,
                'peso_tendencia': 0.05,
            }
        },
        {
            'name': 'Enfoque Reciente',
            'weights': {
                'peso_frecuencia': 0.15,
                'peso_frecuencia_reciente': 0.40,
                'peso_ciclo': 0.15,
                'peso_latencia': 0.20,
                'peso_tendencia': 0.10,
            }
        }
    ]
    
    # Comparar configuraciones
    backtester = Backtester(test_size=20)
    
    try:
        weights_list = [config['weights'] for config in configs]
        names = [config['name'] for config in configs]
        
        comparison = backtester.compare_weights(data, weights_list, names)
        
        print("Comparación de configuraciones:")
        print(comparison.to_string(index=False))
        
        print(f"\n✓ Mejor configuración: {comparison.iloc[0]['configuracion']}")
        
    except ValueError as e:
        print(f"⚠️  No hay suficientes datos para comparación: {e}\n")


if __name__ == "__main__":
    # Ejecutar ejemplo completo
    ejemplo_completo()
    
    # Descomentar para ver comparación de pesos
    # ejemplo_ajuste_pesos()
