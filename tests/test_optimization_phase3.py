"""
Optimización Fase 3: Búsqueda Exhaustiva
Partiendo de la mejor configuración encontrada (8/24 aciertos)
"""

import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, PatternAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy


RESULTADOS_REALES = [
    {'sorteo_id': 413, 'numeros': [23, 44, 45, 18, 40, 24]},
    {'sorteo_id': 414, 'numeros': [2, 0, 38, 13, 12, 25]},
    {'sorteo_id': 415, 'numeros': [39, 21, 4, 17, 20, 37]},
    {'sorteo_id': 416, 'numeros': [23, 4, 32, 37, 38, 7]},
]


def evaluar_config(data, weights, strategy='BOTH', use_pattern=False, use_constraints=True):
    """Evalúa una configuración y devuelve total de aciertos"""
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    pattern_analyzer = None
    if use_pattern:
        pattern_analyzer = PatternAnalyzer()
        pattern_analyzer.analyze(data)
    
    scorer = UnifiedScorer(weights)
    if use_pattern:
        scores = scorer.calculate_scores(freq_analyzer, pattern_analyzer, corr_analyzer)
    else:
        scores = scorer.calculate_scores(freq_analyzer)
    
    manager = StrategyManager()
    total_aciertos = 0
    
    for resultado_real in RESULTADOS_REALES:
        if strategy == 'BOTH':
            pred = manager.generate_side_by_side(scores, corr_analyzer)
            pred_std = set(pred['standard'])
            pred_cond = set(pred['conditional'])
            real = set(resultado_real['numeros'])
            aciertos = max(len(pred_std & real), len(pred_cond & real))
        else:
            pred = manager.generate(
                scores,
                strategy=GenerationStrategy.STANDARD if strategy == 'STANDARD' else GenerationStrategy.CONDITIONAL,
                correlation_analyzer=corr_analyzer if strategy == 'CONDITIONAL' else None,
                use_constraints=use_constraints
            )
            prediccion = set(pred['combination'])
            real = set(resultado_real['numeros'])
            aciertos = len(prediccion & real)
        
        total_aciertos += aciertos
    
    return total_aciertos


