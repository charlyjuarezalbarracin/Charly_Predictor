from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
import pandas as pd

import app
from varios import scraper_quini_oficial as scraper


def extracto(fecha="2026-10-25", sorteo="3420", categoria=5):
    dia = date.fromisoformat(fecha)
    mes_actual = f"{scraper.MESES[dia.month - 1]} {dia.year}"
    meses = "".join(
        f'<option value="{m} 2026" {"selected" if m + " 2026" == mes_actual else ""}>{m} 2026</option>'
        for m in ("Octubre", "Septiembre", "Agosto")
    )
    opciones = [("25", "3420"), ("21", "3419")] if dia.month == 10 else [("30", "3413"), ("27", "3412")]
    sorteos = "".join(
        f'<option value="Domingo {d} - {n}" {"selected" if n == sorteo else ""}>Domingo {d} - {n}</option>'
        for d, n in opciones
    )
    bloques = []
    for titulo in scraper.MODALIDADES:
        filas = (
            '<tr><td>1° Premio</td><td>1.100.000.000,00</td><td>VACANTE*</td><td></td></tr>'
        )
        if titulo.startswith("tradicional"):
            filas += (
                '<tr><td>2° Premio</td><td>54.515.520,00</td><td>21</td><td>2.595.977,14</td></tr>'
                '<tr><td>3° Premio</td><td>16.354.656,00</td><td>1.336</td><td>12.241,51</td></tr>'
            )
        if titulo == "siempre sale":
            filas = (
                f'<tr><td>1° Premio</td><td>489.092.256,00</td><td>{categoria}</td>'
                '<td>8</td><td>61.136.532,00</td></tr>'
            )
        filas += '<tr><td>Estímulo</td><td>11.000.000,00</td><td>VACANTE</td><td></td></tr>'
        numeros = "".join(f'<div class="cuadrado"><b>{n:02d}</b></div>' for n in range(6))
        bloques.append(
            f'<div class="contenedorquini1"><h3>{titulo}</h3>{numeros}'
            f'<table><tbody>{filas}</tbody></table></div>'
        )
    numeros_extra = "".join(
        f'<div class="cuadradoPE"><b>{n:02d}</b></div>'
        for n in list(range(6)) * 3
    )
    bloques.append(
        f'<div class="contenedorquini1"><h3>Premio Extra</h3>{numeros_extra}'
        '<table><thead><tr><th>POZO $</th><th>Ganadores</th><th>Premios $</th></tr></thead>'
        '<tbody><tr><td>200.000.000,00</td><td>724</td><td>276.243,09</td></tr></tbody>'
        '</table></div>'
    )
    return (
        '<form id="form" action="/Extractos/paginas/mostrarQuini6.xhtml">'
        f'<select id="form:mesSeleccionado_input">{meses}</select>'
        f'<select id="form:sorteoSeleccionado_input">{sorteos}</select>'
        '<input name="javax.faces.ViewState" value="estado1" type="hidden">'
        + "".join(bloques) + "</form>"
    )


def respuesta_parcial(html, estado):
    return Mock(content=(
        '<partial-response><changes><update id="form"><![CDATA[' + html
        + ']]></update><update id="j_id1:javax.faces.ViewState:0">'
        + estado + '</update></changes></partial-response>'
    ).encode())


