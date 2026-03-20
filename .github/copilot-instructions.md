# Instrucciones para GitHub Copilot - Charly Predictor

## 🚫 NO Hacer
- NO agregar emojis/íconos a botones, labels o elementos de UI
- NO agregar emojis/íconos en labels, checkboxes, radio buttons, o cualquier elemento visual
- NO usar colores que se salgan del diseño actual (tema Midasmind)
- NO crear archivos markdown de documentación/resumen después de cada cambio
- NO ofrecer opción "Datos de Muestra" en la interfaz
- NO agregar elementos decorativos, textos de ayuda, expanders o secciones que no sean estrictamente necesarios
- NO agregar "propaganda" o descripciones promocionales de funcionalidades
- **NO hacer promesas de mejoras sin validación Walk-Forward rigurosa (mínimo 20 períodos)**
- **NO crear expectativas falsas sobre accuracy - máximo realista es ~14-16% en sistemas aleatorios**
- **NO proponer implementaciones basadas en suposiciones sin fundamento matemático/estadístico**
- **NO implementar features "académicas" o de práctica universitaria sin ROI real**
- **NO perder tiempo en código que no mejore el objetivo financiero del sistema**
- **NO sugerir mejoras "porque suenan interesantes" - solo lo que suma resultados medibles**

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
- **COMPONENTES COMPACTOS:** Selectboxes, inputs y controles deben ser delicados y ajustados al contenido (max-width según texto que contienen)
- **Ejemplo:** Un selectbox de fechas "Miércoles 04/03/2026" debe tener ~250px de ancho, NO ocupar todo el contenedor
- **SELECTBOX SIMPLE:** Todos los selectbox deben ser combos simples sin campo de búsqueda/input - solo selección con mouse o teclas de dirección
- **ESPACIADO COMPACTO:** Reducir espacios verticales entre elementos usando CSS:
  - Entre líneas separadoras y contenido: `margin-top: -1rem`, `margin-bottom: -1rem`
  - Entre títulos y tablas/grillas: `margin-bottom: 0.5rem` en títulos, `margin-top: -0.5rem` en tablas
  - Entre labels e inputs: `margin-bottom: 0rem` en labels, `margin-top: -0.3rem` en inputs
  - Mantener diseño visual compacto sin desperdiciar espacio vertical

