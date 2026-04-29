"""Scraper de resultados históricos de Loto Argentina.

Fuente oficial usada en este módulo:
https://resultados-de-loteria.com/loto-argentina/resultados/<anio>

El CSV generado queda separado del de Quini6 y agrega la columna `numero_plus`.
"""

from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List

import pandas as pd
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

URL_ANIO = "https://resultados-de-loteria.com/loto-argentina/resultados/{anio}"
URL_BASE_RESULTADOS = "https://resultados-de-loteria.com/loto-argentina/resultados"

MODALIDADES_ORDEN = [
    "Loto Tradicional",
    "Loto Match",
    "Loto Desquite",
    "Loto Sale o Sale",
]

MESES_ES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "set": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


def _descargar_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _obtener_anios_disponibles() -> List[int]:
    """Obtiene años disponibles navegando los botones del pie de página anual."""
    anio_actual = datetime.now().year
    soup = _descargar_soup(URL_ANIO.format(anio=anio_actual))
    anios = {anio_actual}

    for a in soup.find_all("a", href=True):
        m = re.search(r"/loto-argentina/resultados/(\d{4})$", a["href"])
        if m:
            anios.add(int(m.group(1)))

    return sorted(anios)


def _parsear_fecha(fecha_raw: str) -> str:
    """Convierte 'sábado 25 abr. 2026' o 'miercoles 7 ene. 2026' a YYYY-MM-DD."""
    texto = " ".join(fecha_raw.lower().replace("á", "a").split())
    m = re.search(r"(\d{1,2})\s+([a-z]{3,})\.?\s+(\d{4})", texto)
    if not m:
        raise ValueError(f"No se pudo parsear fecha: {fecha_raw}")

    dia = int(m.group(1))
    mes_txt = m.group(2)[:3]
    anio = int(m.group(3))
    mes = MESES_ES.get(mes_txt)
    if not mes:
        raise ValueError(f"Mes inválido en fecha: {fecha_raw}")

    return datetime(anio, mes, dia).strftime("%Y-%m-%d")


def _extraer_numeros(texto: str, etiquetas: List[str], cantidad: int) -> List[int]:
    """Busca `cantidad` números luego de alguna etiqueta candidata."""
    for etiqueta in etiquetas:
        patron = rf"{re.escape(etiqueta)}\s+((?:\d+\s+){{{cantidad - 1}}}\d+)"
        m = re.search(patron, texto, flags=re.IGNORECASE)
        if m:
            numeros = [int(n) for n in re.findall(r"\d+", m.group(1))]
            if len(numeros) == cantidad:
                return numeros
    raise ValueError(f"No se encontraron {cantidad} números para etiquetas: {etiquetas}")


def _parsear_resultado_fila(fecha_raw: str, resultado_raw: str) -> List[Dict]:
    """Parsea una fila de tabla anual y devuelve 4 registros (uno por modalidad)."""
    fecha = _parsear_fecha(fecha_raw)
    texto = " ".join(resultado_raw.split())

    tradicional_plus = _extraer_numeros(texto, ["Loto Tradicional", "Tradicional"], 7)
    numeros_tradicional = tradicional_plus[:6]
    numero_plus = tradicional_plus[6]

    numeros_match = _extraer_numeros(texto, ["Loto Match", "Match"], 6)
    numeros_desquite = _extraer_numeros(texto, ["Loto Desquite", "Desquite"], 6)
    numeros_sale = _extraer_numeros(texto, ["Loto Sale o Sale", "Sale o Sale"], 6)

    return [
        {
            "fecha": fecha,
            "modalidad": "Loto Tradicional",
            "num1": numeros_tradicional[0],
            "num2": numeros_tradicional[1],
            "num3": numeros_tradicional[2],
            "num4": numeros_tradicional[3],
            "num5": numeros_tradicional[4],
            "num6": numeros_tradicional[5],
            "numero_plus": numero_plus,
        },
        {
            "fecha": fecha,
            "modalidad": "Loto Match",
            "num1": numeros_match[0],
            "num2": numeros_match[1],
            "num3": numeros_match[2],
            "num4": numeros_match[3],
            "num5": numeros_match[4],
            "num6": numeros_match[5],
            "numero_plus": numero_plus,
        },
        {
            "fecha": fecha,
            "modalidad": "Loto Desquite",
            "num1": numeros_desquite[0],
            "num2": numeros_desquite[1],
            "num3": numeros_desquite[2],
            "num4": numeros_desquite[3],
            "num5": numeros_desquite[4],
            "num6": numeros_desquite[5],
            "numero_plus": numero_plus,
        },
        {
            "fecha": fecha,
            "modalidad": "Loto Sale o Sale",
            "num1": numeros_sale[0],
            "num2": numeros_sale[1],
            "num3": numeros_sale[2],
            "num4": numeros_sale[3],
            "num5": numeros_sale[4],
            "num6": numeros_sale[5],
            "numero_plus": numero_plus,
        },
    ]


