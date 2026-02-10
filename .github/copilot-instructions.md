# Instrucciones para GitHub Copilot - Charly Predictor

## 🚫 NO Hacer
- NO agregar emojis/íconos a botones, labels o elementos de UI
- NO crear archivos markdown de documentación/resumen después de cada cambio
- NO ofrecer opción "Datos de Muestra" en la interfaz

## ✅ SÍ Hacer
- PREGUNTAR antes de implementar cambios para validar comprensión (a menos que usuario diga "hazlo" o "listo")
- Usar `multi_replace_string_in_file` para edits múltiples independientes
- Usar SIEMPRE datos reales del CSV
- Mantener código en español (comentarios, nombres)
- Respuestas concisas y directas

## Configuración Optimizada (NO modificar)
```python
OPTIMAL_WEIGHTS = {
    'peso_frecuencia': 0.25,
    'peso_frecuencia_reciente': 0.25,
    'peso_ciclo': 0.25,
    'peso_latencia': 0.00,  # Eliminado intencionalmente
    'peso_tendencia': 0.25,
}
OPTIMAL_STRATEGY = 'BOTH'
```

## Contexto del Proyecto
- Sistema de predicción de lotería Quini 6
- 412 sorteos históricos reales
- Optimización completada: 9/24 aciertos (2.25/sorteo)
- 130+ configuraciones probadas
- Interfaz web con Streamlit
- Tema Midasmind (naranja #F2A100)

## Archivos Clave
- `app.py` - Interfaz web principal
- `configs/config_optimizada.py` - Configuración óptima
- `core/` - Módulos principales
- `data/quini6_historico.csv` - Datos reales
- `varios/scraper_quiniya_final.py` - Actualización automática

## Patrones de Código
- Usar `@st.cache_data` para funciones de carga
- Limpiar cachés con `.clear()` al actualizar
- Preferir claridad sobre brevedad
