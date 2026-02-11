# Instrucciones para GitHub Copilot - Charly Predictor

## 🚫 NO Hacer
- NO agregar emojis/íconos a botones, labels o elementos de UI
- NO agregar emojis/íconos en labels, checkboxes, radio buttons, o cualquier elemento visual
- NO usar colores que se salgan del diseño actual (tema Midasmind)
- NO crear archivos markdown de documentación/resumen después de cada cambio
- NO ofrecer opción "Datos de Muestra" en la interfaz
- NO agregar elementos decorativos, textos de ayuda, expanders o secciones que no sean estrictamente necesarios
- NO agregar "propaganda" o descripciones promocionales de funcionalidades

## 🎨 Diseño Minimalista y Profesional
- Sistema serio de predicción, NO es un proyecto de estudiante ni demo
- Interfaz limpia, sin decoraciones innecesarias
- Solo texto plano en labels y botones
- Mantener coherencia con paleta de colores existente: #F2A100 (naranja Midasmind), grises neutros
- Evitar iconos decorativos, símbolos, o formateos excesivos en la UI
- Priorizar claridad y funcionalidad sobre estética visual
- Solo agregar elementos estrictamente necesarios para el funcionamiento
- Diseño compacto: tamaños de fuente, padding y márgenes reducidos
- NO usar expanders para ocultar información importante, todo debe ser visible directamente

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
