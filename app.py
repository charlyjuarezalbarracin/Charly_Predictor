"""
================================================================================
  CHARLY PREDICTOR - INTERFAZ GRÁFICA WEB
  Sistema de Predicción de Quini 6
================================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
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
from core.generator.optimizer import CombinationOptimizer
from core.backtesting import WalkForwardBacktester
from utils.data_generator import generate_sample_data
from varios.scraper_quiniya_final import actualizar_historico_csv, obtener_pozos_ultimo_sorteo
from varios.scraper_loto import actualizar_historico_loto_csv, obtener_pozos_loto

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
    page_title="Charly Predictor",
    page_icon="CP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Estilo Midasmind
st.markdown("""
<style>
    /* Ocultar botones +/- de todos los number_input */
    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {
        display: none !important;
    }

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
        margin-bottom: 0.5rem !important;
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
    
    /* Deshabilitar input de búsqueda en selectbox - solo selección con mouse/teclado */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
        user-select: none !important;
        cursor: pointer !important;
        text-shadow: none !important;
        outline: none !important;
        border: none !important;
        box-shadow: none !important;
        color: inherit !important;
    }
    
    /* Eliminar cualquier decoración naranja */
    div[data-baseweb="select"] input::before,
    div[data-baseweb="select"] input::after {
        display: none !important;
    }
    
    /* Ocultar placeholder y cursor */
    div[data-baseweb="select"] input::placeholder {
        opacity: 0 !important;
    }
    
    div[data-baseweb="select"] input:focus {
        caret-color: transparent !important;
        outline: none !important;
        box-shadow: none !important;
        border-color: transparent !important;
    }
    
    /* Remover outline general del selectbox */
    div[data-baseweb="select"]:focus-within {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Ocultar iconos/decoradores dentro del input container */
    div[data-baseweb="select"] .st-emotion-cache-* {
        color: inherit !important;
    }
    
    /* Hacer que solo el container sea clickeable */
    div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    
    /* Prevenir que se vea el cursor de texto */
    div[data-testid="stSelectbox"] * {
        cursor: pointer !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNCIONES DE SESIÓN Y PERSISTENCIA
# ============================================================================

HISTORIAL_FILE = Path('data/historial_predicciones.json')
POZOS_FILE = Path('data/pozos_actuales.json')
POZOS_LOTO_FILE = Path('data/loto/pozos_loto.json')
GASTOS_FILE = Path('data/gastos_inversiones.json')

GAME_CONFIGS = {
    'quini6': {
        'nombre': 'Quini 6',
        'csv_path': 'data/quini6_historico.csv',
        'usa_pozos': True,
        'max_number': 45,
        'numbers_per_draw': 6,
        'dias_sorteo': [2, 6],
        'modalidades': ['Tradicional', 'Segunda', 'Revancha', 'Siempre Sale'],
    },
    'loto': {
        'nombre': 'Loto',
        'csv_path': 'data/loto/loto_historico.csv',
        'usa_pozos': True,
        'max_number': 45,
        'numbers_per_draw': 6,
        'dias_sorteo': [2, 5],
        'modalidades': ['Loto Tradicional', 'Loto Match', 'Loto Desquite', 'Loto Sale o Sale'],
    },
}

GAME_LABEL_TO_KEY = {
    'Quini 6': 'quini6',
    'Loto': 'loto',
}


def obtener_config_juego(juego: str = None):
    juego_key = juego or st.session_state.get('juego_actual', 'quini6')
    return GAME_CONFIGS.get(juego_key, GAME_CONFIGS['quini6'])

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

def calcular_inversion_portfolio(capital_inicial, pct_pf, tasa_pf, pct_fci_cer, tasa_fci_cer, 
                                  pct_fci_usd, tasa_fci_usd, inflacion_mensual, 
                                  meses=12, gastos_iniciales=None):
    """Calcula proyección de inversiones con portfolio diversificado
    
    Args:
        capital_inicial: Capital total a invertir
        pct_pf: Porcentaje en plazo fijo (0-100)
        tasa_pf: Tasa mensual plazo fijo (%)
        pct_fci_cer: Porcentaje en FCI CER (0-100)
        tasa_fci_cer: Tasa mensual FCI CER (%)
        pct_fci_usd: Porcentaje en FCI USD (0-100)
        tasa_fci_usd: Tasa mensual FCI USD (%)
        inflacion_mensual: Inflación mensual (%)
        meses: Número de meses a proyectar
        gastos_iniciales: Dict con {mes: monto} de gastos editables desde grilla
    
    Returns:
        pandas.DataFrame con proyección mensual
    """
    if gastos_iniciales is None:
        gastos_iniciales = {}
    
    # Nombres de meses en orden
    meses_nombres = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    
    # Obtener mes actual (1-12) y calcular índice inicial
    mes_actual = datetime.now().month
    mes_inicio = mes_actual - 1
    
    # Distribución inicial
    capital_pf = capital_inicial * (pct_pf / 100)
    capital_cer = capital_inicial * (pct_fci_cer / 100)
    capital_usd = capital_inicial * (pct_fci_usd / 100)
    
    resultados = []
    total_rentabilidad = 0
    total_neto = 0
    total_gastos = sum(gastos_iniciales.values()) if gastos_iniciales else 0
    
    for i in range(meses):
        indice_mes = (mes_inicio + i) % 12
        mes_nombre = meses_nombres[indice_mes]
        
        # Capital total al inicio del mes
        acumulado = capital_pf + capital_cer + capital_usd
        
        # Rentabilidad de cada activo
        rent_pf = capital_pf * (tasa_pf / 100)
        rent_cer = capital_cer * (tasa_fci_cer / 100)
        rent_usd = capital_usd * (tasa_fci_usd / 100)
        
        rentabilidad_total = rent_pf + rent_cer + rent_usd
        
        # Gastos del mes (solo desde grilla editable)
        gastos_mes = gastos_iniciales.get(i + 1, 0)
        
        # Neto del mes
        neto = rentabilidad_total - gastos_mes
        
        # Guardar resultado
        resultados.append({
            'Mes': mes_nombre,
            'Acumulado': acumulado,
            'TNA': None,  # No aplica en portfolio
            'Rentabilidad': rentabilidad_total,
            'Neto': neto,
            'Gastos': gastos_mes if gastos_mes > 0 else None
        })
        
        # Actualizar capitales para siguiente mes
        # Aplicar rentabilidad y restar gasto proporcionalmente
        capital_pf += rent_pf - (gastos_mes * (pct_pf / 100))
        capital_cer += rent_cer - (gastos_mes * (pct_fci_cer / 100))
        capital_usd += rent_usd - (gastos_mes * (pct_fci_usd / 100))
        
        # Acumular totales
        total_rentabilidad += rentabilidad_total
        total_neto += neto
    
    # Capital final
    capital_final = capital_pf + capital_cer + capital_usd
    
    # Agregar fila de totales
    resultados.append({
        'Mes': 'Total',
        'Acumulado': capital_final,
        'TNA': None,
        'Rentabilidad': total_rentabilidad,
        'Neto': total_neto,
        'Gastos': total_gastos if total_gastos > 0 else None
    })
    
    return pd.DataFrame(resultados)

def calcular_inversiones(premio, base, tna, meses=12, gastos_iniciales=None):
    """Calcula proyección de inversiones con capitalización mensual
    
    Args:
        premio: Monto del premio total
        base: Capital base de inversión
        tna: Tasa Nominal Anual (ej: 0.27 para 27%)
        meses: Número de meses a proyectar
        gastos_iniciales: Dict con {mes: monto} de gastos extraordinarios
    
    Returns:
        pandas.DataFrame con proyección mensual
    """
    if gastos_iniciales is None:
        gastos_iniciales = {}
    
    # Nombres de meses en orden
    meses_nombres = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    
    # Obtener mes actual (1-12) y calcular índice inicial
    mes_actual = datetime.now().month  # 1=ENERO, 2=FEBRERO, ..., 12=DICIEMBRE
    mes_inicio = mes_actual - 1  # Convertir a índice 0-based
    
    resultados = []
    acumulado = base
    total_rentabilidad = 0
    total_neto = 0
    total_gastos = 0
    
    for i in range(meses):
        # Calcular índice del mes, comenzando desde mes_inicio
        indice_mes = (mes_inicio + i) % 12
        mes_nombre = meses_nombres[indice_mes]
        
        # Calcular rentabilidad mensual sobre el acumulado ACTUAL
        rentabilidad = acumulado * (tna / 12)
        
        # Gastos del mes
        gastos = gastos_iniciales.get(i + 1, 0)
        
        # Neto del mes
        neto = rentabilidad - gastos
        
        # Guardar resultado del mes con acumulado ACTUAL (antes de actualizarlo)
        resultados.append({
            'Mes': mes_nombre,
            'Acumulado': acumulado,
            'TNA': tna,
            'Rentabilidad': rentabilidad,
            'Neto': neto,
            'Gastos': gastos if gastos > 0 else None
        })
        
        # Actualizar acumulado para el siguiente mes
        acumulado += neto
        
        # Acumular totales
        total_rentabilidad += rentabilidad
        total_neto += neto
        total_gastos += gastos
    
    # Agregar fila de totales
    resultados.append({
        'Mes': 'Total',
        'Acumulado': acumulado,
        'TNA': None,
        'Rentabilidad': total_rentabilidad,
        'Neto': total_neto,
        'Gastos': total_gastos if total_gastos > 0 else None
    })
    
    return pd.DataFrame(resultados)

def guardar_pozos_json(pozos):
    """Guardar pozos de Quini6 en archivo JSON"""
    try:
        POZOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(POZOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pozos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"No se pudo guardar pozos: {str(e)}")

def cargar_pozos_json():
    """Cargar pozos de Quini6 desde archivo JSON"""
    try:
        if POZOS_FILE.exists():
            with open(POZOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"No se pudo cargar pozos: {str(e)}")
        return None


def guardar_pozos_loto_json(pozos):
    """Guardar pozos de Loto en archivo JSON (separado de Quini6)"""
    try:
        POZOS_LOTO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(POZOS_LOTO_FILE, 'w', encoding='utf-8') as f:
            json.dump(pozos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"No se pudo guardar pozos Loto: {str(e)}")


def _sanear_importes_pozos_loto(pozos):
    """Corrige importes de Loto inflados x100 por parseo histórico de decimales XML."""
    if not isinstance(pozos, dict):
        return pozos, False

    modalidades = ['Tradicional', 'Match', 'Desquite', 'SaleOSale']
    premios = []
    for mod in modalidades:
        data = pozos.get(mod)
        if not isinstance(data, dict):
            continue
        premio = data.get('premio')
        try:
            premios.append((mod, int(premio)))
        except Exception:
            continue

    if len(premios) < 3:
        return pozos, False

    # Patrón observado del bug: varios pozos quedan x100 (dos decimales anexados).
    # Señal robusta: al menos 2 modalidades por encima de 10 mil millones.
    altos = sum(1 for _, v in premios if v >= 10_000_000_000)
    if altos < 2:
        return pozos, False

    pozos_fix = dict(pozos)
    for mod, valor in premios:
        data = dict(pozos_fix.get(mod, {}))
        data['premio'] = str(valor // 100)
        pozos_fix[mod] = data

    return pozos_fix, True

def cargar_pozos_loto_json():
    """Cargar pozos de Loto desde archivo JSON (separado de Quini6)"""
    try:
        if POZOS_LOTO_FILE.exists():
            with open(POZOS_LOTO_FILE, 'r', encoding='utf-8') as f:
                pozos = json.load(f)

            pozos_saneados, cambiado = _sanear_importes_pozos_loto(pozos)
            if cambiado:
                guardar_pozos_loto_json(pozos_saneados)
            return pozos_saneados
        return None
    except Exception as e:
        print(f"No se pudo cargar pozos Loto: {str(e)}")
        return None

def guardar_gastos_json(gastos):
    """Guardar gastos de inversiones en archivo JSON"""
    try:
        GASTOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Convertir keys de int a string para JSON
        gastos_serializables = {str(k): v for k, v in gastos.items()}
        with open(GASTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(gastos_serializables, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"No se pudo guardar gastos: {str(e)}")

def cargar_gastos_json():
    """Cargar gastos de inversiones desde archivo JSON"""
    try:
        if GASTOS_FILE.exists():
            with open(GASTOS_FILE, 'r', encoding='utf-8') as f:
                gastos_str = json.load(f)
                # Convertir keys de string a int
                return {int(k): v for k, v in gastos_str.items()}
        return None
    except Exception as e:
        print(f"No se pudo cargar gastos: {str(e)}")
        return None

def obtener_ultima_fecha_csv(juego='quini6'):
    """Obtener la última fecha del archivo CSV"""
    try:
        config_juego = obtener_config_juego(juego)
        csv_path = Path(config_juego['csv_path'])
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

                # Salvaguarda para Loto: algunas versiones previas guardaron
                # montos del XML inflados x100 al concatenar decimales.
                if st.session_state.get('juego_actual') == 'loto' and numero >= 100_000_000_000:
                    numero = numero // 100

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

def obtener_fechas_validas(data, juego='quini6'):
    """
    Obtiene las fechas válidas (miércoles y domingos) del dataset ordenadas de más reciente a más antigua
    
    Args:
        data: DataFrame con todos los sorteos históricos
    
    Returns:
        Lista de fechas únicas ordenadas descendentemente
    """
    # Obtener fechas únicas y ordenar de más reciente a más antigua
    fechas_unicas = pd.to_datetime(data['fecha']).dt.date.unique()
    fechas_ordenadas = sorted(fechas_unicas, reverse=True)
    
    config_juego = obtener_config_juego(juego)
    dias_sorteo = config_juego.get('dias_sorteo', [])
    if not dias_sorteo:
        return fechas_ordenadas

    # Filtrar días válidos según juego
    fechas_validas = []
    for fecha in fechas_ordenadas:
        dia_semana = pd.Timestamp(fecha).dayofweek
        if dia_semana in dias_sorteo:
            fechas_validas.append(fecha)
    
    return fechas_validas


def controlar_boleta(numeros_jugados, data, fecha_seleccionada=None, juego='quini6'):
    """
    Controla una jugada de 6 números contra los 4 sorteos de una fecha específica
    
    Args:
        numeros_jugados: Lista de 6 números ingresados por el usuario
        data: DataFrame con todos los sorteos históricos
        fecha_seleccionada: Fecha a controlar (si es None, usa la última fecha)
    
    Returns:
        Lista de 4 dicts con resultados (Tradicional, Segunda, Revancha, Siempre Sale)
    """
    # Obtener la fecha a controlar
    if fecha_seleccionada is None:
        fecha_control = data['fecha'].max()
    else:
        # Convertir fecha_seleccionada a string si es necesario
        if hasattr(fecha_seleccionada, 'strftime'):
            fecha_control = fecha_seleccionada.strftime('%Y-%m-%d')
        else:
            fecha_control = str(fecha_seleccionada)
    
    # Filtrar sorteos de la fecha y ordenar por sorteo_id para mantener orden correcto
    sorteos_fecha = data[data['fecha'] == fecha_control].sort_values('sorteo_id')
    
    config_juego = obtener_config_juego(juego)
    modalidades = config_juego.get('modalidades', ['Tradicional', 'Segunda', 'Revancha', 'Siempre Sale'])

    if len(sorteos_fecha) != len(modalidades):
        return None
    
    resultados = []
    for idx, (_, sorteo) in enumerate(sorteos_fecha.iterrows()):
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
            'fecha': fecha_control
        })
    
    return resultados


@st.cache_data
def cargar_resultados_reales_historial(juego='quini6'):
    """Carga sorteos reales desde CSV para evaluar aciertos del historial."""
    config_juego = obtener_config_juego(juego)
    csv_path = config_juego['csv_path']

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame(columns=['fecha', 'modalidad', 'numeros_real', 'numero_plus_real'])

    df['fecha'] = pd.to_datetime(df['fecha']).dt.date

    if 'sorteo_id' not in df.columns:
        df['sorteo_id'] = range(1, len(df) + 1)

    df = df.sort_values(['fecha', 'sorteo_id']).reset_index(drop=True)

    num_cols = ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    df['numeros_real'] = df.apply(
        lambda row: tuple(sorted([int(row[c]) for c in num_cols])),
        axis=1
    )

    if juego == 'quini6':
        modalidades = config_juego.get('modalidades', ['Tradicional', 'Segunda', 'Revancha', 'Siempre Sale'])
        df['modalidad_idx'] = df.groupby('fecha').cumcount()
        df['modalidad'] = df['modalidad_idx'].apply(
            lambda idx: modalidades[idx] if idx < len(modalidades) else f"Sorteo {idx + 1}"
        )
        df['numero_plus_real'] = pd.NA
    else:
        if 'modalidad' not in df.columns:
            modalidades = config_juego.get('modalidades', ['Loto Tradicional', 'Loto Match', 'Loto Desquite', 'Loto Sale o Sale'])
            df['modalidad_idx'] = df.groupby('fecha').cumcount()
            df['modalidad'] = df['modalidad_idx'].apply(
                lambda idx: modalidades[idx] if idx < len(modalidades) else f"Sorteo {idx + 1}"
            )
        if 'numero_plus' in df.columns:
            df['numero_plus_real'] = pd.to_numeric(df['numero_plus'], errors='coerce')
        else:
            df['numero_plus_real'] = pd.NA

    return df[['fecha', 'modalidad', 'numeros_real', 'numero_plus_real']].copy()


def inferir_juego_historial(juego_nombre):
    """Mapea nombre del juego guardado en historial a clave interna."""
    nombre = str(juego_nombre).strip().lower()
    if 'loto' in nombre:
        return 'loto'
    return 'quini6'


def evaluar_entry_historial_con_real(entry, df_real):
    """Evalúa una predicción del historial contra todos los sorteos de la primera fecha disponible."""
    if df_real is None or df_real.empty:
        return None

    prediccion = entry.get('prediccion')
    if not isinstance(prediccion, list) or len(prediccion) != 6:
        return None

    try:
        fecha_pred = datetime.strptime(entry.get('timestamp', ''), "%Y-%m-%d %H:%M:%S").date()
    except Exception:
        return None

    candidatos = df_real[df_real['fecha'] >= fecha_pred]
    if candidatos.empty:
        return {
            'estado': 'pendiente'
        }

    fecha_objetivo = candidatos['fecha'].min()
    sorteos_fecha = candidatos[candidatos['fecha'] == fecha_objetivo]

    pred_set = set(int(n) for n in prediccion)
    resultados_modalidad = []
    for _, row in sorteos_fecha.iterrows():
        numeros_real = row['numeros_real']
        coincidencias = sorted(pred_set & set(numeros_real))
        aciertos = len(coincidencias)
        resultados_modalidad.append({
            'modalidad': str(row['modalidad']),
            'aciertos': int(aciertos),
            'coincidencias': [int(n) for n in coincidencias]
        })

    if not resultados_modalidad:
        return None

    resultado = {
        'estado': 'ok',
        'fecha_real': str(fecha_objetivo),
        'resultados_modalidad': resultados_modalidad,
    }

    plus_pred = entry.get('numero_plus')
    plus_real = sorteos_fecha['numero_plus_real'].iloc[0] if 'numero_plus_real' in sorteos_fecha.columns and len(sorteos_fecha) > 0 else pd.NA
    if plus_pred is not None and pd.notna(plus_real):
        resultado['plus_disponible'] = True
        resultado['acierto_plus'] = int(int(plus_pred) == int(plus_real))
        resultado['plus_real'] = int(plus_real)
    else:
        resultado['plus_disponible'] = False

    return resultado


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
        # Cargar pozos Quini6 desde JSON
        st.session_state.pozos_actuales = cargar_pozos_json()
    if 'pozos_loto' not in st.session_state:
        # Cargar pozos Loto desde JSON (archivo separado)
        st.session_state.pozos_loto = cargar_pozos_loto_json()
    if 'juego_actual' not in st.session_state:
        st.session_state.juego_actual = 'quini6'
    if 'ultima_fecha_csv' not in st.session_state:
        st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv(st.session_state.juego_actual)


def agregar_al_historial(prediccion, metodo, scores_info, numero_plus=None):
    """Agregar predicción al historial y guardar en JSON"""
    entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'juego': obtener_config_juego()['nombre'],
        'prediccion': convertir_a_serializable(prediccion),
        'metodo': metodo,
        'scores': convertir_a_serializable(scores_info),
        'numero_plus': numero_plus
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
def cargar_datos(juego='quini6'):
    """Cargar datos históricos desde CSV"""
    loader = DataLoader()
    config_juego = obtener_config_juego(juego)
    csv_path = config_juego['csv_path']
    
    try:
        # Siempre cargar desde CSV real
        data = loader.load_csv(csv_path)
    except Exception as e:
        if juego == 'quini6':
            # Mantener comportamiento existente para Quini6
            st.warning(f"No se pudo cargar CSV: {e}. Usando datos de muestra.")
            sorteos = generate_sample_data(num_sorteos=200)
            data = loader.load_from_list(sorteos)
        else:
            raise Exception(f"No se pudo cargar historial de {config_juego['nombre']} en {csv_path}: {e}")
    
    return data


@st.cache_data
def ejecutar_analisis(data):
    """Ejecutar análisis estadístico completo"""
    # Análisis de frecuencias
    freq_analyzer = FrequencyAnalyzer()
    freq_analyzer.analyze(data)
    
    # Análisis de correlaciones
    corr_analyzer = CorrelationAnalyzer()
    corr_analyzer.analyze(data)
    
    # Análisis de patrones
    pattern_analyzer = PatternAnalyzer()
    pattern_analyzer.analyze(data)
    
    return freq_analyzer, corr_analyzer, pattern_analyzer


def mostrar_analisis_regresion_equilibrio(regression_analyzer):
    """Muestra el análisis de regresión al equilibrio de forma compacta"""
    summary = regression_analyzer.get_summary()
    
    deseq = summary['desequilibrios_detectados']
    hay_desequilibrios = any(deseq.values())
    
    if not hay_desequilibrios:
        st.info("âœ“ No se detectaron desequilibrios significativos. Sistema en equilibrio normal.")
        return
    
    st.warning("âš ï¸ Desequilibrios detectados - Sistema aplicará correcciones automáticas")
    
    corr = summary['correcciones_aplicar']
    metricas = summary['metricas']
    
    # Mostrar en formato compacto
    cols = st.columns(3)
    
    # Paridad(cont.)
    with cols[0]:
        if deseq['paridad']:
            desbalance_pct = abs(metricas['desbalance_pares']) * 100
            st.markdown("Pares/Impares")
            st.markdown(f"Desbalance: {desbalance_pct:.1f}%")
            if corr['paridad']:
                st.markdown(f"â†’ {corr['paridad'].replace('_', ' ').title()}")
        else:
            st.markdown("Pares/Impares")
            st.markdown("âœ“ En equilibrio")
    
    # Suma
    with cols[1]:
        if deseq['suma']:
            z_score = metricas['z_score_suma']
            st.markdown("Suma Total")
            st.markdown(f"Z-Score: {z_score:+.2f}Ïƒ")
            if corr['suma']:
                st.markdown(f"â†’ {corr['suma'].replace('_', ' ').title()}")
                if metricas['suma_objetivo']:
                    st.markdown(f"Objetivo: ~{metricas['suma_objetivo']:.0f}")
        else:
            st.markdown("Suma Total")
            st.markdown("âœ“ En equilibrio")
    
    # Rangos
    with cols[2]:
        if deseq['rangos']:
            st.markdown("Rangos")
            for rango, accion in corr['rangos'].items():
                rango_nombre = rango.replace('rango_', '').title()
                st.markdown(f"{rango_nombre}: {accion}")
        else:
            st.markdown("Rangos")
            st.markdown("âœ“ En equilibrio")


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
            st.markdown(f"{i}. **Número {num}** - Score: {score:.2f} (Z: {z:+.2f}Ïƒ)")


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


def generar_prediccion_rapida(freq_analyzer):
    """
    Genera predicción simple combinando frecuencia absoluta + calientes.
    NO usa scoring complejo, solo combina 50% frecuencia + 50% calientes.
    Replica EXACTAMENTE el comportamiento de analisis_rapido.py
    """
    from collections import defaultdict
    
    # Obtener datos del freq_analyzer
    freq_abs = freq_analyzer.results['frecuencia_absoluta']
    freq_reciente = freq_analyzer.results['frecuencia_reciente']
    
    # Crear ranking por frecuencia absoluta - determinismo en empates
    sorted_freq = sorted(freq_abs.items(), key=lambda x: (-x[1], x[0]))[:15]
    
    # Crear números calientes con determinismo en empates
    # Ordenar por frecuencia descendente, luego por número ascendente para consistencia
    calientes = sorted(freq_reciente.items(), key=lambda x: (-x[1], x[0]))[:10]
    
    # Crear scores combinados
    scores = defaultdict(float)
    
    # Puntaje por frecuencia absoluta (normalizado) - 50% peso
    max_freq = sorted_freq[0][1]
    for num, count in sorted_freq:
        scores[num] += (count / max_freq) * 50
    
    # Puntaje por calientes (normalizado) - 50% peso
    max_caliente = calientes[0][1]
    for num, count in calientes[:15]:
        scores[num] += (count / max_caliente) * 50
    
    # Ordenar por score combinado (desc) y luego por número (asc) para determinismo en empates
    top_candidatos = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:6]
    numeros = sorted([num for num, _ in top_candidatos])
    
    # Calcular estadísticas
    suma = sum(numeros)
    pares = sum(1 for n in numeros if n % 2 == 0)
    score_promedio = sum(score for _, score in top_candidatos) / 6
    
    return {
        'numeros': numeros,
        'suma': suma,
        'pares': pares,
        'impares': 6 - pares,
        'score_promedio': score_promedio,
        'detalles': dict(top_candidatos)
    }


# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def crear_grafico_frecuencias(freq_analyzer):
    """Crear gráfico de barras de frecuencias"""
    # Obtener datos de frecuencia
    freq_data = freq_analyzer.results['frecuencia_absoluta']
    
    # Crear DataFrame con TODOS los números 0-45
    df = pd.DataFrame(list(freq_data.items()), columns=['Número', 'Frecuencia'])
    df = df.sort_values('Número')
    
    # Crear gráfico con Plotly
    fig = px.bar(
        df, 
        x='Número', 
        y='Frecuencia',
        title='Frecuencia de Aparición de Números',
        color='Frecuencia',
        color_continuous_scale=[[0, '#FFF8E1'], [0.5, '#FFD54F'], [1, '#F2A100']]
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        height=320,
        title_font=dict(size=16, color='#333333', family='sans-serif'),
        xaxis=dict(showgrid=False, tickmode='linear', tick0=0, dtick=1),
        yaxis=dict(gridcolor='#f0f0f0')
    )
    
    return fig


def crear_grafico_calientes_frios(freq_analyzer):
    """Gráfico comparativo de números calientes vs fríos"""
    # Extraer números de las tuplas (numero, frecuencia)
    calientes = [num for num, freq in freq_analyzer.results['numeros_calientes'][:10]]
    frios = [num for num, freq in freq_analyzer.results['numeros_frios'][:10]]
    
    # Crear lista de TODOS los números 0-45
    todos_numeros = list(range(46))
    freq_abs = freq_analyzer.results['frecuencia_absoluta']
    
    # Asignar colores según categoría
    colores = []
    for n in todos_numeros:
        if n in calientes:
            colores.append('#F2A100')  # Naranja para calientes
        elif n in frios:
            colores.append('#BDBDBD')  # Gris para fríos
        else:
            colores.append('#FFE082')  # Amarillo claro para neutrales
    
    fig = go.Figure()
    
    # Una sola traza con TODOS los números y frecuencias reales
    fig.add_trace(go.Bar(
        x=todos_numeros,
        y=[freq_abs.get(n, 0) for n in todos_numeros],
        marker_color=colores,
        showlegend=False
    ))
    
    fig.update_layout(
        title='Números Calientes vs Fríos',
        xaxis_title='Número',
        yaxis_title='Frecuencia',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        height=320,
        title_font=dict(size=16, color='#333333'),
        xaxis=dict(showgrid=False, tickmode='linear', tick0=0, dtick=1),
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
        height=800,
        title_font=dict(size=16, color='#333333'),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=False, dtick=1)
    )
    
    return fig