def _scrapear_anio(anio: int) -> List[Dict]:
    """Scrapea todos los sorteos de un año desde la tabla de resultados."""
    soup = _descargar_soup(URL_ANIO.format(anio=anio))
    tabla = soup.find("table")
    if not tabla:
        raise ValueError(f"No se encontró tabla de resultados para {anio}")

    rows = []
    for tr in tabla.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        fecha_raw = tds[0].get_text(" ", strip=True)
        resultado_raw = tds[1].get_text("\n", strip=True)
        if not fecha_raw or not resultado_raw:
            continue

        try:
            rows.extend(_parsear_resultado_fila(fecha_raw, resultado_raw))
        except Exception:
            # Saltar filas corruptas sin frenar todo el scraping.
            continue

    return rows


def _normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos y orden final para persistencia en CSV."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "sorteo_id",
                "fecha",
                "modalidad",
                "num1",
                "num2",
                "num3",
                "num4",
                "num5",
                "num6",
                "numero_plus",
            ]
        )

    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    for col in ["num1", "num2", "num3", "num4", "num5", "num6", "numero_plus"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["num1", "num2", "num3", "num4", "num5", "num6", "numero_plus"])

    for col in ["num1", "num2", "num3", "num4", "num5", "num6", "numero_plus"]:
        df[col] = df[col].astype(int)

    # Deduplicar por sorteo real.
    clave = ["fecha", "modalidad", "num1", "num2", "num3", "num4", "num5", "num6", "numero_plus"]
    df = df.drop_duplicates(subset=clave, keep="first")

    orden_modalidad = {m: i for i, m in enumerate(MODALIDADES_ORDEN)}
    df["_orden_modalidad"] = df["modalidad"].map(orden_modalidad).fillna(99)
    df = df.sort_values(["fecha", "_orden_modalidad"]).reset_index(drop=True)
    df["sorteo_id"] = range(1, len(df) + 1)
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    df = df[
        [
            "sorteo_id",
            "fecha",
            "modalidad",
            "num1",
            "num2",
            "num3",
            "num4",
            "num5",
            "num6",
            "numero_plus",
        ]
    ]
    return df


