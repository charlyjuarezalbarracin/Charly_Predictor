"""
Test del sistema de estrategias de generación
Prueba ambos métodos: Estándar y Condicional

BACKTESTING REAL:
- Usa datos históricos hasta sorteo 412 (2026-02-04)
- Predice los 4 sorteos del 2026-02-08 (sorteos 413-416)
- Compara predicciones vs resultados reales
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy, ConditionalGenerator
from utils.data_generator import generate_sample_data


def test_backtesting_real():
    """
    TEST DE BACKTESTING REAL CON DATOS DEL 2026-02-08
    
    Objetivo: Predecir los 4 sorteos reales usando datos históricos
    
    Sorteos a predecir (2026-02-08):
    - Sorteo 413: [23, 44, 45, 18, 40, 24]
    - Sorteo 414: [2, 0, 38, 13, 12, 25]
    - Sorteo 415: [39, 21, 4, 17, 20, 37]
    - Sorteo 416: [23, 4, 32, 37, 38, 7]
    """
    print("\n" + "="*80)
    print(" TEST BACKTESTING REAL - Predicción 2026-02-08")
    print("="*80)
    
    # RESULTADOS REALES A PREDECIR
    RESULTADOS_REALES = [
        {'sorteo_id': 413, 'fecha': '2026-02-08', 'numeros': [23, 44, 45, 18, 40, 24]},
        {'sorteo_id': 414, 'fecha': '2026-02-08', 'numeros': [2, 0, 38, 13, 12, 25]},
        {'sorteo_id': 415, 'fecha': '2026-02-08', 'numeros': [39, 21, 4, 17, 20, 37]},
        {'sorteo_id': 416, 'fecha': '2026-02-08', 'numeros': [23, 4, 32, 37, 38, 7]},
    ]
    
    try:
        # 1. Cargar datos históricos (hasta sorteo 412)
        print("\n1. Cargando datos históricos...")
        loader = DataLoader()
        
        try:
            # Cargar CSV completo
            data_full = loader.load_csv('data/quini6_historico_test.csv')
            
            # Filtrar solo hasta sorteo 412 (excluir los 4 últimos para test)
            data = data_full[data_full['sorteo_id'] <= 412].copy()
            
            print(f"   ✓ Datos cargados: {len(data)} sorteos")
            print(f"   ✓ Rango: {data['fecha'].min()} a {data['fecha'].max()}")
            print(f"   ✓ Último sorteo: {data['sorteo_id'].max()}")
            
        except Exception as e:
            print(f"   ✗ Error al cargar CSV: {e}")
            print("   Usando datos de ejemplo...")
            sorteos = generate_sample_data(num_sorteos=200)
            data = loader.load_from_list(sorteos)
        
        # 2. Análisis completo
        print("\n2. Ejecutando análisis estadísticos...")
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(data)
        
        corr_analyzer = CorrelationAnalyzer()
        corr_analyzer.analyze(data)
        
        scorer = UnifiedScorer()
        scores = scorer.calculate_scores(freq_analyzer)
        print("   ✓ Análisis completado")
        
        # 3. Crear manager
        print("\n3. Preparando sistema de predicción...")
        manager = StrategyManager()
        print("   ✓ Sistema listo")
        
        # 4. Generar predicciones para cada sorteo
        print("\n" + "="*80)
        print(" GENERANDO PREDICCIONES Y COMPARANDO CON RESULTADOS REALES")
        print("="*80)
        
        resultados_test = []
        
        for i, resultado_real in enumerate(RESULTADOS_REALES, 1):
            print(f"\n{'─'*80}")
            print(f"SORTEO {resultado_real['sorteo_id']} - {resultado_real['fecha']}")
            print(f"{'─'*80}")
            
            # Generar predicción con ambos métodos
            predicciones = manager.generate_side_by_side(scores, corr_analyzer)
            
            pred_standard = sorted(predicciones['standard'])
            pred_conditional = sorted(predicciones['conditional'])
            real = sorted(resultado_real['numeros'])
            
            # Calcular aciertos
            aciertos_std = len(set(pred_standard) & set(real))
            aciertos_cond = len(set(pred_conditional) & set(real))
            
            print(f"\nResultado REAL:          {real}")
            print(f"Predicción ESTÁNDAR:     {pred_standard}  → {aciertos_std}/6 aciertos")
            print(f"Predicción CONDICIONAL:  {pred_conditional}  → {aciertos_cond}/6 aciertos")
            
            # Mostrar números acertados
            if aciertos_std > 0:
                acertados_std = set(pred_standard) & set(real)
                print(f"  ✓ Estándar acertó: {sorted(acertados_std)}")
            
            if aciertos_cond > 0:
                acertados_cond = set(pred_conditional) & set(real)
                print(f"  ✓ Condicional acertó: {sorted(acertados_cond)}")
            
            # Guardar resultados
            resultados_test.append({
                'sorteo': resultado_real['sorteo_id'],
                'real': real,
                'pred_standard': pred_standard,
                'pred_conditional': pred_conditional,
                'aciertos_standard': aciertos_std,
                'aciertos_conditional': aciertos_cond,
            })
        
        # 5. Resumen estadístico
        print("\n" + "="*80)
        print(" RESUMEN DEL BACKTESTING")
        print("="*80)
        
        total_sorteos = len(resultados_test)
        total_aciertos_std = sum(r['aciertos_standard'] for r in resultados_test)
        total_aciertos_cond = sum(r['aciertos_conditional'] for r in resultados_test)
        
        promedio_std = total_aciertos_std / total_sorteos
        promedio_cond = total_aciertos_cond / total_sorteos
        
        print(f"\nTotal de sorteos evaluados: {total_sorteos}")
        print(f"\nMÉTODO ESTÁNDAR:")
        print(f"  - Total aciertos: {total_aciertos_std}/{total_sorteos * 6}")
        print(f"  - Promedio: {promedio_std:.2f} aciertos por sorteo")
        print(f"  - Porcentaje: {(promedio_std/6)*100:.1f}%")
        
        print(f"\nMÉTODO CONDICIONAL:")
        print(f"  - Total aciertos: {total_aciertos_cond}/{total_sorteos * 6}")
        print(f"  - Promedio: {promedio_cond:.2f} aciertos por sorteo")
        print(f"  - Porcentaje: {(promedio_cond/6)*100:.1f}%")
        
        # Mejor método
        if promedio_std > promedio_cond:
            print(f"\n🏆 GANADOR: Método ESTÁNDAR (+{promedio_std - promedio_cond:.2f} aciertos)")
        elif promedio_cond > promedio_std:
            print(f"\n🏆 GANADOR: Método CONDICIONAL (+{promedio_cond - promedio_std:.2f} aciertos)")
        else:
            print(f"\n🤝 EMPATE: Ambos métodos igual de efectivos")
        
        # Chequear si alguno acertó 6/6
        sorteos_6_std = [r for r in resultados_test if r['aciertos_standard'] == 6]
        sorteos_6_cond = [r for r in resultados_test if r['aciertos_conditional'] == 6]
        
        if sorteos_6_std:
            print(f"\n🎰 ¡PREMIO MAYOR! Estándar acertó 6/6 en sorteo(s): {[r['sorteo'] for r in sorteos_6_std]}")
        
        if sorteos_6_cond:
            print(f"\n🎰 ¡PREMIO MAYOR! Condicional acertó 6/6 en sorteo(s): {[r['sorteo'] for r in sorteos_6_cond]}")
        
        print("\n" + "="*80)
        
        # Validación básica
        assert len(resultados_test) == 4, "Deben evaluarse 4 sorteos"
        
        print("\n✅ TEST BACKTESTING REAL COMPLETADO\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST BACKTESTING FALLIDO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_conditional_generator():
    """Test del generador condicional"""
    print("\n" + "="*70)
    print(" TEST 1: Generador Condicional")
    print("="*70)
    
    try:
        # Preparar datos
        print("\n1. Preparando datos de prueba...")
        sorteos = generate_sample_data(num_sorteos=150)
        loader = DataLoader()
        data = loader.load_from_list(sorteos)
        print("   ✓ Datos preparados")
        
        # Análisis
        print("\n2. Ejecutando análisis...")
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(data)
        
        corr_analyzer = CorrelationAnalyzer()
        corr_analyzer.analyze(data)
        print("   ✓ Análisis completados")
        
        # Scoring
        print("\n3. Calculando scores...")
        scorer = UnifiedScorer()
        scores = scorer.calculate_scores(freq_analyzer)
        print("   ✓ Scores calculados")
        
        # Generar con método condicional
        print("\n4. Generando con método condicional...")
        cond_gen = ConditionalGenerator()
        combination = cond_gen.generate(scores, corr_analyzer)
        
        # Validar
        assert len(combination) == 6, f"Debe generar 6 números, generó {len(combination)}"
        assert len(set(combination)) == 6, "No debe haber números duplicados"
        assert all(0 <= n <= 45 for n in combination), "Números fuera de rango"
        
        print(f"   ✓ Combinación generada: {combination}")
        
        # Analizar combinación
        print("\n5. Analizando combinación...")
        analysis = cond_gen.analyze_combination(combination)
        print(f"   ✓ Suma: {analysis['suma_total']}")
        print(f"   ✓ Score promedio: {analysis['score_promedio']:.4f}")
        print(f"   ✓ Correlation score: {analysis['correlation_score']:.4f}")
        
        # Generar con restricciones
        print("\n6. Generando con restricciones...")
        comb_constrained = cond_gen.generate_with_constraints(scores, corr_analyzer)
        assert len(comb_constrained) == 6, "Debe generar 6 números"
        assert len(set(comb_constrained)) == 6, "No debe haber duplicados"
        print(f"   ✓ Combinación con restricciones: {comb_constrained}")
        
        # Portfolio
        print("\n7. Generando portfolio...")
        portfolio = cond_gen.generate_portfolio(scores, corr_analyzer, portfolio_size=5)
        assert len(portfolio) == 5, "Portfolio debe tener 5 combinaciones"
        assert all(len(c) == 6 for c in portfolio), "Cada combinación debe tener 6 números"
        print(f"   ✓ Portfolio de {len(portfolio)} combinaciones generado")
        
        print("\n✅ TEST 1 PASADO: Generador Condicional funciona correctamente\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FALLIDO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_manager():
    """Test del gestor de estrategias"""
    print("\n" + "="*70)
    print(" TEST 2: Gestor de Estrategias")
    print("="*70)
    
    try:
        # Preparar
        print("\n1. Preparando datos...")
        sorteos = generate_sample_data(num_sorteos=150)
        loader = DataLoader()
        data = loader.load_from_list(sorteos)
        
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(data)
        
        corr_analyzer = CorrelationAnalyzer()
        corr_analyzer.analyze(data)
        
        scorer = UnifiedScorer()
        scores = scorer.calculate_scores(freq_analyzer)
        print("   ✓ Datos preparados")
        
        # Crear manager
        print("\n2. Creando StrategyManager...")
        manager = StrategyManager()
        print("   ✓ Manager creado")
        
        # Test método STANDARD
        print("\n3. Probando estrategia STANDARD...")
        result_std = manager.generate(
            scores,
            strategy=GenerationStrategy.STANDARD,
            use_constraints=True
        )
        
        assert result_std['method'] == 'standard', "Método debe ser 'standard'"
        assert 'combination' in result_std, "Debe tener 'combination'"
        assert 'analysis' in result_std, "Debe tener 'analysis'"
        assert len(result_std['combination']) == 6, "Debe tener 6 números"
        
        print(f"   ✓ STANDARD: {result_std['combination']}")
        
        # Test método CONDITIONAL
        print("\n4. Probando estrategia CONDITIONAL...")
        result_cond = manager.generate(
            scores,
            strategy=GenerationStrategy.CONDITIONAL,
            correlation_analyzer=corr_analyzer,
            use_constraints=True
        )
        
        assert result_cond['method'] == 'conditional', "Método debe ser 'conditional'"
        assert 'combination' in result_cond, "Debe tener 'combination'"
        assert 'analysis' in result_cond, "Debe tener 'analysis'"
        assert len(result_cond['combination']) == 6, "Debe tener 6 números"
        
        print(f"   ✓ CONDITIONAL: {result_cond['combination']}")
        
        # Test estrategia BOTH
        print("\n5. Probando estrategia BOTH...")
        result_both = manager.generate(
            scores,
            strategy=GenerationStrategy.BOTH,
            correlation_analyzer=corr_analyzer,
            use_constraints=True
        )
        
        assert 'standard' in result_both, "Debe tener resultado 'standard'"
        assert 'conditional' in result_both, "Debe tener resultado 'conditional'"
        assert len(result_both['standard']['combination']) == 6, "Standard debe tener 6 números"
        assert len(result_both['conditional']['combination']) == 6, "Conditional debe tener 6 números"
        
        print(f"   ✓ STANDARD:    {result_both['standard']['combination']}")
        print(f"   ✓ CONDITIONAL: {result_both['conditional']['combination']}")
        
        # Test switch de estrategias
        print("\n6. Probando cambio de estrategia...")
        manager.set_strategy(GenerationStrategy.STANDARD)
        assert manager.current_strategy == GenerationStrategy.STANDARD
        
        manager.set_strategy(GenerationStrategy.CONDITIONAL)
        assert manager.current_strategy == GenerationStrategy.CONDITIONAL
        
        print("   ✓ Cambio de estrategia funciona")
        
        print("\n✅ TEST 2 PASADO: StrategyManager funciona correctamente\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FALLIDO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_no_duplicates():
    """Test crítico: verificar que NINGÚN método genera duplicados"""
    print("\n" + "="*70)
    print(" TEST 3: Verificación de No Duplicados (Crítico)")
    print("="*70)
    
    try:
        # Preparar
        print("\n1. Preparando sistema...")
        sorteos = generate_sample_data(num_sorteos=100)
        loader = DataLoader()
        data = loader.load_from_list(sorteos)
        
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(data)
        
        corr_analyzer = CorrelationAnalyzer()
        corr_analyzer.analyze(data)
        
        scorer = UnifiedScorer()
        scores = scorer.calculate_scores(freq_analyzer)
        
        manager = StrategyManager()
        print("   ✓ Sistema preparado")
        
        # Probar 50 combinaciones con cada método
        iterations = 50
        
        print(f"\n2. Generando {iterations} combinaciones con MÉTODO ESTÁNDAR...")
        for i in range(iterations):
            result = manager.generate(scores, strategy=GenerationStrategy.STANDARD)
            comb = result['combination']
            
            # Verificar no duplicados
            if len(comb) != len(set(comb)):
                raise AssertionError(f"Iteración {i}: Método STANDARD generó duplicados: {comb}")
            
            # Verificar rango
            if not all(0 <= n <= 45 for n in comb):
                raise AssertionError(f"Iteración {i}: Números fuera de rango: {comb}")
        
        print(f"   ✓ {iterations} combinaciones sin duplicados")
        
        print(f"\n3. Generando {iterations} combinaciones con MÉTODO CONDICIONAL...")
        for i in range(iterations):
            result = manager.generate(
                scores, 
                strategy=GenerationStrategy.CONDITIONAL,
                correlation_analyzer=corr_analyzer
            )
            comb = result['combination']
            
            # Verificar no duplicados
            if len(comb) != len(set(comb)):
                raise AssertionError(f"Iteración {i}: Método CONDICIONAL generó duplicados: {comb}")
            
            # Verificar rango
            if not all(0 <= n <= 45 for n in comb):
                raise AssertionError(f"Iteración {i}: Números fuera de rango: {comb}")
        
        print(f"   ✓ {iterations} combinaciones sin duplicados")
        
        print("\n✅ TEST 3 PASADO: Ningún método genera duplicados (100 iteraciones)\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FALLIDO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_comparison():
    """Test de comparación entre métodos"""
    print("\n" + "="*70)
    print(" TEST 4: Comparación de Métodos")
    print("="*70)
    
    try:
        # Preparar
        print("\n1. Preparando datos...")
        sorteos = generate_sample_data(num_sorteos=150)
        loader = DataLoader()
        data = loader.load_from_list(sorteos)
        
        freq_analyzer = FrequencyAnalyzer()
        freq_analyzer.analyze(data)
        
        corr_analyzer = CorrelationAnalyzer()
        corr_analyzer.analyze(data)
        
        scorer = UnifiedScorer()
        scores = scorer.calculate_scores(freq_analyzer)
        
        manager = StrategyManager()
        print("   ✓ Datos preparados")
        
        # Comparación lado a lado
        print("\n2. Generando predicciones lado a lado...")
        predictions = manager.generate_side_by_side(scores, corr_analyzer)
        
        assert 'standard' in predictions, "Debe tener predicción 'standard'"
        assert 'conditional' in predictions, "Debe tener predicción 'conditional'"
        assert len(predictions['standard']) == 6, "Standard debe tener 6 números"
        assert len(predictions['conditional']) == 6, "Conditional debe tener 6 números"
        
        print("   ✓ Predicciones lado a lado generadas")
        
        # Comparación estadística (versión reducida para test)
        print("\n3. Ejecutando comparación estadística (5 iteraciones)...")
        comparison = manager.compare_strategies(
            scores,
            correlation_analyzer=corr_analyzer,
            num_iterations=5
        )
        
        assert 'standard' in comparison, "Comparación debe tener 'standard'"
        assert 'conditional' in comparison, "Comparación debe tener 'conditional'"
        assert comparison['iterations'] == 5, "Debe tener 5 iteraciones"
        
        print("   ✓ Comparación estadística completada")
        
        print("\n✅ TEST 4 PASADO: Comparación de métodos funciona\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FALLIDO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*80)
    print(" EJECUTANDO SUITE DE TESTS DEL SISTEMA DE ESTRATEGIAS")
    print("="*80)
    
    results = []
    
    # Test 0: BACKTESTING REAL (PRINCIPAL)
    results.append(("🎯 BACKTESTING REAL 2026-02-08", test_backtesting_real()))
    
    # Test 1: Generador Condicional
    results.append(("Generador Condicional", test_conditional_generator()))
    
    # Test 2: Strategy Manager
    results.append(("Strategy Manager", test_strategy_manager()))
    
    # Test 3: No Duplicados (CRÍTICO)
    results.append(("No Duplicados (Crítico)", test_no_duplicates()))
    
    # Test 4: Comparación
    results.append(("Comparación de Métodos", test_comparison()))
    
    # Resumen
    print("\n" + "="*80)
    print(" RESUMEN DE TESTS")
    print("="*80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASADO" if result else "❌ FALLIDO"
        print(f"  {status} - {test_name}")
    
    print("\n" + "-"*80)
    print(f"\n  Total: {passed}/{total} tests pasados\n")
    
    if passed == total:
        print("  🎉 ¡TODOS LOS TESTS PASARON! 🎉")
        print("  El sistema está listo para usar.\n")
        print("="*80 + "\n")
        return True
    else:
        print("  ⚠️  Algunos tests fallaron. Revisa los errores arriba.\n")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
