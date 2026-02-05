# Charly Predictor - Sistema de Predicción de Quini 6

Sistema profesional de análisis y predicción para el Quini 6 basado en estadísticas, análisis de frecuencias, patrones temporales y modelos avanzados.

## 🎯 Características Principales

### **Core del Sistema**
- ✅ **Módulo de Datos**: Carga, validación y preprocesamiento de datos históricos
- ✅ **Motor de Análisis Estadístico Multi-dimensional**:
  - Análisis de frecuencias (absoluta, relativa, reciente)
  - Análisis de patrones temporales (rachas, sequías, estacionalidad)
  - Análisis de correlaciones (pares frecuentes, anti-correlaciones)
- ✅ **Sistema de Scoring con Pesos Configurables**
- ✅ **Generador de Combinaciones** con restricciones configurables
- ✅ **Sistema de Backtesting** para validación y ajuste de parámetros
- ✅ **Optimización con Algoritmos Genéticos**

## 📁 Estructura del Proyecto

```
Charly_Predictor/
├── core/
│   ├── data/
│   │   ├── loader.py           # Carga de datos CSV/JSON
│   │   ├── validator.py        # Validación de integridad
│   │   └── preprocessor.py     # Cálculo de features
│   ├── analysis/
│   │   ├── frequency.py        # Análisis de frecuencias
│   │   ├── patterns.py         # Patrones temporales
│   │   └── correlations.py     # Co-ocurrencias
│   ├── scoring/
│   │   ├── scorer.py           # Sistema de scoring unificado
│   │   └── weights.py          # Gestión de pesos
│   ├── generator/
│   │   ├── combination.py      # Generación de combinaciones
│   │   └── optimizer.py        # Algoritmos genéticos
│   ├── backtesting/
│   │   ├── backtester.py       # Sistema de backtesting
│   │   └── evaluator.py        # Métricas de rendimiento
│   └── config.py               # Configuración global
├── utils/
│   └── data_generator.py       # Generador de datos de muestra
├── data/                        # Directorio para datos históricos
├── configs/                     # Perfiles de pesos guardados
└── ejemplo_uso.py              # Ejemplo completo de uso
```

## 🚀 Instalación

### Requisitos
- Python 3.8+
- pandas
- numpy

### Instalar dependencias

```bash
pip install pandas numpy
```

## 📖 Uso Rápido

### 1. Preparar Datos Históricos

Tienes dos opciones:

**Opción A: Usar tus datos reales**

Crea un archivo CSV en `data/quini6_historico.csv` con el formato:

```csv
sorteo_id,fecha,num1,num2,num3,num4,num5,num6
1,2024-01-01,5,12,23,34,41,45
2,2024-01-04,2,15,28,30,39,44
...
```

**Opción B: Generar datos de muestra**

```bash
python utils/data_generator.py
```

### 2. Ejecutar el Sistema

```bash
python ejemplo_uso.py
```

### 3. Ejemplo de Código

```python
from core.data import DataLoader
from core.analysis import FrequencyAnalyzer
from core.scoring import UnifiedScorer
from core.generator import CombinationGenerator

# Cargar datos
loader = DataLoader()
data = loader.load_csv('data/quini6_historico.csv')

# Analizar frecuencias
analyzer = FrequencyAnalyzer()
analyzer.analyze(data)

# Calcular scores
scorer = UnifiedScorer()
scores = scorer.calculate_scores(analyzer)

# Generar predicción
generator = CombinationGenerator()
prediccion = generator.generate_with_constraints(scores)

print(f"Predicción: {prediccion}")
```

## ⚙️ Configuración de Pesos

Los pesos controlan cómo se combinan diferentes métricas para calcular scores:

```python
pesos = {
    'peso_frecuencia': 0.35,           # Frecuencia histórica
    'peso_frecuencia_reciente': 0.25,  # Frecuencia últimos N sorteos
    'peso_ciclo': 0.15,                # Ciclo de aparición
    'peso_latencia': 0.15,             # Tiempo desde última aparición
    'peso_tendencia': 0.10,            # Tendencia (aceleración)
}
```

