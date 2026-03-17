# ==============================================================
# PARTE 1: CREAR CONSULTA A BASE DE DATOS
# Archivo : database/db_consulta.py
# Motor   : SQLite3 (base de datos local, archivo .db)
# ==============================================================
 
import sqlite3
import os
from datetime import datetime
 
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
 
    # ── Tabla reservas ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sala_id       INTEGER NOT NULL,
            sala_nombre   TEXT    NOT NULL,
            sala_codigo   TEXT    NOT NULL,
            fecha         TEXT    NOT NULL,
            hora_inicio   TEXT    NOT NULL,
            hora_fin      TEXT    NOT NULL,
            responsable   TEXT    NOT NULL,
            descripcion   TEXT    NOT NULL DEFAULT '',
            estado        TEXT    NOT NULL DEFAULT 'activa',
            FOREIGN KEY (sala_id) REFERENCES salas(id)
        )
    """)
 
    conn.commit()
    conn.close()
 
 
# ════════════════════════════════════════════════════════════
#  RESERVAS — Consultas y acciones
# ════════════════════════════════════════════════════════════
 
def obtener_todas_las_reservas():
    """Retorna la lista completa de reservas ordenadas por fecha y hora."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservas ORDER BY fecha DESC, hora_inicio DESC"
    )
    filas = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas
 
 
def obtener_reserva_por_id(reserva_id: int):
    """Retorna una reserva dado su id. Lanza ValueError si no existe."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
    fila = cursor.fetchone()
    conn.close()
    if fila is None:
        raise ValueError(f"No se encontró ninguna reserva con id: {reserva_id}")
    return dict(fila)
 
 
def buscar_reservas(termino: str):
    """Busca reservas por sala, responsable o descripción."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    like   = f"%{termino.lower()}%"
    cursor.execute(
        """SELECT * FROM reservas
           WHERE LOWER(sala_nombre)  LIKE ?
              OR LOWER(sala_codigo)  LIKE ?
              OR LOWER(responsable)  LIKE ?
              OR LOWER(descripcion)  LIKE ?
              OR fecha               LIKE ?
           ORDER BY fecha DESC, hora_inicio DESC""",
        (like, like, like, like, like)
    )
    filas = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas
 
 
def filtrar_reservas_por_estado(estado: str):
    """Filtra reservas por estado: 'activa', 'cancelada' o 'finalizada'."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservas WHERE LOWER(estado) = LOWER(?) ORDER BY fecha DESC",
        (estado,)
    )
    filas = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas
 
 
def obtener_estadisticas_reservas():
    """Retorna dict con total, activas, canceladas y finalizadas."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reservas")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reservas WHERE estado = 'activa'")
    activas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reservas WHERE estado = 'cancelada'")
    canceladas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reservas WHERE estado = 'finalizada'")
    finalizadas = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "activas": activas,
        "canceladas": canceladas,
        "finalizadas": finalizadas,
    }
# En consulta.py
 
def actualizar_estado_salas_y_reservas():
    """
    Sincroniza el estado de las salas basándose en las reservas activas
    y la hora actual del sistema.
    """
    ahora = datetime.now()
    fecha_actual = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    try:
        # 1. Finalizar automáticamente reservas que ya pasaron
        cursor.execute("""
            UPDATE reservas 
            SET estado = 'finalizada' 
            WHERE estado = 'activa' 
            AND (fecha < ? OR (fecha = ? AND hora_fin <= ?))
        """, (fecha_actual, fecha_actual, hora_actual))
        
        # 2. Resetear todas las salas a disponibles (1)
        cursor.execute("UPDATE salas SET disponible = 1")
        
        # 3. Marcar como ocupadas (0) solo las salas que tienen una reserva 
        # activa en este preciso momento (fecha hoy y hora actual entre inicio y fin)
        cursor.execute("""
            UPDATE salas 
            SET disponible = 0 
            WHERE id IN (
                SELECT DISTINCT sala_id 
                FROM reservas 
                WHERE estado = 'activa' 
                AND fecha = ? 
                AND ? >= hora_inicio 
                AND ? < hora_fin
            )
        """, (fecha_actual, hora_actual, hora_actual))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error actualizando estados: {e}")
    finally:
        conn.close()
 
# Modificar crear_reserva para que llame a esta validación
def crear_reserva_actualizada(datos):
    # ... lógica existente de inserción ...
    # Después de insertar, actualizamos estados inmediatamente
    actualizar_estado_salas_y_reservas()
 
