# 🎯 Charly Predictor - Sistema de Predicción de Quini 6

Sistema profesional de análisis estadístico y predicción de números para la lotería Quini 6, implementado en Python con arquitectura modular y dos estrategias de generación independientes.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Características Principales

### 🔬 Análisis Estadístico Multi-Dimensional
- **Frecuencias**: Análisis de aparición absoluta, relativa y reciente
- **Patrones Temporales**: Detección de ciclos, tendencias y estacionalidad
- **Correlaciones**: Análisis de co-ocurrencias entre números (pares, tripletas)
- **Números Calientes/Fríos**: Identificación de números con mayor/menor probabilidad

### 🎲 Dual Strategy System (Innovación Clave)
- **Método Estándar**: Generación con probabilidades estáticas (rápido)
- **Método Condicional**: Probabilidades dinámicas que consideran correlaciones (inteligente)
- **Comparación Lado a Lado**: Sistema para evaluar ambos métodos simultáneamente

### 🎯 Sistema de Scoring Configurable
- Ponderación ajustable de múltiples métricas
- Perfiles predefinidos (conservador, balanceado, agresivo)
- Capacidad de crear y guardar perfiles personalizados

### 🧬 Optimización Avanzada
- Algoritmos genéticos para búsqueda de combinaciones óptimas
- Monte Carlo para simulación de resultados
- Restricciones configurables (pares/impares, consecutivos, suma, rangos)

### ✅ Validación y Backtesting
- Sistema de train/test split
- Métricas de rendimiento detalladas
- Evaluación histórica de precisión

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/charlyjuarezalbarracin/Charly_Predictor.git
cd Charly_Predictor

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python test_instalacion.py
```

### 2. Uso Inmediato (Script Simple)

```bash
python mi_predictor.py
```

Este script:
- ✅ Genera datos de muestra automáticamente (o usa tus datos reales)
- ✅ Ejecuta análisis completo
- ✅ Muestra top 10 números calientes
- ✅ Genera predicción de 6 números
- ✅ Permite elegir entre métodos estándar, condicional o ambos

### 3. Usar con Datos Reales

1. Crear archivo `data/quini6_historico.csv`:
```csv
sorteo_id,fecha,num1,num2,num3,num4,num5,num6
1,2025-10-22,02,04,10,37,38,44
2,2025-10-26,11,29,36,39,42,43
...
```

2. El script detectará automáticamente el archivo y lo usará.

## 📚 Ejemplos de Uso

### Ejemplo 1: Predicción Simple
```python
from core.data import DataLoader
from core.analysis import FrequencyAnalyzer
from core.scoring import UnifiedScorer
from core.generator import CombinationGenerator

# Cargar datos
loader = DataLoader()
data = loader.load_csv('data/quini6_historico.csv')

# Análisis
analyzer = FrequencyAnalyzer()
analyzer.analyze(data)

# Scoring
scorer = UnifiedScorer()
scores = scorer.calculate_scores(analyzer)

# Generar predicción
generator = CombinationGenerator()
prediccion = generator.generate_with_constraints(scores)
print(f"Predicción: {prediccion}")
```

### Ejemplo 2: Comparar Ambos Métodos
```python
from core.generator import StrategyManager, GenerationStrategy

manager = StrategyManager()

# Generar con ambos métodos
result = manager.generate(
    scores,
    strategy=GenerationStrategy.BOTH,
    correlation_analyzer=corr_analyzer
)

print(f"Estándar:    {result['standard']['combination']}")
print(f"Condicional: {result['conditional']['combination']}")
```

### Ejemplo 3: Sistema Completo con Backtesting
```bash
python ejemplo_uso.py
```

## 🏗️ Arquitectura del Proyecto

```
Charly_Predictor/
├── core/
│   ├── data/              # Carga y validación de datos
│   ├── analysis/          # Análisis estadístico
│   ├── scoring/           # Sistema de puntuación
│   ├── generator/         # Generación de combinaciones
│   │   └── advanced/      # Método condicional (probabilidades dinámicas)
│   └── backtesting/       # Validación histórica
├── tests/                 # Suite de tests
├── utils/                 # Utilidades
├── data/                  # Datos históricos (no incluidos en repo)
├── mi_predictor.py        # 🌟 Script simple para uso diario
├── ejemplo_uso.py         # Ejemplo completo
└── ejemplo_comparacion_metodos.py  # Comparación de estrategias
```

## ⚙️ Configuración

### Cambiar Método de Generación
Editar `mi_predictor.py` línea 28:
```python
metodo_usar = "ESTANDAR"      # Rápido, probabilidades fijas
metodo_usar = "CONDICIONAL"   # Inteligente, considera correlaciones
metodo_usar = "AMBOS"         # Compara ambos
```

### Ajustar Pesos de Scoring
```python
from core.scoring import UnifiedScorer

pesos = {
    'peso_frecuencia': 0.35,
    'peso_frecuencia_reciente': 0.25,
    'peso_ciclo': 0.15,
    'peso_latencia': 0.15,
    'peso_tendencia': 0.10
}

scorer = UnifiedScorer(pesos)
```

## 🧪 Testing

```bash
# Test rápido de instalación
python test_instalacion.py

# Suite completa de tests
python tests/test_strategies.py
```

## 📖 Documentación Completa

| Archivo | Descripción |
|---------|-------------|
| `RESUMEN_EJECUTIVO.txt` | Guía práctica de operación |
| `COMO_USAR_AHORA.txt` | Tutorial paso a paso |
| `GUIA_COMPLETA.txt` | Documentación técnica completa (900+ líneas) |

## 🛣️ Roadmap

- [x] Sistema de análisis estadístico completo
- [x] Dual strategy (estándar + condicional)
- [x] Backtesting y validación
- [x] Scripts de uso simple
- [ ] Interfaz gráfica (GUI) con Streamlit/Tkinter
- [ ] Modelos de Machine Learning (LSTM, Random Forest)
- [ ] API REST para integración
- [ ] Dashboard de visualización avanzada

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para más detalles.

## 👤 Autor

**Charly Juarez Albarracin**
- GitHub: [@charlyjuarezalbarracin](https://github.com/charlyjuarezalbarracin)

## ⚠️ Disclaimer

Este sistema es una herramienta de análisis estadístico con fines educativos y de investigación. Los resultados no garantizan ningún éxito en juegos de azar. Juega responsablemente.

---

⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub!
