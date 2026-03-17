# ==============================================================
# PARTE 5: PRUEBAS DE CARGA AL INICIAR SISTEMA
# Archivo : tests/pruebas_carga.py
# Motor   : unittest (biblioteca estándar de Python)
# Ejecutar: python tests/pruebas_carga.py
#        ó: python -m pytest tests/pruebas_carga.py -v
# ==============================================================

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from consulta import (
    inicializar_base_de_datos,
    obtener_todas_las_salas,
    obtener_sala_por_codigo,
    obtener_salas_disponibles,
    buscar_salas,
    filtrar_por_tipo,
    obtener_estadisticas,
)

# Inicializar BD antes de cualquier prueba
inicializar_base_de_datos()


# ════════════════════════════════════════════════════════════
# BLOQUE 1 — Carga de base de datos
# ════════════════════════════════════════════════════════════
class TestCargaBaseDeDatos(unittest.TestCase):

    def test_01_retorna_exactamente_3_salas(self):
        """La BD debe contener exactamente 3 salas al iniciarse."""
        salas = obtener_todas_las_salas()
        self.assertEqual(len(salas), 3,
            f"Se esperaban 3 salas, se obtuvieron {len(salas)}")

    def test_02_cada_sala_tiene_campos_requeridos(self):
        """Cada sala debe tener: id, nombre, codigo, tipo, disponible."""
        campos = {"id", "nombre", "codigo", "tipo", "disponible"}
        for s in obtener_todas_las_salas():
            for campo in campos:
                self.assertIn(campo, s,
                    f"La sala id={s.get('id')} no tiene el campo '{campo}'")

    def test_03_ningun_nombre_o_codigo_vacio(self):
        """Ningún nombre ni código debe ser cadena vacía."""
        for s in obtener_todas_las_salas():
            self.assertTrue(s["nombre"].strip(),
                f"Sala id={s['id']} tiene nombre vacío")
            self.assertTrue(s["codigo"].strip(),
                f"Sala id={s['id']} tiene código vacío")

    def test_04_disponible_solo_contiene_0_o_1(self):
        """El campo disponible solo debe contener 0 o 1."""
        for s in obtener_todas_las_salas():
            self.assertIn(s["disponible"], (0, 1),
                f"Sala id={s['id']}: valor inválido en 'disponible': {s['disponible']}")


# ════════════════════════════════════════════════════════════
# BLOQUE 2 — Consultas específicas
# ════════════════════════════════════════════════════════════
class TestConsultasEspecificas(unittest.TestCase):

    def test_05_codigo_A101_retorna_aula_101(self):
        """Código A101 debe corresponder a 'Aula 101'."""
        sala = obtener_sala_por_codigo("A101")
        self.assertEqual(sala["nombre"], "Aula 101")

    def test_06_codigo_A303_es_tipo_aula(self):
        """A303 debe existir, llamarse 'Aula 303' y ser de tipo aula."""
        sala = obtener_sala_por_codigo("A303")
        self.assertIsNotNone(sala)
        self.assertEqual(sala["nombre"], "Aula 303")
        self.assertEqual(sala["tipo"], "aula")

    def test_07_codigo_inexistente_lanza_ValueError(self):
        """Un código inexistente debe lanzar ValueError."""
        with self.assertRaises(ValueError):
            obtener_sala_por_codigo("XXXX99")

    def test_08_hay_exactamente_2_salas_disponibles(self):
        """Exactamente 2 salas deben estar disponibles al inicio."""
        disponibles = obtener_salas_disponibles()
        self.assertEqual(len(disponibles), 2,
            f"Se esperaban 2, se obtuvieron {len(disponibles)}")

    def test_09_A303_esta_ocupada(self):
        """Aula 303 debe aparecer como ocupada (disponible=0)."""
        sala = obtener_sala_por_codigo("A303")
        self.assertEqual(sala["disponible"], 0)
