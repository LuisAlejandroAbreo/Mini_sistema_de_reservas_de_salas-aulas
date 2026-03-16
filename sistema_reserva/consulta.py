# ==============================================================
# PARTE 1: CREAR CONSULTA A BASE DE DATOS
# Archivo : database/db_consulta.py
# Motor   : SQLite3 (base de datos local, archivo .db)
# ==============================================================

import sqlite3
import os

# Ruta del archivo de base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "reservas.db")


# ── Conexión ────────────────────────────────────────────────
def obtener_conexion():
    """Retorna una conexión SQLite con Row como factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Crear tabla e insertar datos iniciales ───────────────────
def inicializar_base_de_datos():
    """Crea la tabla 'salas' y carga los datos de ejemplo si está vacía.
    Si el archivo .db está corrupto, lo elimina y lo recrea automáticamente."""
    # ── Verificar integridad del archivo .db ─────────────────
    if os.path.exists(DB_PATH):
        try:
            test = sqlite3.connect(DB_PATH)
            test.execute("PRAGMA integrity_check")
            test.close()
        except sqlite3.DatabaseError:
            print("⚠️  Base de datos corrupta detectada — recreando automáticamente...")
            test.close()
            os.remove(DB_PATH)
            print("🗑️  Archivo corrupto eliminado.")

    conn   = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            codigo      TEXT    NOT NULL UNIQUE,
            tipo        TEXT    NOT NULL,
            disponible  INTEGER NOT NULL DEFAULT 1,
            horario     TEXT    NOT NULL DEFAULT '6:00 AM - 8:00 PM'
        )
    """)

    # Migración: agregar columna horario si la BD ya existía sin ella
    try:
        cursor.execute(
            "ALTER TABLE salas ADD COLUMN horario TEXT NOT NULL DEFAULT '6:00 AM - 8:00 PM'"
        )
    except Exception:
        pass  # columna ya existe

    # Solo insertar si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM salas")
    if cursor.fetchone()[0] == 0:
        datos_iniciales = [
            ("Aula 101", "A101", "aula", 1, "6:00 AM - 8:00 PM"),
            ("Aula 202", "A202", "aula", 1, "6:00 AM - 8:00 PM"),
            ("Aula 303", "A303", "aula", 0, "6:00 AM - 8:00 PM"),
        ]
        cursor.executemany(
            "INSERT INTO salas (nombre, codigo, tipo, disponible, horario) VALUES (?,?,?,?,?)",
            datos_iniciales
        )

    conn.commit()
    conn.close()
# ── CONSULTA 1: Todas las salas ──────────────────────────────
def obtener_todas_las_salas():
    """Retorna la lista completa de salas registradas."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salas ORDER BY id")
    filas  = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas


# ── CONSULTA 2: Sala por código ──────────────────────────────
def obtener_sala_por_codigo(codigo: str):
    """Retorna una sala dado su código exacto (insensible a mayúsculas)."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM salas WHERE LOWER(codigo) = LOWER(?)", (codigo,)
    )
    fila = cursor.fetchone()
    conn.close()
    if fila is None:
        raise ValueError(f"No se encontró ninguna sala con el código: {codigo}")
    return dict(fila)


# ── CONSULTA 3: Salas disponibles ────────────────────────────
def obtener_salas_disponibles():
    """Retorna solo las salas con disponible = 1."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salas WHERE disponible = 1 ORDER BY id")
    filas  = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas


# ── CONSULTA 4: Búsqueda libre (nombre o código) ─────────────
def buscar_salas(termino: str):
    """Busca salas cuyo nombre O código contenga el término dado."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    like   = f"%{termino.lower()}%"
    cursor.execute(
        """SELECT * FROM salas
           WHERE LOWER(nombre) LIKE ?
              OR LOWER(codigo) LIKE ?
           ORDER BY id""",
        (like, like)
    )
    filas = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas 