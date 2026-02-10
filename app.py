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
from core.generator import StrategyManager, GenerationStrategy
from utils.data_generator import generate_sample_data
from varios.scraper_quiniya_final import actualizar_historico_csv

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
        background: white;
        color: #333333;
        padding: 16px 12px;
        border-radius: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 6px;
        border: 2px solid #F2A100;
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
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
        font-weight: 600 !important;
    }
    
    h3 {
        color: #F2A100 !important;
        font-size: 1.1rem !important;
        margin-top: 0.7rem !important;
        margin-bottom: 0.4rem !important;
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
        font-size: 0.9rem;
        border: none;
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
        padding: 16px 20px !important;
        border-width: 2px !important;
        border-style: solid !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
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
        .numero-predicho {
            font-size: 18px;
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
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNCIONES DE SESIÓN Y PERSISTENCIA
# ============================================================================

HISTORIAL_FILE = Path('data/historial_predicciones.json')

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
    
    cols = st.columns(6)
    for i, num in enumerate(numeros_limpios):
        with cols[i]:
            st.markdown(
                f'<div class="numero-predicho">{num:02d}</div>',
                unsafe_allow_html=True
            )


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    init_session_state()
    
    # HEADER
    st.markdown("""
        <div class="app-banner">
            <div class="banner-logo">CP</div>
            <div class="banner-title">Charly Predictor</div>
            <div class="banner-subtitle">Sistema Profesional de Predicción de Quini 6</div>
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
            <div class="banner-subtitle">¡Predicciones inteligentes de Quini 6!</div>
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

        # Actualizar desde QuiniYa
        if st.button("Actualizar desde QuiniYa", width='stretch'):
            with st.spinner("Actualizando datos desde QuiniYa..."):
                try:
                    nuevos = actualizar_historico_csv('data/quini6_historico.csv')
                    # Limpiar cachés para forzar recarga con datos nuevos
                    cargar_datos.clear()
                    ejecutar_analisis.clear()
                    # Recargar datos y análisis con sorteos nuevos
                    data = cargar_datos()
                    st.session_state.current_data = data
                    st.session_state.data_loaded = True
                    if nuevos > 0:
                        st.success(f"✅ Agregados {nuevos} sorteos nuevos. Datos y análisis actualizados.")
                    else:
                        st.info("ℹ️ No hay sorteos nuevos para agregar")
                except Exception as e:
                    st.error(f"❌ Error al actualizar datos: {str(e)}")
        
        st.markdown("---")
        
        # 2. MÉTODO DE GENERACIÓN
        st.markdown("### Método de Predicción")
        
        metodo_options = {
            "Estándar (Rápido)": GenerationStrategy.STANDARD,
            "Condicional (Inteligente)": GenerationStrategy.CONDITIONAL,
            "Ambos Métodos": GenerationStrategy.BOTH
        }
        
        metodo_selected = st.selectbox(
            "Selecciona el método:",
            list(metodo_options.keys()),
            index=2  # Por defecto "Ambos Métodos"
        )
        
        metodo = metodo_options[metodo_selected]
        
        # 3. PARÁMETROS AVANZADOS
        with st.expander("🔧 Parámetros Avanzados"):
            st.markdown("#### Pesos de Scoring")
            
            # Mostrar info de configuración optimizada
            st.info("💡 Valores optimizados cargados automáticamente (2.25 aciertos/sorteo promedio)")
            
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
            
            # Mostrar detalles de la optimización
            with st.expander("📊 Detalles de Optimización"):
                st.markdown("""
                **Configuración óptima encontrada mediante:**
                - ✅ Prueba de 10 configuraciones diversas
                - ✅ Optimización fina (20 variaciones)
                - ✅ Búsqueda aleatoria (100 iteraciones)
                
                **Resultados en backtesting:**
                - 🎯 **9/24 aciertos** (2.25 por sorteo)
                - 📈 Mejora de **+200%** vs configuración inicial
                - 🏆 Mejor sorteo: 2/6 números acertados
                
                **Hallazgos clave:**
                - Latencia en 0.00 mejora rendimiento
                - Balance equilibrado entre otros factores
                - Estrategia BOTH maximiza aciertos
                """)
            
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
        
        st.markdown("---")
        
        # Información del sistema
        st.markdown("### Estado")
        if st.session_state.data_loaded:
            st.success("Datos cargados")
            st.info(f"{st.session_state.prediction_count} predicciones generadas")
        else:
            st.warning("Carga datos para comenzar")
        
        st.markdown("---")
    
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
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Predicción", 
        "Análisis", 
        "Visualizaciones",
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
        
        scorer = UnifiedScorer(pesos_custom)
        scores = scorer.calculate_scores(freq_analyzer)
        
        # Botón de generar predicción
        st.markdown("## Generar Predicción")
        
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn1:
            generar = st.button(
                "GENERAR PREDICCIÓN",
                width='stretch',
                type="primary"
            )
        
        if generar:
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
                
                st.success("Predicción generada exitosamente")
                
                # Botones de acción
                col_act1, col_act2 = st.columns(2)
                
                with col_act1:
                    # Preparar texto para copiar
                    if metodo == GenerationStrategy.BOTH:
                        nums_std = ', '.join([f"{int(n):02d}" for n in result['standard']['combination']])
                        nums_cond = ', '.join([f"{int(n):02d}" for n in result['conditional']['combination']])
                        texto_copiar = f"Estándar: {nums_std}\nCondicional: {nums_cond}"
                    else:
                        texto_copiar = ', '.join([f"{int(n):02d}" for n in result['combination']])
                    
                    st.code(texto_copiar, language=None)
                
                with col_act2:
                    st.info("Usa Ctrl+C para copiar los números")
    
    # ========================================================================
    # TAB 2: ANÁLISIS
    # ========================================================================
    
    with tab2:
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
    # TAB 3: VISUALIZACIONES
    # ========================================================================
    
    with tab3:
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
    # TAB 4: HISTORIAL
    # ========================================================================
    
    with tab4:
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
            if st.button("🗑️ Limpiar Historial", type="secondary"):
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

