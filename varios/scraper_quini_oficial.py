"""Premios por ganador del extracto de Quini 6 de Loteria de Santa Fe."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import requests


URL_QUINI = "https://www.loteriasantafe.gov.ar/quini-6-2/"
URL_EXTRACTO = (
    "https://apps.loteriasantafe.gov.ar:8443/Extractos/paginas/"
    "mostrarQuini6.xhtml?display=0"
)
MESES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
MODALIDADES = {
    "tradicional primer sorteo": "Tradicional",
    "tradicional la segunda del quini": "Segunda",
    "revancha": "Revancha",
    "siempre sale": "SiempreSale",
}


def _opcion_seleccionada(soup, campo):
    selector = soup.find("select", id=f"form:{campo}_input")
    if selector is None:
        raise ValueError(f"No se encontro el selector oficial de {campo}")
    opcion = selector.find("option", selected=True) or selector.find("option")
    if opcion is None:
        raise ValueError(f"No hay opciones oficiales para {campo}")
    return opcion["value"]


def _importe_oficial(texto):
    texto = texto.strip().replace("$", "").replace(".", "").replace(",", ".")
    try:
        importe = Decimal(texto)
    except InvalidOperation as e:
        raise ValueError(f"Importe oficial de Quini invalido: {texto!r}") from e
    if not importe.is_finite() or importe < 0:
        raise ValueError(f"Importe oficial de Quini invalido: {texto!r}")
    return importe


def _nivel_premio(pozo_texto, ganadores_texto, premio_texto, modalidad):
    pozo = _importe_oficial(pozo_texto)
    ganadores_raw = ganadores_texto.replace(".", "")
    if "VACANTE" in ganadores_raw.upper() or ganadores_raw == "0":
        ganadores = "Vacante"
        premio_unitario = None
    elif ganadores_raw.isdigit() and int(ganadores_raw) > 0:
        ganadores = ganadores_raw
        premio_unitario = f"{_importe_oficial(premio_texto):.2f}"
    else:
        raise ValueError(f"Cantidad de ganadores oficial invalida para {modalidad}")
    return {
        "pozo": str(int(pozo)),
        "ganadores": ganadores,
        "premio_unitario": premio_unitario,
    }


def _parsear_premios_quini(soup):
    mes_texto, anio = _opcion_seleccionada(soup, "mesSeleccionado").split()
    if mes_texto not in MESES:
        raise ValueError(f"Mes oficial de Quini desconocido: {mes_texto}")
    sorteo_texto = _opcion_seleccionada(soup, "sorteoSeleccionado")
    coincidencia = re.fullmatch(r".+?\s+(\d{1,2})\s*-\s*(\d+)", sorteo_texto)
    if coincidencia is None:
        raise ValueError(f"Sorteo oficial de Quini invalido: {sorteo_texto}")
    fecha = datetime(
        int(anio), MESES.index(mes_texto) + 1, int(coincidencia.group(1)),
    ).strftime("%Y-%m-%d")
    pozos = {
        "Meta": {
            "fecha": fecha, "sorteo": coincidencia.group(2), "fuente": URL_QUINI,
        },
        "Resultados": {},
        "Premios": {},
    }
    bloque_extra = None
    for bloque in soup.select(".contenedorquini1"):
        titulo = bloque.find("h3")
        nombre = " ".join(titulo.get_text(" ", strip=True).lower().split()) if titulo else ""
        if nombre == "premio extra":
            bloque_extra = bloque
            continue
        modalidad = MODALIDADES.get(nombre)
        if modalidad is None:
            continue
        tabla = bloque.find("table")
        if tabla is None:
            raise ValueError(f"Falta la tabla oficial de premios de {modalidad}")
        numeros = [int(b.get_text(strip=True)) for b in bloque.select(".cuadrado b")]
        if len(numeros) != 6 or len(set(numeros)) != 6 or any(n < 0 or n > 45 for n in numeros):
            raise ValueError(f"Numeros oficiales invalidos para {modalidad}")
        niveles = {}
        for fila in tabla.select("tbody tr"):
            celdas = [td.get_text(" ", strip=True) for td in fila.find_all("td")]
            if not celdas:
                continue
            categoria = re.match(r"^([123])\D", celdas[0])
            if categoria is None:
                continue
            if modalidad == "SiempreSale":
                if len(celdas) != 5:
                    raise ValueError("Columnas oficiales invalidas para Siempre Sale")
                aciertos = int(celdas[2])
                if not 0 <= aciertos <= 6:
                    raise ValueError("Categoria oficial invalida para Siempre Sale")
            else:
                if len(celdas) != 4:
                    raise ValueError(f"Columnas oficiales invalidas para {modalidad}")
                aciertos = 7 - int(categoria.group(1))
            niveles[str(aciertos)] = _nivel_premio(
                celdas[1], celdas[-2], celdas[-1], modalidad,
            )
        esperados = {"4", "5", "6"} if modalidad in ("Tradicional", "Segunda") else {"6"}
        if modalidad == "SiempreSale":
            if len(niveles) != 1 or next(iter(niveles.values()))["ganadores"] == "Vacante":
                raise ValueError("No se encontro la categoria ganadora de Siempre Sale")
        elif set(niveles) != esperados:
            raise ValueError(f"Categorias oficiales incompletas para {modalidad}")
        mayor = niveles[max(niveles, key=int)]
        pozos[modalidad] = {"premio": mayor["pozo"], "ganadores": mayor["ganadores"]}
        pozos["Premios"][modalidad] = niveles
        pozos["Resultados"][modalidad] = numeros
    if set(pozos["Premios"]) != set(MODALIDADES.values()):
        raise ValueError("Faltan modalidades en el extracto oficial de Quini")
    if bloque_extra is None:
        raise ValueError("Falta el Premio Extra en el extracto oficial de Quini")
    numeros_extra = [
        int(b.get_text(strip=True))
        for b in bloque_extra.select(".cuadradoPE b, .cuadradoPET b")
    ]
    union_numeros = set().union(*(
        pozos["Resultados"][modalidad]
        for modalidad in ("Tradicional", "Segunda", "Revancha")
    ))
    if len(numeros_extra) != 18 or set(numeros_extra) != union_numeros:
        raise ValueError("Los numeros del Premio Extra no coinciden con los tres primeros sorteos")
    filas_extra = bloque_extra.select("table tbody tr")
    if len(filas_extra) != 1:
        raise ValueError("Tabla oficial invalida para Premio Extra")
    celdas_extra = [td.get_text(" ", strip=True) for td in filas_extra[0].find_all("td")]
    if len(celdas_extra) != 3:
        raise ValueError("Columnas oficiales invalidas para Premio Extra")
    pozos["Premios"]["Extra"] = {
        "6": _nivel_premio(celdas_extra[0], celdas_extra[1], celdas_extra[2], "Extra"),
    }
    return pozos


def _cambiar_seleccion(session, soup, campo, valor):
    formulario = soup.find("form", id="form")
    estado = soup.find("input", attrs={"name": "javax.faces.ViewState"})
    if formulario is None or estado is None:
        raise ValueError("Falta el estado del formulario oficial de Quini")
    origen = f"form:{campo}"
    datos = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": origen,
        "javax.faces.partial.execute": origen,
        "javax.faces.partial.render": "form",
        "javax.faces.behavior.event": "change",
        "javax.faces.partial.event": "change",
        "form": "form",
        "form:mesSeleccionado_input": _opcion_seleccionada(soup, "mesSeleccionado"),
        "form:sorteoSeleccionado_input": _opcion_seleccionada(soup, "sorteoSeleccionado"),
        "javax.faces.ViewState": estado["value"],
    }
    datos[f"{origen}_input"] = valor
    resp = session.post(
        urljoin(URL_EXTRACTO, formulario["action"]), data=datos,
        headers={"Faces-Request": "partial/ajax"}, timeout=45,
    )
    resp.raise_for_status()
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        raise ValueError("Respuesta de seleccion oficial de Quini invalida") from e
    actualizado = root.find(".//update[@id='form']")
    estado_nuevo = next(
        (n for n in root.findall(".//update") if "javax.faces.ViewState" in n.get("id", "")),
        None,
    )
    if actualizado is None or not actualizado.text or estado_nuevo is None or not estado_nuevo.text:
        raise ValueError("No se pudo actualizar la seleccion oficial de Quini")
    nuevo_soup = BeautifulSoup(actualizado.text, "html.parser")
    nuevo_formulario = nuevo_soup.find("form", id="form")
    if nuevo_formulario is None:
        raise ValueError("No se recibio el formulario oficial de Quini")
    estado = nuevo_soup.find("input", attrs={"name": "javax.faces.ViewState"})
    if estado is None:
        estado = nuevo_soup.new_tag("input", attrs={"name": "javax.faces.ViewState", "type": "hidden"})
        nuevo_formulario.append(estado)
    estado["value"] = estado_nuevo.text
    if _opcion_seleccionada(nuevo_soup, campo) != valor:
        raise ValueError("El sitio oficial no aplico la seleccion solicitada de Quini")
    return nuevo_soup


def _obtener_premios_quini(fecha=None):
    with requests.Session() as session:
        resp = session.get(URL_EXTRACTO, timeout=45)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        if fecha is not None:
            fecha_sorteo = datetime.strptime(fecha, "%Y-%m-%d")
            mes = f"{MESES[fecha_sorteo.month - 1]} {fecha_sorteo.year}"
            selector_mes = soup.find("select", id="form:mesSeleccionado_input")
            if selector_mes is None or not selector_mes.find("option", value=mes):
                raise ValueError(f"El sitio oficial no ofrece extractos de Quini para {mes}")
            if _opcion_seleccionada(soup, "mesSeleccionado") != mes:
                soup = _cambiar_seleccion(session, soup, "mesSeleccionado", mes)
            selector = soup.find("select", id="form:sorteoSeleccionado_input")
            opcion = next(
                (op["value"] for op in selector.find_all("option")
                 if re.search(rf"\s{fecha_sorteo.day}\s*-\s*\d+$", op["value"])),
                None,
            ) if selector else None
            if opcion is None:
                raise ValueError(f"No se encontro el sorteo oficial de Quini del {fecha}")
            if _opcion_seleccionada(soup, "sorteoSeleccionado") != opcion:
                soup = _cambiar_seleccion(session, soup, "sorteoSeleccionado", opcion)
        pozos = _parsear_premios_quini(soup)
        if fecha is not None and pozos["Meta"]["fecha"] != fecha:
            raise ValueError(f"El sitio oficial devolvio premios de otra fecha para {fecha}")
        return pozos


def obtener_pozos_quini_oficial():
    """Obtiene pozos y premios por ganador del ultimo extracto oficial."""
    return _obtener_premios_quini()


def obtener_premios_quini_por_fecha(fecha):
    """Obtiene los premios del sorteo solicitado, sin sustituirlo por el actual."""
    return _obtener_premios_quini(fecha)
