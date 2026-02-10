"""
Script para usar la configuración optimizada y generar predicciones

Ejemplo de uso:
    python usar_config_optimizada.py

Genera predicciones usando los parámetros óptimos encontrados durante
la optimización exhaustiva.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, PatternAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy, CombinationGenerator
from configs.config_optimizada import get_optimal_config, print_config_summary


def generar_prediccion_optimizada(archivo_csv='data/quini6_historico_test.csv', 
                                   num_combinaciones=5):
    """
    Genera predicciones usando la configuración óptima
    
    Args:
        archivo_csv: Ruta al archivo CSV con datos históricos
        num_combinaciones: Número de combinaciones a generar (portfolio)
    
    Returns:
        dict: Resultados con predicción principal y alternativas
    """
    print("\n" + "="*80)
    print(" PREDICTOR CON CONFIGURACIÓN OPTIMIZADA")
    print("="*80)
    
    # Mostrar configuración
    print_config_summary()
    
    # Cargar configuración óptima
    config = get_optimal_config()
    
    # Cargar datos
    print("📂 Cargando datos históricos...")
    loader = DataLoader()
    try:
        data = loader.load_csv(archivo_csv)
        # Filtrar hasta la fecha de corte (si hay datos futuros)
        # data = data[data['sorteo_id'] <= 412].copy()
        print(f"   ✓ {len(data)} sorteos cargados")
        print(f"   Rango: {data['fecha'].min()} a {data['fecha'].max()}")
    except Exception as e:
        print(f"   ⚠️ Error al cargar CSV: {e}")
        print("   Generando datos de ejemplo...")
        from utils.data_generator import generate_sample_data
        sample_sorteos = generate_sample_data(num_sorteos=200)
        data = loader.load_from_list(sample_sorteos)
    
    # Análisis
    print("\n📊 Ejecutando análisis estadísticos...")
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    pattern_analyzer = None
    if config['use_pattern_analysis']:
        pattern_analyzer = PatternAnalyzer()
        pattern_analyzer.analyze(data)
    
    print("   ✓ Análisis completado")
    
    # Scoring con pesos óptimos
    print("\n🎯 Calculando scores con configuración óptima...")
    scorer = UnifiedScorer(config['weights'])
    
    if pattern_analyzer:
        scores = scorer.calculate_scores(freq_analyzer, pattern_analyzer, corr_analyzer)
    else:
        scores = scorer.calculate_scores(freq_analyzer)
    
    top_numbers = scorer.get_top_numbers(15)
    print("   ✓ Scores calculados")
    print("\n   Top 15 números por score:")
    for i, (num, score) in enumerate(top_numbers, 1):
        bar = "█" * int(score * 30)
        print(f"      {i:2d}. Número {num:2d} - Score: {score:.4f} {bar}")
    
    # Generar predicción principal
    print("\n🎲 Generando predicción principal...")
    manager = StrategyManager()
    
    if config['strategy'] == 'BOTH':
        resultado = manager.generate_side_by_side(scores, corr_analyzer)
        pred_std = sorted(resultado['standard'])
        pred_cond = sorted(resultado['conditional'])
        
        print("\n" + "="*80)
        print(" PREDICCIONES GENERADAS")
        print("="*80)
        
        print(f"\n🎯 MÉTODO ESTÁNDAR:")
        print(f"   Combinación: {pred_std}")
        
        print(f"\n🎯 MÉTODO CONDICIONAL:")
        print(f"   Combinación: {pred_cond}")
        
        prediccion_principal = pred_std  # Usar estándar como principal
        
    else:
        resultado = manager.generate(
            scores,
            strategy=GenerationStrategy.STANDARD if config['strategy'] == 'STANDARD' else GenerationStrategy.CONDITIONAL,
            correlation_analyzer=corr_analyzer if config['strategy'] == 'CONDITIONAL' else None,
            use_constraints=config['use_constraints']
        )
        prediccion_principal = sorted(resultado['combination'])
        
        print("\n" + "="*80)
        print(f" PREDICCIÓN ({config['strategy']})")
        print("="*80)
        print(f"\n🎯 {prediccion_principal}")
    
    # Generar portfolio de alternativas
    print("\n📋 Generando portfolio de combinaciones alternativas...")
    generator = CombinationGenerator()
    portfolio = generator.generate_portfolio(scores, portfolio_size=num_combinaciones)
    
    print(f"\n   Portfolio de {len(portfolio)} combinaciones:")
    for i, comb in enumerate(portfolio, 1):
        analysis = generator.analyze_combination(comb)
        print(f"      {i}. {sorted(comb)} (Suma: {analysis['suma_total']}, Score: {analysis['score_promedio']:.3f})")
    
    # Resumen final
    print("\n" + "="*80)
    print(" 🎯 PREDICCIÓN FINAL RECOMENDADA")
    print("="*80)
    print(f"\n   {prediccion_principal}")
    print("\n" + "="*80 + "\n")
    
    return {
        'principal': prediccion_principal,
        'metodo_estandar': pred_std if config['strategy'] == 'BOTH' else None,
        'metodo_condicional': pred_cond if config['strategy'] == 'BOTH' else None,
        'portfolio': portfolio,
        'top_numbers': top_numbers,
        'config_usada': config
    }


if __name__ == "__main__":
    # Generar predicción
    resultados = generar_prediccion_optimizada()
    
    print("\n💡 Tip: Puedes modificar los parámetros en configs/config_optimizada.py")
    print("   para experimentar con diferentes configuraciones.\n")
