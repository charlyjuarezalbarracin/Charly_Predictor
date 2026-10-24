import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app import formatear_resumen_quini


RAIZ = Path(__file__).resolve().parents[1]


class TestResumenQuini(unittest.TestCase):
    def setUp(self):
        self.csv = RAIZ / 'data' / 'quini6_historico.csv'
        historico = pd.read_csv(self.csv)
        self.datos = historico[historico['fecha'] == '2026-10-21'].copy()

    def resumen(self):
        with patch('app.pd.read_csv', return_value=self.datos):
            return formatear_resumen_quini(self.csv)

    def test_formato_y_numeros_ordenados_ascendente(self):
        detalle, linea = self.resumen()
        self.assertEqual(detalle, 'Fecha 21/10/2026')
        self.assertEqual(
            linea,
            'Tradicional 04-05-32-39-40-44 | La segunda 04-20-21-24-42-45 | '
            'Revancha 01-02-11-14-28-33 | Siempre sale 13-21-39-42-43-45',
        )

    def test_fecha_incompleta_reporta_error(self):
        self.datos = self.datos.iloc[:3]
        with self.assertRaisesRegex(ValueError, 'cuatro modalidades'):
            self.resumen()

    def test_historico_vacio_reporta_error(self):
        self.datos = self.datos.iloc[:0]
        with self.assertRaisesRegex(ValueError, 'no contiene sorteos'):
            self.resumen()

    def test_numeros_invalidos_reportan_error(self):
        self.datos.loc[self.datos.index[0], 'num1'] = 46
        with self.assertRaisesRegex(ValueError, 'numeros invalidos'):
            self.resumen()


if __name__ == '__main__':
    unittest.main()