class TestScraperQuiniOficial(unittest.TestCase):
    def parsear(self, html=None):
        return scraper._parsear_premios_quini(BeautifulSoup(html or extracto(), "html.parser"))

    def test_columna_premios_por_ganador_y_pozo_separados(self):
        datos = self.parsear()
        self.assertEqual(datos["Meta"]["fecha"], "2026-10-25")
        self.assertEqual(datos["Meta"]["fuente"], scraper.URL_QUINI)
        self.assertEqual(datos["Premios"]["Tradicional"]["4"]["premio_unitario"], "12241.51")
        self.assertEqual(datos["Premios"]["Tradicional"]["5"]["premio_unitario"], "2595977.14")
        self.assertEqual(datos["Premios"]["Tradicional"]["4"]["ganadores"], "1336")
        self.assertIsNone(datos["Premios"]["Revancha"]["6"]["premio_unitario"])
        self.assertEqual(datos["SiempreSale"]["premio"], "489092256")
        self.assertEqual(datos["Premios"]["SiempreSale"]["5"]["premio_unitario"], "61136532.00")
        self.assertEqual(datos["Premios"]["Extra"]["6"], {
            "pozo": "200000000", "ganadores": "724", "premio_unitario": "276243.09",
        })
        self.assertEqual(len(datos["Premios"]), 5)

    def test_siempre_sale_lee_aciertos_del_extracto(self):
        for aciertos in (3, 4, 5, 6):
            with self.subTest(aciertos=aciertos):
                self.assertEqual(
                    set(self.parsear(extracto(categoria=aciertos))["Premios"]["SiempreSale"]),
                    {str(aciertos)},
                )

    def test_datos_invalidos_no_se_ignoran(self):
        for html in [
            extracto().replace("12.241,51", ""),
            extracto().replace("<b>05</b>", "<b>46</b>"),
            extracto().replace("<h3>revancha</h3>", "<h3>desconocido</h3>"),
            extracto().replace("<b>05</b>", "<b>00</b>"),
            extracto().replace("<h3>Premio Extra</h3>", "<h3>Extra desconocido</h3>"),
            extracto().replace("276.243,09", ""),
            extracto().replace('class="cuadradoPE"><b>05', 'class="cuadradoPE"><b>45'),
        ]:
            with self.subTest(html=html[:40]):
                with self.assertRaises(ValueError):
                    self.parsear(html)

    def test_extra_vacante_no_inventa_importe(self):
        datos = self.parsear(extracto().replace("<td>724</td>", "<td>VACANTE</td>"))
        self.assertEqual(datos["Premios"]["Extra"]["6"]["ganadores"], "Vacante")
        self.assertIsNone(datos["Premios"]["Extra"]["6"]["premio_unitario"])

    def test_consulta_ultima_fecha_no_hace_post(self):
        with patch.object(scraper.requests, "Session") as crear:
            session = crear.return_value.__enter__.return_value
            session.get.return_value.content = extracto().encode()
            datos = scraper.obtener_pozos_quini_oficial()
            self.assertEqual(datos["Meta"]["sorteo"], "3420")
            session.post.assert_not_called()

    def test_navega_mes_y_sorteo_preservando_estado(self):
        with patch.object(scraper.requests, "Session") as crear:
            session = crear.return_value.__enter__.return_value
            session.get.return_value.content = extracto().encode()
            session.post.side_effect = [
                respuesta_parcial(extracto("2026-09-30", "3413"), "estado2"),
                respuesta_parcial(extracto("2026-09-27", "3412"), "estado3"),
            ]
            datos = scraper.obtener_premios_quini_por_fecha("2026-09-27")
            self.assertEqual(datos["Meta"]["fecha"], "2026-09-27")
            self.assertEqual(datos["Meta"]["sorteo"], "3412")
            llamadas = session.post.call_args_list
            self.assertEqual(llamadas[0].kwargs["data"]["form:mesSeleccionado_input"], "Septiembre 2026")
            self.assertEqual(llamadas[1].kwargs["data"]["javax.faces.ViewState"], "estado2")
            self.assertEqual(llamadas[1].kwargs["data"]["form:sorteoSeleccionado_input"], "Domingo 27 - 3412")

    def test_mes_fuera_de_archivo_no_usa_ultima_fecha(self):
        with patch.object(scraper.requests, "Session") as crear:
            session = crear.return_value.__enter__.return_value
            session.get.return_value.content = extracto().encode()
            with self.assertRaisesRegex(ValueError, "no ofrece extractos"):
                scraper.obtener_premios_quini_por_fecha("2026-07-26")
            session.post.assert_not_called()

    def test_seleccion_no_aplicada_se_informa(self):
        with patch.object(scraper.requests, "Session") as crear:
            session = crear.return_value.__enter__.return_value
            session.get.return_value.content = extracto().encode()
            session.post.return_value = respuesta_parcial(extracto(), "estado2")
            with self.assertRaisesRegex(ValueError, "no aplico"):
                scraper.obtener_premios_quini_por_fecha("2026-10-21")


