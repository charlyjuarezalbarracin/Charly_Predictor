"""
Test del sistema de estrategias de generación
Prueba ambos métodos: Estándar y Condicional
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
