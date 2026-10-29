import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd
import requests

import app
from varios import scraper_loto


def datos_oficiales():
    return {
        "sorteo": 3929,
        "fecha": "24/10/2026",
        "pozoEstimado": 28972000000,
        "numeros_juegos": {
            "Tradicional": ["07", "25", "32", "33", "37", "43"],
            "Match": ["00", "02", "07", "17", "29", "42"],
            "Desquite": ["02", "05", "12", "22", "44", "45"],
            "Sale o Sale": ["04", "13", "16", "17", "18", "24"],
            "Número Plus": ["6"],
        },
        "juegos": [
            {"juego": "Tradicional", "niveles": [
                {"aciertos": 6, "pozo": 4424318990.52, "ganadores": "VACANTE", "premio_unid": 0},
                {"aciertos": 5, "pozo": 20981268, "ganadores": 4, "premio_unid": 5245317},
                {"aciertos": 4, "pozo": 4196253.6, "ganadores": 304, "premio_unid": 13803.465789473683},
            ]},
            {"juego": "Match", "niveles": [
                {"aciertos": 6, "pozo": 2292219616.76, "ganadores": "VACANTE", "premio_unid": 0},
                {"aciertos": 5, "pozo": 20981268, "ganadores": 3, "premio_unid": 6993756},
                {"aciertos": 4, "pozo": 4196253.6, "ganadores": 423, "premio_unid": 9920.221276595743},
            ]},
            {"juego": "Desquite", "niveles": [
                {"aciertos": 6, "pozo": 2836877795.2, "ganadores": "VACANTE", "premio_unid": 0},
            ]},
            {"juego": "Sale o Sale", "niveles": [
                {"aciertos": 5, "pozo": 54042660, "ganadores": 14, "premio_unid": 3860190},
            ]},
            {"juego": "Número Plus", "niveles": [
                {"aciertos": 1, "pozo": 0, "ganadores": "VACANTE", "premio_unid": 0},
            ]},
        ],
        "archivos": {"xml": "export/descarga.php?sorteo=2026/10/LTO51X20261024.xml"},
    }


def parsear_datos(datos=None):
    return scraper_loto._parsear_pozos_desde_datos(
        "window.RESULTADOS_DATA = [];window.PREMIOS_DATA = "
        + json.dumps([datos or datos_oficiales()])
        + ";window.POZO_ULTIMO_SORTEO = 28972000000;"
    )


