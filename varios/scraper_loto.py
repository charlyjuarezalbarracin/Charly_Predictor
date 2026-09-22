"""Scraper de resultados históricos de Loto Argentina.

Fuente oficial usada en este módulo:
https://resultados-de-loteria.com/loto-argentina/resultados/<anio>

El CSV generado queda separado del de Quini6 y agrega la columna `numero_plus`.
"""

from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Dict, List
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

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


def _fecha_a_date(fecha_raw):
    """Convierte fecha YYYY-MM-DD a date, si es posible."""
    if not fecha_raw:
        return None
    try:
        return datetime.strptime(str(fecha_raw), "%Y-%m-%d").date()
    except Exception:
        return None


def _ultimo_sorteo_loto_antes_de(fecha_ref=None):
    """Retorna la fecha del ultimo sorteo de Loto (miercoles/sabado) antes de fecha_ref."""
    if fecha_ref is None:
        fecha_ref = datetime.now().date()
    if isinstance(fecha_ref, datetime):
        fecha_ref = fecha_ref.date()

    cursor = fecha_ref - timedelta(days=1)
    while cursor.weekday() not in (2, 5):
        cursor -= timedelta(days=1)
    return cursor


def _obtener_ultima_fecha_csv_loto(destino: Path):
    """Obtiene ultima fecha registrada en CSV de Loto."""
    if not destino.exists() or destino.stat().st_size == 0:
        return None

    try:
        df = pd.read_csv(destino, usecols=["fecha"])
    except Exception:
        return None

    if df.empty or "fecha" not in df.columns:
        return None

    fecha_max = pd.to_datetime(df["fecha"], errors="coerce").max()
    if pd.isna(fecha_max):
        return None
    return fecha_max.date()


def _construir_registros_desde_xml(pozos_xml: dict) -> List[Dict]:
    """Construye filas de historico de Loto desde XML oficial (4 modalidades)."""
    meta = (pozos_xml or {}).get("Meta", {})
    resultados = (pozos_xml or {}).get("Resultados", {})
    fecha = meta.get("fecha")

    numero_plus = resultados.get("Plus")
    if numero_plus is None:
        numero_plus = ((pozos_xml or {}).get("Plus") or {}).get("numero")

    if not fecha or numero_plus is None:
        return []

    try:
        numero_plus = int(numero_plus)
    except Exception:
        return []

    mapa = {
        "Tradicional": "Loto Tradicional",
        "Match": "Loto Match",
        "Desquite": "Loto Desquite",
        "SaleOSale": "Loto Sale o Sale",
    }

    filas = []
    for key_xml, modalidad_csv in mapa.items():
        nums = resultados.get(key_xml) or []
        if len(nums) != 6:
            continue
        try:
            nums = [int(n) for n in nums]
        except Exception:
            continue

        filas.append(
            {
                "fecha": fecha,
                "modalidad": modalidad_csv,
                "num1": nums[0],
                "num2": nums[1],
                "num3": nums[2],
                "num4": nums[3],
                "num5": nums[4],
                "num6": nums[5],
                "numero_plus": numero_plus,
            }
        )

    return filas