def actualizar_historico_loto_csv(
    csv_destino: str = "data/loto/loto_historico.csv",
    anios: List[int] = None,
) -> int:
    """Actualiza histórico de Loto desde resultados-de-loteria.com.
    SOLO puede escribir en CSVs cuyo nombre contenga 'loto' para evitar cruce con Quini6.

    Args:
        csv_destino: Ruta del CSV consolidado de Loto.
        anios: Años a scrapear. Si es None, toma todos los disponibles.

    Returns:
        Cantidad de filas nuevas agregadas respecto al CSV existente.
    """
    csv_destino_norm = str(csv_destino).replace('\\', '/').lower()
    if 'loto' not in csv_destino_norm:
        raise ValueError(
            f"Ruta destino inválida para scraper de Loto: '{csv_destino}'.\n"
            f"Este scraper extrae datos de resultados-de-loteria.com (Loto Argentina) "
            f"y solo puede escribir en el CSV de Loto (la ruta debe contener 'loto')."
        )
    if anios is None:
        anios = _obtener_anios_disponibles()

    registros = []
    for anio in sorted(set(anios)):
        registros.extend(_scrapear_anio(anio))

    if not registros:
        raise ValueError("No se pudieron extraer resultados de Loto")

    df_nuevo = _normalizar_dataframe(pd.DataFrame(registros))

    destino = Path(csv_destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and destino.stat().st_size > 0:
        try:
            df_actual = _normalizar_dataframe(pd.read_csv(destino))
        except Exception:
            df_actual = pd.DataFrame(columns=df_nuevo.columns)
    else:
        df_actual = pd.DataFrame(columns=df_nuevo.columns)

    if df_actual.empty:
        nuevas = len(df_nuevo)
        df_final = df_nuevo
    else:
        clave = ["fecha", "modalidad", "num1", "num2", "num3", "num4", "num5", "num6", "numero_plus"]
        existentes = set(tuple(row) for row in df_actual[clave].to_numpy())
        mask_nuevas = [tuple(row) not in existentes for row in df_nuevo[clave].to_numpy()]
        df_a_agregar = df_nuevo[mask_nuevas].copy()
        nuevas = len(df_a_agregar)

        df_final = pd.concat([df_actual, df_a_agregar], ignore_index=True)
        df_final = _normalizar_dataframe(df_final)

    df_final.to_csv(destino, index=False, encoding="utf-8")
    return int(nuevas)


# ============================================================================
# POZOS DEL ÚLTIMO SORTEO (loto.loteriadelaciudad.gob.ar)
# ============================================================================

# URL EXCLUSIVA para pozos de Loto. NO mezclar con QuiniYa ni con resultados-de-loteria.com
_URL_POZOS_LOTO = "https://loto.loteriadelaciudad.gob.ar/"

# (clave_dict, keyword_heading, aciertos_objetivo)
_MODALIDADES_POZOS = [
    ("Tradicional", "TRADICIONAL", "6"),
    ("Match", "MATCH", "6"),
    ("Desquite", "DESQUITE", "6"),
    ("SaleOSale", "SALE O SALE", "5"),
]


def _normalizar_premio(premio_raw: str) -> str:
    """Normaliza premio a solo dígitos de la parte entera."""
    return re.sub(r"[^\d]", "", str(premio_raw).split(",")[0])


def _obtener_soup_resultado_actual_loto() -> BeautifulSoup:
    """Obtiene el HTML del resultado actual vía endpoint oficial del sitio."""
    soup_home = _descargar_soup(_URL_POZOS_LOTO)

    codigo_input = soup_home.find(id="valor1")
    jurisdiccion_input = soup_home.find(id="valor2")
    sorteo_select = soup_home.find(id="valor3")

    if not codigo_input or not jurisdiccion_input or not sorteo_select:
        raise ValueError("No se encontró configuración de sorteo en la portada de Loto")

    primer_sorteo = sorteo_select.find("option")
    if not primer_sorteo:
        raise ValueError("No se encontró el sorteo más reciente en la portada de Loto")

    params = {
        "codigo": codigo_input.get("value", ""),
        "juridiccion": jurisdiccion_input.get("value", ""),
        "sorteo": primer_sorteo.get("value", ""),
    }

    if not params["codigo"] or not params["juridiccion"] or not params["sorteo"]:
        raise ValueError("Parámetros incompletos para consultar resultados de Loto")

    endpoint = "https://loto.loteriadelaciudad.gob.ar/resultadosLoto/consultaResultados.php"
    resp = requests.post(endpoint, headers=HEADERS, data=params, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _parsear_pozo_grilla(grilla, aciertos_target: str):
    """Extrae premio y ganadores desde una grilla de modalidad del resultado actual."""
    columnas = grilla.select("div.infoJuego div.item-info")
    if len(columnas) < 3:
        return None

    aciertos = [p.get_text(" ", strip=True) for p in columnas[0].find_all("p")][1:]
    ganadores = [p.get_text(" ", strip=True) for p in columnas[1].find_all("p")][1:]
    premios = [p.get_text(" ", strip=True) for p in columnas[2].find_all("p")][1:]

    for acierto, ganador, premio in zip(aciertos, ganadores, premios):
        if acierto.strip() == aciertos_target:
            ganador_txt = (ganador or "").strip()
            if "vacante" in ganador_txt.lower() or ganador_txt in ("", "0"):
                ganador_norm = "Vacante"
            else:
                ganador_norm = ganador_txt
            return {
                "premio": _normalizar_premio(premio),
                "ganadores": ganador_norm,
            }

    return None


def _mapear_modalidad(label: str):
    """Mapea el label de modalidad del HTML al nombre usado por la app."""
    label_up = (label or "").upper().strip()
    if "TRADICIONAL" in label_up:
        return "Tradicional"
    if "MATCH" in label_up:
        return "Match"
    if "DESQUITE" in label_up:
        return "Desquite"
    if "SALE O SALE" in label_up:
        return "SaleOSale"
    return None


def _parsear_tabla_pozo(table, aciertos_target: str):
    """Extrae premio y ganadores de una tabla para la fila con `aciertos_target` aciertos."""
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue
        texts = [c.get_text(" ", strip=True) for c in cells]
        if texts[0].strip() == aciertos_target:
            ganadores_raw = texts[1].strip()
            premio_raw = texts[2]
            # Quitar simbolos y dejar solo dígitos hasta la coma decimal
            premio_limpio = re.sub(r"[^\d]", "", premio_raw.split(",")[0])
            # Normalizar "Vacante" vs número de ganadores
            if "vacante" in ganadores_raw.lower() or ganadores_raw in ("0", ""):
                ganadores_norm = "Vacante"
            else:
                ganadores_norm = ganadores_raw
            return {"premio": premio_limpio, "ganadores": ganadores_norm}
    return None


def obtener_pozos_loto() -> dict:
    """Obtiene los pozos del último sorteo de Loto desde loto.loteriadelaciudad.gob.ar.

    EXCLUSIVO: solo accede a loto.loteriadelaciudad.gob.ar.
    Nunca accede a QuiniYa.com.ar ni a resultados-de-loteria.com.

    Returns:
        dict con claves 'Tradicional', 'Match', 'Desquite', 'SaleOSale', 'Plus'
        (cada una con 'premio' y 'ganadores'/'vacante'), o None si falla.
    """
    from urllib.parse import urlparse

    parsed = urlparse(_URL_POZOS_LOTO)
    if "loto.loteriadelaciudad.gob.ar" not in parsed.netloc:
        raise ValueError(
            f"URL inválida para pozos Loto: '{_URL_POZOS_LOTO}'. "
            "Solo se permite acceder a loto.loteriadelaciudad.gob.ar"
        )

    try:
        soup = _obtener_soup_resultado_actual_loto()
    except Exception as e:
        print(f"Error al consultar pozos Loto: {e}")
        return None

    pozos = {k: {"premio": None, "ganadores": None} for k, _, _ in _MODALIDADES_POZOS}
    pozos["Plus"] = {"vacante": None}
    target_por_modalidad = {k: a for k, _, a in _MODALIDADES_POZOS}

    for grilla in soup.select("div.grilla"):
        label_elem = grilla.select_one("div.label p")
        pozo_key = _mapear_modalidad(label_elem.get_text(" ", strip=True) if label_elem else "")
        if not pozo_key:
            continue

        aciertos_target = target_por_modalidad.get(pozo_key)
        if not aciertos_target:
            continue

        result = _parsear_pozo_grilla(grilla, aciertos_target)
        if result:
            pozos[pozo_key] = result

    # Detectar estado del Número Plus en el texto completo
    texto = " ".join(soup.get_text(" ", strip=True).upper().split())
    if "PLUS VACANTE" in texto:
        pozos["Plus"] = {"vacante": True}
    elif re.search(r"PLUS\s+\d", texto):
        pozos["Plus"] = {"vacante": False}

    obtenidos = sum(1 for k, v in pozos.items() if k != "Plus" and v.get("premio"))
    print(f"Pozos Loto obtenidos: {obtenidos}/4")

    return pozos if obtenidos > 0 else None