class TestScrapingPremiosLoto(unittest.TestCase):
    def test_importes_por_persona_no_pozos(self):
        pozos = parsear_datos()
        self.assertEqual(pozos["Tradicional"]["premio"], "4424318990")
        self.assertEqual(pozos["Premios"]["Tradicional"]["4"]["premio_unitario"], "13803.47")
        self.assertEqual(pozos["Premios"]["Match"]["4"]["premio_unitario"], "9920.22")
        self.assertEqual(pozos["Premios"]["Tradicional"]["5"]["premio_unitario"], "5245317.00")
        self.assertEqual(pozos["Premios"]["Match"]["5"]["premio_unitario"], "6993756.00")
        self.assertIsNone(pozos["Premios"]["Tradicional"]["6"]["premio_unitario"])
        self.assertEqual(pozos["Resultados"]["Plus"], 6)
        self.assertEqual(pozos["Meta"]["fecha"], "2026-10-24")

    def test_no_calcula_importe_desde_pozo(self):
        datos = datos_oficiales()
        datos["juegos"][0]["niveles"][2]["premio_unid"] = 12345.67
        self.assertEqual(
            parsear_datos(datos)["Premios"]["Tradicional"]["4"]["premio_unitario"],
            "12345.67",
        )

    def test_datos_ausentes_o_incompletos_fallan(self):
        with self.assertRaises(ValueError):
            scraper_loto._parsear_pozos_desde_datos("<html>Error</html>")
        datos = datos_oficiales()
        datos["juegos"] = datos["juegos"][:1]
        with self.assertRaises(ValueError):
            parsear_datos(datos)
        datos = datos_oficiales()
        datos["juegos"][0]["niveles"].pop()
        with self.assertRaisesRegex(ValueError, "Faltan niveles"):
            parsear_datos(datos)

    def test_consulta_por_fecha_rechaza_otro_sorteo(self):
        xml = Mock(
            text="<DatosSorteo><Sorteo>3928</Sorteo><FechaSorteo>21-10-2026</FechaSorteo></DatosSorteo>"
        )
        datos = Mock(text="window.PREMIOS_DATA = " + json.dumps([datos_oficiales()]))
        with patch.object(scraper_loto.requests, "get", side_effect=[xml, datos]) as get:
            with self.assertRaisesRegex(ValueError, "otra fecha"):
                scraper_loto.obtener_premios_loto_por_fecha("2026-10-21")
            self.assertEqual(get.call_args.kwargs["params"], {"sorteo": "3928"})

    def test_fecha_no_publicada_no_usa_ultimo(self):
        with patch.object(scraper_loto.requests, "get") as get:
            get.return_value.raise_for_status.side_effect = requests.HTTPError("404")
            with self.assertRaises(requests.HTTPError):
                scraper_loto.obtener_premios_loto_por_fecha("2026-10-21")
            get.assert_called_once()

    def test_fecha_historica_fuera_del_mes_actual(self):
        xml = Mock(
            text="<DatosSorteo><Sorteo>3921</Sorteo><FechaSorteo>26-09-2026</FechaSorteo></DatosSorteo>"
        )
        datos = datos_oficiales()
        datos["fecha"] = "26/09/2026"
        datos["sorteo"] = 3921
        respuesta = Mock(text="window.PREMIOS_DATA = " + json.dumps([datos]))
        with patch.object(scraper_loto.requests, "get", side_effect=[xml, respuesta]) as get:
            pozos = scraper_loto.obtener_premios_loto_por_fecha("2026-09-26")
            self.assertEqual(pozos["Meta"]["fecha"], "2026-09-26")
            self.assertEqual(get.call_args_list[0].kwargs["params"], {
                "sorteo": "2026/09/LTO51X20260926.xml",
            })


