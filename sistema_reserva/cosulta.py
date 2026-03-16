# ==============================================================
# PARTE 4: MOSTRAR NOMBRE O CÓDIGO DE SALA
# Archivo : ui/mostrar_sala.py
# Función : Utilidades para formatear y mostrar datos de salas
# ==============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from consulta import (
    obtener_todas_las_salas,
    obtener_sala_por_codigo,
    buscar_salas,
)


# ── Mostrar nombre y código de todas las salas ───────────────
def mostrar_listado_nombres_codigos():
    """Imprime en consola una tabla con nombre y código de cada sala."""
    salas = obtener_todas_las_salas()

    linea = "─" * 58
    print(f"\n┌{linea}┐")
    print(f"│{'LISTADO DE SALAS REGISTRADAS':^58}│")
    print(f"├{'─'*4}┬{'─'*30}┬{'─'*10}┬{'─'*11}┤")
    print(f"│{'ID':^4}│{'NOMBRE':^30}│{'CÓDIGO':^10}│{'ESTADO':^11}│")
    print(f"├{'─'*4}┼{'─'*30}┼{'─'*10}┼{'─'*11}┤")

    for s in salas:
        id_     = str(s["id"]).center(4)
        nombre  = s["nombre"][:28].ljust(30)
        codigo  = s["codigo"].center(10)
        estado  = "Disponible" if s["disponible"] else "Ocupada   "
        print(f"│{id_}│ {nombre}│{codigo}│ {estado}│")

    print(f"└{'─'*4}┴{'─'*30}┴{'─'*10}┴{'─'*11}┘")
    print(f"  Total: {len(salas)} salas registradas\n")


# ── Buscar y mostrar sala por código ─────────────────────────
def mostrar_nombre_por_codigo(codigo: str):
    """Busca una sala por código y muestra su nombre y detalles."""
    try:
        sala = obtener_sala_por_codigo(codigo)
        print(f"\n✅ Sala encontrada:")
        print(f"   Nombre    : {sala['nombre']}")
        print(f"   Código    : {sala['codigo']}")
        print(f"   Tipo      : {sala['tipo'].capitalize()}")
        print(f"   Disponible: {'Sí' if sala['disponible'] else 'No'}\n")
        return sala
    except ValueError as e:
        print(f"\n❌ {e}\n")
        return None
# ── Formatear info de una sala para mostrar en la UI ─────────
def formatear_info_sala(sala: dict) -> dict:
    """Devuelve un dict listo para mostrar en etiquetas Tkinter."""
    return {
        "encabezado": f"{sala['nombre']}   [{sala['codigo']}]",
        "tipo":       sala["tipo"].capitalize(),
        "estado":     "✅ Disponible" if sala["disponible"] else "🔴 Ocupada",
    }


# ── Buscar y mostrar coincidencias ────────────────────────────
def buscar_y_mostrar(termino: str):
    """Busca salas por nombre o código e imprime los resultados."""
    resultados = buscar_salas(termino)

    if not resultados:
        print(f'⚠️  No se encontraron salas con: "{termino}"')
        return []

    print(f'\n🔍 Resultados para: "{termino}" ({len(resultados)} encontradas)\n')
    for s in resultados:
        estado = "✅" if s["disponible"] else "🔴"
        print(f"  {estado}  {s['nombre']:<32}  Código: {s['codigo']}")
    print()
    return resultados


# ── Demo al ejecutar directamente ────────────────────────────
if __name__ == "__main__":
    mostrar_listado_nombres_codigos()
    mostrar_nombre_por_codigo("LAB01")
    buscar_y_mostrar("sala")