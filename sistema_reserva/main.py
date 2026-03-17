# ==============================================================
# PUNTO DE ENTRADA PRINCIPAL
# Archivo : main.py
# Ejecutar: python main.py
# ==============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consulta import inicializar_base_de_datos
from visualizacion import VentanaPrincipal


def main():
    # 1. Inicializar base de datos (crea archivo .db si no existe)
    print("🔧 Inicializando base de datos SQLite...")
    inicializar_base_de_datos()
    print("✅ Base de datos lista.")

    # 2. Lanzar la interfaz gráfica Tkinter
    print("🚀 Abriendo interfaz gráfica...\n")
    app = VentanaPrincipal()
    app.mainloop()


if __name__ == "__main__":
    main()