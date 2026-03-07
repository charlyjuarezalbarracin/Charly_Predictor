"""
Test Walk-Forward: Validación de IDEAS en múltiples períodos

Compara rendimiento de:
1. BASELINE (sin IDEAS)
2. IDEA #3 sola (Regresión)
3. IDEA #1 + #3 (Resonancia + Regresión)
4. TODAS (#1 + #2 + #3)

Usa ventana móvil para validar estabilidad temporal
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.data.loader import DataLoader
from core.backtesting.walk_forward import WalkForwardBacktester
from configs.config_optimizada import OPTIMAL_WEIGHTS


def test_walkforward_ideas():
    """
    Ejecuta Walk-Forward con diferentes configuraciones de IDEAS
    """
    print("\n" + "="*90)
    print("WALK-FORWARD VALIDATION: BASELINE vs IDEAS")
    print("="*90)
    
    # Cargar datos
    loader = DataLoader()
    df = loader.load_csv('data/quini6_historico_test.csv')
    
    print(f"\nDatos cargados: {len(df)} sorteos")
    print(f"Rango de fechas: {df['fecha'].min()} a {df['fecha'].max()}")
    
    # Configuración Walk-Forward
    train_window = 200  # ~25 semanas de entrenamiento
    test_window = 8     # 1 semana de test
    step_size = 8       # Deslizar 1 semana cada vez
    
    print(f"\nConfiguración Walk-Forward:")
    print(f"  Train window: {train_window} sorteos (~25 semanas)")
    print(f"  Test window:  {test_window} sorteos (1 semana)")
    print(f"  Step size:    {step_size} sorteos (1 semana)")
    
    # Calcular períodos esperados
    max_start = len(df) - train_window - test_window
    periodos_esperados = (max_start // step_size) + 1
    print(f"  Períodos esperados: ~{periodos_esperados}")
    
    escenarios = []
    
    # =========================================================================
    # ESCENARIO 1: BASELINE (sin IDEAS)
    # =========================================================================
    print("\n" + "="*90)
    print("ESCENARIO 1: BASELINE (sin IDEAS)")
    print("="*90)
    
    wf_baseline = WalkForwardBacktester(
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        use_ideas=False
    )
    
    results_baseline = wf_baseline.run_walk_forward(df, OPTIMAL_WEIGHTS)
    
    escenarios.append({
        'nombre': 'BASELINE',
        'backtester': wf_baseline,
        'results': results_baseline
    })
    
    # =========================================================================
    # ESCENARIO 2: SOLO IDEA #3 (Regresión al Equilibrio)
    # =========================================================================
    print("\n" + "="*90)
    print("ESCENARIO 2: SOLO IDEA #3 (Regresión al Equilibrio)")
    print("="*90)
    
    wf_idea3 = WalkForwardBacktester(
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        use_ideas=True,
        use_idea1=False,
        use_idea2=False,
        use_idea3=True,
        idea3_ventana=16,    # 2 semanas
        idea3_umbral=0.12   # 12%
    )
    
    results_idea3 = wf_idea3.run_walk_forward(df, OPTIMAL_WEIGHTS)
    
    escenarios.append({
        'nombre': 'IDEA #3',
        'backtester': wf_idea3,
        'results': results_idea3
    })
    
    # =========================================================================
    # ESCENARIO 3: IDEA #1 + #3
    # =========================================================================
    print("\n" + "="*90)
    print("ESCENARIO 3: IDEA #1 + IDEA #3 (Resonancia + Regresión)")
    print("="*90)
    
    wf_idea1_3 = WalkForwardBacktester(
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        use_ideas=True,
        use_idea1=True,
        use_idea2=False,
        use_idea3=True,
        idea3_ventana=16,
        idea3_umbral=0.12
    )
    
    results_idea1_3 = wf_idea1_3.run_walk_forward(df, OPTIMAL_WEIGHTS)
    
    escenarios.append({
        'nombre': 'IDEA #1+#3',
        'backtester': wf_idea1_3,
        'results': results_idea1_3
    })
    
    # =========================================================================
    # ESCENARIO 4: TODAS LAS IDEAS
    # =========================================================================
    print("\n" + "="*90)
    print("ESCENARIO 4: TODAS LAS IDEAS (#1 + #2 + #3)")
    print("="*90)
    
    wf_todas = WalkForwardBacktester(
        train_window=train_window,
        test_window=test_window,
        step_size=step_size,
        use_ideas=True,
        use_idea1=True,
        use_idea2=True,
        use_idea3=True,
        idea3_ventana=16,
        idea3_umbral=0.12
    )
    
    results_todas = wf_todas.run_walk_forward(df, OPTIMAL_WEIGHTS)
    
    escenarios.append({
        'nombre': 'TODAS (#1+#2+#3)',
        'backtester': wf_todas,
        'results': results_todas
    })
    
    # =========================================================================
    # COMPARACIÓN FINAL
    # =========================================================================
    print("\n" + "="*90)
    print("COMPARACIÓN FINAL - WALK-FORWARD VALIDATION")
    print("="*90)
    
    print(f"\n{'Escenario':<20} {'Períodos':<10} {'Accuracy':<12} {'Std Dev':<12} {'Estabilidad'}")
    print("-" * 90)
    
    resultados_comparacion = []
    
    for esc in escenarios:
        summary = esc['results']['summary']
        stability = esc['backtester'].get_stability_score()
        
        resultados_comparacion.append({
            'nombre': esc['nombre'],
            'periodos': summary['total_periodos'],
            'accuracy': summary['accuracy_promedio'],
            'std': summary['accuracy_std'],
            'stability': stability
        })
        
        print(f"{esc['nombre']:<20} {summary['total_periodos']:<10} "
              f"{summary['accuracy_promedio']:<12.2%} "
              f"{summary['accuracy_std']:<12.2%} "
              f"{stability:.2%}")
    
    # Determinar ganador
    print("\n" + "="*90)
    print("ANÁLISIS DE RESULTADOS")
    print("="*90)
    
    mejor_accuracy = max(r['accuracy'] for r in resultados_comparacion)
    mejor_stability = max(r['stability'] for r in resultados_comparacion)
    
    ganador_accuracy = [r for r in resultados_comparacion if r['accuracy'] == mejor_accuracy][0]
    ganador_stability = [r for r in resultados_comparacion if r['stability'] == mejor_stability][0]
    
    print(f"\n🏆 MEJOR ACCURACY:    {ganador_accuracy['nombre']} ({ganador_accuracy['accuracy']:.2%})")
    print(f"🏆 MEJOR ESTABILIDAD: {ganador_stability['nombre']} ({ganador_stability['stability']:.2%})")
    
    # Comparación vs BASELINE
    baseline = resultados_comparacion[0]
    
    print(f"\n{'Mejora vs BASELINE:':<30}")
    print("-" * 90)
    
    for r in resultados_comparacion[1:]:
        mejora_acc = (r['accuracy'] - baseline['accuracy']) / baseline['accuracy'] * 100
        mejora_stb = (r['stability'] - baseline['stability']) / baseline['stability'] * 100
        
        signo_acc = '+' if mejora_acc > 0 else ''
        signo_stb = '+' if mejora_stb > 0 else ''
        
        print(f"{r['nombre']:<20} Accuracy: {signo_acc}{mejora_acc:>6.2f}%  |  "
              f"Estabilidad: {signo_stb}{mejora_stb:>6.2f}%")
    
    # Recomendación
    print("\n" + "="*90)
    print("RECOMENDACIÓN")
    print("="*90)
    
    if ganador_accuracy['nombre'] == 'BASELINE':
        print("⚠️  El sistema base (BASELINE) es superior a las IDEAS en este dataset.")
        print("    Las IDEAS no mejoran el rendimiento temporal.")
    else:
        print(f"✅ Se recomienda usar: {ganador_accuracy['nombre']}")
        print(f"   Mejora de accuracy: {((ganador_accuracy['accuracy'] - baseline['accuracy']) / baseline['accuracy'] * 100):+.2f}%")
        print(f"   Score de estabilidad: {ganador_accuracy['stability']:.2%}")
    
    print("\n" + "="*90)
    print("FIN DE LA VALIDACIÓN WALK-FORWARD")
    print("="*90 + "\n")
    
    return resultados_comparacion


if __name__ == '__main__':
    resultados = test_walkforward_ideas()
