"""
Test de Optimización de Parámetros
Busca la mejor configuración de pesos para maximizar aciertos
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, PatternAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy
import itertools


# RESULTADOS REALES A PREDECIR
RESULTADOS_REALES = [
    {'sorteo_id': 413, 'fecha': '2026-02-08', 'numeros': [23, 44, 45, 18, 40, 24]},
    {'sorteo_id': 414, 'fecha': '2026-02-08', 'numeros': [2, 0, 38, 13, 12, 25]},
    {'sorteo_id': 415, 'fecha': '2026-02-08', 'numeros': [39, 21, 4, 17, 20, 37]},
    {'sorteo_id': 416, 'fecha': '2026-02-08', 'numeros': [23, 4, 32, 37, 38, 7]},
]


def test_configuracion(data, config_name, weights, strategy, use_pattern=False):
    """
    Prueba una configuración específica
    """
    # Análisis
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    pattern_analyzer = None
    if use_pattern:
        pattern_analyzer = PatternAnalyzer()
        pattern_analyzer.analyze(data)
    
    # Scoring con pesos personalizados
    scorer = UnifiedScorer(weights)
    if use_pattern:
        scores = scorer.calculate_scores(freq_analyzer, pattern_analyzer, corr_analyzer)
    else:
        scores = scorer.calculate_scores(freq_analyzer)
    
    # Generar predicciones
    manager = StrategyManager()
    
    total_aciertos = 0
    mejor_sorteo = {'aciertos': 0, 'sorteo': None}
    
    for resultado_real in RESULTADOS_REALES:
        if strategy == 'BOTH':
            pred_result = manager.generate_side_by_side(scores, corr_analyzer)
            # Probar ambos métodos y tomar el mejor
            pred_std = sorted(pred_result['standard'])
            pred_cond = sorted(pred_result['conditional'])
            real = sorted(resultado_real['numeros'])
            
            aciertos_std = len(set(pred_std) & set(real))
            aciertos_cond = len(set(pred_cond) & set(real))
            aciertos = max(aciertos_std, aciertos_cond)
        else:
            pred_result = manager.generate(
                scores,
                strategy=GenerationStrategy.STANDARD if strategy == 'STANDARD' else GenerationStrategy.CONDITIONAL,
                correlation_analyzer=corr_analyzer if strategy == 'CONDITIONAL' else None,
                use_constraints=True
            )
            prediccion = sorted(pred_result['combination'])
            real = sorted(resultado_real['numeros'])
            aciertos = len(set(prediccion) & set(real))
        
        total_aciertos += aciertos
        
        if aciertos > mejor_sorteo['aciertos']:
            mejor_sorteo = {'aciertos': aciertos, 'sorteo': resultado_real['sorteo_id']}
    
    promedio = total_aciertos / len(RESULTADOS_REALES)
    
    return {
        'config': config_name,
        'total_aciertos': total_aciertos,
        'promedio': promedio,
        'mejor_sorteo': mejor_sorteo,
        'weights': weights,
        'strategy': strategy
    }


def optimizar_configuraciones():
    """
    Prueba múltiples configuraciones y encuentra la mejor
    """
    print("\n" + "="*80)
    print(" OPTIMIZACIÓN DE CONFIGURACIONES")
    print("="*80)
    
    # Cargar datos
    print("\n📂 Cargando datos históricos...")
    loader = DataLoader()
    data = loader.load_csv('data/quini6_historico_test.csv')
    data = data[data['sorteo_id'] <= 412].copy()
    print(f"   ✓ {len(data)} sorteos cargados (hasta 2026-02-04)")
    
    # Definir configuraciones a probar
    configuraciones = []
    
    # CONFIG 1: Default balanceado
    configuraciones.append({
        'name': 'Default Balanceado',
        'weights': {
            'peso_frecuencia': 0.25,
            'peso_frecuencia_reciente': 0.25,
            'peso_ciclo': 0.20,
            'peso_latencia': 0.15,
            'peso_tendencia': 0.15,
        },
        'strategy': 'BOTH',
        'use_pattern': False
    })
    
    # CONFIG 2: Énfasis en Frecuencia Reciente
    configuraciones.append({
        'name': 'Énfasis Reciente',
        'weights': {
            'peso_frecuencia': 0.15,
            'peso_frecuencia_reciente': 0.45,
            'peso_ciclo': 0.15,
            'peso_latencia': 0.15,
            'peso_tendencia': 0.10,
        },
        'strategy': 'CONDITIONAL',
        'use_pattern': False
    })
    
    # CONFIG 3: Énfasis en Frecuencia Total
    configuraciones.append({
        'name': 'Énfasis Frecuencia Total',
        'weights': {
            'peso_frecuencia': 0.50,
            'peso_frecuencia_reciente': 0.20,
            'peso_ciclo': 0.15,
            'peso_latencia': 0.10,
            'peso_tendencia': 0.05,
        },
        'strategy': 'STANDARD',
        'use_pattern': False
    })
    
    # CONFIG 4: Énfasis en Ciclos y Patrones
    configuraciones.append({
        'name': 'Énfasis Ciclos',
        'weights': {
            'peso_frecuencia': 0.20,
            'peso_frecuencia_reciente': 0.20,
            'peso_ciclo': 0.35,
            'peso_latencia': 0.15,
            'peso_tendencia': 0.10,
        },
        'strategy': 'CONDITIONAL',
        'use_pattern': True
    })
    
    # CONFIG 5: Énfasis en Latencia (números "atrasados")
    configuraciones.append({
        'name': 'Énfasis Latencia',
        'weights': {
            'peso_frecuencia': 0.15,
            'peso_frecuencia_reciente': 0.15,
            'peso_ciclo': 0.15,
            'peso_latencia': 0.40,
            'peso_tendencia': 0.15,
        },
        'strategy': 'BOTH',
        'use_pattern': False
    })
    
    # CONFIG 6: Tendencia Fuerte
    configuraciones.append({
        'name': 'Énfasis Tendencia',
        'weights': {
            'peso_frecuencia': 0.20,
            'peso_frecuencia_reciente': 0.30,
            'peso_ciclo': 0.10,
            'peso_latencia': 0.10,
            'peso_tendencia': 0.30,
        },
        'strategy': 'CONDITIONAL',
        'use_pattern': False
    })
    
    # CONFIG 7: Extremo Reciente
    configuraciones.append({
        'name': 'Ultra Reciente',
        'weights': {
            'peso_frecuencia': 0.10,
            'peso_frecuencia_reciente': 0.60,
            'peso_ciclo': 0.10,
            'peso_latencia': 0.10,
            'peso_tendencia': 0.10,
        },
        'strategy': 'CONDITIONAL',
        'use_pattern': False
    })
    
    # CONFIG 8: Balance Ciclo-Latencia
    configuraciones.append({
        'name': 'Balance Ciclo-Latencia',
        'weights': {
            'peso_frecuencia': 0.15,
            'peso_frecuencia_reciente': 0.15,
            'peso_ciclo': 0.35,
            'peso_latencia': 0.30,
            'peso_tendencia': 0.05,
        },
        'strategy': 'CONDITIONAL',
        'use_pattern': True
    })
    
    # CONFIG 9: Frecuencia Pura
    configuraciones.append({
        'name': 'Frecuencia Pura',
        'weights': {
            'peso_frecuencia': 0.70,
            'peso_frecuencia_reciente': 0.15,
            'peso_ciclo': 0.05,
            'peso_latencia': 0.05,
            'peso_tendencia': 0.05,
        },
        'strategy': 'STANDARD',
        'use_pattern': False
    })
    
    # CONFIG 10: Todo Equilibrado
    configuraciones.append({
        'name': 'Ultra Equilibrado',
        'weights': {
            'peso_frecuencia': 0.20,
            'peso_frecuencia_reciente': 0.20,
            'peso_ciclo': 0.20,
            'peso_latencia': 0.20,
            'peso_tendencia': 0.20,
        },
        'strategy': 'BOTH',
        'use_pattern': True
    })
    
    print(f"\n🔬 Probando {len(configuraciones)} configuraciones...\n")
    
    resultados = []
    
    for i, config in enumerate(configuraciones, 1):
        print(f"[{i}/{len(configuraciones)}] Probando: {config['name']}...", end=' ')
        
        resultado = test_configuracion(
            data,
            config['name'],
            config['weights'],
            config['strategy'],
            config.get('use_pattern', False)
        )
        
        resultados.append(resultado)
        print(f"✓ {resultado['total_aciertos']}/24 aciertos (Promedio: {resultado['promedio']:.2f})")
    
    # Ordenar por total de aciertos
    resultados.sort(key=lambda x: x['total_aciertos'], reverse=True)
    
    # Mostrar resultados
    print("\n" + "="*80)
    print(" RANKING DE CONFIGURACIONES")
    print("="*80 + "\n")
    
    for i, res in enumerate(resultados, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
        print(f"{emoji} {res['config']:25s} │ {res['total_aciertos']:2d}/24 │ Promedio: {res['promedio']:.2f} │ Estrategia: {res['strategy']}")
    
    # Mejor configuración
    mejor = resultados[0]
    print("\n" + "="*80)
    print(" 🏆 MEJOR CONFIGURACIÓN")
    print("="*80)
    print(f"\nNombre: {mejor['config']}")
    print(f"Aciertos totales: {mejor['total_aciertos']}/24")
    print(f"Promedio por sorteo: {mejor['promedio']:.2f}/6")
    print(f"Mejor sorteo: {mejor['mejor_sorteo']['aciertos']} aciertos (Sorteo {mejor['mejor_sorteo']['sorteo']})")
    print(f"Estrategia: {mejor['strategy']}")
    print(f"\nPesos:")
    for key, value in mejor['weights'].items():
        print(f"  {key:30s}: {value:.2f}")
    
    print("\n" + "="*80)
    
    return mejor


def optimizacion_fina(mejor_config, data):
    """
    Hace ajustes finos alrededor de la mejor configuración
    """
    print("\n" + "="*80)
    print(" OPTIMIZACIÓN FINA")
    print("="*80)
    print(f"\nPartiendo de: {mejor_config['config']}")
    print(f"Aciertos base: {mejor_config['total_aciertos']}/24\n")
    
    # Generar variaciones alrededor de los mejores pesos
    base_weights = mejor_config['weights']
    variaciones = []
    
    # Para cada peso, probar incrementarlo/decrementarlo en ±0.05 y redistribuir
    for key_modificar in base_weights.keys():
        for delta in [-0.10, -0.05, 0.05, 0.10]:
            new_weights = base_weights.copy()
            
            # Aplicar cambio
            new_weights[key_modificar] = max(0.05, min(0.80, base_weights[key_modificar] + delta))
            
            # Redistribuir el resto proporcionalmente
            total_otros = sum(v for k, v in new_weights.items() if k != key_modificar)
            if total_otros > 0:
                factor = (1 - new_weights[key_modificar]) / total_otros
                for k in new_weights:
                    if k != key_modificar:
                        new_weights[k] *= factor
            
            variaciones.append({
                'name': f"{key_modificar.replace('peso_', '')} {delta:+.2f}",
                'weights': new_weights,
                'strategy': mejor_config['strategy']
            })
    
    print(f"Probando {len(variaciones)} variaciones finas...")
    
    resultados_finos = []
    
    for i, var in enumerate(variaciones, 1):
        resultado = test_configuracion(
            data,
            var['name'],
            var['weights'],
            var['strategy'],
            False
        )
        resultados_finos.append(resultado)
        
        if i % 5 == 0:
            print(f"  Progreso: {i}/{len(variaciones)}")
    
    # Ordenar
    resultados_finos.sort(key=lambda x: x['total_aciertos'], reverse=True)
    
    # Mostrar top 5
    print("\n🎯 TOP 5 VARIACIONES FINAS:")
    for i, res in enumerate(resultados_finos[:5], 1):
        mejora = res['total_aciertos'] - mejor_config['total_aciertos']
        print(f"  {i}. {res['config']:30s} │ {res['total_aciertos']}/24 ({mejora:+d})")
    
    if resultados_finos[0]['total_aciertos'] > mejor_config['total_aciertos']:
        print(f"\n✨ ¡MEJORA ENCONTRADA! +{resultados_finos[0]['total_aciertos'] - mejor_config['total_aciertos']} aciertos")
        return resultados_finos[0]
    else:
        print(f"\n💡 No se encontró mejora. La configuración original sigue siendo la mejor.")
        return mejor_config


if __name__ == "__main__":
    # Fase 1: Probar configuraciones diversas
    mejor = optimizar_configuraciones()
    
    # Fase 2: Optimización fina
    if mejor['total_aciertos'] < 24:  # Si no es perfecto, intentar mejorar
        loader = DataLoader()
        data = loader.load_csv('data/quini6_historico_test.csv')
        data = data[data['sorteo_id'] <= 412].copy()
        
        mejor_final = optimizacion_fina(mejor, data)
        
        print("\n" + "="*80)
        print(" 🎯 CONFIGURACIÓN FINAL ÓPTIMA")
        print("="*80)
        print(f"\nNombre: {mejor_final['config']}")
        print(f"Aciertos: {mejor_final['total_aciertos']}/24 ({mejor_final['promedio']:.2f} por sorteo)")
        print(f"\nPesos optimizados:")
        for key, value in mejor_final['weights'].items():
            print(f"  {key:30s}: {value:.3f}")
        print("\n" + "="*80)
