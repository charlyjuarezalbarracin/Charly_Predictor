import unittest

from app import formatear_numeros_loto


class TestResumenLoto(unittest.TestCase):
    def test_numeros_ordenados_ascendente(self):
        self.assertEqual(
            formatear_numeros_loto([6, 32, 17, 42, 4, 18]),
            '04-06-17-18-32-42',
        )

    def test_cantidad_incorrecta_retorna_none(self):
        self.assertIsNone(formatear_numeros_loto([6, 32, 17]))

    def test_valor_no_numerico_retorna_none(self):
        self.assertIsNone(formatear_numeros_loto([6, 32, 17, 42, 4, 'x']))


if __name__ == '__main__':
    unittest.main()
