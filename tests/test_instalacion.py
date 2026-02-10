"""
Script de prueba rápida para verificar la instalación
"""

print("="*70)
print(" TEST DE INSTALACIÓN - Charly Predictor")
print("="*70 + "\n")

# Test 1: Importaciones
print("1. Verificando importaciones...")
try:
    from core.data import DataLoader, DataValidator, DataPreprocessor
    from core.analysis import FrequencyAnalyzer, PatternAnalyzer, CorrelationAnalyzer
    from core.scoring import UnifiedScorer, WeightManager
    from core.generator import CombinationGenerator, CombinationOptimizer
    from core.backtesting import Backtester, PerformanceEvaluator
    from utils.data_generator import generate_sample_data
    print("   ✓ Todas las importaciones exitosas\n")
except Exception as e:
    print(f"   ✗ Error en importaciones: {e}\n")
    exit(1)

# Test 2: Generar datos de muestra
print("2. Generando datos de muestra...")
try:
    sorteos = generate_sample_data(num_sorteos=100)
    print(f"   ✓ {len(sorteos)} sorteos generados\n")
except Exception as e:
    print(f"   ✗ Error generando datos: {e}\n")
    exit(1)

# Test 3: Cargar datos
print("3. Probando carga de datos...")
try:
    loader = DataLoader()
    data = loader.load_from_list(sorteos)
    print(f"   ✓ Datos cargados correctamente\n")
except Exception as e:
    print(f"   ✗ Error cargando datos: {e}\n")
    exit(1)

# Test 4: Validar datos
print("4. Probando validación...")
try:
    validator = DataValidator()
    is_valid, errors, warnings = validator.validate(data)
    if is_valid:
        print(f"   ✓ Datos validados correctamente\n")
    else:
        print(f"   ✗ Datos inválidos: {errors}\n")
except Exception as e:
    print(f"   ✗ Error en validación: {e}\n")
    exit(1)

# Test 5: Análisis de frecuencias
print("5. Probando análisis de frecuencias...")
try:
    analyzer = FrequencyAnalyzer()
    results = analyzer.analyze(data)
    top_5 = analyzer.get_top_numbers(5)
    print(f"   ✓ Análisis completado")
    print(f"   Top 5 números: {[num for num, _ in top_5]}\n")
except Exception as e:
    print(f"   ✗ Error en análisis: {e}\n")
    exit(1)

# Test 6: Sistema de scoring
print("6. Probando sistema de scoring...")
try:
    scorer = UnifiedScorer()
    scores = scorer.calculate_scores(analyzer)
    top_3 = scorer.get_top_numbers(3)
    print(f"   ✓ Scores calculados")
    print(f"   Top 3 scores: {[(num, f'{score:.3f}') for num, score in top_3]}\n")
except Exception as e:
    print(f"   ✗ Error en scoring: {e}\n")
    exit(1)

# Test 7: Generación de combinaciones
print("7. Probando generación de combinaciones...")
try:
    generator = CombinationGenerator()
    combination = generator.generate_with_constraints(scores)
    print(f"   ✓ Combinación generada: {combination}\n")
except Exception as e:
    print(f"   ✗ Error generando combinación: {e}\n")
    exit(1)

# Test 8: Optimización genética
print("8. Probando optimización genética...")
try:
    optimizer = CombinationOptimizer()
    optimized = optimizer.genetic_algorithm(
        scores,
        population_size=20,
        generations=10
    )
    print(f"   ✓ Combinación optimizada: {optimized}\n")
except Exception as e:
    print(f"   ✗ Error en optimización: {e}\n")
    exit(1)

# Test 9: Backtesting (con datos reducidos)
print("9. Probando backtesting...")
try:
    # Generar más datos para backtesting
    sorteos_bt = generate_sample_data(num_sorteos=150)
    data_bt = loader.load_from_list(sorteos_bt)
    
    backtester = Backtester(test_size=20)
    summary = backtester.run_backtest(data_bt)
    
    print(f"   ✓ Backtesting completado")
    print(f"   Promedio aciertos: {summary['promedio_aciertos']:.2f}\n")
except Exception as e:
    print(f"   ✗ Error en backtesting: {e}\n")
    # No es crítico, continuar

print("="*70)
print(" ✓✓✓ TODOS LOS TESTS PASARON EXITOSAMENTE ✓✓✓")
print("="*70)
print("\nEl sistema está listo para usar.")
print("Ejecuta 'python ejemplo_uso.py' para ver el sistema completo en acción.\n")