def _actualizar_loto_desde_xml_si_falta_ultimo(destino: Path) -> int:
    """Actualiza CSV desde XML si falta solo el ultimo sorteo inmediato anterior."""
    ultima_fecha_csv = _obtener_ultima_fecha_csv_loto(destino)
    if not ultima_fecha_csv:
        return 0

    ultimo = _ultimo_sorteo_loto_antes_de(datetime.now().date())
    penultimo = _ultimo_sorteo_loto_antes_de(ultimo)

    # Caso objetivo: el CSV llega hasta el penultimo, por lo que falta solo el ultimo.
    if ultima_fecha_csv != penultimo:
        return 0

    try:
        xml_text, xml_url = _descargar_xml_ultimo_sorteo()
        pozos_xml = _parsear_pozos_desde_xml(xml_text, xml_url)
        if not pozos_xml:
            return 0

        fecha_xml = _fecha_a_date(((pozos_xml.get("Meta") or {}).get("fecha")))
        if fecha_xml != ultimo:
            return 0

        registros_xml = _construir_registros_desde_xml(pozos_xml)
        if not registros_xml:
            return 0

        try:
            df_actual = _normalizar_dataframe(pd.read_csv(destino))
        except Exception:
            df_actual = pd.DataFrame(
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

        df_xml = _normalizar_dataframe(pd.DataFrame(registros_xml))
        df_final = _normalizar_dataframe(pd.concat([df_actual, df_xml], ignore_index=True))

        nuevas = max(0, len(df_final) - len(df_actual))
        if nuevas > 0:
            df_final.to_csv(destino, index=False, encoding="utf-8")
            print(f"Actualizacion Loto por XML oficial: +{nuevas} filas")
            return int(nuevas)
    except Exception as e:
        print(f"No se pudo aplicar actualizacion directa por XML de Loto: {e}")

    return 0


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
    destino = Path(csv_destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    # Atajo: si solo falta el ultimo sorteo inmediato anterior, usar XML oficial.
    nuevas_xml = _actualizar_loto_desde_xml_si_falta_ultimo(destino)
    if nuevas_xml > 0:
        return int(nuevas_xml)

    if anios is None:
        anios = _obtener_anios_disponibles()

    registros = []
    for anio in sorted(set(anios)):
        registros.extend(_scrapear_anio(anio))

    if not registros:
        raise ValueError("No se pudieron extraer resultados de Loto")

    df_nuevo = _normalizar_dataframe(pd.DataFrame(registros))

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
    """Normaliza premio a solo digitos de la parte entera.

    Soporta formatos:
    - XML: 2159041117.14
    - Web ES: 2.159.041.117 o 2.159.041.117,14
    - Fallback con mezcla de separadores.
    """
    txt = (str(premio_raw or "").strip())
    if not txt:
        return ""

    # Conservar solo digitos y separadores para analizar el formato.
    txt = re.sub(r"[^\d\.,]", "", txt)
    if not txt:
        return ""

    if "." in txt and "," in txt:
        # El separador decimal suele ser el ultimo que aparece.
        decimal_sep = "." if txt.rfind(".") > txt.rfind(",") else ","
        parte_entera = txt.split(decimal_sep)[0]
        return re.sub(r"[^\d]", "", parte_entera)

    if "." in txt:
        partes = txt.split(".")
        if len(partes) > 2 and all(p.isdigit() for p in partes):
            # Caso mixto con puntos de miles + punto decimal final.
            # Ej: 2.159.041.117.14 -> 2159041117
            if 1 <= len(partes[-1]) <= 2:
                return "".join(partes[:-1])
            return "".join(partes)
        # Caso XML decimal (ej: 2159041117.14): tomar parte entera.
        if re.fullmatch(r"\d+\.\d{1,2}", txt):
            return txt.split(".")[0]
        # Caso miles (ej: 2.159.041.117): quitar puntos.
        return txt.replace(".", "")

    if "," in txt:
        partes = txt.split(",")
        if len(partes) > 2 and all(p.isdigit() for p in partes):
            if 1 <= len(partes[-1]) <= 2:
                return "".join(partes[:-1])
            return "".join(partes)
        # Caso decimal con coma (ej: 2159041117,14)
        if re.fullmatch(r"\d+,\d{1,2}", txt):
            return txt.split(",")[0]
        # Caso miles con coma.
        return txt.replace(",", "")

    return re.sub(r"[^\d]", "", txt)


def _normalizar_ganadores(ganadores_raw: str):
    """Normaliza ganadores a 'Vacante' o cantidad numerica en string."""
    txt = (ganadores_raw or "").strip()
    if not txt or txt == "0" or "vacante" in txt.lower() or "sin ganadores" in txt.lower():
        return "Vacante"
    return txt


def _parsear_fecha_xml(fecha_raw: str):
    """Convierte fecha DD-MM-YYYY del XML a YYYY-MM-DD."""
    txt = (fecha_raw or "").strip()
    if not txt:
        return None

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return txt


def _obtener_link_xml_desde_bloque_descargas() -> str:
    """Obtiene el link XML del bloque de descargas del ultimo sorteo."""
    soup = _descargar_soup(f"{_URL_POZOS_LOTO}#resultados")

    # Prioridad 1: enlace explicito de XML (sin asumir estructura exacta).
    a_xml = soup.select_one('a[href*=".xml"]')
    if a_xml and a_xml.get("href"):
        return urljoin(_URL_POZOS_LOTO, a_xml["href"])

    # Prioridad 2: derivar .xml desde un enlace PDF de descarga.php.
    a_pdf = soup.select_one('a[href*="descarga.php"][href*=".pdf"]')
    if a_pdf and a_pdf.get("href"):
        href_xml = re.sub(r"\.pdf($|[?#])", r".xml\1", a_pdf["href"], flags=re.IGNORECASE)
        return urljoin(_URL_POZOS_LOTO, href_xml)

    # Prioridad 3: regex directa sobre el HTML por si el markup cambia.
    html = str(soup)
    m_xml = re.search(r'(export/descarga\.php\?sorteo=[^"\'\s>]+\.xml)', html, flags=re.IGNORECASE)
    if m_xml:
        return urljoin(_URL_POZOS_LOTO, m_xml.group(1))

    m_pdf = re.search(r'(export/descarga\.php\?sorteo=[^"\'\s>]+\.pdf)', html, flags=re.IGNORECASE)
    if m_pdf:
        href_xml = re.sub(r"\.pdf($|[?#])", r".xml\1", m_pdf.group(1), flags=re.IGNORECASE)
        return urljoin(_URL_POZOS_LOTO, href_xml)

    # Prioridad 4: fallback por patron oficial de nombre de archivo.
    # LTO51XYYYYMMDD.xml para la fecha del ultimo sorteo (miercoles/sabado).
    base = _URL_POZOS_LOTO.rstrip('/') + '/'
    ref = datetime.now().date()
    for _ in range(5):
        fecha = _ultimo_sorteo_loto_antes_de(ref)
        ymd = fecha.strftime("%Y%m%d")
        ym = fecha.strftime("%Y/%m")
        candidato = f"{base}export/descarga.php?sorteo={ym}/LTO51X{ymd}.xml"
        try:
            resp = requests.get(candidato, headers=HEADERS, timeout=20)
            if resp.status_code == 200 and "<DatosSorteo" in resp.text:
                return candidato
        except Exception:
            pass
        ref = fecha

    raise ValueError("No se encontro enlace XML del ultimo sorteo en el sitio de Loto")


def _descargar_xml_ultimo_sorteo() -> tuple[str, str]:
    """Descarga XML oficial del ultimo sorteo y retorna (contenido, url)."""
    xml_url = _obtener_link_xml_desde_bloque_descargas()
    resp = requests.get(xml_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text, xml_url


def _extraer_numeros_modalidad_xml(extracto) -> List[int]:
    """Extrae lista de numeros de Suerte (N01..N06) desde un Extracto XML."""
    suerte = extracto.find("Suerte")
    if suerte is None:
        return []

    numeros = []
    for tag in ("N01", "N02", "N03", "N04", "N05", "N06"):
        nodo = suerte.find(tag)
        if nodo is not None and nodo.text and nodo.text.strip():
            try:
                numeros.append(int(nodo.text.strip()))
            except Exception:
                continue
    return numeros


def _parsear_pozos_desde_xml(xml_text: str, xml_url: str) -> dict:
    """Parsea pozos y resultados desde XML oficial de Loto."""
    root = ET.fromstring(xml_text)

    pozos = {
        "Tradicional": {"premio": None, "ganadores": None},
        "Match": {"premio": None, "ganadores": None},
        "Desquite": {"premio": None, "ganadores": None},
        "SaleOSale": {"premio": None, "ganadores": None},
        "Plus": {"vacante": None},
        "Meta": {
            "sorteo": (root.findtext("Sorteo") or "").strip() or None,
            "fecha": _parsear_fecha_xml(root.findtext("FechaSorteo") or ""),
            "pozo_estimado": _normalizar_premio(root.findtext("PozoEstimado") or ""),
            "xml_url": xml_url,
        },
        "Resultados": {
            "Tradicional": [],
            "Match": [],
            "Desquite": [],
            "SaleOSale": [],
            "Plus": None,
        },
    }

    mapa_modalidades = {
        "tradicional": "Tradicional",
        "match": "Match",
        "desquite": "Desquite",
        "sale o sale": "SaleOSale",
    }

    for extracto in root.findall("Extracto"):
        modalidad_raw = (extracto.findtext("Modalidad") or "").strip()
        modalidad_low = modalidad_raw.lower()

        if modalidad_low == "numero plus":
            nodo_plus = extracto.find("./Suerte/N01")
            numero_plus = None
            if nodo_plus is not None and nodo_plus.text and nodo_plus.text.strip():
                try:
                    numero_plus = int(nodo_plus.text.strip())
                except Exception:
                    numero_plus = None

            ganadores_plus = (
                extracto.findtext("./Ganadores/GanadoresSS")
                or extracto.findtext("./Ganadores/Ganadores6T")
                or ""
            )
            ganador_norm = _normalizar_ganadores(ganadores_plus)
            if ganador_norm == "Vacante":
                pozos["Plus"] = {"vacante": True, "numero": numero_plus}
            else:
                pozos["Plus"] = {"vacante": False, "numero": numero_plus}

            pozos["Resultados"]["Plus"] = numero_plus
            continue

        key = mapa_modalidades.get(modalidad_low)
        if not key:
            continue

        premio01 = extracto.findtext("./Pozos/Premio01") or ""
        premio = _normalizar_premio(premio01)

        ganadores01 = extracto.findtext("./Ganadores/Ganadores01") or ""
        ganadores = _normalizar_ganadores(ganadores01)

        if premio:
            pozos[key] = {
                "premio": premio,
                "ganadores": ganadores,
            }

        pozos["Resultados"][key] = _extraer_numeros_modalidad_xml(extracto)

    obtenidos = sum(1 for k in ("Tradicional", "Match", "Desquite", "SaleOSale") if pozos[k].get("premio"))
    print(f"Pozos Loto obtenidos por XML: {obtenidos}/4")

    return pozos if obtenidos > 0 else None


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
    parsed = urlparse(_URL_POZOS_LOTO)
    if "loto.loteriadelaciudad.gob.ar" not in parsed.netloc:
        raise ValueError(
            f"URL inválida para pozos Loto: '{_URL_POZOS_LOTO}'. "
            "Solo se permite acceder a loto.loteriadelaciudad.gob.ar"
        )

    # Intento 1: XML oficial descargado desde el bloque de resultados.
    try:
        xml_text, xml_url = _descargar_xml_ultimo_sorteo()
        pozos_xml = _parsear_pozos_desde_xml(xml_text, xml_url)
        if pozos_xml:
            return pozos_xml
    except Exception as e:
        print(f"No se pudo obtener pozos desde XML oficial: {e}")

    # Intento 2: fallback al metodo HTML anterior.
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
