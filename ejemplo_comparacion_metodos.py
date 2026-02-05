"""
Ejemplo de comparación entre métodos de generación:
- Método Estándar (Probabilidades Estáticas)
- Método Condicional (Probabilidades Dinámicas con Correlaciones)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy


def ejemplo_comparacion_metodos():
    """Compara los dos métodos de generación"""
    
    print("\n" + "="*80)
    print(" COMPARACIÓN DE MÉTODOS DE GENERACIÓN")
    print("="*80 + "\n")
    
    # =========================================================================
    # PASO 1: Preparar datos y análisis
    # =========================================================================
    print("📂 Preparando sistema...")
    
    loader = DataLoader()
    
    try:
        data = loader.load_csv('data/quini6_historico.csv')
    except:
        print("Generando datos de muestra...")
        from utils.data_generator import generate_sample_data
        sample_sorteos = generate_sample_data(num_sorteos=200)
        data = loader.load_from_list(sample_sorteos)
    
    # Análisis
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    # Scoring
    scorer = UnifiedScorer()
    scores = scorer.calculate_scores(freq_analyzer)
    
    print("✓ Sistema preparado\n")
    
    # =========================================================================
    # PASO 2: Crear gestor de estrategias
    # =========================================================================
    manager = StrategyManager()
    
    # =========================================================================
    # PASO 3: Generar con MÉTODO ESTÁNDAR
    # =========================================================================
    print("\n" + "="*80)
    print(" MÉTODO 1: ESTÁNDAR (Probabilidades Estáticas)")
    print("="*80)
    print("\nCARACTERÍSTICAS:")
    print("- Selecciona 6 números de una vez")
    print("- Probabilidades fijas basadas en scores individuales")
    print("- NO considera correlaciones durante la generación")
    print("- MÁS RÁPIDO\n")
    
    result_standard = manager.generate(
        scores,
        strategy=GenerationStrategy.STANDARD,
        use_constraints=True
    )
    
    print(f"🎯 RESULTADO MÉTODO ESTÁNDAR:")
    print(f"   Combinación: {result_standard['combination']}")
    print(f"   Suma: {result_standard['analysis']['suma_total']}")
    print(f"   Score promedio: {result_standard['analysis']['score_promedio']:.4f}")
    print(f"   Pares/Impares: {result_standard['analysis']['pares']}/{result_standard['analysis']['impares']}")
    print(f"   Consecutivos: {result_standard['analysis']['consecutivos']}\n")
    
    # =========================================================================
    # PASO 4: Generar con MÉTODO CONDICIONAL
    # =========================================================================
    print("\n" + "="*80)
    print(" MÉTODO 2: CONDICIONAL (Probabilidades Dinámicas)")
    print("="*80)
    print("\nCARACTERÍSTICAS:")
    print("- Selecciona números SECUENCIALMENTE (uno por uno)")
    print("- Recalcula probabilidades después de cada selección")
    print("- Considera correlaciones con números ya seleccionados")
    print("- Ajusta scores dinámicamente")
    print("- MÁS INTELIGENTE (pero más lento)\n")
    
    result_conditional = manager.generate(
        scores,
        strategy=GenerationStrategy.CONDITIONAL,
        correlation_analyzer=corr_analyzer,
        use_constraints=True
    )
    
    print(f"🎯 RESULTADO MÉTODO CONDICIONAL:")
    print(f"   Combinación: {result_conditional['combination']}")
    print(f"   Suma: {result_conditional['analysis']['suma_total']}")
    print(f"   Score promedio: {result_conditional['analysis']['score_promedio']:.4f}")
    print(f"   Correlation Score: {result_conditional['analysis']['correlation_score']:.4f}")
    print(f"   Pares/Impares: {result_conditional['analysis']['pares']}/{result_conditional['analysis']['impares']}")
    print(f"   Consecutivos: {result_conditional['analysis']['consecutivos']}\n")
    
    # =========================================================================
    # PASO 5: Comparación lado a lado
    # =========================================================================
    print("\n" + "="*80)
    print(" COMPARACIÓN LADO A LADO")
    print("="*80 + "\n")
    
    manager.generate_side_by_side(scores, corr_analyzer)
    
    # =========================================================================
    # PASO 6: Comparación estadística (múltiples generaciones)
    # =========================================================================
    print("\n" + "="*80)
    print(" COMPARACIÓN ESTADÍSTICA")
    print("="*80 + "\n")
    
    comparison = manager.compare_strategies(
        scores,
        correlation_analyzer=corr_analyzer,
        num_iterations=20
    )
    
    # =========================================================================
    # CONCLUSIÓN
    # =========================================================================
    print("\n" + "="*80)
    print(" CONCLUSIÓN")
    print("="*80 + "\n")
    
    print("¿Cuál método usar?")
    print("-" * 40)
    print("\n📊 MÉTODO ESTÁNDAR:")
    print("  ✓ Más rápido")
    print("  ✓ Más simple de entender")
    print("  ✓ Bueno para generar muchas combinaciones rápido")
    print("  ✓ Usa scores individuales de cada número")
    
    print("\n📊 MÉTODO CONDICIONAL:")
    print("  ✓ Considera correlaciones históricas")
    print("  ✓ Genera combinaciones más 'coherentes' con patrones")
    print("  ✓ Ajusta probabilidades dinámicamente")
    print("  ✓ Potencialmente más preciso")
    print("  ✗ Más lento (especialmente para portfolios grandes)")
    
    print("\n💡 RECOMENDACIÓN:")
    print("  - Usa AMBOS y compara resultados")
    print("  - Para análisis rápidos: Método Estándar")
    print("  - Para predicción final: Método Condicional")
    print("  - Genera portfolio con ambos métodos para mayor cobertura")
    
    print("\n" + "="*80 + "\n")


def ejemplo_switch_entre_metodos():
    """Muestra cómo hacer switch entre métodos"""
    
    print("\n" + "="*80)
    print(" EJEMPLO: SWITCH ENTRE MÉTODOS")
    print("="*80 + "\n")
    
    # Preparar (simplificado)
    loader = DataLoader()
    from utils.data_generator import generate_sample_data
    data = loader.load_from_list(generate_sample_data(150))
    
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    scorer = UnifiedScorer()
    scores = scorer.calculate_scores(freq_analyzer)
    
    # Crear manager
    manager = StrategyManager()
    
    print("Simulación de selección por usuario:\n")
    
    # Usuario elige método 1
    print("👤 Usuario elige: MÉTODO ESTÁNDAR")
    manager.set_strategy(GenerationStrategy.STANDARD)
    result1 = manager.generate(scores)
    print(f"   → Combinación: {result1['combination']}\n")
    
    # Usuario cambia a método 2
    print("👤 Usuario cambia a: MÉTODO CONDICIONAL")
    manager.set_strategy(GenerationStrategy.CONDITIONAL)
    result2 = manager.generate(scores, correlation_analyzer=corr_analyzer)
    print(f"   → Combinación: {result2['combination']}\n")
    
    # Usuario pide ambos
    print("👤 Usuario selecciona: AMBOS MÉTODOS")
    manager.set_strategy(GenerationStrategy.BOTH)
    results = manager.generate(scores, correlation_analyzer=corr_analyzer)
    print(f"   → Estándar:    {results['standard']['combination']}")
    print(f"   → Condicional: {results['conditional']['combination']}\n")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    # Ejecutar comparación completa
    ejemplo_comparacion_metodos()
    
    # Mostrar cómo hacer switch
    ejemplo_switch_entre_metodos()
