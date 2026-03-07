"""
================================================================================
  CHARLY PREDICTOR - INTERFAZ GRÁFICA WEB
  Sistema de Predicción de Quini 6
================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from pathlib import Path

# Importaciones del core
from core.data import DataLoader
from core.analysis import FrequencyAnalyzer, CorrelationAnalyzer, PatternAnalyzer
from core.scoring import UnifiedScorer
from core.generator import StrategyManager, GenerationStrategy, PortfolioGenerator
from core.backtesting import WalkForwardBacktester
from utils.data_generator import generate_sample_data
from varios.scraper_quiniya_final import actualizar_historico_csv, obtener_pozos_ultimo_sorteo

# Importar configuración optimizada
try:
    from configs.config_optimizada import OPTIMAL_WEIGHTS, OPTIMAL_STRATEGY
except ImportError:
    # Valores por defecto si no existe la config optimizada
    OPTIMAL_WEIGHTS = {
        'peso_frecuencia': 0.25,
        'peso_frecuencia_reciente': 0.25,
        'peso_ciclo': 0.25,
        'peso_latencia': 0.00,
        'peso_tendencia': 0.25,
    }
    OPTIMAL_STRATEGY = 'BOTH'


# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Charly Predictor - Quini 6",
    page_icon="CP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Estilo Midasmind
st.markdown("""
<style>
    /* Forzar tema claro en toda la aplicación */
    .stApp {
        background-color: #F9F9F9;
    }
    
    /* Tema principal */
    .main {
        background-color: #F9F9F9;
        padding: 1.2rem 1rem;
    }
    
    /* Forzar fondo claro en el área de contenido */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }
    
    /* Área principal de contenido */
    section[data-testid="stMain"] {
        background-color: #f8f9fa;
    }

    /* Reducir padding vertical general del contenedor principal */
    section[data-testid="stMain"] .block-container {
        padding-top: 0.6rem;
        padding-bottom: 1rem;
    }

    /* Banner unificado para header principal y sidebar */
    .app-banner,
    .sidebar-banner {
        text-align: center;
        padding: 16px 14px;
        background: linear-gradient(135deg, #F2A100 0%, #E58E00 100%);
        border-radius: 0;
        margin: -1rem -1rem 0.9rem -1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 112px;
        position: relative;
    }

    .app-banner {
        min-height: 120px;
        padding-top: 60px;
        padding-bottom: 10px;
    }

    .banner-logo {
        background: white;
        width: 38px;
        height: 38px;
        border-radius: 11px;
        margin: 0 auto 10px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: #F2A100;
        font-weight: 700;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
    }

    .banner-title {
        color: white;
        margin: 0;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .banner-subtitle {
        color: rgba(255,255,255,0.95);
        margin: 6px 0 0 0;
        font-size: 12px;
        font-weight: 400;
    }

    .banner-fecha {
        position: absolute;
        right: 20px;
        bottom: 18px;
        color: rgba(255,255,255,0.85);
        font-size: 11px;
        font-weight: 400;
    }

    /* Tamaños especificos por panel */
    .app-banner .banner-title {
        font-size: 22px !important;
    }

    .app-banner .banner-subtitle {
        font-size: 18px !important;
    }

    .sidebar-banner .banner-title {
        font-size: 20px !important;
    }

    .sidebar-banner .banner-subtitle {
        font-size: 12px !important;
    }
    
    /* Tarjetas de números predichos - Estilo Midasmind */
    .numero-predicho {
        background: linear-gradient(135deg, #F2A100 0%, #E58E00 100%);
        color: white;
        padding: 16px 12px;
        border-radius: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(242, 161, 0, 0.3);
        margin: 0;
        border: none;
        width: 95px;
    }
    
    /* Contenedor grid para números */
    .numeros-grid {
        display: grid;
        grid-template-columns: repeat(6, 95px);
        gap: 12px;
        justify-content: flex-start;
        margin: 2px 0 15px 0;
    }
    
    /* Tarjetas de estadísticas */
    .stat-card {
        background: white;
        padding: 16px 20px;
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #F2A100;
    }
    
    /* Tarjetas en sidebar */
    [data-testid="stSidebar"] .stat-card {
        border-left-color: #F2A100;
    }
    
    /* Botones estilo Píldora Midasmind */
    .stButton>button {
        background: white;
        color: #333333;
        border-radius: 50px;
        padding: 12px 24px;
        border: 2px solid #F2A100;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s;
        box-shadow: 0 2px 6px rgba(242, 161, 0, 0.15);
    }
    
    .stButton>button:hover {
        background: #F2A100;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(242, 161, 0, 0.3);
    }
    
    .stButton>button::after {
        content: " ›";
        margin-left: 8px;
        font-size: 18px;
    }
    
    /* Headers - Estilo limpio Midasmind */
    h1 {
        color: #333333 !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.5rem !important;
        font-weight: 700 !important;
    }
    
    h2 {
        color: #333333 !important;
        font-size: 1.5rem !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.2rem !important;
        font-weight: 600 !important;
    }
    
    h3 {
        color: #F2A100 !important;
        font-size: 1.1rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.2rem !important;
        font-weight: 600 !important;
    }

    
    h4, h5, h6 {
        color: #666666 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    
    /* Texto general */
    p, span, div {
        color: #333333;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* Métricas - Estilo Midasmind */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #F2A100 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666666 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar - Estilo Midasmind */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-radius: 0 30px 30px 0 !important;
        margin: 0 !important;
        box-shadow: 4px 0 20px rgba(0,0,0,0.08);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: white !important;
        border-radius: 0 30px 30px 0 !important;
    }
    
    /* Botón de colapsar sidebar */
    [data-testid="collapsedControl"] {
        background-color: #F2A100 !important;
        border-radius: 0 15px 15px 0 !important;
    }
    
    [data-testid="collapsedControl"] svg {
        color: white !important;
    }
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1 {
        font-size: 1.3rem !important;
        color: #333333 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem !important;
        color: #F2A100 !important;
        font-weight: 600 !important;
        margin-top: 0.6rem !important;
    }
    
    [data-testid="stSidebar"] h3 {
        font-size: 1rem !important;
        color: #333333 !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar labels y texto */
    [data-testid="stSidebar"] label {
        color: #666666 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stSidebar"] p {
        color: #666666 !important;
    }
    
    /* Sidebar divisores */
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
        border: none !important;
        border-top: 1px solid #f0f0f0 !important;
    }
    
    /* Sidebar - Botones estilo Píldora */
    [data-testid="stSidebar"] .stButton>button {
        background: white;
        color: #333333;
        border-radius: 50px;
        padding: 8px 12px;
        border: 2px solid #F2A100;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s;
        width: 100%;
        box-shadow: 0 2px 6px rgba(242, 161, 0, 0.12);
    }
    
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #F2A100;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(242, 161, 0, 0.25);
    }
    
    [data-testid="stSidebar"] .stButton>button::after {
        content: " ›";
        margin-left: 8px;
        font-size: 16px;
    }
    
    /* Sidebar - Radio buttons estilo limpio */
    [data-testid="stSidebar"] [data-baseweb="radio"] > div {
        gap: 0.35rem;
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"] label {
        padding: 6px 10px;
        border-radius: 50px;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    
    [data-testid="stSidebar"] [data-baseweb="radio"] label:hover {
        background-color: rgba(242, 161, 0, 0.08);
        border-color: #F2A100;
    }
    
    /* Sidebar - Expander estilo Midasmind */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: rgba(242, 161, 0, 0.06);
        border-radius: 15px;
        font-weight: 600;
        padding: 6px 10px;
        border: 1px solid rgba(242, 161, 0, 0.2);
    }
    
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background-color: rgba(242, 161, 0, 0.12);
        border-color: #F2A100;
    }
    
    /* Sidebar - Sliders con color dorado */
    [data-testid="stSidebar"] .stSlider > div > div > div {
        background-color: #F2A100;
    }
    
    /* Mensajes de info/success/warning */
    [data-testid="stSidebar"] .stAlert {
        padding: 6px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        border: none;
    }

    [data-testid="stSidebar"] .stAlert p {
        font-size: 0.75rem !important;
    }

    /* Sidebar - Compactar contenedores */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }

    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.35rem !important;
    }
    
    /* Tabs - Estilo Píldora Midasmind */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 0.8rem;
        border-bottom: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #666666;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 0.8rem 1.5rem;
        border-radius: 50px;
        border: 2px solid transparent;
        background-color: white;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #F2A100;
        color: #F2A100;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #F2A100;
        color: white;
        border-color: #F2A100;
    }
    
    /* Dataframes y tablas */
    [data-testid="stDataFrame"] {
        background-color: white;
        font-size: 0.9rem;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    /* Labels y textos de inputs */
    label {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #666666 !important;
    }
    
    /* Espaciado entre elementos - Más compacto */
    .element-container {
        margin-bottom: 0.5rem;
    }

    /* Separadores mas compactos */
    hr {
        margin: 0.6rem 0 !important;
    }
    
    /* Eliminar bordes externos de contenedores Streamlit */
    div[data-testid="column"],
    div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"],
    .stMarkdown,
    .row-widget,
    .element-container,
    [class*="st-emotion-cache"],
    div[class^="st-"] {
        border: none !important;
        outline: none !important;
    }
    
    /* Forzar sin sombras en contenedores generales */
    div[data-testid="column"],
    div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"] {
        box-shadow: none !important;
    }
    
    /* Inputs y selectbox estilo Midasmind */
    input, select, textarea {
        border-radius: 50px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 10px 16px !important;
    }
    
    input:focus, select:focus, textarea:focus {
        border-color: #F2A100 !important;
        box-shadow: 0 0 0 3px rgba(242, 161, 0, 0.1) !important;
    }
    
    /* Mensajes Success/Info/Warning - Estilo Midasmind con mayor especificidad */
    .stAlert, 
    [data-testid="stAlertContainer"],
    [data-testid="stNotification"], 
    div[data-baseweb="notification"],
    .stAlertContainer {
        border-radius: 20px !important;
        padding: 10px 16px !important;
        border-width: 2px !important;
        border-style: solid !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        min-height: auto !important;
    }
    
    /* Success - Verde suave Midasmind */
    [data-testid="stAlertContainer"][class*="success"],
    .stSuccess,
    div[data-baseweb="notification"][kind="success"],
    [data-testid="stNotification"][kind="success"] {
        background-color: rgba(76, 175, 80, 0.08) !important;
        border-color: #4CAF50 !important;
        color: #2E7D32 !important;
    }
    
    [data-testid="stAlertContainer"][class*="success"] *,
    .stSuccess * {
        color: #2E7D32 !important;
    }
    
    /* Info - Dorado Midasmind */
    [data-testid="stAlertContainer"][class*="info"],
    .stInfo,
    div[data-baseweb="notification"][kind="info"],
    [data-testid="stNotification"][kind="info"] {
        background-color: rgba(242, 161, 0, 0.08) !important;
        border-color: #F2A100 !important;
        color: #E58E00 !important;
    }
    
    [data-testid="stAlertContainer"][class*="info"] *,
    .stInfo * {
        color: #E58E00 !important;
    }
    
    /* Warning - Naranja */
    [data-testid="stAlertContainer"][class*="warning"],
    .stWarning,
    div[data-baseweb="notification"][kind="warning"],
    [data-testid="stNotification"][kind="warning"] {
        background-color: rgba(255, 152, 0, 0.08) !important;
        border-color: #FF9800 !important;
        color: #E65100 !important;
    }
    
    [data-testid="stAlertContainer"][class*="warning"] *,
    .stWarning * {
        color: #E65100 !important;
    }
    
    /* Remover iconos de alertas */
    .stAlert svg, 
    [data-testid="stNotification"] svg,
    [data-testid="stAlertContainer"] svg {
        display: none !important;
    }
    
    /* Forzar estilos para contenido interno de alertas */
    [data-testid="stAlertContentSuccess"],
    [data-testid="stAlertContentInfo"],
    [data-testid="stAlertContentWarning"] {
        background-color: transparent !important;
    }
    
    /* Eliminar bordes de contenedores padre de alertas */
    div:has(> [data-testid="stAlertContainer"]),
    div:has(> .stAlert) {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    
    /* Bloque de código estilo Midasmind */
    .stCodeBlock, 
    pre,
    [data-testid="stCode"] {
        border-radius: 15px !important;
        border: 2px solid #F2A100 !important;
        background-color: white !important;
        padding: 16px !important;
    }
    
    /* Eliminar bordes de contenedores padre de código */
    div:has(> [data-testid="stCode"]),
    div:has(> pre),
    div:has(> .stCodeBlock) {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    code {
        color: #333333 !important;
        font-family: 'Courier New', monospace !important;
        background-color: white !important;
    }
    
    /* Sobrescribir clases dinámicas de Streamlit para alertas */
    div[data-testid="stAlertContainer"] div[class*="st-c"],
    div[data-testid="stAlertContainer"][class*="st-c"] {
        background-color: inherit !important;
        color: inherit !important;
        border-color: inherit !important;
    }
    
    /* Success - sobrescribir TODO incluyendo clases dinámicas */
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]),
    div[data-testid="stAlertContainer"].st-c9,
    div[data-testid="stAlertContainer"][class*="st-c9"] {
        background-color: rgba(76, 175, 80, 0.08) !important;
        border: 2px solid #4CAF50 !important;
    }
    
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) *,
    div[data-testid="stAlertContainer"].st-c3 *,
    div[data-testid="stAlertContainer"][class*="st-c3"] * {
        color: #2E7D32 !important;
    }
    
    /* Info - sobrescribir TODO */
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
        background-color: rgba(242, 161, 0, 0.08) !important;
        border: 2px solid #F2A100 !important;
    }
    
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) * {
        color: #E58E00 !important;
    }
    
    /* Warning - sobrescribir TODO */
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
        background-color: rgba(255, 152, 0, 0.08) !important;
        border: 2px solid #FF9800 !important;
    }
    
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) * {
        color: #E65100 !important;
    }
    
    /* Ajustar columnas para resoluciones pequeñas */
    @media (max-width: 768px) {
        .numeros-grid {
            grid-template-columns: repeat(3, 90px);
            gap: 10px;
        }
        
        .numero-predicho {
            width: 90px;
            font-size: 20px;
            padding: 10px 6px;
        }
        
        h1 {
            font-size: 1.8rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 0.95rem !important;
        }
        
        [data-testid="stSidebar"] h1 {
            font-size: 1.1rem !important;
        }
        
        [data-testid="stSidebar"] h2 {
            font-size: 0.95rem !important;
        }
        
        [data-testid="stSidebar"] h3 {
            font-size: 0.85rem !important;
        }
    }

    /* Sección de Pozos */
    .pozos-container {
        background: white;
        border-radius: 15px;
        padding: 16px 20px;
        margin: 10px 0 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    .pozos-title {
        color: #333333;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 12px;
        text-align: center;
    }

    .pozos-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }

    .pozo-card {
        background: linear-gradient(135deg, rgba(242, 161, 0, 0.08) 0%, rgba(229, 142, 0, 0.08) 100%);
        border: 2px solid #F2A100;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
    }

    .pozo-modalidad {
        color: #666666;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .pozo-valor {
        color: #F2A100;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .pozo-info {
        color: rgba(102, 102, 102, 0.85);
        font-size: 11px;
        font-weight: 400;
        margin-top: 4px;
    }

    @media (max-width: 768px) {
        .pozos-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    /* Estilos compactos para UI minimalista */
    .stCheckbox label {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    
    .stSlider label {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stExpander"] {
        border: none !important;
    }
    
    [data-testid="stExpander"] summary {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNCIONES DE SESIÓN Y PERSISTENCIA
# ============================================================================

HISTORIAL_FILE = Path('data/historial_predicciones.json')
POZOS_FILE = Path('data/pozos_actuales.json')

def convertir_a_serializable(obj):
    """Convertir tipos numpy a tipos nativos de Python para JSON"""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [convertir_a_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convertir_a_serializable(value) for key, value in obj.items()}
    return obj

def guardar_historial_json():
    """Guardar historial en archivo JSON"""
    try:
        # Crear directorio si no existe
        HISTORIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir historial a formato serializable
        historial_serializable = convertir_a_serializable(st.session_state.historial)
        
        # Guardar en JSON
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(historial_serializable, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.warning(f"No se pudo guardar el historial: {str(e)}")

def cargar_historial_json():
    """Cargar historial desde archivo JSON"""
    try:
        if HISTORIAL_FILE.exists():
            with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.warning(f"No se pudo cargar el historial: {str(e)}")
        return []

def guardar_pozos_json(pozos):
    """Guardar pozos en archivo JSON"""
    try:
        POZOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(POZOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pozos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"No se pudo guardar pozos: {str(e)}")

def cargar_pozos_json():
    """Cargar pozos desde archivo JSON"""
    try:
        if POZOS_FILE.exists():
            with open(POZOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"No se pudo cargar pozos: {str(e)}")
        return None

def obtener_ultima_fecha_csv():
    """Obtener la última fecha del archivo CSV"""
    try:
        csv_path = Path('data/quini6_historico.csv')
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if 'fecha' in df.columns and len(df) > 0:
                ultima_fecha = df['fecha'].max()
                # Formatear fecha a DD/MM/YYYY
                try:
                    fecha_obj = pd.to_datetime(ultima_fecha)
                    return fecha_obj.strftime('%d/%m/%Y')
                except:
                    return ultima_fecha
        return None
    except Exception:
        return None

def formatear_pozo(data):
    """Formatear valor de pozo con separadores de miles"""
    if not data:
        return 'N/A', ''
    
    # Si es un dict con premio y ganadores
    if isinstance(data, dict):
        premio = data.get('premio')
        ganadores = data.get('ganadores') or ''
        
        if premio:
            try:
                numero = int(premio)
                premio_formateado = f"{numero:,}".replace(',', '.')
                
                # Formatear ganadores: si es un número, agregar "Ganadores"
                if ganadores:
                    try:
                        int(ganadores)
                        ganadores = f"Ganadores {ganadores}"
                    except:
                        pass  # Mantener el texto original (ej: "Pozo Vacante")
                
                return premio_formateado, ganadores
            except:
                return premio, ganadores
        return 'N/A', ''
    
    # Compatibilidad con formato antiguo (string simple)
    if not data or data == 'N/A':
        return 'N/A', ''
    try:
        numero = int(data)
        return f"{numero:,}".replace(',', '.'), ''
    except:
        return data, ''

def controlar_boleta(numeros_jugados, data):
    """
    Controla una jugada de 6 números contra los últimos 4 sorteos (última fecha)
    
    Args:
        numeros_jugados: Lista de 6 números ingresados por el usuario
        data: DataFrame con todos los sorteos históricos
    
    Returns:
        Lista de 4 dicts con resultados (Tradicional, Segunda, Revancha, Siempre Sale)
    """
    # Obtener la última fecha (día con 4 sorteos)
    ultima_fecha = data['fecha'].max()
    ultimos_sorteos = data[data['fecha'] == ultima_fecha].tail(4)
    
    if len(ultimos_sorteos) != 4:
        return None
    
    # Nombres de las modalidades en orden
    modalidades = ['Tradicional', 'Segunda', 'Revancha', 'Siempre Sale']
    
    resultados = []
    for idx, (_, sorteo) in enumerate(ultimos_sorteos.iterrows()):
        # El DataFrame tiene una columna 'numeros' que es una lista
        numeros_sorteo = sorteo['numeros'] if isinstance(sorteo['numeros'], list) else list(sorteo['numeros'])
        
        # Calcular coincidencias
        numeros_acertados = [n for n in numeros_jugados if n in numeros_sorteo]
        aciertos = len(numeros_acertados)
        
        resultados.append({
            'modalidad': modalidades[idx],
            'numeros_sorteo': numeros_sorteo,
            'numeros_jugados': numeros_jugados,
            'numeros_acertados': numeros_acertados,
            'aciertos': aciertos,
            'fecha': ultima_fecha
        })
    
    return resultados


def mostrar_bolillas(numeros_sorteo, numeros_acertados):
    """
    Muestra números como bolillas/esferas con estilo QuiniYa
    Destaca en verde los números acertados
    """
    html_parts = ['<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 8px; margin: 20px 0;">']
    
    for num in numeros_sorteo:
        # Verde si es un acierto, gris claro si no
        if num in numeros_acertados:
            color = 'linear-gradient(135deg, #32CD32, #228B22)'  # Verde
            text_color = 'white'
        else:
            color = '#E8E8E8'  # Gris claro
            text_color = '#666666'  # Texto gris oscuro
        
        bolilla = f'<div style="width: 52px; height: 52px; border-radius: 50%; background: {color}; color: {text_color}; font-weight: bold; font-size: 24px; display: flex; justify-content: center; align-items: center; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2); border: 3px solid #CCCCCC; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);">{num:02d}</div>'
        html_parts.append(bolilla)
    
    html_parts.append('</div>')
    return ''.join(html_parts)


def init_session_state():
    """Inicializar variables de sesión"""
    if 'historial' not in st.session_state:
        # Cargar historial desde JSON
        st.session_state.historial = cargar_historial_json()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'prediction_count' not in st.session_state:
        st.session_state.prediction_count = len(st.session_state.historial)
    if 'pozos_actuales' not in st.session_state:
        # Cargar pozos desde JSON
        st.session_state.pozos_actuales = cargar_pozos_json()
    if 'ultima_fecha_csv' not in st.session_state:
        st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv()


def agregar_al_historial(prediccion, metodo, scores_info):
    """Agregar predicción al historial y guardar en JSON"""
    entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'prediccion': convertir_a_serializable(prediccion),
        'metodo': metodo,
        'scores': convertir_a_serializable(scores_info)
    }
    st.session_state.historial.insert(0, entry)  # Más reciente primero
    if len(st.session_state.historial) > 20:  # Mantener solo últimas 20
        st.session_state.historial.pop()
    st.session_state.prediction_count += 1
    
    # Guardar en JSON
    guardar_historial_json()


# ============================================================================
# FUNCIONES DE CARGA Y ANÁLISIS
# ============================================================================

@st.cache_data
def cargar_datos():
    """Cargar datos históricos desde CSV"""
    loader = DataLoader()
    
    try:
        # Siempre cargar desde CSV real
        data = loader.load_csv('data/quini6_historico.csv')
    except Exception as e:
        # Fallback a datos de muestra solo si falla completamente
        st.warning(f"No se pudo cargar CSV: {e}. Usando datos de muestra.")
        sorteos = generate_sample_data(num_sorteos=200)
        data = loader.load_from_list(sorteos)
    
    return data


@st.cache_data
def ejecutar_analisis(_data):
    """Ejecutar análisis estadístico completo"""
    # Análisis de frecuencias
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(_data)
    
    # Análisis de correlaciones
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(_data)
    
    # Análisis de patrones
    pattern_analyzer = PatternAnalyzer()
    pattern_analyzer.analyze(_data)
    
    return freq_analyzer, corr_analyzer, pattern_analyzer


def mostrar_analisis_regresion_equilibrio(regression_analyzer):
    """Muestra el análisis de regresión al equilibrio de forma compacta"""
    summary = regression_analyzer.get_summary()
    
    deseq = summary['desequilibrios_detectados']
    hay_desequilibrios = any(deseq.values())
    
    if not hay_desequilibrios:
        st.info("✓ No se detectaron desequilibrios significativos. Sistema en equilibrio normal.")
        return
    
    st.warning("⚠️ Desequilibrios detectados - Sistema aplicará correcciones automáticas")
    
    corr = summary['correcciones_aplicar']
    metricas = summary['metricas']
    
    # Mostrar en formato compacto
    cols = st.columns(3)
    
    # Paridad(cont.)
    with cols[0]:
        if deseq['paridad']:
            desbalance_pct = abs(metricas['desbalance_pares']) * 100
            st.markdown(f"**Pares/Impares**")
            st.markdown(f"Desbalance: {desbalance_pct:.1f}%")
            if corr['paridad']:
                st.markdown(f"→ {corr['paridad'].replace('_', ' ').title()}")
        else:
            st.markdown("**Pares/Impares**")
            st.markdown("✓ En equilibrio")
    
    # Suma
    with cols[1]:
        if deseq['suma']:
            z_score = metricas['z_score_suma']
            st.markdown(f"**Suma Total**")
            st.markdown(f"Z-Score: {z_score:+.2f}σ")
            if corr['suma']:
                st.markdown(f"→ {corr['suma'].replace('_', ' ').title()}")
                if metricas['suma_objetivo']:
                    st.markdown(f"Objetivo: ~{metricas['suma_objetivo']:.0f}")
        else:
            st.markdown("**Suma Total**")
            st.markdown("✓ En equilibrio")
    
    # Rangos
    with cols[2]:
        if deseq['rangos']:
            st.markdown(f"**Rangos**")
            for rango, accion in corr['rangos'].items():
                rango_nombre = rango.replace('rango_', '').title()
                st.markdown(f"{rango_nombre}: {accion}")
        else:
            st.markdown("**Rangos**")
            st.markdown("✓ En equilibrio")


def mostrar_analisis_resonancia_ciclos(cycle_resonance_analyzer):
    """Muestra el análisis de resonancia de ciclos de forma compacta"""
    summary = cycle_resonance_analyzer.get_summary()
    
    # Información general
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "En Ventana Óptima",
            summary['total_en_ventana_optima'],
            help="Números en su momento ideal de aparición"
        )
    
    with col2:
        st.metric(
            "Sweet Spot",
            summary['total_en_sweet_spot'],
            help="Números en el punto perfecto del ciclo"
        )
    
    with col3:
        st.metric(
            "Mega Atrasados",
            summary['total_mega_atrasados'],
            help="Números muy atrasados (Z > 3.0)"
        )
    
    # Mostrar números destacados
    if summary['numeros_sweet_spot']:
        st.success(f"**Sweet Spot:** {', '.join(map(str, summary['numeros_sweet_spot'][:10]))}")
    
    if summary['numeros_mega_atrasados']:
        st.warning(f"**Mega Atrasados:** {', '.join(map(str, summary['numeros_mega_atrasados']))}")
    
    # Top 10 por resonancia
    with st.expander("Ver Top 10 por Resonancia"):
        top = summary['top_resonancia']
        for i, (num, score, z) in enumerate(top, 1):
            st.markdown(f"{i}. **Número {num}** - Score: {score:.2f} (Z: {z:+.2f}σ)")


def mostrar_analisis_multi_timeframe(multi_timeframe_analyzer):
    """Muestra el análisis multi-timeframe de forma compacta"""
    summary = multi_timeframe_analyzer.get_summary()
    
    # Información general
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Convergentes 100%",
            summary['total_convergentes'],
            help="Números en top 15 de TODAS las ventanas temporales"
        )
    
    with col2:
        st.metric(
            "Parciales 60-80%",
            summary['total_parciales'],
            help="Números en top 15 de 3-4 ventanas"
        )
    
    with col3:
        st.metric(
            "Divergentes <60%",
            summary['total_divergentes'],
            help="Números en pocas o ninguna ventana"
        )
    
    # Mostrar números convergentes
    if summary['numeros_convergentes']:
        st.success(f"**Convergentes:** {', '.join(map(str, summary['numeros_convergentes']))}")
    else:
        st.info("No hay números con convergencia 100% en este momento")
    
    # Top 10 por convergencia
    with st.expander("Ver Top 10 por Convergencia"):
        top = summary['top_convergencia']
        ventanas_str = f"Ventanas: {summary['ventanas_analizadas']}"
        st.caption(ventanas_str)
        for i, (num, score, ventanas) in enumerate(top, 1):
            pct = score * 100
            st.markdown(f"{i}. **Número {num}** - {ventanas}/{len(summary['ventanas_analizadas'])} ventanas ({pct:.0f}%)")




# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def crear_grafico_frecuencias(freq_analyzer):
    """Crear gráfico de barras de frecuencias"""
    # Obtener datos de frecuencia
    freq_data = freq_analyzer.results['frecuencia_absoluta']
    
    # Crear DataFrame
    df = pd.DataFrame(list(freq_data.items()), columns=['Número', 'Frecuencia'])
    df = df.sort_values('Frecuencia', ascending=False).head(20)
    
    # Crear gráfico con Plotly
    fig = px.bar(
        df, 
        x='Número', 
        y='Frecuencia',
        title='Top 20 Números Más Frecuentes',
        color='Frecuencia',
        color_continuous_scale=[[0, '#FFF8E1'], [0.5, '#FFD54F'], [1, '#F2A100']]
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        height=320,
        title_font=dict(size=16, color='#333333', family='sans-serif'),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def crear_grafico_calientes_frios(freq_analyzer):
    """Gráfico comparativo de números calientes vs fríos"""
    # Extraer números de las tuplas (numero, frecuencia)
    calientes = [num for num, freq in freq_analyzer.results['numeros_calientes'][:10]]
    frios = [num for num, freq in freq_analyzer.results['numeros_frios'][:10]]
    
    fig = go.Figure()
    
    # Calientes
    fig.add_trace(go.Bar(
        name='Calientes',
        x=[str(n) for n in calientes],
        y=[freq_analyzer.results['frecuencia_absoluta'][n] for n in calientes],
        marker_color='#F2A100'
    ))
    
    # Fríos
    fig.add_trace(go.Bar(
        name='Fríos',
        x=[str(n) for n in frios],
        y=[freq_analyzer.results['frecuencia_absoluta'][n] for n in frios],
        marker_color='#BDBDBD'
    ))
    
    fig.update_layout(
        title='Números Calientes vs Fríos',
        xaxis_title='Número',
        yaxis_title='Frecuencia',
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        height=320,
        title_font=dict(size=16, color='#333333'),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def crear_grafico_tendencias(freq_analyzer):
    """Gráfico de tendencias de números"""
    tendencias = freq_analyzer.results['tendencia']
    
    # Top 15 números por tendencia
    items = sorted(tendencias.items(), key=lambda x: abs(x[1]), reverse=True)[:15]
    numeros = [str(n) for n, _ in items]
    valores = [t for _, t in items]
    colores = ['#F2A100' if v > 0 else '#BDBDBD' for v in valores]
    
    fig = go.Figure(go.Bar(
        x=valores,
        y=numeros,
        orientation='h',
        marker_color=colores
    ))
    
    fig.update_layout(
        title='Tendencias de Números (Dorado = En alza)',
        xaxis_title='Tendencia',
        yaxis_title='Número',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        height=380,
        title_font=dict(size=16, color='#333333'),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=False)
    )
    
    return fig


def mostrar_numeros_predichos(numeros, titulo="Predicción"):
    """Mostrar números predichos en formato visual atractivo"""
    st.markdown(f"### {titulo}")
    
    # Convertir a lista de enteros para manejar tipos numpy
    numeros_limpios = [int(n) for n in numeros]
    
    # Generar HTML con grid centrado
    numeros_html = ''.join([f'<div class="numero-predicho">{num:02d}</div>' for num in numeros_limpios])
    
    st.markdown(
        f'<div class="numeros-grid">{numeros_html}</div>',
        unsafe_allow_html=True
    )


def mostrar_portfolio(portfolio, freq_analyzer, portfolio_gen, metodo_nombre):
    """Muestra un portfolio de combinaciones generadas"""
    st.markdown(f"### {len(portfolio)} Combinaciones Generadas")
    
    # Mostrar cada combinación
    for idx, combo_data in enumerate(portfolio, 1):
        st.markdown(f"**#{idx} {combo_data['nombre']}** - {combo_data['descripcion']}")
        
        # Números con indicador de momentum
        numeros = combo_data['numeros']
        momentum_results = freq_analyzer.results.get('momentum', {})
        
        # Generar HTML de números con momentum
        numeros_html_parts = []
        for num in numeros:
            mom = momentum_results.get(num, 0)
            if mom > 0.3:
                indicador = "↑"
            elif mom < -0.3:
                indicador = "↓"
            else:
                indicador = ""
            
            numeros_html_parts.append(
                f"<div style='text-align: center; padding: 12px 8px; "
                f"background: linear-gradient(135deg, #F2A100 0%, #E58E00 100%); "
                f"border-radius: 20px; width: 95px;'>"
                f"<span style='font-size: 20px; font-weight: bold; color: white;'>{int(num):02d}</span>"
                f"<span style='font-size: 12px; color: white;'> {indicador}</span>"
                f"</div>"
            )
        
        st.markdown(
            f'<div class="numeros-grid">{"".join(numeros_html_parts)}</div>',
            unsafe_allow_html=True
        )
        
        # Estadísticas compactas en una sola línea
        suma = sum(numeros)
        pares = sum(1 for n in numeros if n % 2 == 0)
        momentum_text = f"Momentum: {combo_data['momentum_promedio']:+.2f}" if 'momentum_promedio' in combo_data else ""
        
        st.markdown(
            f"<p style='margin: 15px 0 20px 0; font-size: 0.9rem; color: #666;'>"
            f"Suma: {suma} &nbsp;&nbsp;&nbsp; "
            f"Score: {combo_data['score_promedio']:.2f} &nbsp;&nbsp;&nbsp; "
            f"Pares: {pares}/6 &nbsp;&nbsp;&nbsp; "
            f"{momentum_text}"
            f"</p>",
            unsafe_allow_html=True
        )
        
        # Agregar al historial
        agregar_al_historial(
            numeros,
            f"Portfolio {metodo_nombre} - {combo_data['nombre']}",
            {
                'suma_total': suma,
                'score_promedio': combo_data['score_promedio'],
                'pares': pares,
                'impares': 6 - pares,
                'consecutivos': 0
            }
        )
    
    # Resumen de cobertura
    coverage = portfolio_gen.analyze_portfolio_coverage(portfolio)
    st.markdown("---")
    st.markdown("### Análisis de Cobertura")
    
    st.markdown(
        f"<div style='display: flex; gap: 40px; margin: 10px 0 15px 0;'>"
        f"<div>"
        f"<div style='color: #666; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; margin-bottom: 5px;'>NÚMEROS ÚNICOS TOTALES</div>"
        f"<div style='color: #F2A100; font-size: 1.75rem; font-weight: 700;'>{coverage['numeros_unicos']}</div>"
        f"</div>"
        f"<div>"
        f"<div style='color: #666; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; margin-bottom: 5px;'>SCORE DE DIVERSIFICACIÓN</div>"
        f"<div style='color: #F2A100; font-size: 1.75rem; font-weight: 700;'>{coverage['diversificacion_score']:.2%}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Resumen para copiar
    st.markdown("---")
    
    # Generar texto con todas las combinaciones
    texto_copiar_lines = []
    for idx, combo_data in enumerate(portfolio, 1):
        nums_formatted = ', '.join([f"{int(n):02d}" for n in combo_data['numeros']])
        texto_copiar_lines.append(f"#{idx} {combo_data['nombre']}: {nums_formatted}")
    
    texto_copiar = '\n'.join(texto_copiar_lines)
    st.code(texto_copiar, language=None)


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    init_session_state()
    
    # HEADER
    fecha_info = f"<div class='banner-fecha'>Datos actualizados al {st.session_state.ultima_fecha_csv}</div>" if st.session_state.ultima_fecha_csv else ""
    
    st.markdown(f"""
        <div class="app-banner">
            <div class="banner-logo">CP</div>
            <div class="banner-title">Charly Predictor</div>
            <div class="banner-subtitle">Quini 6</div>
            {fecha_info}
        </div>
    """, unsafe_allow_html=True)
    
    # POZOS ACTUALES
    if st.session_state.pozos_actuales:
        pozos = st.session_state.pozos_actuales
        
        # Formatear valores con separadores de miles y obtener info de ganadores
        tradicional, trad_info = formatear_pozo(pozos.get('Tradicional'))
        segunda, seg_info = formatear_pozo(pozos.get('Segunda'))
        revancha, rev_info = formatear_pozo(pozos.get('Revancha'))
        siempre_sale, ss_info = formatear_pozo(pozos.get('SiempreSale'))
        
        # Reemplazar strings vacíos por guión para mejor visualización
        trad_info = trad_info if trad_info else '-'
        seg_info = seg_info if seg_info else '-'
        rev_info = rev_info if rev_info else '-'
        ss_info = ss_info if ss_info else '-'
        
        pozos_html = f"""
        <div class="pozos-container">
            <div class="pozos-title">Pozos Actuales</div>
            <div class="pozos-grid">
                <div class="pozo-card">
                    <div class="pozo-modalidad">Tradicional</div>
                    <div class="pozo-valor">${tradicional}</div>
                    <div class="pozo-info">{trad_info}</div>
                </div>
                <div class="pozo-card">
                    <div class="pozo-modalidad">La Segunda</div>
                    <div class="pozo-valor">${segunda}</div>
                    <div class="pozo-info">{seg_info}</div>
                </div>
                <div class="pozo-card">
                    <div class="pozo-modalidad">Revancha</div>
                    <div class="pozo-valor">${revancha}</div>
                    <div class="pozo-info">{rev_info}</div>
                </div>
                <div class="pozo-card">
                    <div class="pozo-modalidad">Siempre Sale</div>
                    <div class="pozo-valor">${siempre_sale}</div>
                    <div class="pozo-info">{ss_info}</div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(pozos_html, unsafe_allow_html=True)
    
    # ========================================================================
    # SIDEBAR - CONFIGURACIÓN
    # ========================================================================
    
    with st.sidebar:
        # Logo/Header del sidebar - Estilo Midasmind
        st.markdown("""
        <div class="sidebar-banner">
            <div class="banner-logo">CP</div>
            <div class="banner-title">Charly Predictor</div>
            <div class="banner-subtitle">Quini 6</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Banner informativo de configuración optimizada
        # st.info("""
        # ✨ **Configuración Optimizada Activa** | Rendimiento: 2.25 aciertos/sorteo promedio  
        # Los parámetros predeterminados han sido optimizados mediante 130+ pruebas de configuración.
        # """)
        
        # 1. CARGA DE DATOS
        
        # Cargar datos automáticamente al inicio
        if not st.session_state.data_loaded:
            with st.spinner("Cargando datos históricos..."):
                data = cargar_datos()
                st.session_state.current_data = data
                st.session_state.data_loaded = True
                st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv()

        # Actualizar desde QuiniYa
        if st.button("Actualizar datos", width='stretch'):
            with st.spinner("Actualizando datos desde la red"):
                try:
                    nuevos = actualizar_historico_csv('data/quini6_historico.csv')
                    # Limpiar cachés para forzar recarga con datos nuevos
                    cargar_datos.clear()
                    ejecutar_analisis.clear()
                    # Recargar datos y análisis con sorteos nuevos
                    data = cargar_datos()
                    st.session_state.current_data = data
                    st.session_state.data_loaded = True
                    
                    # Actualizar última fecha del CSV
                    st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv()
                    
                    # Obtener pozos actuales
                    pozos = obtener_pozos_ultimo_sorteo()
                    if pozos:
                        st.session_state.pozos_actuales = pozos
                        # Guardar pozos en JSON para persistencia
                        guardar_pozos_json(pozos)
                    
                    # Construir mensaje combinado
                    mensajes = []
                    if nuevos > 0:
                        mensajes.append(f"Agregados {nuevos} sorteos nuevos.")
                    else:
                        mensajes.append("No hay sorteos nuevos para agregar.")
                    
                    if pozos:
                        mensajes.append("Pozos actualizados correctamente")
                    
                    # Mostrar mensaje combinado
                    mensaje_final = "\n".join(mensajes)
                    if nuevos > 0 or pozos:
                        st.success(mensaje_final)
                    else:
                        st.info(mensaje_final)
                    
                    # Recargar la página para mostrar los pozos actualizados
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar datos: {str(e)}")
        
        st.markdown("---")
        
        # 2. MÉTODO DE GENERACIÓN
        st.markdown("### Método de Predicción")
        
        metodo_options = {
            "Estándar (Rápido)": GenerationStrategy.STANDARD,
            "Condicional (Inteligente)": GenerationStrategy.CONDITIONAL,
            "Ambos Métodos": GenerationStrategy.BOTH
        }
        
        metodo_selected = st.radio(
            "Selecciona el método:",
            list(metodo_options.keys()),
            index=2  # Por defecto "Ambos Métodos"
        )
        
        metodo = metodo_options[metodo_selected]
        
        # 3. MULTI-COMBINACIONES
        st.markdown("---")
        st.markdown("### Generación Múltiple")
        
        usar_portfolio = st.checkbox(
            "Generar múltiples combinaciones",
            value=False,
            help="Genera varias combinaciones usando diferentes estrategias"
        )
        
        if usar_portfolio:
            n_combinaciones = st.radio(
                "Cantidad de combinaciones:",
                options=[1, 2, 5, 10, 15, 20],
                index=2,  # Default 5
                help="Más combinaciones = mayor cobertura",
                horizontal=True
            )
        else:
            n_combinaciones = 1
        
        st.markdown("---")
        
        # 4. PARÁMETROS AVANZADOS
        st.markdown("### Parámetros")
        
        with st.expander("Avanzados"):
            st.markdown("#### Optimizaciones Avanzadas")
            
            usar_regresion_equilibrio = st.checkbox(
                "Regresión al Equilibrio (IDEA #3)",
                value=True,
                help="Detecta desequilibrios en pares/impares, sumas y rangos, y ajusta predicciones automáticamente"
            )
            
            # Parámetros de Regresión al Equilibrio (solo si está activado)
            if usar_regresion_equilibrio:
                st.markdown("##### Configuración Regresión")
                
                ventana_regresion = st.slider(
                    "Ventana de Análisis (sorteos)",
                    min_value=8,
                    max_value=120,
                    value=16,
                    step=4,
                    help="Sorteos recientes (8 sorteos = 1 semana, 2 sorteos/semana). Default: 16 = 2 semanas"
                )
                
                umbral_regresion = st.slider(
                    "Umbral de Desbalance (%)",
                    min_value=5,
                    max_value=25,
                    value=12,
                    step=1,
                    help="% de desviación para activar correcciones. Menor = más sensible"
                )
            else:
                ventana_regresion = 16
                umbral_regresion = 12
            
            st.markdown("---")
            
            usar_resonancia_ciclos = st.checkbox(
                "Resonancia de Ciclos (IDEA #1)",
                value=False,
                help="Detecta números en su 'ventana óptima' según análisis de ciclos. Identifica números a punto de salir."
            )
            
            usar_multi_timeframe = st.checkbox(
                "Multi-Timeframe (IDEA #2)",
                value=False,
                help="Analiza señales convergentes en ventanas temporales: 10, 20, 50, 100, 200 sorteos. Boost a números consistentes."
            )
            
            st.markdown("#### Pesos de Scoring")
            
            peso_frecuencia = st.slider(
                "Frecuencia General",
                0.0, 1.0, OPTIMAL_WEIGHTS['peso_frecuencia'], 0.05
            )
            
            peso_frecuencia_reciente = st.slider(
                "Frecuencia Reciente",
                0.0, 1.0, OPTIMAL_WEIGHTS['peso_frecuencia_reciente'], 0.05
            )
            
            peso_ciclo = st.slider(
                "Ciclos",
                0.0, 1.0, OPTIMAL_WEIGHTS['peso_ciclo'], 0.05
            )
            
            peso_latencia = st.slider(
                "Latencia",
                0.0, 1.0, OPTIMAL_WEIGHTS['peso_latencia'], 0.05,
                help="⚠️ Optimización: Latencia en 0.00 mejora el rendimiento"
            )
            
            peso_tendencia = st.slider(
                "Tendencia",
                0.0, 1.0, OPTIMAL_WEIGHTS['peso_tendencia'], 0.05
            )
            
            st.markdown("---")
            
            if metodo != GenerationStrategy.STANDARD:
                st.markdown("#### Correlaciones")
                peso_correlaciones = st.slider(
                    "Peso de Correlaciones",
                    0.0, 1.0, 0.3, 0.1,
                    help="Solo aplica al método condicional"
                )
            else:
                peso_correlaciones = 0.3
    
    # ========================================================================
    # ÁREA PRINCIPAL
    # ========================================================================
    
    if not st.session_state.data_loaded:
        # Pantalla de bienvenida
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("Carga los datos desde el panel lateral para comenzar")
            
            st.markdown("""
            ### Cómo usar:
            
            1. **Cargar Datos**: Selecciona la fuente (CSV o muestra)
            2. **Elegir Método**: Estándar, Condicional o Ambos
            3. **Ajustar Parámetros**: (Opcional) Configura pesos
            4. **Generar Predicción**: Click en el botón grande
            5. **Ver Resultados**: Analiza gráficos y estadísticas
            6. **Exportar**: Guarda tus predicciones
            
            ### Métodos Disponibles:
            
            - **Estándar**: Probabilidades estáticas, rápido
            - **Condicional**: Considera correlaciones, más preciso
            - **Ambos**: Compara resultados lado a lado
            """)
        
        return
    
    # ========================================================================
    # PESTAÑAS PRINCIPALES
    # ========================================================================
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Predicción",
        "Control Boleta",
        "Análisis", 
        "Visualizaciones",
        "Validación Temporal",
        "Historial"
    ])
    
    # ========================================================================
    # TAB 1: PREDICCIÓN
    # ========================================================================
    
    with tab1:
        data = st.session_state.current_data
        
        # Ejecutar análisis
        with st.spinner("Analizando datos históricos..."):
            freq_analyzer, corr_analyzer, pattern_analyzer = ejecutar_analisis(data)
        
        # Calcular scores
        pesos_custom = {
            'peso_frecuencia': peso_frecuencia,
            'peso_frecuencia_reciente': peso_frecuencia_reciente,
            'peso_ciclo': peso_ciclo,
            'peso_latencia': peso_latencia,
            'peso_tendencia': peso_tendencia
        }
        
        scorer = UnifiedScorer(
            pesos_custom, 
            use_regression_equilibrium=usar_regresion_equilibrio,
            use_cycle_resonance=usar_resonancia_ciclos,
            use_multi_timeframe=usar_multi_timeframe
        )
        
        regression_analyzer = None
        cycle_resonance_analyzer = None
        multi_timeframe_analyzer = None
        
        # Si usa regresión al equilibrio, configurar parámetros personalizados
        if usar_regresion_equilibrio:
            from core.analysis import RegressionEquilibriumAnalyzer
            regression_analyzer = RegressionEquilibriumAnalyzer()
            regression_analyzer.ventana_analisis = ventana_regresion
            regression_analyzer.umbral_desbalance = umbral_regresion / 100.0
        
        # Si usa resonancia de ciclos, configurar analizador
        if usar_resonancia_ciclos:
            from core.analysis import CycleResonanceAnalyzer
            cycle_resonance_analyzer = CycleResonanceAnalyzer()
        
        # Si usa multi-timeframe, configurar analizador
        if usar_multi_timeframe:
            from core.analysis import MultiTimeframeAnalyzer
            multi_timeframe_analyzer = MultiTimeframeAnalyzer()
        
        # Calcular scores con todos los analizadores activos
        scores = scorer.calculate_scores(
            freq_analyzer,
            regression_analyzer=regression_analyzer,
            cycle_resonance_analyzer=cycle_resonance_analyzer,
            multi_timeframe_analyzer=multi_timeframe_analyzer
        )
        
        # Mostrar análisis si están activos
        if usar_regresion_equilibrio and regression_analyzer:
            st.markdown("### Análisis de Regresión al Equilibrio")
            mostrar_analisis_regresion_equilibrio(regression_analyzer)
        
        if usar_resonancia_ciclos and cycle_resonance_analyzer:
            st.markdown("### Análisis de Resonancia de Ciclos")
            mostrar_analisis_resonancia_ciclos(cycle_resonance_analyzer)
        
        if usar_multi_timeframe and multi_timeframe_analyzer:
            st.markdown("### Análisis Multi-Timeframe")
            mostrar_analisis_multi_timeframe(multi_timeframe_analyzer)
        
        # Botón de generar predicción
        st.markdown("## Generar Predicción")
        
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn1:
            texto_boton = "GENERAR PREDICCIONES" if usar_portfolio and n_combinaciones > 1 else "GENERAR PREDICCIÓN"
            generar = st.button(
                texto_boton,
                width='stretch',
                type="primary"
            )
        
        if generar:
            # Incrementar contador
            st.session_state.prediction_count += 1
            
            # GENERACIÓN CON PORTFOLIO
            if usar_portfolio and n_combinaciones > 1:
                # Si es BOTH, generar ambos métodos
                if metodo == GenerationStrategy.BOTH:
                    # MÉTODO ESTÁNDAR
                    with st.spinner(f"Generando {n_combinaciones} combinaciones (Método Estándar)..."):
                        portfolio_gen = PortfolioGenerator()
                        portfolio_std = portfolio_gen.generate_portfolio(
                            scores,
                            n_combinaciones,
                            freq_analyzer,
                            method=GenerationStrategy.STANDARD
                        )
                    
                    st.markdown("---")
                    st.markdown("## Método Estándar")
                    mostrar_portfolio(portfolio_std, freq_analyzer, portfolio_gen, "Estándar")
                    
                    # MÉTODO CONDICIONAL
                    with st.spinner(f"Generando {n_combinaciones} combinaciones (Método Condicional)..."):
                        portfolio_gen_cond = PortfolioGenerator()
                        portfolio_cond = portfolio_gen_cond.generate_portfolio(
                            scores,
                            n_combinaciones,
                            freq_analyzer,
                            method=GenerationStrategy.CONDITIONAL,
                            correlation_analyzer=corr_analyzer
                        )
                    
                    st.markdown("---")
                    st.markdown("## Método Condicional")
                    mostrar_portfolio(portfolio_cond, freq_analyzer, portfolio_gen_cond, "Condicional")
                
                else:
                    # Un solo método
                    metodo_texto = "Estándar" if metodo == GenerationStrategy.STANDARD else "Condicional"
                    with st.spinner(f"Generando {n_combinaciones} combinaciones..."):
                        portfolio_gen = PortfolioGenerator()
                        portfolio = portfolio_gen.generate_portfolio(
                            scores,
                            n_combinaciones,
                            freq_analyzer,
                            method=metodo,
                            correlation_analyzer=corr_analyzer if metodo == GenerationStrategy.CONDITIONAL else None
                        )
                    
                    st.markdown("---")
                    mostrar_portfolio(portfolio, freq_analyzer, portfolio_gen, metodo_texto)
            
            # GENERACIÓN TRADICIONAL (sin portfolio)
            else:
                with st.spinner("Generando predicción..."):
                    manager = StrategyManager()
                    
                    # Ajustar peso de correlaciones si es condicional
                    if metodo != GenerationStrategy.STANDARD:
                        manager.conditional_generator.correlation_weight = peso_correlaciones
                    
                    # Generar
                    result = manager.generate(
                        scores,
                        strategy=metodo,
                        correlation_analyzer=corr_analyzer,
                        use_constraints=True
                    )
                    
                    st.markdown("---")
                    
                    # Mostrar resultados según método
                    if metodo == GenerationStrategy.BOTH:
                        # AMBOS MÉTODOS
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### Método Estándar")
                            mostrar_numeros_predichos(
                                result['standard']['combination'],
                                ""
                            )
                            
                            st.markdown("##### Estadísticas")
                            analysis_std = result['standard']['analysis']
                            
                            subcol1, subcol2, subcol3 = st.columns(3)
                            with subcol1:
                                st.metric("Suma", analysis_std['suma_total'])
                            with subcol2:
                                st.metric("Score", f"{analysis_std['score_promedio']:.3f}")
                            with subcol3:
                                st.metric("Pares", f"{analysis_std['pares']}/6")
                        
                        with col2:
                            st.markdown("### Método Condicional")
                            mostrar_numeros_predichos(
                                result['conditional']['combination'],
                                ""
                            )
                            
                            st.markdown("##### Estadísticas")
                            analysis_cond = result['conditional']['analysis']
                            
                            subcol1, subcol2, subcol3 = st.columns(3)
                            with subcol1:
                                st.metric("Suma", analysis_cond['suma_total'])
                            with subcol2:
                                st.metric("Score", f"{analysis_cond['score_promedio']:.3f}")
                            with subcol3:
                                st.metric("Correlation", f"{analysis_cond['correlation_score']:.3f}")
                        
                        # Agregar ambas al historial
                        agregar_al_historial(
                            result['standard']['combination'],
                            "Estándar",
                            analysis_std
                        )
                        agregar_al_historial(
                            result['conditional']['combination'],
                            "Condicional",
                            analysis_cond
                        )
                    
                    else:
                        # UN SOLO MÉTODO
                        mostrar_numeros_predichos(result['combination'])
                        
                        st.markdown("---")
                        
                        analysis = result['analysis']
                        
                        # Métricas
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.metric("Suma Total", analysis['suma_total'])
                        with col2:
                            st.metric("Score Promedio", f"{analysis['score_promedio']:.3f}")
                        with col3:
                            st.metric("Pares", f"{analysis['pares']}/6")
                        with col4:
                            st.metric("Impares", f"{analysis['impares']}/6")
                        with col5:
                            st.metric("Consecutivos", analysis['consecutivos'])
                        
                        # Agregar al historial
                        metodo_nombre = "Estándar" if metodo == GenerationStrategy.STANDARD else "Condicional"
                        agregar_al_historial(
                            result['combination'],
                            metodo_nombre,
                            analysis
                        )
                    
                    # Resumen para copiar
                    # Preparar texto para copiar
                    if metodo == GenerationStrategy.BOTH:
                        nums_std = ', '.join([f"{int(n):02d}" for n in result['standard']['combination']])
                        nums_cond = ', '.join([f"{int(n):02d}" for n in result['conditional']['combination']])
                        texto_copiar = f"Estándar: {nums_std}\nCondicional: {nums_cond}"
                    else:
                        texto_copiar = ', '.join([f"{int(n):02d}" for n in result['combination']])
                    
                    st.code(texto_copiar, language=None)
    
    # ========================================================================
    # TAB 2: CONTROL BOLETA
    # ========================================================================
    
    with tab2:
        st.markdown("## Control de Boleta")
        st.markdown("Ingresa tus 6 números y verifica cuántos aciertos tuviste en la última fecha.")
        
        # Área de ingreso de números
        st.markdown("### Ingresa tus números")
        
        # CSS para inputs circulares limpios
        st.markdown("""
        <style>
        /* Contenedor principal de inputs con flexbox */
        div[data-testid="column"]:has([data-testid="stTextInput"]) {
            padding: 0 3px !important;
            min-width: 0 !important;
        }
        
        /* Estilos para los text inputs */
        [data-testid="stTextInput"] {
            width: 64px !important;
        }
        [data-testid="stTextInput"] > div {
            width: 64px !important;
            height: 70px !important;
        }
        [data-testid="stTextInput"] > div > div {
            width: 64px !important;
            height: 64px !important;
        }
        [data-testid="stTextInput"] input {
            width: 64px !important;
            height: 64px !important;
            border-radius: 50% !important;
            text-align: center !important;
            font-size: 24px !important;
            font-weight: bold !important;
            border: 3px solid #CCCCCC !important;
            background: #F5F5F5 !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
            padding: 0 !important;
            line-height: 64px !important;
            box-sizing: border-box !important;
        }
        [data-testid="stTextInput"] input:focus {
            border: 3px solid #F2A100 !important;
            outline: none !important;
        }
        [data-testid="stTextInput"] label {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Layout centrado: columna vacía | 6 inputs | columna vacía
        cols_layout = st.columns([0.25, 0.5, 0.25])
        
        with cols_layout[1]:
            cols_input = st.columns(6, gap="small")
            numeros_texto = []
            
            for i, col in enumerate(cols_input):
                with col:
                    num_str = st.text_input(
                        f"N{i}",
                        value="",
                        max_chars=2,
                        key=f"control_num_{i}",
                        label_visibility="collapsed",
                        placeholder=""
                    )
                    numeros_texto.append(num_str)
        
        # Convertir y validar
        numeros_ingresados = []
        for num_str in numeros_texto:
            try:
                num = int(num_str) if num_str.strip() else 0
                if 0 <= num <= 45:
                    numeros_ingresados.append(num)
                else:
                    numeros_ingresados.append(0)
            except:
                numeros_ingresados.append(0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón con el mismo ancho que las 6 esferas
        cols_button = st.columns([0.25, 0.5, 0.25])
        with cols_button[1]:
            verificar = st.button("Verificar", type="primary", use_container_width=True)
        
        # Validaciones
        if verificar:
            # Validar que no haya números repetidos
            if len(set(numeros_ingresados)) != 6:
                st.error("⚠️ No puedes repetir números. Cada número debe ser único.")
            elif 0 in numeros_ingresados:
                st.warning("⚠️ Por favor completa los 6 números (no pueden ser 0).")
            else:
                # Realizar control
                data = st.session_state.current_data
                resultados = controlar_boleta(numeros_ingresados, data)
                
                if resultados:
                    st.success(f"✅ Controlando contra los sorteos del {resultados[0]['fecha']}")
                    
                    # Mostrar resultados en 4 tarjetas (2x2)
                    st.markdown("---")
                    
                    for i in range(0, 4, 2):
                        cols = st.columns(2)
                        
                        for j in range(2):
                            if i + j < len(resultados):
                                resultado = resultados[i + j]
                                
                                with cols[j]:
                                    # Título de la modalidad con estilo simple
                                    st.markdown(f"""
                                    <h3 style="
                                        color: #F2A100;
                                        text-align: center;
                                        margin-bottom: 15px;
                                        padding-bottom: 10px;
                                        border-bottom: 2px solid #F2A100;
                                    ">
                                        {resultado['modalidad']}
                                    </h3>
                                    """, unsafe_allow_html=True)
                                    
                                    # Mostrar bolillas
                                    bolillas_html = mostrar_bolillas(
                                        resultado['numeros_sorteo'],
                                        resultado['numeros_acertados']
                                    )
                                    st.markdown(bolillas_html, unsafe_allow_html=True)
                                    
                                    # Mostrar aciertos
                                    st.markdown(f"""
                                    <div style="text-align: center; margin: 20px 0;">
                                        <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">
                                            Aciertos: {resultado['aciertos']}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Mensaje según aciertos
                                    if resultado['aciertos'] >= 4:
                                        if resultado['aciertos'] == 6:
                                            st.success("🎉 ¡FELICITACIONES! ¡Ganaste el premio mayor!")
                                        elif resultado['aciertos'] == 5:
                                            st.success("🎊 ¡Excelente! ¡5 aciertos! ¡Premio importante!")
                                        else:
                                            st.info("👏 ¡Bien hecho! Tienes premio.")
                                    else:
                                        st.warning(f"No tienes premio. El mínimo para ganar en {resultado['modalidad']} son 4 aciertos.")
                else:
                    st.error("❌ No se pudieron obtener los resultados. Verifica que haya datos cargados.")
    
    # ========================================================================
    # TAB 3: ANÁLISIS
    # ========================================================================
    
    with tab3:
        st.markdown("## Análisis Estadístico Detallado")
        
        data = st.session_state.current_data
        freq_analyzer, corr_analyzer, pattern_analyzer = ejecutar_analisis(data)
        
        # Top números
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Top 10 Números Calientes")
            # numeros_calientes es una lista de tuplas (numero, frecuencia)
            calientes_df = pd.DataFrame([
                {
                    'Número': num,
                    'Frecuencia': freq,
                    'Latencia': freq_analyzer.results['latencia'][num]
                }
                for num, freq in freq_analyzer.results['numeros_calientes'][:10]
            ])
            st.dataframe(calientes_df, width='stretch', hide_index=True)
        
        with col2:
            st.markdown("### Top 10 Números Fríos")
            # numeros_frios es una lista de tuplas (numero, frecuencia)
            frios_df = pd.DataFrame([
                {
                    'Número': num,
                    'Frecuencia': freq,
                    'Latencia': freq_analyzer.results['latencia'][num]
                }
                for num, freq in freq_analyzer.results['numeros_frios'][:10]
            ])
            st.dataframe(frios_df, width='stretch', hide_index=True)
        
        st.markdown("---")
        
        # Correlaciones
        st.markdown("### Pares Más Frecuentes")
        
        pares = corr_analyzer.results['pares_frecuentes'][:10]
        pares_df = pd.DataFrame([
            {
                'Par': f"{p[0][0]}-{p[0][1]}",
                'Veces Juntos': p[1]
            }
            for p in pares
        ])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(pares_df, width='stretch', hide_index=True)
    
    # ========================================================================
    # TAB 4: VISUALIZACIONES
    # ========================================================================
    
    with tab4:
        st.markdown("## Visualizaciones Interactivas")
        
        data = st.session_state.current_data
        freq_analyzer, corr_analyzer, pattern_analyzer = ejecutar_analisis(data)
        
        # Gráfico 1: Frecuencias
        st.plotly_chart(
            crear_grafico_frecuencias(freq_analyzer),
            width='stretch'
        )
        
        # Gráfico 2: Calientes vs Fríos
        st.plotly_chart(
            crear_grafico_calientes_frios(freq_analyzer),
            width='stretch'
        )
        
        # Gráfico 3: Tendencias
        st.plotly_chart(
            crear_grafico_tendencias(freq_analyzer),
            width='stretch'
        )
    
    # ========================================================================
    # TAB 5: VALIDACIÓN TEMPORAL
    # ========================================================================
    
    with tab5:
        st.markdown("## Validación Temporal Walk-Forward")
        
        st.info(
            "Esta validación simula cómo funcionaría el sistema en condiciones reales, "
            "usando una ventana móvil de entrenamiento para validar la estabilidad de los pesos optimizados."
        )
        
        # Calcular límites dinámicos basados en datos disponibles
        data = st.session_state.current_data
        total_sorteos = len(data)
        
        # Dejar margen para al menos 5-10 períodos de validación
        # Fórmula: períodos = (total - train - test) / step
        # Con test=10 y step=10, necesitamos: total - train - 60 > 0
        max_train_window = max(100, total_sorteos - 100)
        default_train_window = min(200, max_train_window - 50)
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        with col_w1:
            ventana_train = st.number_input(
                "Ventana de entrenamiento:",
                min_value=100,
                max_value=max_train_window,
                value=default_train_window,
                step=10,
                help=f"Cantidad de sorteos para entrenar en cada periodo (Disponibles: {total_sorteos})"
            )
        
        with col_w2:
            ventana_test = st.number_input(
                "Ventana de test:",
                min_value=5,
                max_value=20,
                value=10,
                step=1,
                help="Cantidad de sorteos para evaluar en cada periodo"
            )
        
        with col_w3:
            step_size = st.number_input(
                "Step size:",
                min_value=5,
                max_value=20,
                value=10,
                step=5,
                help="Cuánto deslizar la ventana en cada iteración"
            )
        
        st.markdown("---")
        
        # Configuración de IDEAS para Walk-Forward
        usar_ideas_walkforward = st.checkbox(
            "Usar IDEAS en validación",
            value=False,
            help="Aplica las optimizaciones avanzadas (IDEAS) durante la validación Walk-Forward"
        )
        
        if usar_ideas_walkforward:
            ideas_activas = []
            if usar_regresion_equilibrio:
                ideas_activas.append("IDEA #3 (Regresión)")
            if usar_resonancia_ciclos:
                ideas_activas.append("IDEA #1 (Resonancia)")
            if usar_multi_timeframe:
                ideas_activas.append("IDEA #2 (Multi-Timeframe)")
            
            if ideas_activas:
                st.info(f"✓ Se usarán: {', '.join(ideas_activas)}")
            else:
                st.warning("⚠️ Ninguna IDEA activada en Parámetros → Avanzados")
        
        if st.button("Ejecutar Validación Walk-Forward", type="primary"):
            try:
                with st.spinner("Ejecutando validación temporal..."):
                    data = st.session_state.current_data
                    
                    # Pesos a validar
                    pesos_validar = {
                        'peso_frecuencia': peso_frecuencia,
                        'peso_frecuencia_reciente': peso_frecuencia_reciente,
                        'peso_ciclo': peso_ciclo,
                        'peso_latencia': peso_latencia,
                        'peso_tendencia': peso_tendencia
                    }
                    
                    # Crear backtester con configuración de IDEAS
                    wf_backtester = WalkForwardBacktester(
                        train_window=ventana_train,
                        test_window=ventana_test,
                        step_size=step_size,
                        use_ideas=usar_ideas_walkforward,
                        use_idea1=usar_resonancia_ciclos,
                        use_idea2=usar_multi_timeframe,
                        use_idea3=usar_regresion_equilibrio,
                        idea3_ventana=ventana_regresion if usar_regresion_equilibrio else 16,
                        idea3_umbral=umbral_regresion / 100.0 if usar_regresion_equilibrio else 0.12
                    )
                    
                    # Ejecutar
                    results = wf_backtester.run_walk_forward(data, pesos_validar)
                    
                    # Mostrar resultados
                    if usar_ideas_walkforward and ideas_activas:
                        st.success(f"✓ Validación completada con {', '.join(ideas_activas)}")
                    else:
                        st.success("Validación completada (sistema base)")
                    
                    summary = results['summary']
                    
                    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                    
                    with col_r1:
                        st.metric("Periodos evaluados", summary['total_periodos'])
                    with col_r2:
                        st.metric("Accuracy promedio", f"{summary['accuracy_promedio']:.2%}")
                    with col_r3:
                        st.metric("Desviación std", f"{summary['accuracy_std']:.2%}")
                    with col_r4:
                        stability = wf_backtester.get_stability_score()
                        st.metric("Score de estabilidad", f"{stability:.2%}")
                    
                    st.markdown("---")
                    
                    # Gráfico de evolución
                    plot_data = wf_backtester.plot_results()
                    
                    if plot_data:
                        fig = go.Figure()
                        
                        # Línea de accuracy por periodo
                        fig.add_trace(go.Scatter(
                            x=plot_data['periodos'],
                            y=plot_data['accuracies'],
                            mode='lines+markers',
                            name='Accuracy',
                            line=dict(color='#F2A100', width=2),
                            marker=dict(size=8)
                        ))
                        
                        # Línea de promedio
                        fig.add_trace(go.Scatter(
                            x=plot_data['periodos'],
                            y=[plot_data['accuracy_promedio']] * len(plot_data['periodos']),
                            mode='lines',
                            name='Promedio',
                            line=dict(color='#757575', width=1, dash='dash')
                        ))
                        
                        fig.update_layout(
                            title='Evolución del Accuracy por Periodo',
                            xaxis_title='Periodo',
                            yaxis_title='Accuracy',
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(color='#333333'),
                            height=400,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Interpretación
                        st.markdown("### Interpretación")
                        
                        if stability > 0.7:
                            st.success(
                                "Los pesos optimizados muestran alta estabilidad temporal. "
                                "El modelo funciona consistentemente en diferentes periodos."
                            )
                        elif stability > 0.5:
                            st.warning(
                                "Estabilidad moderada. Hay variabilidad en el rendimiento según el periodo. "
                                "Considera ajustar los pesos o usar ventanas adaptativas."
                            )
                        else:
                            st.error(
                                "Baja estabilidad temporal. El rendimiento varía significativamente. "
                                "Los pesos pueden estar sobreajustados a un periodo específico."
                            )
            
            except Exception as e:
                st.error(f"Error en validación: {str(e)}")
    
    # ========================================================================
    # TAB 6: HISTORIAL
    # ========================================================================
    
    with tab6:
        st.markdown("## Historial de Predicciones")
        
        if len(st.session_state.historial) == 0:
            st.info("No hay predicciones en el historial todavía. ¡Genera tu primera predicción!")
        else:
            for i, entry in enumerate(st.session_state.historial):
                with st.expander(f"Predicción #{len(st.session_state.historial) - i} - {entry['timestamp']} - Método: {entry['metodo']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("**Números:**")
                        numeros_texto = ', '.join([f"{n:02d}" for n in entry['prediccion']])
                        st.markdown(f"### {numeros_texto}")
                    
                    with col2:
                        st.markdown("**Estadísticas:**")
                        if 'suma_total' in entry['scores']:
                            st.write(f"Suma: {entry['scores']['suma_total']}")
                            st.write(f"Score: {entry['scores']['score_promedio']:.3f}")
                            st.write(f"Pares: {entry['scores']['pares']}/6")
            
            # Botón para limpiar historial
            if st.button("Limpiar Historial", type="secondary"):
                st.session_state.historial = []
                st.session_state.prediction_count = 0
                # Eliminar archivo JSON
                if HISTORIAL_FILE.exists():
                    HISTORIAL_FILE.unlink()
                st.rerun()


# ============================================================================
# EJECUTAR APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    main()

