"""Script temporal para análisis rápido de números candidatos"""
import sys
sys.path.insert(0, 'd:\\Repo\\Charly_Predictor')

from core.data import DataLoader
from core.analysis import FrequencyAnalyzer

# Cargar datos
loader = DataLoader()
data = loader.load_csv('data/quini6_historico.csv')

print(f"\n{'='*70}")
print(f"ANÁLISIS DE FRECUENCIA - {len(data)} sorteos históricos")
print(f"Período: {data['fecha'].min()} a {data['fecha'].max()}")
print(f"{'='*70}\n")

# Análisis de frecuencias
freq_analyzer = FrequencyAnalyzer()
freq_analyzer.analyze(data)

# 1. Top por Frecuencia Absoluta (histórico completo)
print("📊 TOP 10 - FRECUENCIA ABSOLUTA (Histórico Completo)")
print("-" * 70)
freq_abs = freq_analyzer.results['frecuencia_absoluta']
sorted_freq = sorted(freq_abs.items(), key=lambda x: x[1], reverse=True)[:10]
for i, (num, count) in enumerate(sorted_freq, 1):
    pct = (count / len(data)) * 100
    bars = "█" * int(pct / 2)
    print(f"{i:2d}. Número {num:2d}: {count:3d} veces ({pct:5.2f}%) {bars}")

# 2. Números Calientes (top frecuencia)
print(f"\n🔥 TOP 10 - NÚMEROS CALIENTES")
print("-" * 70)
calientes = freq_analyzer.results['numeros_calientes']
for i, (num, count) in enumerate(calientes, 1):
    pct = (count / len(data)) * 100
    bars = "█" * int(pct / 2)
    print(f"{i:2d}. Número {num:2d}: {count:3d} veces ({pct:5.2f}%) {bars}")

# 3. Frecuencia Reciente (últimos 50 sorteos)
print(f"\n🔥 TOP 10 - FRECUENCIA RECIENTE (Últimos 50 sorteos ~ 1.5 meses)")
print("-" * 70)
freq_reciente = freq_analyzer.results['frecuencia_reciente']
sorted_reciente = sorted(freq_reciente.items(), key=lambda x: x[1], reverse=True)[:10]
for i, (num, count) in enumerate(sorted_reciente, 1):
    pct = (count / 50) * 100
    bars = "█" * int(pct / 2)
    print(f"{i:2d}. Número {num:2d}: {count:2d} veces ({pct:5.2f}%) {bars}")

# 4. COMBINACIÓN - Top 6 candidatos (promedio entre frecuencia absoluta y calientes)
print(f"\n{'='*70}")
print("🎯 TOP 6 CANDIDATOS - Combinación Frecuencia + Calientes")
print(f"{'='*70}\n")

# Crear ranking combinado
from collections import defaultdict
scores = defaultdict(float)

# Puntaje por frecuencia absoluta (normalizado)
max_freq = sorted_freq[0][1]
for num, count in sorted_freq[:15]:  # Top 15
    scores[num] += (count / max_freq) * 50  # 50% peso

# Puntaje por calientes (normalizado)
max_caliente = calientes[0][1]
for num, count in calientes[:15]:  # Top 15
    scores[num] += (count / max_caliente) * 50  # 50% peso

# Ordenar por score combinado
top_candidatos = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:6]

print("Número | Score Combinado | Freq.Absoluta | Freq.Reciente")
print("-" * 70)
for num, score in top_candidatos:
    freq_abs_val = freq_abs[num]
    freq_rec_val = freq_reciente[num]
    print(f"  {num:2d}   |     {score:5.1f}      |     {freq_abs_val:3d}      |      {freq_rec_val:2d}")

print(f"\n{'='*70}")
print("🎲 COMBINACIÓN SUGERIDA (Top 6 números):")
print(f"{'='*70}")
print(f"\n   {sorted([num for num, _ in top_candidatos])}")
print()