@st.cache_data
def predecir_numero_plus(csv_path: str) -> dict:
    """
    Predice el Número plus del Loto (rango 0-9).
    Usa frecuencia histórica, frecuencia reciente y latencia (sorteos desde última aparición).
    Retorna el número con mayor score y el top 3.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    if 'numero_plus' not in df.columns:
        return {'numero_plus': 0, 'top3': [0, 1, 2], 'scores': {}}

    serie = df['numero_plus'].dropna().astype(int)
    total = len(serie)
    if total == 0:
        return {'numero_plus': 0, 'top3': [0, 1, 2], 'scores': {}}

    recientes = min(50, total)
    serie_reciente = serie.iloc[-recientes:]

    scores = {}
    for d in range(10):
        # Frecuencia histórica (normalizada)
        freq_hist = (serie == d).sum() / total

        # Frecuencia reciente
        freq_rec = (serie_reciente == d).sum() / recientes

        # Latencia inversa: cuántos sorteos desde la última aparición
        apariciones = serie[serie == d].index.tolist()
        if apariciones:
            latencia = total - 1 - apariciones[-1]
        else:
            latencia = total
        lat_inv = latencia / (total + 1)  # cuanto más ausente, mayor penalización → invertir

        # Score: 40% hist + 40% reciente + 20% latencia-inversa (penaliza mucho ausente)
        scores[d] = 0.40 * freq_hist + 0.40 * freq_rec + 0.20 * (1 - lat_inv)

    ordenados = sorted(scores.items(), key=lambda x: -x[1])
    return {
        'numero_plus': ordenados[0][0],
        'top3': [d for d, _ in ordenados[:3]],
        'scores': scores
    }


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


def mostrar_bloque_copiable(texto, key_base="pred"):
    """Muestra texto con el botón nativo de copiar de Streamlit."""
    st.code(texto, language=None)


def aplicar_fallback_copiado_nativo():
    """Parchea el botón nativo de copiar de st.code con fallback execCommand."""
    components.html(
        """
        <script>
        (function () {
            let doc = document;
            try {
                if (window.parent && window.parent.document) {
                    doc = window.parent.document;
                }
            } catch (e) {
                doc = document;
            }

            if (doc.__charlyCopyPatched) {
                return;
            }
            doc.__charlyCopyPatched = true;

            async function fallbackCopy(texto) {
                try {
                    const navParent = (window.parent && window.parent.navigator) ? window.parent.navigator : null;
                    if (navParent && navParent.clipboard) {
                        await navParent.clipboard.writeText(texto);
                        return true;
                    }
                } catch (e) {}

                try {
                    if (navigator.clipboard && window.isSecureContext) {
                        await navigator.clipboard.writeText(texto);
                        return true;
                    }
                } catch (e) {}

                try {
                    const area = doc.createElement("textarea");
                    area.value = texto;
                    area.setAttribute("readonly", "");
                    area.style.position = "fixed";
                    area.style.left = "-9999px";
                    doc.body.appendChild(area);
                    area.focus();
                    area.select();
                    area.setSelectionRange(0, area.value.length);
                    const ok = doc.execCommand("copy");
                    doc.body.removeChild(area);
                    return ok;
                } catch (e) {
                    return false;
                }
            }

            function encontrarContenedorConCode(inicio) {
                let el = inicio;
                for (let i = 0; i < 10 && el; i++) {
                    if (el.querySelector && el.querySelector("code")) {
                        return el;
                    }
                    el = el.parentElement;
                }
                return null;
            }

            async function manejarEventoCopia(ev) {
                const btn = ev.target.closest("button");
                if (!btn) return;

                const aria = (btn.getAttribute("aria-label") || "").toLowerCase();
                const testid = (btn.getAttribute("data-testid") || "").toLowerCase();
                const isCopyBtn = aria.includes("copy to clipboard") || aria.includes("copiar") || testid.includes("copy");
                if (!isCopyBtn) return;

                const bloque = encontrarContenedorConCode(btn);
                if (!bloque) return;

                const nodoTexto = bloque.querySelector("pre code") || bloque.querySelector("code") || bloque.querySelector("pre");
                if (!nodoTexto) return;

                const texto = (nodoTexto.innerText || "").trim();
                if (!texto) return;

                await fallbackCopy(texto);
            }

            doc.addEventListener("pointerdown", manejarEventoCopia, true);
            doc.addEventListener("click", manejarEventoCopia, true);
        })();
        </script>
        """,
        height=0,
    )


def mostrar_portfolio(portfolio, freq_analyzer, portfolio_gen, metodo_nombre, numero_plus=None):
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
                indicador = "â†‘"
            elif mom < -0.3:
                indicador = "â†“"
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
            },
            numero_plus=numero_plus
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
    
    nombre_juego_copiar = "Loto" if st.session_state.juego_actual == 'loto' else "Quini6"
    texto_copiar = f"{nombre_juego_copiar}:\n" + '\n'.join(texto_copiar_lines)
    mostrar_bloque_copiable(texto_copiar, key_base="portfolio")


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    init_session_state()
    aplicar_fallback_copiado_nativo()
    config_juego_actual = obtener_config_juego(st.session_state.juego_actual)
    
    # HEADER
    fecha_info = f"<div class='banner-fecha'>Datos actualizados al {st.session_state.ultima_fecha_csv}</div>" if st.session_state.ultima_fecha_csv else ""
    
    st.markdown(f"""
        <div class="app-banner">
            <div class="banner-logo">CP</div>
            <div class="banner-title">Charly Predictor</div>
            <div class="banner-subtitle">{config_juego_actual['nombre']}</div>
            {fecha_info}
        </div>
    """, unsafe_allow_html=True)
    
    # POZOS ACTUALES
    if config_juego_actual['usa_pozos']:
        if st.session_state.juego_actual == 'quini6' and st.session_state.pozos_actuales:
            pozos = st.session_state.pozos_actuales
            trad,    trad_info = formatear_pozo(pozos.get('Tradicional'))
            segunda, seg_info  = formatear_pozo(pozos.get('Segunda'))
            revancha,rev_info  = formatear_pozo(pozos.get('Revancha'))
            ss,      ss_info   = formatear_pozo(pozos.get('SiempreSale'))
            trad_info = trad_info or '-'
            seg_info  = seg_info  or '-'
            rev_info  = rev_info  or '-'
            ss_info   = ss_info   or '-'
            st.markdown(f"""
            <div class="pozos-container">
                <div class="pozos-title">Pozos Actuales</div>
                <div class="pozos-grid">
                    <div class="pozo-card">
                        <div class="pozo-modalidad">Tradicional</div>
                        <div class="pozo-valor">${trad}</div>
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
                        <div class="pozo-valor">${ss}</div>
                        <div class="pozo-info">{ss_info}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state.juego_actual == 'loto' and st.session_state.pozos_loto:
            pozos = st.session_state.pozos_loto
            trad,    trad_info  = formatear_pozo(pozos.get('Tradicional'))
            match,   match_info = formatear_pozo(pozos.get('Match'))
            desq,    desq_info  = formatear_pozo(pozos.get('Desquite'))
            sale,    sale_info  = formatear_pozo(pozos.get('SaleOSale'))
            trad_info  = trad_info  or '-'
            match_info = match_info or '-'
            desq_info  = desq_info  or '-'
            sale_info  = sale_info  or '-'

            # Resultados del ultimo sorteo desde XML (si existen).
            resultados = pozos.get('Resultados', {})
            meta = pozos.get('Meta', {})

            def _fmt_nums(nums):
                if not isinstance(nums, list) or len(nums) != 6:
                    return None
                try:
                    return '-'.join([f"{int(n):02d}" for n in nums])
                except Exception:
                    return None

            lineas_resultados = []
            trad_nums = _fmt_nums(resultados.get('Tradicional'))
            match_nums = _fmt_nums(resultados.get('Match'))
            desq_nums = _fmt_nums(resultados.get('Desquite'))
            sale_nums = _fmt_nums(resultados.get('SaleOSale'))
            plus_num = resultados.get('Plus')

            if trad_nums:
                lineas_resultados.append(f"Tradicional {trad_nums}")
            if match_nums:
                lineas_resultados.append(f"Match {match_nums}")
            if desq_nums:
                lineas_resultados.append(f"Desquite {desq_nums}")
            if sale_nums:
                lineas_resultados.append(f"Sale o Sale {sale_nums}")
            if plus_num is not None:
                try:
                    lineas_resultados.append(f"Numero plus {int(plus_num):02d}")
                except Exception:
                    lineas_resultados.append(f"Numero plus {plus_num}")

            fecha_meta = meta.get('fecha')
            if isinstance(fecha_meta, str) and len(fecha_meta) == 10 and '-' in fecha_meta:
                try:
                    yyyy, mm, dd = fecha_meta.split('-')
                    fecha_meta = f"{dd}/{mm}/{yyyy}"
                except Exception:
                    pass
            sorteo_meta = meta.get('sorteo')

            detalle_sorteo = ''
            if sorteo_meta or fecha_meta:
                sorteo_txt = f"Sorteo {sorteo_meta}" if sorteo_meta else ''
                fecha_txt = f"Fecha {fecha_meta}" if fecha_meta else ''
                separador = ' | ' if sorteo_txt and fecha_txt else ''
                detalle_sorteo = f"{sorteo_txt}{separador}{fecha_txt}"

            bloque_resultados = ''
            if detalle_sorteo or lineas_resultados:
                resultados_txt = ' | '.join(lineas_resultados)
                detalle_html = f'<div style="margin-top:0.2rem;color:#999;font-size:0.78rem;">{detalle_sorteo}</div>' if detalle_sorteo else ''
                resultados_html = f'<div style="margin-top:0.2rem;color:#ddd;font-size:0.76rem;line-height:1.35;">{resultados_txt}</div>' if resultados_txt else ''
                bloque_resultados = f'{detalle_html}{resultados_html}'

            st.markdown(f"""
            <div class="pozos-container">
                <div class="pozos-title">Pozos Actuales</div>
                <div class="pozos-grid">
                    <div class="pozo-card">
                        <div class="pozo-modalidad">Tradicional</div>
                        <div class="pozo-valor">${trad}</div>
                        <div class="pozo-info">{trad_info}</div>
                    </div>
                    <div class="pozo-card">
                        <div class="pozo-modalidad">Match</div>
                        <div class="pozo-valor">${match}</div>
                        <div class="pozo-info">{match_info}</div>
                    </div>
                    <div class="pozo-card">
                        <div class="pozo-modalidad">Desquite</div>
                        <div class="pozo-valor">${desq}</div>
                        <div class="pozo-info">{desq_info}</div>
                    </div>
                    <div class="pozo-card">
                        <div class="pozo-modalidad">Sale o Sale</div>
                        <div class="pozo-valor">${sale}</div>
                        <div class="pozo-info">{sale_info}</div>
                    </div>
                </div>
                {bloque_resultados}
                <div style="margin-top:0.2rem;color:#888;font-size:0.76rem;">Plus: Vacante</div>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # SIDEBAR - CONFIGURACIÓN
    # ========================================================================
    
    with st.sidebar:
        # Logo/Header del sidebar - Estilo Midasmind
        st.markdown("""
        <div class="sidebar-banner">
            <div class="banner-logo">CP</div>
            <div class="banner-title">Charly Predictor</div>
            <div class="banner-subtitle">%s</div>
        </div>
        """ % config_juego_actual['nombre'], unsafe_allow_html=True)

        st.markdown("### Juego")
        juego_label = st.radio(
            "Selecciona el juego:",
            options=list(GAME_LABEL_TO_KEY.keys()),
            index=0 if st.session_state.juego_actual == 'quini6' else 1,
            horizontal=True,
            label_visibility='collapsed'
        )
        juego_seleccionado = GAME_LABEL_TO_KEY[juego_label]

        if juego_seleccionado != st.session_state.juego_actual:
            st.session_state.juego_actual = juego_seleccionado
            st.session_state.data_loaded = False
            st.session_state.current_data = None
            st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv(juego_seleccionado)
            st.rerun()

        config_juego_actual = obtener_config_juego(st.session_state.juego_actual)
        
        # Banner informativo de configuración optimizada
        # st.info("""
        # âœ¨ **Configuración Optimizada Activa** | Rendimiento: 2.25 aciertos/sorteo promedio  
        # Los parámetros predeterminados han sido optimizados mediante 130+ pruebas de configuración.
        # """)
        
        # 1. CARGA DE DATOS
        
        # Cargar datos automáticamente al inicio
        if not st.session_state.data_loaded:
            with st.spinner("Cargando datos históricos..."):
                try:
                    data = cargar_datos(st.session_state.juego_actual)
                    st.session_state.current_data = data
                    st.session_state.data_loaded = True
                    st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv(st.session_state.juego_actual)
                except Exception as e:
                    st.session_state.data_loaded = False
                    st.session_state.current_data = None
                    st.error(str(e))

        # Actualizar desde QuiniYa
        # Detectar si estamos en Streamlit Cloud
        import os
        es_cloud = os.path.exists('/mount/src')  # Path típico de Streamlit Cloud
        
        if es_cloud:
            st.info("La actualización automática no está disponible en la versión cloud")
        else:
            if st.button(f"Actualizar datos de {config_juego_actual['nombre']}", width='stretch'):
                with st.spinner("Actualizando datos desde la red"):
                    try:
                        if st.session_state.juego_actual == 'quini6':
                            nuevos = actualizar_historico_csv(config_juego_actual['csv_path'])
                        elif st.session_state.juego_actual == 'loto':
                            nuevos = actualizar_historico_loto_csv(config_juego_actual['csv_path'])
                        else:
                            raise ValueError(f"Juego desconocido: {st.session_state.juego_actual}. No se puede actualizar datos.")

                        # Limpiar cachés para forzar recarga con datos nuevos
                        cargar_datos.clear()
                        ejecutar_analisis.clear()

                        # Recargar datos y análisis con sorteos nuevos
                        data = cargar_datos(st.session_state.juego_actual)
                        st.session_state.current_data = data
                        st.session_state.data_loaded = True
                        
                        # Actualizar última fecha del CSV
                        st.session_state.ultima_fecha_csv = obtener_ultima_fecha_csv(st.session_state.juego_actual)
                        
                        pozos = None
                        if config_juego_actual['usa_pozos']:
                            if st.session_state.juego_actual == 'quini6':
                                # QuiniYa.com.ar → pozos Quini6
                                pozos = obtener_pozos_ultimo_sorteo()
                                if pozos:
                                    st.session_state.pozos_actuales = pozos
                                    guardar_pozos_json(pozos)
                            elif st.session_state.juego_actual == 'loto':
                                # loto.loteriadelaciudad.gob.ar → pozos Loto
                                pozos = obtener_pozos_loto()
                                if pozos:
                                    st.session_state.pozos_loto = pozos
                                    guardar_pozos_loto_json(pozos)

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
        # st.markdown("### Generación Múltiple")
        
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
        
        # 4. OPTIMIZER
        usar_optimizer = st.checkbox(
            "Optimizer (Mejor Estadísticas)",
            value=False,
            help="Genera 5000 combinaciones internas y selecciona la de mejor balance entre score, suma (~137), pares (3/6) y spread"
        )
        
        st.markdown("---")
        
        # 5. PARÁMETROS AVANZADOS
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
                help="âš ï¸ Optimización: Latencia en 0.00 mejora el rendimiento"
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Predicción",
        "Control Boleta",
        "Análisis", 
        "Visualizaciones",
        "Validación Temporal",
        "Historial",
        "Inversiones"
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

            # Calcular número plus para Loto (una sola vez, se reutiliza en historial y display)
            _plus_loto = None
            if st.session_state.juego_actual == 'loto':
                _config_loto = obtener_config_juego('loto')
                _plus_result = predecir_numero_plus(_config_loto['csv_path'])
                _plus_loto = _plus_result['numero_plus']
                _plus_top3 = _plus_result['top3']
            
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
                    mostrar_portfolio(portfolio_std, freq_analyzer, portfolio_gen, "Estándar", numero_plus=_plus_loto)
                    
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
                    mostrar_portfolio(portfolio_cond, freq_analyzer, portfolio_gen_cond, "Condicional", numero_plus=_plus_loto)
                
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
                    mostrar_portfolio(portfolio, freq_analyzer, portfolio_gen, metodo_texto, numero_plus=_plus_loto)
                
                # NÚMERO PLUS para portfolio (solo Loto)
                if st.session_state.juego_actual == 'loto':
                    st.markdown("---")
                    st.markdown("### Número plus sugerido - Loto")
                    st.markdown(
                        f'<div style="display:flex;gap:12px;align-items:center;margin-bottom:0.5rem;">'
                        f'<div class="numero-predicho" style="background:#F2A100;color:#1a1a1a;font-weight:700;font-size:1.3rem;'
                        f'width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:50%;">'
                        f'{_plus_loto}</div>'
                        f'<span style="color:#888;font-size:0.85rem;">Alternativas: {_plus_top3[1]} · {_plus_top3[2]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # GENERACIÓN TRADICIONAL (sin portfolio)
            else:
                spinner_text = "Optimizando predicción (Monte Carlo 5000 iteraciones)..." if usar_optimizer else "Generando predicción..."
                with st.spinner(spinner_text):
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
                    
                    # Si optimizer activo, reemplazar combinaciones por las óptimas
                    if usar_optimizer:
                        optimizer = CombinationOptimizer()
                        
                        if metodo == GenerationStrategy.BOTH:
                            # Optimizar estándar - búsqueda 1
                            best_std, _ = optimizer.best_combination_search(scores, iterations=5000)
                            result['standard']['combination'] = best_std
                            analysis_std = result['standard']['analysis']
                            analysis_std['suma_total'] = sum(best_std)
                            analysis_std['pares'] = sum(1 for n in best_std if n % 2 == 0)
                            analysis_std['impares'] = 6 - analysis_std['pares']
                            analysis_std['score_promedio'] = sum(scores.get(n, 0) for n in best_std) / 6
                            analysis_std['consecutivos'] = sum(1 for i in range(5) if best_std[i+1] - best_std[i] == 1)
                            
                            # Optimizar condicional - búsqueda 2 (excluye la mejor anterior para diversidad)
                            scores_cond = {k: v * (0.7 if k in best_std else 1.0) for k, v in scores.items()}
                            best_cond, _ = optimizer.best_combination_search(scores_cond, iterations=5000)
                            result['conditional']['combination'] = best_cond
                            analysis_cond = result['conditional']['analysis']
                            analysis_cond['suma_total'] = sum(best_cond)
                            analysis_cond['pares'] = sum(1 for n in best_cond if n % 2 == 0)
                            analysis_cond['impares'] = 6 - analysis_cond['pares']
                            analysis_cond['score_promedio'] = sum(scores.get(n, 0) for n in best_cond) / 6
                            analysis_cond['consecutivos'] = sum(1 for i in range(5) if best_cond[i+1] - best_cond[i] == 1)
                        else:
                            best, _ = optimizer.best_combination_search(scores, iterations=5000)
                            result['combination'] = best
                            analysis = result['analysis']
                            analysis['suma_total'] = sum(best)
                            analysis['pares'] = sum(1 for n in best if n % 2 == 0)
                            analysis['impares'] = 6 - analysis['pares']
                            analysis['score_promedio'] = sum(scores.get(n, 0) for n in best) / 6
                            analysis['consecutivos'] = sum(1 for i in range(5) if best[i+1] - best[i] == 1)
                    
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
                        sufijo_opt = " + Optimizer" if usar_optimizer else ""
                        agregar_al_historial(
                            result['standard']['combination'],
                            f"Estándar{sufijo_opt}",
                            analysis_std,
                            numero_plus=_plus_loto
                        )
                        agregar_al_historial(
                            result['conditional']['combination'],
                            f"Condicional{sufijo_opt}",
                            analysis_cond,
                            numero_plus=_plus_loto
                        )
                        
                        # ANÁLISIS RÁPIDO - Tercera opción (sin scoring complejo)
                        st.markdown("---")
                        st.markdown("### Análisis Rápido (Frecuencia + Calientes)")
                        st.caption("Combinación simple: 50% frecuencia histórica + 50% números calientes recientes")
                        
                        prediccion_rapida = generar_prediccion_rapida(freq_analyzer)
                        mostrar_numeros_predichos(prediccion_rapida['numeros'], "")
                        
                        st.markdown("##### Estadísticas")
                        subcol1, subcol2, subcol3 = st.columns(3)
                        with subcol1:
                            st.metric("Suma", prediccion_rapida['suma'])
                        with subcol2:
                            st.metric("Score Simple", f"{prediccion_rapida['score_promedio']:.1f}")
                        with subcol3:
                            st.metric("Pares", f"{prediccion_rapida['pares']}/6")
                        
                        # Agregar al historial
                        agregar_al_historial(
                            prediccion_rapida['numeros'],
                            "Análisis Rápido",
                            {
                                'suma_total': prediccion_rapida['suma'],
                                'score_promedio': prediccion_rapida['score_promedio'],
                                'pares': prediccion_rapida['pares'],
                                'impares': prediccion_rapida['impares'],
                                'consecutivos': 0
                            },
                            numero_plus=_plus_loto
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
                        if usar_optimizer:
                            metodo_nombre += " + Optimizer"
                        agregar_al_historial(
                            result['combination'],
                            metodo_nombre,
                            analysis,
                            numero_plus=_plus_loto
                        )
                    
                    # Resumen para copiar
                    # Preparar texto para copiar
                    opt_suffix = " (Opt)" if usar_optimizer else ""

                    if st.session_state.juego_actual == 'loto':
                        lineas_pozos = [
                            "Tradicional: $2.953.483.488",
                            "Match: $821.384.114",
                            "Desquite: $1.268.201.915",
                        ]
                    else:
                        lineas_pozos = [
                            "Tradicional: $5.060.737.231",
                            "La Segunda: $2.346.625.033",
                            "Revancha: $2.953.483.488",
                        ]

                    nombre_juego_copiar = "Loto" if st.session_state.juego_actual == 'loto' else "Quini6"

                    if metodo == GenerationStrategy.BOTH:
                        nums_std = ', '.join([f"{int(n):02d}" for n in result['standard']['combination']])
                        nums_cond = ', '.join([f"{int(n):02d}" for n in result['conditional']['combination']])
                        nums_rapido = ', '.join([f"{int(n):02d}" for n in prediccion_rapida['numeros']])
                        texto_copiar = f"{nombre_juego_copiar}:\nEstándar{opt_suffix}: {nums_std}\nCondicional{opt_suffix}: {nums_cond}\nRápido: {nums_rapido}\n\n" + "\n".join(lineas_pozos)
                    else:
                        texto_copiar = ', '.join([f"{int(n):02d}" for n in result['combination']])
                        if usar_optimizer:
                            texto_copiar = f"(Opt) {texto_copiar}"
                        texto_copiar = f"{nombre_juego_copiar}:\n" + texto_copiar + "\n\n" + "\n".join(lineas_pozos)
                    
                    # NÚMERO PLUS (solo para Loto, siempre)
                    if st.session_state.juego_actual == 'loto':
                        st.markdown("---")
                        st.markdown("### Número plus sugerido - Loto")
                        st.markdown(
                            f'<div style="display:flex;gap:12px;align-items:center;margin-bottom:0.5rem;">'
                            f'<div class="numero-predicho" style="background:#F2A100;color:#1a1a1a;font-weight:700;font-size:1.3rem;'
                            f'width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:50%;">'
                            f'{_plus_loto}</div>'
                            f'<span style="color:#888;font-size:0.85rem;">Alternativas: {_plus_top3[1]} · {_plus_top3[2]}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        # Actualizar texto_copiar para incluir plus
                        texto_copiar = texto_copiar + f"\nNumero plus: {_plus_loto}"

                    mostrar_bloque_copiable(
                        texto_copiar,
                        key_base=f"pred_{st.session_state.prediction_count}"
                    )
    
    # ========================================================================
    # TAB 2: CONTROL BOLETA
    # ========================================================================
    
    with tab2:
        # CSS ULTRA ESPECÍFICO para eliminar espacios en Control de Boleta
        st.markdown("""
        <style>
        /* ELIMINAR TODOS los espacios en el tab de Control de Boleta */
        div[role="tabpanel"][id*="tabpanel-1"] .stVerticalBlock {
            gap: 0.3rem !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] .stElementContainer {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] .stMarkdown {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        /* h2 - Título principal con espacio abajo (separar sección 1) */
        div[role="tabpanel"][id*="tabpanel-1"] h2 {
            margin-bottom: 0.3rem !important;
            padding-bottom: 0.8rem !important;
        }
        /* h3 - Subtítulos de secciones con espacio arriba (separar secciones 2 y 3) */
        div[role="tabpanel"][id*="tabpanel-1"] h3 {
            margin-top: 1rem !important;
            margin-bottom: 0.2rem !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] p {
            margin-top: 0 !important;
            margin-bottom: 0.3rem !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] div[data-testid="stLayoutWrapper"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Selector de fecha
        # CSS para selectbox compacto y pegado al título
        st.markdown("""
        <style>
        div[data-testid="stSelectbox"] {
            max-width: 250px !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] h3 + div {
            margin-top: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] .stSelectbox {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### Selecciona la fecha del sorteo")
        
        data = st.session_state.current_data
        es_quini = st.session_state.juego_actual == 'quini6'
        fechas_disponibles = obtener_fechas_validas(data, juego=st.session_state.juego_actual)

        if not fechas_disponibles:
            st.warning("No hay fechas disponibles para controlar con los datos cargados.")
            return
        
        # Formatear fechas para mostrar con día de la semana
        opciones_fecha = []
        for fecha in fechas_disponibles:
            fecha_dt = pd.Timestamp(fecha)
            if es_quini:
                dia_semana = "Miércoles" if fecha_dt.dayofweek == 2 else "Domingo"
                opciones_fecha.append(f"{dia_semana} {fecha.strftime('%d/%m/%Y')}")
            else:
                opciones_fecha.append(fecha.strftime('%d/%m/%Y'))
        
        # Crear diccionario para mapear opción -> fecha
        mapa_fechas = dict(zip(opciones_fecha, fechas_disponibles))
        
        fecha_seleccionada_str = st.selectbox(
            "Fecha del sorteo",
            options=opciones_fecha,
            index=0,  # Por defecto la más reciente
            key="control_fecha_selector",
            label_visibility="collapsed"
        )
        
        fecha_seleccionada = mapa_fechas[fecha_seleccionada_str]
        
        # Área de ingreso de números
        st.markdown("### Ingresa tus números")
        
        # CSS para inputs circulares compactos SIN ESPACIOS
        st.markdown("""
        <style>
        /* ELIMINAR espacios alrededor de inputs */
        div[role="tabpanel"][id*="tabpanel-1"] div[data-testid="column"]:has([data-testid="stTextInput"]) {
            padding: 0 3px !important;
            min-width: 0 !important;
            margin: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] {
            width: 64px !important;
            margin: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] > div {
            width: 64px !important;
            height: 64px !important;
            margin: 0 !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] > div > div {
            width: 64px !important;
            height: 64px !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] input {
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
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] input:focus {
            border: 3px solid #F2A100 !important;
            outline: none !important;
        }
        div[role="tabpanel"][id*="tabpanel-1"] [data-testid="stTextInput"] label {
            display: none !important;
        }
        /* Margen entre esferas y botón Verificar */
        div[role="tabpanel"][id*="tabpanel-1"] button[kind="primary"] {
            margin-top: 0.5rem !important;
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
        
        # Convertir y validar (0 es válido; None representa campo incompleto)
        numeros_ingresados = []
        for num_str in numeros_texto:
            txt = num_str.strip()
            if txt == "":
                numeros_ingresados.append(None)
                continue

            try:
                num = int(txt)
                if 0 <= num <= 45:
                    numeros_ingresados.append(num)
                else:
                    numeros_ingresados.append(None)
            except:
                numeros_ingresados.append(None)
        
        # Botón con el mismo ancho que las 6 esferas
        cols_button = st.columns([0.25, 0.5, 0.25])
        with cols_button[1]:
            verificar = st.button("Verificar", type="primary", width='stretch')
        
        # Validaciones
        if verificar:
            # Validar que no haya números repetidos
            if any(n is None for n in numeros_ingresados):
                st.warning("âš ï¸ Por favor completa los 6 números con valores entre 0 y 45.")
            elif len(set(numeros_ingresados)) != 6:
                st.error("âš ï¸ No puedes repetir números. Cada número debe ser único.")
            else:
                # Realizar control
                data = st.session_state.current_data
                resultados = controlar_boleta(
                    numeros_ingresados,
                    data,
                    fecha_seleccionada,
                    juego=st.session_state.juego_actual
                )
                
                if resultados:
                    fecha_formateada = pd.Timestamp(resultados[0]['fecha']).strftime('%d/%m/%Y')
                    if es_quini:
                        dia_semana = "Miércoles" if pd.Timestamp(resultados[0]['fecha']).dayofweek == 2 else "Domingo"
                        st.success(f"âœ… Controlando contra los sorteos del {dia_semana} {fecha_formateada}")
                    else:
                        st.success(f"âœ… Controlando contra los sorteos del {fecha_formateada}")
                    
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
                                            st.success("ðŸŽ‰ Â¡FELICITACIONES! Â¡Ganaste el premio mayor!")
                                        elif resultado['aciertos'] == 5:
                                            st.success("ðŸŽŠ Â¡Excelente! Â¡5 aciertos! Â¡Premio importante!")
                                        else:
                                            st.info("ðŸ‘ Â¡Bien hecho! Tienes premio.")
                                    else:
                                        st.warning(f"No tienes premio. El mínimo para ganar en {resultado['modalidad']} son 4 aciertos.")
                else:
                    st.error("âŒ No se pudieron obtener los resultados. Verifica que haya datos cargados.")
    
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
                st.info(f"âœ“ Se usarán: {', '.join(ideas_activas)}")
            else:
                st.warning("âš ï¸ Ninguna IDEA activada en Parámetros â†’ Avanzados")
        
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
                        st.success(f"âœ“ Validación completada con {', '.join(ideas_activas)}")
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
                        
                        st.plotly_chart(fig, width='stretch')
                        
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

        historial_filtrado = [
            entry for entry in st.session_state.historial
            if inferir_juego_historial(entry.get('juego', 'Quini 6')) == st.session_state.juego_actual
        ]

        if len(historial_filtrado) == 0:
            st.info("No hay predicciones en el historial para este juego todavía.")
        else:
            resultados_reales_cache = {}
            for juego_key in [st.session_state.juego_actual]:
                try:
                    resultados_reales_cache[juego_key] = cargar_resultados_reales_historial(juego_key)
                except Exception:
                    resultados_reales_cache[juego_key] = None

            # Agrupar predicciones por timestamp (misma fecha/hora = misma sesión)
            from collections import OrderedDict
            grupos_historial = OrderedDict()
            for i, entry in enumerate(historial_filtrado):
                ts = entry['timestamp']
                if ts not in grupos_historial:
                    grupos_historial[ts] = []
                grupos_historial[ts].append(entry)
            
            for ts, entries in grupos_historial.items():
                n_preds = len(entries)
                metodos = ', '.join([e['metodo'] for e in entries])
                label = f"{ts} - {n_preds} prediccion{'es' if n_preds > 1 else ''}"
                
                with st.expander(label):
                    for entry in entries:
                        juego_entry = entry.get('juego', 'Quini 6')
                        juego_key = inferir_juego_historial(juego_entry)

                        evaluacion = evaluar_entry_historial_con_real(
                            entry,
                            resultados_reales_cache.get(juego_key)
                        )

                        coincidencias_map = {}
                        if evaluacion and evaluacion.get('estado') == 'ok':
                            coincidencias_map = {
                                r.get('modalidad', ''): set(r.get('coincidencias', []))
                                for r in evaluacion.get('resultados_modalidad', [])
                            }

                        modalidades_juego = obtener_config_juego(juego_key).get('modalidades', [])
                        if not modalidades_juego:
                            modalidades_juego = ['Modalidad 1', 'Modalidad 2', 'Modalidad 3', 'Modalidad 4']

                        plus_entry = entry.get('numero_plus')

                        # Construir stats inline
                        stats_parts = []
                        if 'scores' in entry and 'suma_total' in entry['scores']:
                            stats_parts.append(f"Suma: {entry['scores']['suma_total']}")
                            stats_parts.append(f"Score: {entry['scores']['score_promedio']:.3f}")
                            stats_parts.append(f"Pares: {entry['scores']['pares']}/6")
                        stats_texto = " &nbsp;|&nbsp; ".join(stats_parts)

                        filas_modalidad_html = []
                        for idx, modalidad in enumerate(modalidades_juego):
                            coincidencias_modalidad = coincidencias_map.get(modalidad, set())

                            numeros_html_parts = []
                            for n in entry['prediccion']:
                                if int(n) in coincidencias_modalidad:
                                    numeros_html_parts.append(
                                        f"<span style='display:inline-flex;align-items:center;justify-content:center;"
                                        f"width:24px;height:24px;border-radius:50%;background:#2e7d32;color:#fff;"
                                        f"font-size:0.80rem;font-weight:700;margin-right:4px;'>{int(n):02d}</span>"
                                    )
                                else:
                                    numeros_html_parts.append(f"<span>{int(n):02d}</span>")

                            numeros_texto = "<span style='display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap;'>" + "".join(numeros_html_parts) + "</span>"
                            if plus_entry is not None:
                                numeros_texto += f" &nbsp;+&nbsp; <span style='color:#F2A100;font-weight:700;'>Plus: {plus_entry}</span>"

                            stats_columna = stats_texto if idx == 0 else ""
                            borde_fila = "border-bottom: 1px solid rgba(200,200,200,0.2);" if idx < len(modalidades_juego) - 1 else ""

                            filas_modalidad_html.append(
                                f"<div style='display:flex;align-items:center;gap:20px;padding:5px 0;{borde_fila}'>"
                                f"<div style='min-width: 220px; font-weight: 600; color: #F2A100; font-size: 0.85rem;'>{juego_entry} - {entry['metodo']} - {modalidad}</div>"
                                f"<div style='font-size: 0.95rem; min-width: 220px;'>{numeros_texto}</div>"
                                f"<div style='color: #888; font-size: 0.82rem;'>{stats_columna}</div>"
                                f"</div>"
                            )

                        st.markdown(
                            f"<div style='border-bottom: 1px solid rgba(200,200,200,0.3);'>"
                            f"{''.join(filas_modalidad_html)}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
            
            # Botón para limpiar historial
            if st.button("Limpiar Historial", type="secondary"):
                st.session_state.historial = []
                st.session_state.prediction_count = 0
                # Eliminar archivo JSON
                if HISTORIAL_FILE.exists():
                    HISTORIAL_FILE.unlink()
                st.rerun()

    # ========================================================================
    # TAB 7: INVERSIONES
    # ========================================================================
    
    with tab7:
        st.markdown("""
        <style>
        /* Reducir espacio entre labels e inputs en sección inversiones */
        #inversiones-params {
            margin-top: -0.5rem !important;
            margin-bottom: -0.5rem !important;
        }
        #inversiones-params p {
            margin-bottom: 0rem !important;
        }
        #inversiones-params div[data-testid="stTextInput"] {
            margin-top: -0.3rem !important;
        }
        #inversiones-params div[data-testid="stNumberInput"] {
            margin-top: -0.5rem !important;
        }
        #inversiones-params label {
            margin-bottom: 0rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='margin-bottom: 0.5rem;'>Proyección de Inversiones</h2>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 0.2rem 0;'><hr style='margin: 0;'/></div>", unsafe_allow_html=True)

        # Inicializar valores en session_state
        if 'premio_inv' not in st.session_state:
            st.session_state.premio_inv = 7310000000.0
        
        # Todos los parámetros en una sola fila compacta
        st.markdown('<div id="inversiones-params">', unsafe_allow_html=True)
        col_premio, col_base, col_tna, col_meses, col_spacer = st.columns([0.7, 0.7, 0.7, 0.4, 2.2])
        
        with col_premio:
            st.markdown('<p style="margin-bottom: 0rem;">Premio</p>', unsafe_allow_html=True)
            
            # Callback para formatear con puntos de miles al cambiar
            def formatear_premio():
                raw = st.session_state.premio_input.replace('.', '').replace(',', '.')
                try:
                    numero = int(float(raw))
                    st.session_state.premio_inv = float(numero)
                    st.session_state.premio_input = f"{numero:,}".replace(',', '.')
                except:
                    pass
            
            # Inicializar valor formateado si no existe en session_state
            if 'premio_input' not in st.session_state:
                st.session_state.premio_input = f"{int(st.session_state.premio_inv):,}".replace(',', '.')
            
            # Input de texto con formato
            st.text_input(
                "Premio",
                label_visibility="collapsed",
                key="premio_input",
                on_change=formatear_premio
            )
            
            # Leer valor numérico actual
            try:
                premio = float(st.session_state.premio_input.replace('.', '').replace(',', '.'))
                st.session_state.premio_inv = premio
            except:
                premio = st.session_state.premio_inv
        
        with col_base:
            st.markdown('<p style="margin-bottom: 0rem;">Base</p>', unsafe_allow_html=True)
            # BASE se calcula según fórmula: PREMIO - ((PREMIO * 0.9) * 0.31)
            base = premio - ((premio * 0.9) * 0.31)
            base_formateado = f"{base:,.0f}".replace(',', '.')
            st.markdown(f"<div style='padding: 8px 12px; background-color: #f0f2f6; border-radius: 4px; text-align: center; font-size: 16px;'>{base_formateado}</div>", unsafe_allow_html=True)
        
        with col_tna:
            tna_texto = st.text_input(
                "TNA (%)",
                value="27.00",
                key="tna_input"
            )
            try:
                tna_percent = float(tna_texto.replace(',', '.'))
                tna_percent = max(0.0, min(100.0, tna_percent))
            except:
                tna_percent = 27.0
            tna = tna_percent / 100
        
        with col_meses:
            meses = st.number_input(
                "Meses",
                value=12,
                min_value=1,
                max_value=60,
                step=1
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin: 0.2rem 0;'><hr style='margin: 0;'/></div>", unsafe_allow_html=True)
        
        # Inicializar gastos en session_state si no existe
        if 'gastos_inversiones' not in st.session_state:
            # Intentar cargar desde JSON
            gastos_guardados = cargar_gastos_json()
            if gastos_guardados:
                st.session_state.gastos_inversiones = gastos_guardados
            else:
                # Valores por defecto
                st.session_state.gastos_inversiones = {1: 15000000.0}
        
        # Limpiar gastos de meses que exceden el nuevo límite
        if st.session_state.gastos_inversiones:
            gastos_validos = {mes: monto for mes, monto in st.session_state.gastos_inversiones.items() if mes <= meses}
            if len(gastos_validos) != len(st.session_state.gastos_inversiones):
                st.session_state.gastos_inversiones = gastos_validos
                # Guardar cambio en JSON
                guardar_gastos_json(st.session_state.gastos_inversiones)
        
        # Calcular proyección con gastos guardados
        df_inversiones = calcular_inversiones(
            premio=premio,
            base=base,
            tna=tna,
            meses=meses,
            gastos_iniciales=st.session_state.gastos_inversiones
        )
        
        # Mostrar tabla EDITABLE
        st.markdown("<h3 style='margin-bottom: 0.3rem; margin-top: 0.5rem;'>Proyección Mensual</h3>", unsafe_allow_html=True)
        
        # CSS para deshabilitar ordenamiento y compactar tabla
        st.markdown("""
        <style>
        /* Deshabilitar ordenamiento en data_editor */
        [data-testid="stDataFrameResizable"] [data-testid^="stDataFrameCell"] button {
            display: none !important;
        }
        [data-testid="stDataFrameResizable"] th button {
            display: none !important;
        }
        [data-testid="stDataFrameResizable"] thead button {
            display: none !important;
        }
        div[data-testid="stDataFrameResizable"] button[kind="header"] {
            display: none !important;
        }
        /* Compactar tabla */
        [data-testid="stDataFrameResizable"] {
            margin-top: -0.3rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Preparar DataFrame para edición (sin fila Total)
        df_editable = df_inversiones[df_inversiones['Mes'] != 'Total'].copy()
        
        # Reemplazar None por 0 en Gastos para mostrar correctamente
        df_editable['Gastos'] = df_editable['Gastos'].fillna(0)
        
        # Función formato argentino
        def formato_argentino(valor, decimales=2, signo_pesos=True):
            if decimales > 0:
                texto = f"{valor:,.{decimales}f}"
            else:
                texto = f"{valor:,.0f}"
            partes = texto.split('.')
            if len(partes) == 2:
                miles = partes[0].replace(',', '.')
                return f"${miles},{partes[1]}" if signo_pesos else f"{miles},{partes[1]}"
            else:
                miles = texto.replace(',', '.')
                return f"${miles}" if signo_pesos else miles
        
        # Formatear columnas de solo lectura como texto con formato argentino
        df_display = df_editable.copy()
        df_display['Acumulado_fmt'] = df_display['Acumulado'].apply(lambda x: formato_argentino(x, 2))
        df_display['TNA_fmt'] = df_display['TNA'].apply(lambda x: f"{x:.2%}".replace('.', ','))
        df_display['Rentabilidad_fmt'] = df_display['Rentabilidad'].apply(lambda x: formato_argentino(x, 2))
        df_display['Neto_fmt'] = df_display['Neto'].apply(lambda x: formato_argentino(x, 2))
        df_display['Gastos_fmt'] = df_display['Gastos'].apply(lambda x: formato_argentino(x, 0, signo_pesos=False) if pd.notna(x) and x > 0 else '')
        
        # Crear DataFrame para mostrar con columnas formateadas
        df_para_editar = pd.DataFrame({
            'Mes': df_display['Mes'],
            'Acumulado': df_display['Acumulado_fmt'],
            'TNA': df_display['TNA_fmt'],
            'Rentabilidad': df_display['Rentabilidad_fmt'],
            'Neto': df_display['Neto_fmt'],
            'Gastos': df_display['Gastos_fmt']
        })
        
        # Configurar columnas editables (solo Gastos es editable)
        column_config = {
            "Mes": st.column_config.TextColumn("Mes", disabled=True, width=120),
            "Acumulado": st.column_config.TextColumn("Acumulado", disabled=True, width=120),
            "TNA": st.column_config.TextColumn("TNA", disabled=True, width=120),
            "Rentabilidad": st.column_config.TextColumn("Rentabilidad", disabled=True, width=120),
            "Neto": st.column_config.TextColumn("Neto", disabled=True, width=120),
            "Gastos": st.column_config.TextColumn(
                "Gastos",
                help="Edita el monto de gastos para este mes (formato: 10.000.000)",
                width=120
            )
        }
        
        # Calcular altura según cantidad de meses
        num_filas = len(df_para_editar)
        
        # Mostrar tabla editable con altura dinámica
        if num_filas <= 12:
            # Para <=12 meses, calcular altura exacta para mostrar todo sin scroll
            altura_fila = 35
            altura_header = 38
            altura_tabla = (num_filas * altura_fila) + altura_header + 10
            df_editado = st.data_editor(
                df_para_editar,
                column_config=column_config,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                height=altura_tabla,
                key="tabla_inversiones"
            )
        else:
            # Para más de 12 meses, limitar a 12 filas visibles con scroll
            altura_fija = (12 * 35) + 38 + 10
            df_editado = st.data_editor(
                df_para_editar,
                column_config=column_config,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                height=altura_fija,
                key="tabla_inversiones"
            )
        
        # Extraer gastos editados y actualizar session_state
        gastos_dict_editado = {}
        cambios_detectados = False
        
        for idx, row in df_editado.iterrows():
            gastos_str = str(row['Gastos']).strip()
            mes_num = idx + 1  # idx + 1 porque mes empieza en 1
            
            if gastos_str and gastos_str != '':
                try:
                    # Parsear formato argentino: quitar puntos y convertir comas a punto
                    gastos_num = float(gastos_str.replace('.', '').replace(',', '.'))
                    if gastos_num > 0:
                        gastos_dict_editado[mes_num] = gastos_num
                        # Detectar cambios (nuevo o modificado)
                        if mes_num not in st.session_state.gastos_inversiones or \
                           st.session_state.gastos_inversiones[mes_num] != gastos_num:
                            cambios_detectados = True
                except:
                    pass  # Ignorar valores inválidos
        
        # Detectar gastos eliminados (meses que tenían gastos y ahora no)
        for mes_num in st.session_state.gastos_inversiones:
            if mes_num not in gastos_dict_editado:
                cambios_detectados = True
                break
        
        # Si hay cambios, actualizar session_state, guardar en JSON y rerun para reformatear
        if cambios_detectados:
            st.session_state.gastos_inversiones = gastos_dict_editado
            guardar_gastos_json(st.session_state.gastos_inversiones)
            st.rerun()
        
        # Recalcular con gastos actualizados
        df_inversiones_final = calcular_inversiones(
            premio=premio,
            base=base,
            tna=tna,
            meses=meses,
            gastos_iniciales=st.session_state.gastos_inversiones
        )
        
        # Mostrar fila Total
        fila_total = df_inversiones_final[df_inversiones_final['Mes'] == 'Total'].iloc[0]
        
        # Preparar DataFrame de Total para mostrar
        df_total = pd.DataFrame([{
            'Mes': 'Total',
            'Acumulado': formato_argentino(fila_total['Acumulado'], 2),
            'TNA': '',
            'Rentabilidad': formato_argentino(fila_total['Rentabilidad'], 2),
            'Neto': formato_argentino(fila_total['Neto'], 2),
            'Gastos': formato_argentino(fila_total['Gastos'], 0) if pd.notna(fila_total['Gastos']) else ''
        }])
        
        st.dataframe(
            df_total,
            width='stretch',
            hide_index=True,
            column_config={
                "Mes": st.column_config.TextColumn("Mes", width=120),
                "Acumulado": st.column_config.TextColumn("Acumulado", width=120),
                "TNA": st.column_config.TextColumn("TNA", width=120),
                "Rentabilidad": st.column_config.TextColumn("Rentabilidad", width=120),
                "Neto": st.column_config.TextColumn("Neto", width=120),
                "Gastos": st.column_config.TextColumn("Gastos", width=120)
            }
        )
        
        # Botón para limpiar gastos
        col_btn1, col_btn2, col_spacer_btn = st.columns([1, 1, 3])
        with col_btn1:
            if st.button("Limpiar gastos", type="secondary", key="limpiar_gastos_simple"):
                st.session_state.gastos_inversiones = {}
                guardar_gastos_json(st.session_state.gastos_inversiones)
                st.rerun()
        
        # ====================================================================
        # PROYECCIÓN CON PORTFOLIO DIVERSIFICADO
        # ====================================================================
        
        st.markdown("<div style='margin: 1.5rem 0 0.2rem 0;'><hr style='margin: 0;'/></div>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='margin-bottom: 0.3rem; margin-top: 0.5rem;'>Simulación Portfolio Diversificado</h3>", unsafe_allow_html=True)
        
        # Inicializar valores en session_state
        if 'premio_portfolio' not in st.session_state:
            st.session_state.premio_portfolio = 7310000000.0
        if 'gastos_portfolio' not in st.session_state:
            st.session_state.gastos_portfolio = {}
        
        # Inputs en una fila compacta
        col1, col2, col3, col4, col_spacer = st.columns([0.7, 0.7, 0.7, 0.4, 2.5])
        
        with col1:
            st.markdown('<p style="margin-bottom: 0rem;">Premio</p>', unsafe_allow_html=True)
            
            # Callback para formatear con puntos de miles al cambiar
            def formatear_premio_portfolio():
                raw = st.session_state.premio_portfolio_input.replace('.', '').replace(',', '.')
                try:
                    numero = int(float(raw))
                    st.session_state.premio_portfolio = float(numero)
                    st.session_state.premio_portfolio_input = f"{numero:,}".replace(',', '.')
                except:
                    pass
            
            # Inicializar valor formateado si no existe en session_state
            if 'premio_portfolio_input' not in st.session_state:
                st.session_state.premio_portfolio_input = f"{int(st.session_state.premio_portfolio):,}".replace(',', '.')
            
            # Input de texto con formato
            st.text_input(
                "Premio",
                label_visibility="collapsed",
                key="premio_portfolio_input",
                on_change=formatear_premio_portfolio
            )
            
            # Leer valor numérico actual
            try:
                premio_portfolio = float(st.session_state.premio_portfolio_input.replace('.', '').replace(',', '.'))
                st.session_state.premio_portfolio = premio_portfolio
            except:
                premio_portfolio = st.session_state.premio_portfolio
        
        with col2:
            st.markdown('<p style="margin-bottom: 0rem;">Base</p>', unsafe_allow_html=True)
            # BASE se calcula según fórmula: PREMIO - ((PREMIO * 0.9) * 0.31)
            base_portfolio = premio_portfolio - ((premio_portfolio * 0.9) * 0.31)
            base_portfolio_formateado = f"{base_portfolio:,.0f}".replace(',', '.')
            st.markdown(f"<div style='padding: 8px 12px; background-color: #f0f2f6; border-radius: 4px; text-align: center; font-size: 16px;'>{base_portfolio_formateado}</div>", unsafe_allow_html=True)
        
        with col3:
            inflacion = st.number_input(
                "Inflación mensual (%)",
                value=3.0,
                min_value=0.0,
                max_value=50.0,
                step=0.5,
                format="%.2f"
            )
        
        with col4:
            meses_portfolio = st.number_input(
                "Meses",
                value=12,
                min_value=1,
                max_value=60,
                step=1,
                key="meses_portfolio"
            )
        
        # Distribución y tasas con columnas compactas
        st.markdown('<p style="margin-top: 0.5rem; margin-bottom: 0.3rem; font-weight: 500;">Distribución y tasas</p>', unsafe_allow_html=True)
        
        col_pf1, col_pf2, col_cer1, col_cer2, col_usd1, col_usd2, col_spacer2 = st.columns([0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 2.25])
        
        with col_pf1:
            st.markdown('<p style="margin-bottom: 0.3rem;">PF %</p>', unsafe_allow_html=True)
            pct_pf = st.number_input("Porcentaje (%)", value=30.0, min_value=0.0, max_value=100.0, step=5.0, format="%.1f", key="pct_pf", label_visibility="collapsed")
        with col_pf2:
            st.markdown('<p style="margin-bottom: 0.3rem;">PF Tasa</p>', unsafe_allow_html=True)
            tasa_pf = st.number_input("Tasa mensual (%)", value=7.0, min_value=0.0, max_value=50.0, step=0.5, format="%.2f", key="tasa_pf", label_visibility="collapsed")
        
        with col_cer1:
            st.markdown('<p style="margin-bottom: 0.3rem;">FCI CER %</p>', unsafe_allow_html=True)
            pct_cer = st.number_input("Porcentaje (%)", value=30.0, min_value=0.0, max_value=100.0, step=5.0, format="%.1f", key="pct_cer", label_visibility="collapsed")
        with col_cer2:
            st.markdown('<p style="margin-bottom: 0.3rem;">FCI CER Tasa</p>', unsafe_allow_html=True)
            tasa_cer = st.number_input("Tasa mensual (%)", value=3.5, min_value=0.0, max_value=50.0, step=0.5, format="%.2f", key="tasa_cer", label_visibility="collapsed")
        
        with col_usd1:
            st.markdown('<p style="margin-bottom: 0.3rem;">FCI USD %</p>', unsafe_allow_html=True)
            pct_usd = st.number_input("Porcentaje (%)", value=40.0, min_value=0.0, max_value=100.0, step=5.0, format="%.1f", key="pct_usd", label_visibility="collapsed")
        with col_usd2:
            st.markdown('<p style="margin-bottom: 0.3rem;">FCI USD Tasa</p>', unsafe_allow_html=True)
            tasa_usd = st.number_input("Tasa mensual (%)", value=0.5, min_value=0.0, max_value=50.0, step=0.5, format="%.2f", key="tasa_usd", label_visibility="collapsed")
        
        # Validar que la suma de porcentajes sea 100%
        suma_pct = pct_pf + pct_cer + pct_usd
        if abs(suma_pct - 100.0) > 0.1:
            st.warning(f"âš ï¸ La suma de porcentajes debe ser 100% (actual: {suma_pct:.1f}%)")
        
        # Limpiar gastos de meses que exceden el nuevo límite
        if st.session_state.gastos_portfolio:
            gastos_validos = {mes: monto for mes, monto in st.session_state.gastos_portfolio.items() if mes <= meses_portfolio}
            if len(gastos_validos) != len(st.session_state.gastos_portfolio):
                st.session_state.gastos_portfolio = gastos_validos
        
        # Calcular proyección de portfolio con gastos guardados
        df_portfolio = calcular_inversion_portfolio(
            capital_inicial=base_portfolio,
            pct_pf=pct_pf,
            tasa_pf=tasa_pf,
            pct_fci_cer=pct_cer,
            tasa_fci_cer=tasa_cer,
            pct_fci_usd=pct_usd,
            tasa_fci_usd=tasa_usd,
            inflacion_mensual=inflacion,
            meses=meses_portfolio,
            gastos_iniciales=st.session_state.gastos_portfolio
        )
        
        # Preparar DataFrame para edición (sin fila Total)
        df_editable_portfolio = df_portfolio[df_portfolio['Mes'] != 'Total'].copy()
        
        # Eliminar columna TNA (no aplica en portfolio)
        df_editable_portfolio = df_editable_portfolio.drop(columns=['TNA'])
        
        # Formatear columnas de solo lectura como texto con formato argentino
        df_display_portfolio = df_editable_portfolio.copy()
        df_display_portfolio['Acumulado_fmt'] = df_display_portfolio['Acumulado'].apply(lambda x: formato_argentino(x, 2))
        df_display_portfolio['Rentabilidad_fmt'] = df_display_portfolio['Rentabilidad'].apply(lambda x: formato_argentino(x, 2))
        df_display_portfolio['Neto_fmt'] = df_display_portfolio['Neto'].apply(lambda x: formato_argentino(x, 2))
        df_display_portfolio['Gastos_fmt'] = df_display_portfolio['Gastos'].apply(lambda x: formato_argentino(x, 0, signo_pesos=False) if pd.notna(x) and x > 0 else '')
        
        # Crear DataFrame para mostrar con columnas formateadas
        df_para_editar_portfolio = pd.DataFrame({
            'Mes': df_display_portfolio['Mes'],
            'Acumulado': df_display_portfolio['Acumulado_fmt'],
            'Rentabilidad': df_display_portfolio['Rentabilidad_fmt'],
            'Neto': df_display_portfolio['Neto_fmt'],
            'Gastos': df_display_portfolio['Gastos_fmt']
        })
        
        # Configurar columnas editables (solo Gastos es editable)
        column_config_portfolio = {
            "Mes": st.column_config.TextColumn("Mes", disabled=True, width=120),
            "Acumulado": st.column_config.TextColumn("Acumulado", disabled=True, width=120),
            "Rentabilidad": st.column_config.TextColumn("Rentabilidad", disabled=True, width=120),
            "Neto": st.column_config.TextColumn("Neto", disabled=True, width=120),
            "Gastos": st.column_config.TextColumn(
                "Gastos",
                help="Edita el monto de gastos para este mes (formato: 10.000.000)",
                width=120
            )
        }
        
        # Calcular altura según cantidad de meses
        num_filas_portfolio = len(df_para_editar_portfolio)
        
        # CSS para compactar tabla de portfolio
        st.markdown("""
        <style>
        /* Compactar tabla de portfolio */
        div[data-testid="stDataFrame"] {
            margin-top: -0.5rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Mostrar tabla editable con altura dinámica
        if num_filas_portfolio <= 12:
            altura_fila = 35
            altura_header = 38
            altura_tabla_portfolio = (num_filas_portfolio * altura_fila) + altura_header + 10
            df_editado_portfolio = st.data_editor(
                df_para_editar_portfolio,
                column_config=column_config_portfolio,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                height=altura_tabla_portfolio,
                key="tabla_portfolio"
            )
        else:
            altura_fija = (12 * 35) + 38 + 10
            df_editado_portfolio = st.data_editor(
                df_para_editar_portfolio,
                column_config=column_config_portfolio,
                width='stretch',
                hide_index=True,
                num_rows="fixed",
                height=altura_fija,
                key="tabla_portfolio"
            )
        
        # Extraer gastos editados y actualizar session_state
        gastos_dict_editado_portfolio = {}
        cambios_detectados_portfolio = False
        
        for idx, row in df_editado_portfolio.iterrows():
            gastos_str = str(row['Gastos']).strip()
            mes_num = idx + 1
            
            if gastos_str and gastos_str != '':
                try:
                    gastos_num = float(gastos_str.replace('.', '').replace(',', '.'))
                    if gastos_num > 0:
                        gastos_dict_editado_portfolio[mes_num] = gastos_num
                        # Comparar con tolerancia para evitar errores de precisión
                        if mes_num not in st.session_state.gastos_portfolio or \
                           abs(st.session_state.gastos_portfolio[mes_num] - gastos_num) > 0.01:
                            cambios_detectados_portfolio = True
                except:
                    pass
        
        # Detectar gastos eliminados
        for mes_num in st.session_state.gastos_portfolio:
            if mes_num not in gastos_dict_editado_portfolio:
                cambios_detectados_portfolio = True
                break
        
        # Si hay cambios, actualizar session_state y rerun
        if cambios_detectados_portfolio:
            st.session_state.gastos_portfolio = gastos_dict_editado_portfolio
            st.rerun()
        
        # Recalcular con gastos actualizados
        df_portfolio_final = calcular_inversion_portfolio(
            capital_inicial=base_portfolio,
            pct_pf=pct_pf,
            tasa_pf=tasa_pf,
            pct_fci_cer=pct_cer,
            tasa_fci_cer=tasa_cer,
            pct_fci_usd=pct_usd,
            tasa_fci_usd=tasa_usd,
            inflacion_mensual=inflacion,
            meses=meses_portfolio,
            gastos_iniciales=st.session_state.gastos_portfolio
        )
        
        # Mostrar fila Total
        fila_total_portfolio = df_portfolio_final[df_portfolio_final['Mes'] == 'Total'].iloc[0]
        
        df_total_portfolio = pd.DataFrame([{
            'Mes': 'Total',
            'Acumulado': formato_argentino(fila_total_portfolio['Acumulado'], 2),
            'Rentabilidad': formato_argentino(fila_total_portfolio['Rentabilidad'], 2),
            'Neto': formato_argentino(fila_total_portfolio['Neto'], 2),
            'Gastos': formato_argentino(fila_total_portfolio['Gastos'], 0) if pd.notna(fila_total_portfolio['Gastos']) else ''
        }])
        
        st.dataframe(
            df_total_portfolio,
            width='stretch',
            hide_index=True,
            column_config={
                "Mes": st.column_config.TextColumn("Mes", width=120),
                "Acumulado": st.column_config.TextColumn("Acumulado", width=120),
                "Rentabilidad": st.column_config.TextColumn("Rentabilidad", width=120),
                "Neto": st.column_config.TextColumn("Neto", width=120),
                "Gastos": st.column_config.TextColumn("Gastos", width=120)
            }
        )
        
        # Botón para limpiar gastos
        col_btn1_pf, col_btn2_pf, col_spacer_btn_pf = st.columns([1, 1, 3])
        with col_btn1_pf:
            if st.button("Limpiar gastos", type="secondary", key="limpiar_gastos_portfolio"):
                st.session_state.gastos_portfolio = {}
                st.rerun()
        
        # Resumen de resultados
        st.markdown('<p style="margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 500;">Resumen</p>', unsafe_allow_html=True)
        
        capital_final = fila_total_portfolio['Acumulado']
        rentabilidad_total = fila_total_portfolio['Rentabilidad']
        
        # Calcular valor real ajustado por inflación acumulada
        inflacion_acumulada = ((1 + inflacion / 100) ** meses_portfolio) - 1
        capital_real = capital_final / (1 + inflacion_acumulada)
        
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            st.metric("Capital final", f"${capital_final:,.0f}".replace(',', '.'))
        
        with col_res2:
            st.metric("Capital real (ajustado)", f"${capital_real:,.0f}".replace(',', '.'))
        
        with col_res3:
            cambio_pct = ((capital_final - base_portfolio) / base_portfolio) * 100
            st.metric("Variación nominal", f"{cambio_pct:.1f}%")
        
        with col_res4:
            cambio_real_pct = ((capital_real - base_portfolio) / base_portfolio) * 100
            st.metric("Variación real", f"{cambio_real_pct:.1f}%")
        
        # ====================================================================
        # GRÁFICO COMPARATIVO DE AMBOS MÉTODOS
        # ====================================================================
        
        st.markdown("<div style='margin: 1.5rem 0 0.2rem 0;'><hr style='margin: 0;'/></div>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='margin-bottom: 0.5rem; margin-top: 0.5rem;'>Comparación de Métodos</h3>", unsafe_allow_html=True)
        
        # Preparar datos para gráfico (excluir Total de ambos)
        df_grafico_simple = df_inversiones_final[df_inversiones_final['Mes'] != 'Total'].copy()
        df_grafico_portfolio = df_portfolio_final[df_portfolio_final['Mes'] != 'Total'].copy()
        
        # Crear gráfico comparativo
        fig_comparativo = go.Figure()
        
        # Trace 1: Inversión Simple TNA
        fig_comparativo.add_trace(go.Scatter(
            x=df_grafico_simple['Mes'],
            y=df_grafico_simple['Acumulado'],
            mode='lines+markers',
            name='Inversión Simple TNA',
            line=dict(color='#F2A100', width=3),
            marker=dict(size=8)
        ))
        
        # Trace 2: Portfolio Diversificado
        fig_comparativo.add_trace(go.Scatter(
            x=df_grafico_portfolio['Mes'],
            y=df_grafico_portfolio['Acumulado'],
            mode='lines+markers',
            name='Portfolio Diversificado',
            line=dict(color='#6C757D', width=3),
            marker=dict(size=8)
        ))
        
        fig_comparativo.update_layout(
            xaxis_title="Mes",
            yaxis_title="Monto ($)",
            hovermode='x unified',
            height=450,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            separators=',.'
        )
        
        # Formatear eje Y con puntos de miles
        fig_comparativo.update_yaxes(tickformat="$,.0f", separatethousands=True)
        
        st.plotly_chart(fig_comparativo, width='stretch')


# ============================================================================
# EJECUTAR APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    main()