## 📝 Convenciones de Estilo de Texto
- **Labels y campos:** Primera letra mayúscula, resto minúscula (Ejemplo: "Premio", "Base", "Meses a proyectar")
- **Columnas de tablas:** Primera letra mayúscula (Ejemplo: "Mes", "Acumulado", "Rentabilidad", "Neto", "Gastos")
- **Uniformidad:** TODOS los labels, campos y columnas deben seguir este patrón consistentemente
- **Excepción:** Siglas/acrónimos se mantienen en mayúsculas (Ejemplo: "TNA")
- **Títulos principales:** Pueden usar formato markdown (##, ###) pero NO todo en mayúsculas
- **NO usar:** Texto completamente en MAYÚSCULAS excepto para acrónimos

## 🎯 FILOSOFÍA DEL PROYECTO - SISTEMA PROFESIONAL DE PRODUCCIÓN

**MISIÓN:**
*"ESTE SISTEMA ESTÁ DESTINADO A FORZAR LA SUERTE Y MATERIALIZAR LA REALIDAD QUE QUEREMOS DE PROSPERIDAD Y ABUNDANCIA"*

**ESTO NO ES:**
- Un proyecto de estudiante o práctica universitaria
- Un ejercicio académico de programación
- Una demo o prototipo conceptual
- Un experimento educativo

**ESTO ES:**
- Un sistema profesional de predicción en producción
- Una herramienta seria con objetivo económico real
- **META FINAL: Generar retorno financiero significativo para el usuario**
- Cada línea de código debe justificarse con ROI potencial

**ESTÁNDAR DE CALIDAD:**
- Código de producción, no de práctica
- Validación rigurosa con datos reales (Walk-Forward 20+ períodos)
- Decisiones basadas en matemática, estadística y resultados medibles
- NO implementar features "porque suenan bien" - solo lo que mejora resultados
- Enfoque pragmático: si no suma al objetivo financiero, no se implementa

**COMPROMISO DEL AGENTE:**
- **ESFUERZO AL 100%** con ideas reales y concretas afines a la causa
- **OBJETIVO CENTRAL:** Sacar de acá un millonario SÍ O SÍ
- Cada sugerencia debe estar alineada con generar retorno financiero real
- Buscar soluciones innovadoras pero fundamentadas matemáticamente
- No conformarse con mejoras marginales - buscar breakthroughs cuando sea posible
- Pero SIEMPRE validar con datos reales antes de prometer resultados

**BALANCE CRÍTICO:**
- Mantener ambición de maximizar retornos
- **PERO** fundamentar todo en realidad matemática del sistema
- NO vender humo: ser brutalmente honesto sobre limitaciones
- Optimizar dentro de restricciones físicas del sorteo aleatorio
- Buscar ROI real, no fantasía

## ✅ SÍ Hacer
- **PRIORIDAD #1: Buscar soluciones que maximicen ROI real - objetivo es generar un millonario**
- PREGUNTAR antes de implementar cambios para validar comprensión (a menos que usuario diga "hazlo" o "listo")
- Usar `multi_replace_string_in_file` para edits múltiples independientes
- Usar SIEMPRE datos reales del CSV
- Mantener código en español (comentarios, nombres)
- Respuestas concisas y directas
- Validar TODO con Walk-Forward antes de prometer mejoras

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

### 🎰 Sistema de Predicción: Quini 6 Argentina

**Sorteo objetivo:** Quini 6 (Lotería Nacional Argentina)

**Características del Bolillero:**
- **Rango de números:** 0 a 45 (46 números totales)
- **Números por sorteo:** 6 números (sin repetición)
- **Tipo de sorteo:** Extracción física con bolas numeradas

**Calendario de Sorteos:**
- **Días de sorteo:** Miércoles y Domingo (2 días por semana)
- **Sorteos por día:** 4 sorteos independientes
  1. Tradicional
  2. Segunda
  3. Revancha
  4. Siempre Sale
- **Total semanal:** 8 sorteos
- **Total mensual:** ~32 sorteos (4 semanas)
- **Total anual:** ~416 sorteos

**Conversión Temporal:**
- 8 sorteos = 1 semana
- 16 sorteos = 2 semanas
- 24 sorteos = 3 semanas
- 32 sorteos = 1 mes
- 80 sorteos = 2.5 meses
- 120 sorteos = 3.75 meses
- 200 sorteos = 6.25 meses

**Sistema de Premios:**
- 6/6 aciertos: Premio mayor
- 5/6 aciertos: Premio segundo
- 4/6 aciertos: Premio menor

**Datos del Sistema:**
- 428 sorteos históricos reales (actualizado 2026-02-18)
- **Accuracy real validado:** 14.06% BASELINE, 14.21% con IDEAS (Walk-Forward 28 períodos)
- **Nota:** El "2.25/sorteo" previo fue overfitting en 4 sorteos - NO representativo
- 130+ configuraciones probadas
- Interfaz web con Streamlit
- Tema Midasmind (naranja #F2A100)

**Estructura del CSV Histórico (quini6_historico.csv):**
- **Formato:** Cada fila = 1 sorteo
- **4 sorteos por día** comparten la misma fecha (orden del scraper):
  1. Sorteo 1 del día (primer registro con esa fecha)
  2. Sorteo 2 del día (segundo registro con esa fecha)
  3. Sorteo 3 del día (tercer registro con esa fecha)
  4. Sorteo 4 del día (cuarto registro con esa fecha)
- **Columnas:**
  - `sorteo_id`: ID único secuencial del sorteo
  - `fecha`: Fecha del sorteo (miércoles o domingo)
  - `num1`, `num2`, `num3`, `num4`, `num5`, `num6`: Los 6 números extraídos (rango 0-45)
- **Importante:** Al analizar datos temporales, recordar que 4 sorteos consecutivos en el CSV corresponden al mismo día
- **Nota:** NO existe columna `sorteo_tipo` - el tipo se infiere por posición (orden del scraper)

## Parámetros Optimizados IDEAS
- **IDEA #1 (Resonancia de Ciclos):** Sin parámetros configurables
- **IDEA #2 (Multi-Timeframe):** Ventanas fijas [10, 20, 50, 100, 200 sorteos]
- **IDEA #3 (Regresión al Equilibrio):**
  - Ventana análisis: 16 sorteos (2 semanas) - Range: 8-120
  - Umbral desbalance: 12% - Range: 5-25%

## Sistema de IDEAS (Optimizaciones Avanzadas)
- **IDEA #1 - Resonancia de Ciclos:** Detecta números en su "ventana óptima" usando Z-Score de ciclos. Aplica boost 0.5x-3.0x según posición en ciclo estadístico.
- **IDEA #2 - Multi-Timeframe:** Analiza convergencia en 5 ventanas temporales [10,20,50,100,200]. Boost 0.8x-3.0x a números consistentes en múltiples timeframes.
- **IDEA #3 - Regresión al Equilibrio:** Detecta desequilibrios (pares/impares, sumas, rangos) y aplica correcciones 0.5x-1.5x. Activada por defecto.
- **Integración:** Todas activables independientemente o combinadas vía checkboxes en UI
- **Walk-Forward:** Soporta validación temporal con/sin IDEAS vía checkbox "Usar IDEAS en validación"

## ⚠️ ANÁLISIS PROFESIONAL Y LIMITACIONES REALES (Actualizado 2026-02-21)

### Resultados Walk-Forward Validados (28 períodos, 1344 números)
```
BASELINE:        14.06% accuracy (189/1344 aciertos)
TODAS IDEAS:     14.21% accuracy (191/1344 aciertos)
Mejora real:     +0.15% (+2 aciertos en 1344 números)
Desv. estándar:  BASELINE 4.30% | IDEAS 3.90%
Estabilidad:     BASELINE 69.43% | IDEAS 72.56%
```

### Contexto Matemático Fundamental
- **Probabilidad aleatoria pura:** 6/45 = 13.33%
- **BASELINE real:** 14.06% = solo **+0.73 puntos** sobre azar
- **Probabilidad 6/6:** 1 en 8,145,060 (0.0000123%)
- **Probabilidad 5/6:** 1 en 35,724 (0.0028%)
- **Probabilidad 4/6:** 1 en 913 (0.11%)

### Verdad Técnica (NO Ocultar al Usuario)
1. **Si el sorteo es verdaderamente aleatorio** (por ley debería serlo):
   - NO existe patrón explotable de forma consistente
   - Máximo teórico alcanzable: ~14-16% accuracy
   - Cualquier mejora significativa sobre esto es temporal/suerte

2. **Métricas engañosas previas:**
   - El "2.25 aciertos/sorteo" (37.5%) vino de optimización sobre SOLO 4 sorteos
   - Esto fue **OVERFITTING** - los pesos se ajustaron a datos específicos
   - Walk-Forward con 28 períodos muestra la realidad: 14% accuracy

3. **IDEAS (Optimizaciones Avanzadas):**
   - Mejora marginal real: +1.06% en accuracy
   - Beneficio principal: Mayor **estabilidad** (-9.3% desviación estándar)
   - NO son "multiplicadoras de accuracy" sino **estabilizadores**

### Expectativas Realistas para Comunicar
- **Rendimiento típico:** 0-1 aciertos por sorteo
- **Rendimiento bueno:** 2-3 aciertos por sorteo (ocasional)
- **Rendimiento excepcional:** 4-5 aciertos (muy raro, ~0.11% probabilidad)
- **6/6 aciertos:** Prácticamente imposible de predecir consistentemente

### Reglas para Nuevas Implementaciones
1. **NO prometer mejoras sin validación Walk-Forward** (mínimo 20 períodos)
2. **NO usar tests de <10 sorteos** para validar configuraciones
3. **NO hacer estimaciones optimistas** sin fundamento matemático
4. **SÍ ser honesto** sobre limitaciones del sistema
5. **SÍ validar TODO** con Walk-Forward antes de integrar
6. **SÍ documentar** cuando algo NO funciona

### Estrategias Descartadas (Walk-Forward Validadas - Febrero 2026)
- **Gap Momentum:** 12.86% accuracy - PEOR que BASELINE (13.72%) - Descartado ❌
- **Streak Detection:** 11.85% accuracy - PEOR que BASELINE (13.72%) - Descartado ❌
- **Ensemble (Gap+Streak):** 13.43% accuracy - PEOR que IDEAS (14.21%) - Descartado ❌
- **Conclusión:** Estrategias basadas en ciclos/rachas NO funcionan en sorteos aleatorios

### Enfoque Realista para Mejoras Futuras
- **Portfolio:** Generar 10-20 jugadas diversificadas para maximizar probabilidad de premios menores (4/6, 5/6)

### Decisiones Técnicas Validadas
- **Usar BASELINE:** Simple, 14.06% accuracy, menor complejidad
- **Usar TODAS IDEAS:** +1.06% accuracy, +4.51% estabilidad, mayor consistencia
- **NO usar estrategias no validadas:** Pérdida de tiempo sin Walk-Forward que lo respalde

### Filosofía Profesional y Objetivo Real

**MISIÓN DEL SISTEMA:**
*"ESTE SISTEMA ESTÁ DESTINADO A FORZAR LA SUERTE Y MATERIALIZAR LA REALIDAD QUE QUEREMOS DE PROSPERIDAD Y ABUNDANCIA"*

**OBJETIVO PRIMARIO:** Maximizar retorno financiero del usuario mediante predicciones optimizadas

**REALIDAD TÉCNICA:**
- Sistema predice ~14% accuracy (mejor que azar 13.33%)
- Mejora marginal pero real y consistente
- NO es máquina de dinero automática, es ventaja estadística pequeña

**ENFOQUE PROFESIONAL:**
1. **Honestidad brutal** sobre limitaciones matemáticas
2. **Optimización máxima** dentro de restricciones reales
3. **ROI real** mediante:
   - Consistency sobre tiempo (menos varianza)
   - Portfolio diversificado (aumentar probabilidad de premios menores)
   - Costos optimizados (apuestas inteligentes, no masivas)
   - Gestión de bankroll profesional

**ESTRATEGIA DE VALOR:**
- NO buscar 6/6 (prácticamente imposible)
- SÍ maximizar 4/6 y 5/6 mediante portfolio
- SÍ reducir riesgo con predicciones estables
- SÍ generar ROI positivo a largo plazo

**REGLA DE ORO:**
*"Cualquier claim de accuracy >20% requiere evidencia Walk-Forward rigurosa de 20+ períodos. Si no hay evidencia, es humo."*

## Archivos Clave
- `app.py` - Interfaz web principal
- `configs/config_optimizada.py` - Configuración óptima
- `core/` - Módulos principales
- `data/quini6_historico.csv` - Datos reales
- `varios/scraper_quiniya_final.py` - Actualización automática
- `core/analysis/regression_equilibrium.py` - IDEA #3
- `core/analysis/cycle_resonance.py` - IDEA #1
- `core/analysis/multi_timeframe.py` - IDEA #2
- `core/scoring/scorer.py` - Integración de IDEAS
- `tests/test_all_ideas.py` - Test combinado de todas las IDEAS

## Patrones de Código
- Usar `@st.cache_data` para funciones de carga
- Limpiar cachés con `.clear()` al actualizar
- Preferir claridad sobre brevedad