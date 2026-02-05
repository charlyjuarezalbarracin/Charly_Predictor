"""
Configuración global del sistema de predicción
"""

# Configuración del Quini 6
QUINI6_CONFIG = {
    'min_number': 0,
    'max_number': 45,
    'numbers_per_draw': 6,
}

# Parámetros ajustables del sistema de scoring
DEFAULT_WEIGHTS = {
    'peso_frecuencia': 0.35,           # Peso de frecuencia absoluta
    'peso_frecuencia_reciente': 0.25,  # Peso de frecuencia en últimos N sorteos
    'peso_ciclo': 0.15,                # Peso del ciclo esperado
    'peso_latencia': 0.15,             # Peso del tiempo desde última aparición
    'peso_tendencia': 0.10,            # Peso de tendencia temporal
}

# Parámetros de análisis temporal
TEMPORAL_PARAMS = {
    'ventana_reciente': 50,      # Últimos N sorteos para análisis reciente
    'decay_factor': 0.95,        # Factor de decaimiento exponencial
    'min_sorteos_ciclo': 10,     # Mínimo de sorteos para calcular ciclos
}

# Parámetros de backtesting
BACKTESTING_PARAMS = {
    'test_size': 20,             # Cantidad de sorteos para validación
    'min_train_size': 100,       # Mínimo de sorteos históricos necesarios
}

# Restricciones para generación de combinaciones
COMBINATION_CONSTRAINTS = {
    'min_pares': 2,              # Mínimo de números pares
    'max_pares': 4,              # Máximo de números pares
    'min_consecutivos': 0,       # Mínimo de números consecutivos
    'max_consecutivos': 2,       # Máximo de números consecutivos
    'suma_min': 60,              # Suma mínima de la combinación
    'suma_max': 200,             # Suma máxima de la combinación
    'rango_bajo': (0, 15),       # Números bajos
    'rango_medio': (16, 30),     # Números medios
    'rango_alto': (31, 45),      # Números altos
    'min_por_rango': 1,          # Mínimo un número de cada rango
}
