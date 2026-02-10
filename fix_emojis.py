#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script temporal para reemplazar emojis por iconos sobrios"""

import re

# Leer el archivo
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazos de emojis a iconos sobrios
replacements = {
    # Sidebar
    'st.markdown("### � Datos Históricos")': 'st.markdown("### ◉ Datos Históricos")',
    'st.markdown("###  Datos Históricos")': 'st.markdown("### ◉ Datos Históricos")',
    'st.markdown("###  Datos Hist�ricos")': 'st.markdown("### ◉ Datos Históricos")',
    'st.markdown("### 🎲 Método de Predicción")': 'st.markdown("### ◈ Método de Predicción")',
    
    # Área principal - Análisis
    'st.markdown("### 🔥 Top 10 Números Calientes")': 'st.markdown("### ▲ Top 10 Números Calientes")',
    'st.markdown("### ❄️ Top 10 Números Fríos")': 'st.markdown("### ▼ Top 10 Números Fríos")',
    'st.markdown("### 🔗 Pares Más Frecuentes")': 'st.markdown("### ◆ Pares Más Frecuentes")',
    
    # Predicción
    'st.markdown("### 📌 Método Estándar")': 'st.markdown("### ○ Método Estándar")',
    'st.markdown("### 🧠 Método Condicional")': 'st.markdown("### ● Método Condicional")',
    
    # Títulos nivel 2
    'st.markdown("## 🎲 Generar Predicción")': 'st.markdown("## ◉ Generar Predicción")',
    'st.markdown("## 📊 Análisis Estadístico Detallado")': 'st.markdown("## ◐ Análisis Estadístico Detallado")',
    'st.markdown("## 📈 Visualizaciones Interactivas")': 'st.markdown("## ◪ Visualizaciones Interactivas")',
    'st.markdown("## 📜 Historial de Predicciones")': 'st.markdown("## ◫ Historial de Predicciones")',
}

# Aplicar reemplazos
for old, new in replacements.items():
    content = content.replace(old, new)

# Guardar el archivo actualizado
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Emojis reemplazados exitosamente")