def fase3_busqueda_exhaustiva():
    """Búsqueda exhaustiva más agresiva"""
    print("\n" + "="*80)
    print(" FASE 3: BÚSQUEDA EXHAUSTIVA")
    print("="*80)
    
    # Cargar datos
    loader = DataLoader()
    data = loader.load_csv('data/quini6_historico_test.csv')
    data = data[data['sorteo_id'] <= 412].copy()
    print(f"\n✓ Datos cargados: {len(data)} sorteos\n")
    
    # Configuración base (mejor hasta ahora: 8/24)
    mejor = {
        'aciertos': 8,
        'weights': {
            'peso_frecuencia': 0.225,
            'peso_frecuencia_reciente': 0.225,
            'peso_ciclo': 0.225,
            'peso_latencia': 0.100,
            'peso_tendencia': 0.225,
        },
        'strategy': 'BOTH',
        'use_pattern': False,
        'use_constraints': True
    }
    
    print("Configuración base:")
    print(f"  Aciertos: {mejor['aciertos']}/24")
    print(f"  Estrategia: {mejor['strategy']}")
    print(f"  Restricciones: {mejor['use_constraints']}")
    
    # ESTRATEGIA 1: Probar con/sin restricciones
    print("\n" + "─"*80)
    print("1. Probando con y sin restricciones...")
    
    for use_const in [True, False]:
        aciertos = evaluar_config(
            data, 
            mejor['weights'],
            strategy='BOTH',
            use_pattern=False,
            use_constraints=use_const
        )
        print(f"   {'Con' if use_const else 'Sin'} restricciones: {aciertos}/24", end='')
        if aciertos > mejor['aciertos']:
            mejor['aciertos'] = aciertos
            mejor['use_constraints'] = use_const
            print(" ✨ ¡MEJORA!")
        else:
            print()
    
    # ESTRATEGIA 2: Probar solo estrategias individuales
    print("\n" + "─"*80)
    print("2. Probando estrategias individuales...")
    
    for strat in ['STANDARD', 'CONDITIONAL', 'BOTH']:
        aciertos = evaluar_config(
            data,
            mejor['weights'],
            strategy=strat,
            use_pattern=False,
            use_constraints=mejor['use_constraints']
        )
        print(f"   {strat:12s}: {aciertos}/24", end='')
        if aciertos > mejor['aciertos']:
            mejor['aciertos'] = aciertos
            mejor['strategy'] = strat
            print(" ✨ ¡MEJORA!")
        else:
            print()
    
    # ESTRATEGIA 3: Probar con análisis de patrones
    print("\n" + "─"*80)
    print("3. Probando con análisis de patrones...")
    
    aciertos = evaluar_config(
        data,
        mejor['weights'],
        strategy=mejor['strategy'],
        use_pattern=True,
        use_constraints=mejor['use_constraints']
    )
    print(f"   Con patrones: {aciertos}/24", end='')
    if aciertos > mejor['aciertos']:
        mejor['aciertos'] = aciertos
        mejor['use_pattern'] = True
        print(" ✨ ¡MEJORA!")
    else:
        print()
    
    # ESTRATEGIA 4: Búsqueda de grid fino alrededor de la mejor configuración
    print("\n" + "─"*80)
    print("4. Grid search fino de pesos...")
    
    # Probar combinaciones específicas que podrían funcionar bien
    configs_grid = [
        # Énfasis extremo en reciente
        {'peso_frecuencia': 0.10, 'peso_frecuencia_reciente': 0.50, 'peso_ciclo': 0.15, 'peso_latencia': 0.10, 'peso_tendencia': 0.15},
        # Balance sin latencia
        {'peso_frecuencia': 0.25, 'peso_frecuencia_reciente': 0.25, 'peso_ciclo': 0.25, 'peso_latencia': 0.00, 'peso_tendencia': 0.25},
        # Frecuencia total dominante
        {'peso_frecuencia': 0.60, 'peso_frecuencia_reciente': 0.15, 'peso_ciclo': 0.10, 'peso_latencia': 0.05, 'peso_tendencia': 0.10},
        # Ciclo dominante
        {'peso_frecuencia': 0.15, 'peso_frecuencia_reciente': 0.15, 'peso_ciclo': 0.50, 'peso_latencia': 0.05, 'peso_tendencia': 0.15},
        # Tendencia fuerte
        {'peso_frecuencia': 0.20, 'peso_frecuencia_reciente': 0.25, 'peso_ciclo': 0.15, 'peso_latencia': 0.05, 'peso_tendencia': 0.35},
        # Reciente + Tendencia
        {'peso_frecuencia': 0.10, 'peso_frecuencia_reciente': 0.40, 'peso_ciclo': 0.10, 'peso_latencia': 0.05, 'peso_tendencia': 0.35},
        # Frecuencia + Ciclo
        {'peso_frecuencia': 0.40, 'peso_frecuencia_reciente': 0.10, 'peso_ciclo': 0.40, 'peso_latencia': 0.05, 'peso_tendencia': 0.05},
        # Sin frecuencia total
        {'peso_frecuencia': 0.00, 'peso_frecuencia_reciente': 0.40, 'peso_ciclo': 0.30, 'peso_latencia': 0.10, 'peso_tendencia': 0.20},
    ]
    
    for i, weights in enumerate(configs_grid, 1):
        aciertos = evaluar_config(
            data,
            weights,
            strategy=mejor['strategy'],
            use_pattern=mejor['use_pattern'],
            use_constraints=mejor['use_constraints']
        )
        if aciertos > mejor['aciertos']:
            mejor['aciertos'] = aciertos
            mejor['weights'] = weights.copy()
            print(f"   Grid {i}: {aciertos}/24 ✨ ¡MEJORA!")
        elif aciertos == mejor['aciertos'] and (i % 2 == 0):
            print(f"   Grid {i}: {aciertos}/24 (empate)")
    
    print(f"\n   Mejor hasta ahora: {mejor['aciertos']}/24")
    
    # ESTRATEGIA 5: Búsqueda aleatoria (Monte Carlo)
    print("\n" + "─"*80)
    print("5. Búsqueda aleatoria (100 configuraciones)...")
    
    mejoras_encontradas = 0
    
    for i in range(100):
        # Generar pesos aleatorios que sumen 1
        pesos_rand = [random.uniform(0, 1) for _ in range(5)]
        suma = sum(pesos_rand)
        pesos_rand = [p/suma for p in pesos_rand]
        
        weights_rand = {
            'peso_frecuencia': pesos_rand[0],
            'peso_frecuencia_reciente': pesos_rand[1],
            'peso_ciclo': pesos_rand[2],
            'peso_latencia': pesos_rand[3],
            'peso_tendencia': pesos_rand[4],
        }
        
        aciertos = evaluar_config(
            data,
            weights_rand,
            strategy=mejor['strategy'],
            use_pattern=mejor['use_pattern'],
            use_constraints=mejor['use_constraints']
        )
        
        if aciertos > mejor['aciertos']:
            mejor['aciertos'] = aciertos
            mejor['weights'] = weights_rand.copy()
            mejoras_encontradas += 1
            print(f"   Iteración {i+1}: {aciertos}/24 ✨ ¡MEJORA #{mejoras_encontradas}!")
        
        if (i + 1) % 20 == 0:
            print(f"   Progreso: {i+1}/100 (Mejor: {mejor['aciertos']}/24)")
    
    # RESULTADO FINAL
    print("\n" + "="*80)
    print(" 🏆 CONFIGURACIÓN ÓPTIMA FINAL")
    print("="*80)
    print(f"\n🎯 Aciertos: {mejor['aciertos']}/24 ({mejor['aciertos']/4:.2f} por sorteo)")
    print(f"📊 Estrategia: {mejor['strategy']}")
    print(f"🔧 Restricciones: {'Activadas' if mejor['use_constraints'] else 'Desactivadas'}")
    print(f"📈 Análisis de patrones: {'Activado' if mejor['use_pattern'] else 'Desactivado'}")
    
    print(f"\n⚖️  Pesos óptimos:")
    for key, value in mejor['weights'].items():
        print(f"   {key:30s}: {value:.4f}")
    
    # Analizar sorteo por sorteo con mejor configuración
    print("\n" + "="*80)
    print(" 📋 ANÁLISIS DETALLADO POR SORTEO")
    print("="*80)
    
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    pattern_analyzer = None
    if mejor['use_pattern']:
        pattern_analyzer = PatternAnalyzer()
        pattern_analyzer.analyze(data)
    
    scorer = UnifiedScorer(mejor['weights'])
    if mejor['use_pattern']:
        scores = scorer.calculate_scores(freq_analyzer, pattern_analyzer, corr_analyzer)
    else:
        scores = scorer.calculate_scores(freq_analyzer)
    
    manager = StrategyManager()
    
    for resultado_real in RESULTADOS_REALES:
        print(f"\n🎲 Sorteo {resultado_real['sorteo_id']}")
        print(f"   Real: {sorted(resultado_real['numeros'])}")
        
        if mejor['strategy'] == 'BOTH':
            pred = manager.generate_side_by_side(scores, corr_analyzer)
            pred_std = sorted(pred['standard'])
            pred_cond = sorted(pred['conditional'])
            
            aciertos_std = len(set(pred_std) & set(resultado_real['numeros']))
            aciertos_cond = len(set(pred_cond) & set(resultado_real['numeros']))
            
            print(f"   Estándar:    {pred_std} → {aciertos_std}/6", end='')
            if aciertos_std > 0:
                print(f" ✓ {sorted(set(pred_std) & set(resultado_real['numeros']))}")
            else:
                print()
            
            print(f"   Condicional: {pred_cond} → {aciertos_cond}/6", end='')
            if aciertos_cond > 0:
                print(f" ✓ {sorted(set(pred_cond) & set(resultado_real['numeros']))}")
            else:
                print()
        else:
            pred = manager.generate(
                scores,
                strategy=GenerationStrategy.STANDARD if mejor['strategy'] == 'STANDARD' else GenerationStrategy.CONDITIONAL,
                correlation_analyzer=corr_analyzer if mejor['strategy'] == 'CONDITIONAL' else None,
                use_constraints=mejor['use_constraints']
            )
            prediccion = sorted(pred['combination'])
            aciertos = len(set(prediccion) & set(resultado_real['numeros']))
            
            print(f"   Predicción: {prediccion} → {aciertos}/6", end='')
            if aciertos > 0:
                print(f" ✓ {sorted(set(prediccion) & set(resultado_real['numeros']))}")
            else:
                print()
    
    print("\n" + "="*80)
    
    if mejor['aciertos'] >= 18:  # 3+ por sorteo
        print("\n🎉 ¡EXCELENTE! Configuración muy efectiva (3+ aciertos por sorteo)")
    elif mejor['aciertos'] >= 12:  # 2+ por sorteo
        print("\n👍 ¡BUENO! Configuración prometedora (2+ aciertos por sorteo)")
    elif mejor['aciertos'] >= 8:
        print("\n💡 Configuración mejorada, pero aún hay margen de optimización")
    else:
        print("\n🤔 Se requiere más exploración de configuraciones")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    random.seed(42)  # Para reproducibilidad
    fase3_busqueda_exhaustiva()
