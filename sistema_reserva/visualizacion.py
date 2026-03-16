# ==============================================================
# PARTE 2: DISEÑAR INTERFAZ DE VISUALIZACIÓN
# PARTE 3: LISTADO DE SALAS REGISTRADAS
# Archivo : ui/ui_visualizacion.py
# Motor   : Tkinter + ttk
# Diseño  : Dashboard profesional — sidebar oscuro, tarjetas
#           KPI, tabla con zebra-striping, panel de detalle
#           lateral, tooltips y hover interactivo.
# ==============================================================

import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from consulta import (
    obtener_todas_las_salas,
    buscar_salas,
    filtrar_por_tipo,
    obtener_estadisticas,
)

# ════════════════════════════════════════════════════════════
#  PALETA DE COLORES — Sistema de diseño unificado
# ════════════════════════════════════════════════════════════
C = {
    # Fondos estructurales
    "bg_app":       "#0f172a",   # azul marino oscuro — fondo global
    "bg_sidebar":   "#1e293b",   # sidebar oscuro
    "bg_content":   "#f1f5f9",   # área de contenido clara
    "bg_card":      "#ffffff",   # tarjetas blancas
    "bg_table_alt": "#f8fafc",   # fila alterna de la tabla
    "bg_header":    "#ffffff",   # barra superior

    # Colores de acción principal
    "primary":      "#2563eb",
    "primary_dark": "#1d4ed8",
    "primary_glow": "#dbeafe",
    "primary_text": "#1e40af",

    # Semáforo de estado
    "green":        "#16a34a",
    "green_bg":     "#dcfce7",
    "amber":        "#d97706",
    "amber_bg":     "#fef3c7",
    "red":          "#dc2626",
    "red_bg":       "#fee2e2",

    # Tipografía
    "text_white":   "#f8fafc",
    "text_1":       "#0f172a",
    "text_2":       "#475569",
    "text_3":       "#94a3b8",
    "text_sidebar": "#cbd5e1",

    # Bordes y separadores
    "border":       "#e2e8f0",

    # Sidebar estados
    "sid_active":   "#2563eb",
    "sid_hover":    "#334155",
}

# ── Fuentes ──────────────────────────────────────────────────
# Segoe UI disponible en Windows; degrada a Helvetica en macOS/Linux
F_DISPLAY = ("Segoe UI", 20, "bold")
F_HEADING = ("Segoe UI", 11, "bold")
F_BODY    = ("Segoe UI", 10)
F_BOLD    = ("Segoe UI", 10, "bold")
F_SMALL   = ("Segoe UI",  9)
F_MICRO   = ("Segoe UI",  8)
F_KPI     = ("Segoe UI", 26, "bold")
F_NAV     = ("Segoe UI", 10, "bold")
F_CODE    = ("Consolas",  10, "bold")

# Texto placeholder de búsqueda
PLACEHOLDER = "Buscar sala por nombre o código…"


# ════════════════════════════════════════════════════════════
#  COMPONENTE: Tooltip flotante
# ════════════════════════════════════════════════════════════
class Tooltip:
    """Muestra una pequeña etiqueta flotante al pasar el cursor."""

    def __init__(self, widget, texto):
        self.widget = widget
        self.texto  = texto
        self.ventana = None
        widget.bind("<Enter>", self._mostrar)
        widget.bind("<Leave>", self._ocultar)

    def _mostrar(self, _=None):
        x = self.widget.winfo_rootx() + 22
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.ventana = tk.Toplevel(self.widget)
        self.ventana.wm_overrideredirect(True)
        self.ventana.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.ventana, text=self.texto,
            font=F_SMALL, bg="#1e293b", fg="#f8fafc",
            relief="flat", padx=10, pady=6
        ).pack()

    def _ocultar(self, _=None):
        if self.ventana:
            self.ventana.destroy()
            self.ventana = None