class TestHistorialPremiosQuini(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "pozos_quini.json"
        parche = patch.object(app, "POZOS_FILE", self.ruta)
        parche.start()
        self.addCleanup(parche.stop)
        self.pozos = scraper._parsear_premios_quini(BeautifulSoup(extracto(), "html.parser"))
        app.guardar_pozos_json(self.pozos)
        self.entry = {
            "juego": "Quini 6", "timestamp": "2026-10-23 12:00:00",
            "prediccion": [0, 1, 2, 3, 10, 11],
        }

    def reales(self, fecha="2026-10-25", numeros_por_modalidad=None):
        filas = [
            {"fecha": fecha, **{f"num{i + 1}": n for i, n in enumerate(numeros)}}
            for numeros in (numeros_por_modalidad or [list(range(6))] * 4)
        ]
        with patch.object(app.pd, "read_csv", return_value=pd.DataFrame(filas)):
            return app.cargar_resultados_reales_historial("quini6")

    def test_categorias_y_texto_solo_con_premio(self):
        for aciertos in range(7):
            entry = dict(self.entry, prediccion=list(range(aciertos)) + list(range(10, 16 - aciertos)))
            resultados = app.evaluar_entry_historial_con_real(entry, self.reales())["resultados_modalidad"]
            for resultado in resultados:
                modalidad = resultado["modalidad"]
                # En el extracto de prueba el 1° premio (6 aciertos) quedó vacante.
                esperados = {"Tradicional": {4, 5}, "Segunda": {4, 5}, "Revancha": set(), "Siempre Sale": {5}}
                with self.subTest(modalidad=modalidad, aciertos=aciertos):
                    self.assertEqual(resultado["tiene_premio"], aciertos in esperados[modalidad])
                    self.assertEqual(bool(app.formatear_premio_historial(resultado)), resultado["tiene_premio"])

    def test_importe_correcto_por_fecha_sin_tomar_pozo(self):
        evaluacion = app.evaluar_entry_historial_con_real(self.entry, self.reales())
        self.assertEqual(evaluacion["fecha_real"], "2026-10-25")
        self.assertEqual(
            app.formatear_premio_historial(evaluacion["resultados_modalidad"][0]),
            "4 aciertos | Premio: $ 12.241,51",
        )
        futuro = app.evaluar_entry_historial_con_real(self.entry, self.reales("2026-10-28"))
        self.assertIn("no disponible", app.formatear_premio_historial(futuro["resultados_modalidad"][0]))

    def test_historial_persistente_y_separado_de_loto(self):
        nuevos = dict(self.pozos, Meta=dict(self.pozos["Meta"], fecha="2026-10-28"))
        nuevos.pop("Historial_premios")
        with patch.object(app, "POZOS_LOTO_FILE", Path(self.temporal.name) / "loto.json"):
            app.guardar_pozos_json(nuevos)
            with self.ruta.open(encoding="utf-8") as f:
                historico = json.load(f)["Historial_premios"]
            self.assertEqual(set(historico), {"2026-10-25", "2026-10-28"})
            self.assertFalse(app.POZOS_LOTO_FILE.exists())

    def test_categoria_vacante_no_se_muestra(self):
        pozos = dict(self.pozos)
        pozos["Premios"] = {
            m: {k: dict(v) for k, v in niveles.items()}
            for m, niveles in self.pozos["Premios"].items()
        }
        for modalidad in ("Tradicional", "Segunda"):
            pozos["Premios"][modalidad]["4"] = {
                "pozo": "16354656", "ganadores": "Vacante", "premio_unitario": None,
            }
        app.guardar_pozos_json(pozos)
        for aciertos in (4, 6):
            entry = dict(self.entry, prediccion=list(range(aciertos)) + list(range(10, 16 - aciertos)))
            for resultado in app.evaluar_entry_historial_con_real(entry, self.reales())["resultados_modalidad"]:
                if resultado["modalidad"] not in ("Tradicional", "Segunda", "Revancha"):
                    continue
                with self.subTest(modalidad=resultado["modalidad"], aciertos=aciertos):
                    if not (resultado["modalidad"] == "Revancha" and aciertos == 4):
                        self.assertTrue(resultado["vacante"])
                    self.assertFalse(resultado["tiene_premio"])
                    self.assertEqual(app.formatear_premio_historial(resultado), "")

    def test_completar_premios_consulta_fuente_quini_una_vez(self):
        futuros = dict(self.pozos, Meta=dict(self.pozos["Meta"], fecha="2026-10-28"))
        reales = self.reales("2026-10-28")
        with patch.object(app.st, "session_state", {"historial": [self.entry, self.entry]}), \
                patch.object(app, "cargar_resultados_reales_historial", return_value=reales), \
                patch.object(app, "obtener_premios_quini_por_fecha", return_value=futuros) as obtener, \
                patch.object(app, "obtener_premios_loto_por_fecha") as obtener_loto:
            app.actualizar_premios_historial(self.pozos, "quini6")
            app.actualizar_premios_historial(self.pozos, "quini6")
            obtener.assert_called_once_with("2026-10-28")
            obtener_loto.assert_not_called()

    def test_extra_gana_con_numeros_repartidos_sin_premio_individual(self):
        reales = self.reales(numeros_por_modalidad=[
            [0, 1, 2, 3, 4, 5],
            [0, 2, 6, 7, 8, 9],
            [1, 3, 4, 5, 10, 11],
            [12, 13, 14, 15, 16, 17],
        ])
        entry = dict(self.entry, prediccion=[0, 1, 6, 7, 10, 11])
        evaluacion = app.evaluar_entry_historial_con_real(entry, reales)
        self.assertFalse(any(r["tiene_premio"] for r in evaluacion["resultados_modalidad"]))
        extra = evaluacion["pozo_extra"]
        self.assertEqual(extra["aciertos"], 6)
        self.assertEqual(extra["coincidencias"], entry["prediccion"])
        self.assertTrue(extra["tiene_premio"])
        self.assertEqual(
            app.formatear_premio_extra_historial(extra),
            "GANASTE EL POZO EXTRA $ 276.243,09",
        )

    def test_extra_requiere_seis_distintos_y_no_cuenta_siempre_sale(self):
        reales = self.reales(numeros_por_modalidad=[
            list(range(6)), list(range(6)), list(range(6)), [0, 1, 2, 3, 4, 10],
        ])
        for prediccion in ([0, 1, 2, 3, 10, 11], [0, 1, 2, 3, 4, 10], [0, 0, 1, 2, 3, 4]):
            with self.subTest(prediccion=prediccion):
                evaluacion = app.evaluar_entry_historial_con_real(
                    dict(self.entry, prediccion=list(prediccion)), reales,
                )
                self.assertFalse(evaluacion["pozo_extra"]["tiene_premio"])
                self.assertEqual(app.formatear_premio_extra_historial(evaluacion["pozo_extra"]), "")

    def test_extra_no_se_evalua_con_modalidades_incompletas_ni_en_loto(self):
        reales = self.reales()
        entry = dict(self.entry, prediccion=list(range(6)))
        incompletos = reales[reales["modalidad"] != "Revancha"]
        self.assertNotIn("pozo_extra", app.evaluar_entry_historial_con_real(entry, incompletos))
        duplicados = pd.concat([reales, reales[reales["modalidad"] == "Tradicional"]])
        self.assertNotIn("pozo_extra", app.evaluar_entry_historial_con_real(entry, duplicados))
        self.assertNotIn(
            "pozo_extra", app.evaluar_entry_historial_con_real(dict(entry, juego="Loto"), reales),
        )

    def test_extra_no_usa_importe_de_otra_fecha(self):
        entry = dict(self.entry, prediccion=list(range(6)))
        evaluacion = app.evaluar_entry_historial_con_real(entry, self.reales("2026-10-28"))
        self.assertIsNone(evaluacion["pozo_extra"]["premio_unitario"])
        self.assertEqual(
            app.formatear_premio_extra_historial(evaluacion["pozo_extra"]),
            "POZO EXTRA: 6 ACIERTOS | PREMIO NO DISPONIBLE",
        )

    def test_extra_vacante_no_se_muestra_en_historial(self):
        self.pozos["Premios"]["Extra"]["6"].update(ganadores="Vacante", premio_unitario=None)
        app.guardar_pozos_json(self.pozos)
        evaluacion = app.evaluar_entry_historial_con_real(
            dict(self.entry, prediccion=list(range(6))), self.reales(),
        )
        self.assertFalse(evaluacion["pozo_extra"]["tiene_premio"])
        self.assertEqual(app.formatear_premio_extra_historial(evaluacion["pozo_extra"]), "")

    def test_completa_extra_faltante_sin_perderlo_al_guardar_fecha_actual(self):
        datos = dict(self.pozos, Premios=dict(self.pozos["Premios"]))
        self.pozos["Premios"] = dict(self.pozos["Premios"])
        self.pozos["Premios"].pop("Extra")
        app.guardar_pozos_json(self.pozos)
        reales = self.reales()
        with patch.object(app.st, "session_state", {"historial": [self.entry, self.entry]}), \
                patch.object(app, "cargar_resultados_reales_historial", return_value=reales), \
                patch.object(app, "obtener_premios_quini_por_fecha", return_value=datos) as obtener:
            app.actualizar_premios_historial(self.pozos, "quini6")
            app.actualizar_premios_historial(self.pozos, "quini6")
            obtener.assert_called_once_with("2026-10-25")
        guardados = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertEqual(guardados["Premios"]["Extra"], datos["Premios"]["Extra"])
        self.assertEqual(
            guardados["Historial_premios"]["2026-10-25"]["Premios"]["Extra"],
            datos["Premios"]["Extra"],
        )

    def test_error_al_completar_extra_se_informa(self):
        self.pozos["Premios"].pop("Extra")
        app.guardar_pozos_json(self.pozos)
        reales = self.reales()
        with patch.object(app.st, "session_state", {"historial": [self.entry]}), \
                patch.object(app, "cargar_resultados_reales_historial", return_value=reales), \
                patch.object(app, "obtener_premios_quini_por_fecha", side_effect=ValueError("sin extracto")):
            with self.assertRaisesRegex(ValueError, "2026-10-25: sin extracto"):
                app.actualizar_premios_historial(self.pozos, "quini6")


if __name__ == "__main__":
    unittest.main()
