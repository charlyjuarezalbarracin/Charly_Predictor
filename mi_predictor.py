"""
================================================================================
  MI PREDICTOR PERSONAL - SCRIPT SIMPLE
================================================================================

CÓMO USAR:
  1. Ejecuta: py mi_predictor.py
  2. Ve los resultados en consola
  3. Copia los números que te gusten
  4. ¡Listo!

PERSONALIZAR:
  - Cambia cantidad_sorteos para más/menos datos
  - Cambia metodo_usar para cambiar entre métodos
  - Cambia peso_correlaciones para ajustar el método condicional
"""

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy
from utils.data_generator import generate_sample_data


# ============================================================================
# ⚙️ CONFIGURACIÓN - CAMBIA ESTOS VALORES A TU GUSTO
# ============================================================================

cantidad_sorteos = 200           # Cantidad de sorteos históricos a usar
metodo_usar = "AMBOS"            # Opciones: "ESTANDAR", "CONDICIONAL", "AMBOS"
peso_correlaciones = 0.3         # Solo para condicional (0.0 a 1.0)


# ============================================================================
# 🚀 EJECUCIÓN DEL SISTEMA
# ============================================================================

print("\n" + "="*80)
print(" 🎯 MI PREDICTOR PERSONAL DE QUINI 6")
print("="*80 + "\n")

# 1. DATOS
print(f"📂 Cargando datos históricos reales...")
loader = DataLoader()
data = loader.load_csv('data/quini6_historico.csv')
print(f"   ✓ {len(data)} sorteos cargados (desde {data['fecha'].min()} hasta {data['fecha'].max()})\n")

# 2. ANÁLISIS
print("📊 Analizando datos...")
freq = FrequencyAnalyzer()
freq.analyze(data)

corr = CorrelationAnalyzer()
corr.analyze(data)
print("   ✓ Análisis completados\n")

# 3. SCORING
print("🎯 Calculando scores...")
scorer = UnifiedScorer()
scores = scorer.calculate_scores(freq)

# Mostrar top 10
top_10 = scorer.get_top_numbers(10)
print("\n   📊 Top 10 Números con Mejor Score:")
print("   " + "-"*45)
for i, (num, score) in enumerate(top_10, 1):
    bars = "█" * int(score * 30)
    print(f"   {i:2d}. Número {num:2d}  {score:.4f}  {bars}")
print()

# 4. GENERAR PREDICCIÓN
manager = StrategyManager()

print("="*80)
print(" 🎲 GENERANDO PREDICCIÓN")
print("="*80 + "\n")

if metodo_usar == "ESTANDAR":
    print("   Método: ESTÁNDAR (Probabilidades Estáticas)")
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.STANDARD,
        use_constraints=True
    )
    
    print(f"\n   🎯 PREDICCIÓN: {result['combination']}\n")
    print(f"   Suma total: {result['analysis']['suma_total']}")
    print(f"   Score promedio: {result['analysis']['score_promedio']:.4f}")
    print(f"   Pares: {result['analysis']['pares']}, Impares: {result['analysis']['impares']}")
    print(f"   Consecutivos: {result['analysis']['consecutivos']}")

elif metodo_usar == "CONDICIONAL":
    print(f"   Método: CONDICIONAL (Probabilidades Dinámicas)")
    print(f"   Peso correlaciones: {peso_correlaciones}")
    
    # Ajustar peso de correlaciones
    manager.conditional_generator.correlation_weight = peso_correlaciones
    
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.CONDITIONAL,
        correlation_analyzer=corr,
        use_constraints=True
    )
    
    print(f"\n   🎯 PREDICCIÓN: {result['combination']}\n")
    print(f"   Suma total: {result['analysis']['suma_total']}")
    print(f"   Score promedio: {result['analysis']['score_promedio']:.4f}")
    print(f"   Correlation score: {result['analysis']['correlation_score']:.4f}")
    print(f"   Pares: {result['analysis']['pares']}, Impares: {result['analysis']['impares']}")
    print(f"   Consecutivos: {result['analysis']['consecutivos']}")

elif metodo_usar == "AMBOS":
    print("   Método: AMBOS (Comparación)")
    
    # Ajustar peso de correlaciones
    manager.conditional_generator.correlation_weight = peso_correlaciones
    
    result = manager.generate(
        scores,
        strategy=GenerationStrategy.BOTH,
        correlation_analyzer=corr,
        use_constraints=True
    )
    
    print("\n   🎯 PREDICCIÓN ESTÁNDAR:")
    print(f"      {result['standard']['combination']}")
    print(f"      Score: {result['standard']['analysis']['score_promedio']:.4f}")
    
    print("\n   🎯 PREDICCIÓN CONDICIONAL:")
    print(f"      {result['conditional']['combination']}")
    print(f"      Score: {result['conditional']['analysis']['score_promedio']:.4f}")
    print(f"      Correlation: {result['conditional']['analysis']['correlation_score']:.4f}")

else:
    print(f"   ⚠️  Método '{metodo_usar}' no reconocido.")
    print("   Usa: ESTANDAR, CONDICIONAL, o AMBOS")

print("\n" + "="*80)
print(" ✅ Predicción completa")
print("="*80 + "\n")


# ============================================================================
# 💡 TIPS DE USO
# ============================================================================

print("💡 TIPS:")
print("   - Ejecuta varias veces para ver diferentes predicciones")
print("   - Cambia 'metodo_usar' arriba para probar otros métodos:")
print("     • ESTANDAR: Rápido, probabilidades fijas")
print("     • CONDICIONAL: Inteligente, considera correlaciones")
print("     • AMBOS: Compara ambos métodos lado a lado")
print("   - Ajusta 'peso_correlaciones' (0.1 a 0.8) para el método condicional")
print("   - Actualmente usando DATOS REALES desde data/quini6_historico.csv")
print()