# ════════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ════════════════════════════════════════════════════════════
class VentanaPrincipal(tk.Tk):
    """
    Ventana raíz de la aplicación.
    Estructura:
        ┌──────────┬─────────────────────────────────┐
        │          │  Header (breadcrumb + acciones)  │
        │ Sidebar  ├─────────────────────────────────┤
        │          │  Título + KPIs + Toolbar         │
        │          ├──────────────────────┬──────────┤
        │          │  Tabla de salas      │  Detalle │
        └──────────┴──────────────────────┴──────────┘
    """

    def __init__(self):
        super().__init__()
        self.title("Sistema de Reservas de Salas")
        self.geometry("1180x730")
        self.minsize(940, 620)
        self.configure(bg=C["bg_app"])

        # Estado interno
        self._filtro_activo = "todas"
        self._filtro_btns   = {}
        self._orden_desc    = {}   # columna → bool (orden descendente)

        self._aplicar_estilos_ttk()
        self._construir_layout()

    # ────────────────────────────────────────────────────────
    #  ESTILOS TTK
    # ────────────────────────────────────────────────────────
    def _aplicar_estilos_ttk(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        # Tabla
        s.configure(
            "Pro.Treeview",
            background=C["bg_card"],
            foreground=C["text_1"],
            fieldbackground=C["bg_card"],
            rowheight=46,
            font=F_BODY,
            borderwidth=0,
            relief="flat",
        )
        s.configure(
            "Pro.Treeview.Heading",
            background=C["bg_content"],
            foreground=C["text_2"],
            font=F_HEADING,
            relief="flat",
            borderwidth=0,
            padding=(12, 12),
        )
        s.map(
            "Pro.Treeview",
            background=[("selected", C["primary_glow"])],
            foreground=[("selected", C["primary_text"])],
        )

        # Scrollbar delgado
        s.configure(
            "Thin.Vertical.TScrollbar",
            troughcolor=C["bg_content"],
            background=C["border"],
            borderwidth=0,
            arrowsize=0,
            width=5,
        )

    # ────────────────────────────────────────────────────────
    #  LAYOUT RAÍZ
    # ────────────────────────────────────────────────────────
    def _construir_layout(self):
        # Sidebar fijo izquierdo
        self.sidebar = tk.Frame(self, bg=C["bg_sidebar"], width=234)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._construir_sidebar()

        # Columna derecha (header + contenido)
        derecha = tk.Frame(self, bg=C["bg_content"])
        derecha.pack(side="left", fill="both", expand=True)
        self._construir_header(derecha)
        self._construir_cuerpo(derecha)

    # ════════════════════════════════════════════════════════
    #  SIDEBAR
    # ════════════════════════════════════════════════════════
    def _construir_sidebar(self):
        sb = self.sidebar

        # ── Logo ──────────────────────────────────────────
        lf = tk.Frame(sb, bg=C["bg_sidebar"])
        lf.pack(fill="x", pady=(28, 18), padx=20)

        icon_box = tk.Frame(lf, bg=C["primary"], width=44, height=44)
        icon_box.pack_propagate(False)
        icon_box.pack(side="left")
        tk.Label(
            icon_box, text="🏫", font=("Segoe UI", 18),
            bg=C["primary"], fg="white"
        ).pack(expand=True)

        nombre_frame = tk.Frame(lf, bg=C["bg_sidebar"])
        nombre_frame.pack(side="left", padx=(12, 0))
        tk.Label(
            nombre_frame, text="ReservaSalas",
            font=("Segoe UI", 12, "bold"),
            bg=C["bg_sidebar"], fg=C["text_white"]
        ).pack(anchor="w")
        tk.Label(
            nombre_frame, text="Panel administrativo",
            font=F_MICRO, bg=C["bg_sidebar"], fg=C["text_3"]
        ).pack(anchor="w")

        # Separador
        tk.Frame(sb, bg="#334155", height=1).pack(fill="x", padx=20, pady=(0, 14))

        # ── Menú principal ────────────────────────────────
        tk.Label(
            sb, text="MENÚ PRINCIPAL", font=F_MICRO,
            bg=C["bg_sidebar"], fg=C["text_3"], padx=20
        ).pack(anchor="w", pady=(0, 4))

        nav_items = [
            ("🏠", "Dashboard",   False),
            ("🚪", "Salas",        True),
            ("📅", "Reservas",    False),
            ("👥", "Usuarios",    False),
            ("📊", "Reportes",    False),
        ]
        for ico, nombre, activo in nav_items:
            self._nav_btn(sb, ico, nombre, activo)

        # Separador
        tk.Frame(sb, bg="#334155", height=1).pack(fill="x", padx=20, pady=14)
        tk.Label(
            sb, text="SISTEMA", font=F_MICRO,
            bg=C["bg_sidebar"], fg=C["text_3"], padx=20
        ).pack(anchor="w", pady=(0, 4))

        for ico, nombre in [("⚙️", "Configuración"), ("❓", "Ayuda")]:
            self._nav_btn(sb, ico, nombre, False)

        # ── Avatar (anclado al fondo) ─────────────────────
        av_frame = tk.Frame(sb, bg=C["bg_sidebar"])
        av_frame.pack(side="bottom", fill="x", pady=20, padx=20)
        tk.Frame(av_frame, bg="#334155", height=1).pack(fill="x", pady=(0, 14))

        row = tk.Frame(av_frame, bg=C["bg_sidebar"])
        row.pack(fill="x")

        av_circle = tk.Frame(row, bg=C["primary"], width=38, height=38)
        av_circle.pack_propagate(False)
        av_circle.pack(side="left")
        tk.Label(
            av_circle, text="AD", font=("Segoe UI", 10, "bold"),
            bg=C["primary"], fg="white"
        ).pack(expand=True)

        av_info = tk.Frame(row, bg=C["bg_sidebar"])
        av_info.pack(side="left", padx=(10, 0))
        tk.Label(
            av_info, text="Administrador",
            font=("Segoe UI", 9, "bold"),
            bg=C["bg_sidebar"], fg=C["text_white"]
        ).pack(anchor="w")
        tk.Label(
            av_info, text="admin@institución.edu",
            font=F_MICRO, bg=C["bg_sidebar"], fg=C["text_3"]
        ).pack(anchor="w")

    def _nav_btn(self, parent, ico, texto, activo):
        """Crea un ítem de navegación en el sidebar."""
        bg = C["sid_active"] if activo else C["bg_sidebar"]
        fg = C["text_white"]  if activo else C["text_sidebar"]

        row = tk.Frame(parent, bg=bg, cursor="hand2")
        row.pack(fill="x", padx=10, pady=1)

        # Barra lateral de selección
        acento = tk.Frame(row, bg="white" if activo else bg, width=4)
        acento.pack(side="left", fill="y")

        tk.Label(
            row, text=ico, font=("Segoe UI", 12),
            bg=bg, fg=fg, width=2
        ).pack(side="left", padx=(10, 6), pady=10)

        tk.Label(row, text=texto, font=F_NAV, bg=bg, fg=fg).pack(side="left")

        if not activo:
            row.bind("<Enter>",
                     lambda e, r=row, a=acento:
                     (r.config(bg=C["sid_hover"]), a.config(bg=C["sid_hover"])))
            row.bind("<Leave>",
                     lambda e, r=row, a=acento:
                     (r.config(bg=C["bg_sidebar"]), a.config(bg=C["bg_sidebar"])))
 