class TestHistorialPremiosLoto(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "pozos_loto.json"
        self.parche = patch.object(app, "POZOS_LOTO_FILE", self.ruta)
        self.parche.start()
        self.addCleanup(self.parche.stop)
        self.pozos = parsear_datos()
        app.guardar_pozos_loto_json(self.pozos)

    def cargar_reales(self, fecha="2026-10-24"):
        filas = []
        for modalidad, numeros in self.pozos["Resultados"].items():
            if modalidad == "Plus":
                continue
            nombre = "Sale o Sale" if modalidad == "SaleOSale" else modalidad
            filas.append({
                "fecha": fecha, "modalidad": "Loto " + nombre, "numero_plus": 6,
                **{f"num{i}": n for i, n in enumerate(numeros, 1)},
            })
        with patch.object(app.pd, "read_csv", return_value=pd.DataFrame(filas)):
            return app.cargar_resultados_reales_historial("loto")

    def evaluar(self, prediccion, df=None):
        entry = {
            "juego": "Loto", "timestamp": "2026-10-23 12:00:00",
            "prediccion": prediccion, "numero_plus": 6,
        }
        return app.evaluar_entry_historial_con_real(
            entry, self.cargar_reales() if df is None else df,
        )

    def test_cuatro_aciertos_tradicional_y_match(self):
        for modalidad, prediccion, importe in [
            ("Loto Tradicional", [7, 25, 32, 33, 1, 3], "13803.47"),
            ("Loto Match", [0, 2, 7, 17, 1, 3], "9920.22"),
        ]:
            with self.subTest(modalidad=modalidad):
                evaluacion = self.evaluar(prediccion)
                self.assertEqual(evaluacion["fecha_real"], "2026-10-24")
                resultado = next(r for r in evaluacion["resultados_modalidad"] if r["modalidad"] == modalidad)
                self.assertEqual(resultado["aciertos"], 4)
                self.assertTrue(resultado["tiene_premio"])
                self.assertEqual(resultado["premio_unitario"], importe)
                self.assertEqual(evaluacion["acierto_plus"], 1)

    def test_cinco_y_seis_aciertos(self):
        for prediccion, aciertos, importe, vacante, premiado in [
            ([7, 25, 32, 33, 37, 1], 5, "5245317.00", False, True),
            ([7, 25, 32, 33, 37, 43], 6, None, True, False),
        ]:
            resultado = self.evaluar(prediccion)["resultados_modalidad"][0]
            self.assertEqual(resultado["aciertos"], aciertos)
            self.assertEqual(resultado["tiene_premio"], premiado)
            self.assertEqual(resultado["premio_unitario"], importe)
            self.assertEqual(resultado["vacante"], vacante)
            self.assertEqual(bool(app.formatear_premio_historial(resultado)), premiado)

    def test_tres_aciertos_sin_premio(self):
        resultado = self.evaluar([7, 25, 32, 1, 3, 8])["resultados_modalidad"][0]
        self.assertFalse(resultado["tiene_premio"])
        self.assertEqual(app.formatear_premio_historial(resultado), "")

    def test_solo_muestra_aciertos_en_categorias_premiadas(self):
        for modalidad, premiados, niveles in [
            ("Loto Tradicional", {4, 5, 6}, {}),
            ("Loto Match", {4, 5, 6}, {}),
            ("Loto Desquite", {6}, {}),
            ("Loto Sale o Sale", {5}, {
                "5": {"ganadores": "14", "premio_unitario": "3860190.00"},
            }),
        ]:
            for aciertos in range(7):
                with self.subTest(modalidad=modalidad, aciertos=aciertos):
                    df = pd.DataFrame([{
                        "fecha": date(2026, 10, 24), "modalidad": modalidad,
                        "numeros_real": tuple(range(6)), "numero_plus_real": 6,
                        "premios_modalidad": niveles,
                    }])
                    prediccion = list(range(aciertos)) + list(range(10, 16 - aciertos))
                    resultado = self.evaluar(prediccion, df)["resultados_modalidad"][0]
                    self.assertEqual(resultado["aciertos"], aciertos)
                    self.assertEqual(resultado["tiene_premio"], aciertos in premiados)
                    texto = app.formatear_premio_historial(resultado)
                    self.assertEqual(bool(texto), aciertos in premiados)
                    if aciertos in premiados:
                        self.assertIn(f"{aciertos} aciertos", texto)
                    else:
                        self.assertEqual(texto, "")

    def test_sale_o_sale_sigue_la_categoria_del_sorteo(self):
        for categoria in (3, 4, 5, 6):
            for aciertos in range(7):
                with self.subTest(categoria=categoria, aciertos=aciertos):
                    df = pd.DataFrame([{
                        "fecha": date(2026, 10, 24), "modalidad": "Loto Sale o Sale",
                        "numeros_real": tuple(range(6)), "numero_plus_real": 6,
                        "premios_modalidad": {
                            str(categoria): {"ganadores": "2", "premio_unitario": "1000.00"},
                        },
                    }])
                    prediccion = list(range(aciertos)) + list(range(10, 16 - aciertos))
                    resultado = self.evaluar(prediccion, df)["resultados_modalidad"][0]
                    self.assertEqual(bool(app.formatear_premio_historial(resultado)), aciertos == categoria)

    def test_no_reutiliza_premios_de_otra_fecha(self):
        df = self.cargar_reales("2026-10-28")
        resultado = self.evaluar([7, 25, 32, 33, 1, 3], df)["resultados_modalidad"][0]
        self.assertTrue(resultado["tiene_premio"])
        self.assertIsNone(resultado["premio_unitario"])
        self.assertIn("no disponible", app.formatear_premio_historial(resultado))

    def test_importe_formateado_y_sin_multiplicar_plus(self):
        resultado = self.evaluar([7, 25, 32, 33, 1, 3])["resultados_modalidad"][0]
        self.assertEqual(
            app.formatear_premio_historial(resultado),
            "4 aciertos | Premio: $ 13.803,47",
        )

    def test_premios_persisten_al_cambiar_sorteo(self):
        nuevos = copy.deepcopy(self.pozos)
        nuevos["Meta"]["fecha"] = "2026-10-28"
        nuevos["Premios"]["Tradicional"]["4"]["premio_unitario"] = "15000.00"
        nuevos.pop("Historial_premios")
        app.guardar_pozos_loto_json(nuevos)
        with self.ruta.open(encoding="utf-8") as f:
            guardados = json.load(f)
        historico = guardados["Historial_premios"]
        self.assertEqual(historico["2026-10-24"]["Premios"]["Tradicional"]["4"]["premio_unitario"], "13803.47")
        self.assertEqual(historico["2026-10-28"]["Premios"]["Tradicional"]["4"]["premio_unitario"], "15000.00")

    def test_quini_conserva_coincidencias_y_reconoce_categoria_premiada(self):
        df = pd.DataFrame([{
            "fecha": date(2026, 10, 24), "modalidad": "Tradicional",
            "numeros_real": (7, 25, 32, 33, 37, 43), "numero_plus_real": pd.NA,
        }])
        resultado = self.evaluar([7, 25, 32, 33, 1, 3], df)["resultados_modalidad"][0]
        self.assertEqual(resultado, {
            "modalidad": "Tradicional", "aciertos": 4, "coincidencias": [7, 25, 32, 33],
            "tiene_premio": True, "premio_unitario": None, "vacante": False,
        })

    def test_completar_historial_consulta_cada_fecha_una_vez(self):
        entry = {
            "juego": "Loto", "timestamp": "2026-10-23 12:00:00",
            "prediccion": [7, 25, 32, 33, 1, 3],
        }
        nuevos = copy.deepcopy(self.pozos)
        nuevos["Meta"]["fecha"] = "2026-10-28"
        df = self.cargar_reales("2026-10-28")
        with patch.object(app.st, "session_state", {"historial": [entry, entry]}), \
                patch.object(app, "cargar_resultados_reales_historial", return_value=df), \
                patch.object(app, "obtener_premios_loto_por_fecha", return_value=nuevos) as obtener:
            app.actualizar_premios_historial(self.pozos, 'loto')
            app.actualizar_premios_historial(self.pozos, 'loto')
            obtener.assert_called_once_with("2026-10-28")
        with self.ruta.open(encoding="utf-8") as f:
            guardados = json.load(f)
        self.assertEqual(guardados["Meta"]["fecha"], "2026-10-24")
        self.assertIn("2026-10-28", guardados["Historial_premios"])

    def test_error_de_consulta_historica_se_informa(self):
        entry = {
            "juego": "Loto", "timestamp": "2026-10-23 12:00:00",
            "prediccion": [7, 25, 32, 33, 1, 3],
        }
        df = self.cargar_reales("2026-10-28")
        with patch.object(app.st, "session_state", {"historial": [entry]}), \
                patch.object(app, "cargar_resultados_reales_historial", return_value=df), \
                patch.object(app, "obtener_premios_loto_por_fecha", side_effect=requests.HTTPError("404")):
            with self.assertRaisesRegex(ValueError, "2026-10-28"):
                app.actualizar_premios_historial(self.pozos, 'loto')
        with self.ruta.open(encoding="utf-8") as f:
            self.assertIn("2026-10-24", json.load(f)["Historial_premios"])


if __name__ == "__main__":
    unittest.main()