def crear_reserva(sala_id: int, sala_nombre: str, sala_codigo: str,
                  fecha: str, hora_inicio: str, hora_fin: str,
                  responsable: str, descripcion: str = ""):
    # 1. Validar formato de fecha (YYYY-MM-DD)
    
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        if fecha_dt < datetime.now().date():
            raise ValueError("No se pueden hacer reservas en fechas pasadas.")
    except ValueError:
        raise ValueError("Formato de fecha inválido. Use AAAA-MM-DD.")
 
    # 2. Validar formato, rango permitido (06:00–20:00) y que hora_fin > hora_inicio
    HORA_APERTURA = datetime.strptime("06:00", "%H:%M")
    HORA_CIERRE   = datetime.strptime("20:00", "%H:%M")
    try:
        h_ini = datetime.strptime(hora_inicio, "%H:%M")
        h_fin = datetime.strptime(hora_fin,    "%H:%M")
    except ValueError:
        raise ValueError("Formato de hora inválido. Use HH:MM en formato 24 horas.")
 
    if h_fin <= h_ini:
        raise ValueError("La hora de finalización debe ser mayor a la de inicio.")
 
    if h_ini < HORA_APERTURA or h_fin > HORA_CIERRE:
        raise ValueError(
            "El horario de reservas es de 06:00 a 20:00. "
            "No se pueden registrar reservas fuera de ese rango."
        )
 
    # 3. Validar disponibilidad de la sala y cruces
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Verificar si la sala ya está ocupada en ese horario
    query_cruce = """
        SELECT id FROM reservas 
        WHERE sala_id = ? AND fecha = ? AND estado = 'activa'
        AND ((hora_inicio < ? AND hora_fin > ?) OR (hora_inicio >= ? AND hora_inicio < ?))
    """
    cursor.execute(query_cruce, (sala_id, fecha, hora_fin, hora_inicio, hora_inicio, hora_fin))
    if cursor.fetchone():
        conn.close()
        raise ValueError("La sala ya tiene una reserva activa en este horario.")
 
    # ... proceder con el INSERT
    """Inserta una nueva reserva. Valida solapamiento de horarios.
 
    Retorna el id asignado si tiene éxito.
    Lanza ValueError si hay conflicto de horario o datos inválidos.
    """
    responsable = responsable.strip()
    descripcion = descripcion.strip()
 
    if not responsable:
        raise ValueError("El nombre del responsable no puede estar vacío.")
    if not fecha:
        raise ValueError("La fecha es obligatoria.")
    if not hora_inicio or not hora_fin:
        raise ValueError("Las horas de inicio y fin son obligatorias.")
    if hora_inicio >= hora_fin:
        raise ValueError("La hora de inicio debe ser anterior a la hora de fin.")
 
    conn   = obtener_conexion()
    cursor = conn.cursor()
    actualizar_estado_salas_y_reservas()
 
    # Verificar solapamiento en la misma sala y fecha
    cursor.execute(
        """SELECT id FROM reservas
           WHERE sala_id = ?
             AND fecha   = ?
             AND estado  != 'cancelada'
             AND hora_inicio < ?
             AND hora_fin    > ?""",
        (sala_id, fecha, hora_fin, hora_inicio)
    )
    if cursor.fetchone() is not None:
        conn.close()
        raise ValueError(
            f"Ya existe una reserva activa para '{sala_nombre}' "
            f"en esa fecha que se solapa con el horario indicado."
        )
 
    cursor.execute(
        """INSERT INTO reservas
           (sala_id, sala_nombre, sala_codigo, fecha,
            hora_inicio, hora_fin, responsable, descripcion, estado)
           VALUES (?,?,?,?,?,?,?,?,'activa')""",
        (sala_id, sala_nombre, sala_codigo, fecha,
         hora_inicio, hora_fin, responsable, descripcion),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id
 
    
 
 
def cancelar_reserva(reserva_id: int):
    """Cambia el estado de una reserva a 'cancelada'."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"No se encontró la reserva con id: {reserva_id}")
    conn.commit()
    conn.close()
 
 
# ── CONSULTA 1: Todas las salas ──────────────────────────────
def obtener_todas_las_salas():
    
    """Retorna la lista de salas, asegurando que el estado esté al día."""
    # LLAMADA CRÍTICA: Actualiza antes de consultar
    actualizar_estado_salas_y_reservas() 
    
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
    """Retorna solo las salas que no tienen reservas en curso ahora mismo."""
    actualizar_estado_salas_y_reservas()
    
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
# ── CONSULTA 5: Filtrar por tipo ─────────────────────────────
def filtrar_por_tipo(tipo: str):
    """Retorna las salas que coincidan con el tipo indicado."""
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM salas WHERE LOWER(tipo) = LOWER(?) ORDER BY id",
        (tipo,)
    )
    filas = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return filas
 
 
# ── CONSULTA 6: Estadísticas ──────────────────────────────────
def obtener_estadisticas():
    """Retorna un dict con total, disponibles y ocupadas."""
    actualizar_estado_salas_y_reservas()
    conn   = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM salas")
    total  = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM salas WHERE disponible = 1")
    disp   = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "disponibles": disp, "ocupadas": total - disp}
 
 
# ── ACCIÓN 1: Crear nueva sala ────────────────────────────────
def crear_sala(nombre: str, codigo: str, tipo: str,
               disponible: int = 1, horario: str = "6:00 AM - 8:00 PM"):
    """Inserta una nueva sala en la BD.
 
    Retorna el id asignado si tiene éxito.
    Lanza ValueError si el código ya existe o los datos son inválidos.
    """
    nombre  = nombre.strip()
    codigo  = codigo.strip().upper()
    tipo    = tipo.strip().lower()
 
    if not nombre:
        raise ValueError("El nombre de la sala no puede estar vacío.")
    if not codigo:
        raise ValueError("El código de la sala no puede estar vacío.")
    if tipo not in ("aula", "laboratorio", "sala"):
        raise ValueError(f"Tipo '{tipo}' no válido. Use: aula, laboratorio o sala.")
 
    conn   = obtener_conexion()
    cursor = conn.cursor()
 
    # Verificar que el código no se repita
    cursor.execute("SELECT id FROM salas WHERE LOWER(codigo) = LOWER(?)", (codigo,))
    if cursor.fetchone() is not None:
        conn.close()
        raise ValueError(f"Ya existe una sala con el código '{codigo}'.")
 
    cursor.execute(
        "INSERT INTO salas (nombre, codigo, tipo, disponible, horario) VALUES (?,?,?,?,?)",
        (nombre, codigo, tipo, disponible, horario),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id