### Perfiles Predefinidos

- **balanced**: Equilibrio entre todas las métricas
- **frequency_focused**: Prioriza números más frecuentes
- **recent_trends**: Prioriza tendencias recientes
- **conservative**: Prioriza números con mayor latencia

```python
from core.scoring import WeightManager

weight_manager = WeightManager()
weight_manager.create_default_profiles()
weight_manager.load_profile('balanced')
```

## 🧪 Backtesting y Validación

El sistema incluye backtesting para validar predicciones:

```python
from core.backtesting import Backtester

backtester = Backtester(test_size=20)
summary = backtester.run_backtest(data, weights=pesos)
backtester.print_results()
```

Esto divide los datos en train/test y evalúa:
- ✅ Distribución de aciertos (6/6, 5/6, 4/6, 3/6)
- ✅ Promedio de aciertos
- ✅ ROI simulado

## 🎲 Restricciones de Combinaciones

El generador aplica restricciones configurables:

```python
restricciones = {
    'min_pares': 2,              # Mínimo de números pares
    'max_pares': 4,              # Máximo de números pares
    'min_consecutivos': 0,       # Mínimo consecutivos
    'max_consecutivos': 2,       # Máximo consecutivos
    'suma_min': 60,              # Suma mínima
    'suma_max': 200,             # Suma máxima
    'min_por_rango': 1,          # Mínimo por rango (bajo/medio/alto)
}

generator.update_constraints(restricciones)
```

## 🧬 Optimización con Algoritmos Genéticos

Para predicciones más sofisticadas:

```python
from core.generator import CombinationOptimizer

optimizer = CombinationOptimizer()
mejor_combinacion = optimizer.genetic_algorithm(
    scores,
    population_size=100,
    generations=50,
    mutation_rate=0.1
)
```

## 📊 Análisis Incluidos

### Análisis de Frecuencias
- Frecuencia absoluta y relativa
- Números "calientes" y "fríos"
- Ciclos de aparición
- Latencia (tiempo desde última aparición)
- Tendencias (aceleración/desaceleración)

### Análisis de Patrones
- Rachas y sequías
- Patrones mensuales
- Estacionalidad

### Análisis de Correlaciones
- Pares que salen juntos
- Tripletas recurrentes
- Anti-correlaciones

## 📈 Métricas y Reportes

```python
from core.backtesting import PerformanceEvaluator

evaluator = PerformanceEvaluator()
evaluator.add_prediction(prediccion, resultado_real)
metrics = evaluator.calculate_metrics()
evaluator.print_report()
```

## ⚠️ Consideraciones Importantes

**Este sistema es para análisis estadístico y aprendizaje:**

- ❌ El Quini 6 es un sistema completamente aleatorio
- ❌ NO HAY forma de predecir con certeza los resultados
- ✅ Este sistema permite explorar patrones estadísticos
- ✅ Útil para aprender sobre probabilidades, ML y análisis de datos
- ✅ Las predicciones son probabilísticas, no garantías

**Uso responsable:**
- No inviertas más de lo que puedes permitirte perder
- El juego debe ser recreativo, no una inversión
- Conoce las probabilidades reales del Quini 6

## 🔮 Próximas Mejoras (Roadmap)

- [ ] Modelos de Machine Learning (Random Forest, LSTM)
- [ ] Optimización automática de hiperparámetros (Bayesian Optimization)
- [ ] Interfaz gráfica (GUI)
- [ ] API REST
- [ ] Visualizaciones interactivas
- [ ] Base de datos SQL para historial

## 📝 Licencia

MIT License - Uso libre con atribución

## 👤 Autor

Charly Predictor Team

---

**¿Preguntas o sugerencias?**  
Este es un sistema modular y extensible. Puedes agregar tus propios análisis, métricas o algoritmos.
