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
    # ════════════════════════════════════════════════════════
    #  HEADER SUPERIOR
    # ════════════════════════════════════════════════════════
    def _construir_header(self, parent):
        hdr = tk.Frame(parent, bg=C["bg_header"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        # Línea divisoria inferior
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")

        # Breadcrumb izquierda
        bc = tk.Frame(hdr, bg=C["bg_header"])
        bc.pack(side="left", padx=32, fill="y")
        tk.Label(
            bc, text="Inicio  ›  ", font=F_SMALL,
            bg=C["bg_header"], fg=C["text_3"]
        ).pack(side="left")
        tk.Label(
            bc, text="Salas", font=("Segoe UI", 9, "bold"),
            bg=C["bg_header"], fg=C["primary"]
        ).pack(side="left")

        # Botones de acción derecha
        ac = tk.Frame(hdr, bg=C["bg_header"])
        ac.pack(side="right", padx=28)

        # Botón Nueva Sala
        btn_nueva = tk.Label(
            ac, text="   ＋  Nueva Sala   ",
            font=("Segoe UI", 9, "bold"),
            bg=C["primary"], fg="white",
            cursor="hand2", pady=9
        )
        btn_nueva.pack(side="right", padx=(10, 0))
        btn_nueva.bind("<Enter>", lambda e: btn_nueva.config(bg=C["primary_dark"]))
        btn_nueva.bind("<Leave>", lambda e: btn_nueva.config(bg=C["primary"]))
        Tooltip(btn_nueva, "Agregar una nueva sala al sistema")

        # Botón Exportar
        btn_exp = tk.Label(
            ac, text="   ↓  Exportar   ",
            font=F_SMALL, bg=C["bg_content"], fg=C["text_2"],
            cursor="hand2", pady=9,
            highlightbackground=C["border"],
            highlightthickness=1
        )
        btn_exp.pack(side="right")
        btn_exp.bind("<Enter>", lambda e: btn_exp.config(bg=C["border"]))
        btn_exp.bind("<Leave>", lambda e: btn_exp.config(bg=C["bg_content"]))
        Tooltip(btn_exp, "Exportar listado de salas a archivo")

    # ════════════════════════════════════════════════════════
    #  CUERPO PRINCIPAL
    # ════════════════════════════════════════════════════════
    def _construir_cuerpo(self, parent):
        pad = tk.Frame(parent, bg=C["bg_content"])
        pad.pack(fill="both", expand=True, padx=32, pady=28)

        # Título de sección
        self._construir_titulo(pad)

        # Tarjetas KPI
        self.frame_kpi = tk.Frame(pad, bg=C["bg_content"])
        self.frame_kpi.pack(fill="x", pady=(20, 22))
        self._construir_kpis()

        # Barra de búsqueda y filtros
        self._construir_toolbar(pad)

        # Tabla + panel de detalle (lado a lado)
        contenedor = tk.Frame(pad, bg=C["bg_content"])
        contenedor.pack(fill="both", expand=True, pady=(14, 0))
        self._construir_tabla(contenedor)
        self._construir_panel_detalle(contenedor)

        # Carga inicial de datos
        self._cargar_salas(obtener_todas_las_salas())

    # ── Título ────────────────────────────────────────────────
    def _construir_titulo(self, parent):
        fila = tk.Frame(parent, bg=C["bg_content"])
        fila.pack(fill="x")
        tk.Label(
            fila, text="Listado de Salas Registradas",
            font=F_DISPLAY, bg=C["bg_content"], fg=C["text_1"]
        ).pack(anchor="w")
        tk.Label(
            fila,
            text="Gestiona, consulta y administra las salas del sistema educativo",
            font=F_BODY, bg=C["bg_content"], fg=C["text_2"]
        ).pack(anchor="w", pady=(3, 0))

    # ════════════════════════════════════════════════════════
    #  TARJETAS KPI
    # ════════════════════════════════════════════════════════
    def _construir_kpis(self):
        """Construye (o reconstruye) las 4 tarjetas de estadísticas."""
        for w in self.frame_kpi.winfo_children():
            w.destroy()

        stats = obtener_estadisticas()
        total = max(stats["total"], 1)
        pct   = int(stats["disponibles"] / total * 100)

        definiciones = [
            ("Total Salas",    str(stats["total"]),       "🏢", C["primary"], C["primary_glow"]),
            ("Disponibles",    str(stats["disponibles"]), "✅", C["green"],   C["green_bg"]),
            ("Ocupadas",       str(stats["ocupadas"]),    "🔴", C["red"],     C["red_bg"]),
            ("Disponibilidad", f"{pct}%",                 "📊", C["amber"],   C["amber_bg"]),
        ]

        for titulo, valor, ico, color, ico_bg in definiciones:
            # Marco exterior de tarjeta
            card = tk.Frame(
                self.frame_kpi, bg=C["bg_card"],
                highlightbackground=C["border"],
                highlightthickness=1
            )
            card.pack(side="left", fill="both", expand=True, padx=(0, 14))

            inner = tk.Frame(card, bg=C["bg_card"], padx=20, pady=18)
            inner.pack(fill="both", expand=True)

            # Fila superior: número grande + ícono con fondo
            top = tk.Frame(inner, bg=C["bg_card"])
            top.pack(fill="x")

            # Ícono (cuadrado con fondo de color)
            ib = tk.Frame(top, bg=ico_bg, width=50, height=50)
            ib.pack_propagate(False)
            ib.pack(side="right")
            tk.Label(ib, text=ico, font=("Segoe UI", 20), bg=ico_bg).pack(expand=True)

            # Número KPI
            tk.Label(
                top, text=valor, font=F_KPI,
                bg=C["bg_card"], fg=color
            ).pack(side="left", anchor="w")

            # Etiqueta descriptiva
            tk.Label(
                inner, text=titulo, font=F_BODY,
                bg=C["bg_card"], fg=C["text_2"]
            ).pack(anchor="w", pady=(8, 0))

            # Barra de acento inferior (3px)
            tk.Frame(card, bg=color, height=3).pack(fill="x", side="bottom")

    # ════════════════════════════════════════════════════════
    #  TOOLBAR — búsqueda + filtros
    # ════════════════════════════════════════════════════════
    def _construir_toolbar(self, parent):
        bar = tk.Frame(parent, bg=C["bg_content"])
        bar.pack(fill="x")

        # ── Campo de búsqueda ──────────────────────────────
        search_wrap = tk.Frame(
            bar, bg=C["bg_card"],
            highlightbackground=C["border"],
            highlightthickness=1
        )
        search_wrap.pack(side="left", fill="x", expand=True, padx=(0, 12))

        tk.Label(
            search_wrap, text="🔍", font=("Segoe UI", 11),
            bg=C["bg_card"], fg=C["text_3"], padx=10
        ).pack(side="left")

        self.var_busqueda = tk.StringVar()
        self.entry = tk.Entry(
            search_wrap, textvariable=self.var_busqueda,
            font=F_BODY, bd=0, relief="flat",
            bg=C["bg_card"], fg=C["text_1"],
            insertbackground=C["primary"]
        )
        self.entry.pack(side="left", fill="both", expand=True, pady=11, padx=(0, 8))
        self._ph_set()

        self.entry.bind("<FocusIn>",  self._ph_clear)
        self.entry.bind("<FocusOut>", self._ph_restore)
        self.var_busqueda.trace_add("write", self._on_busqueda)

        # Botón limpiar búsqueda
        btn_clear = tk.Label(
            search_wrap, text=" ✕ ", font=F_SMALL,
            bg=C["bg_card"], fg=C["text_3"], cursor="hand2", padx=6
        )
        btn_clear.pack(side="right")
        btn_clear.bind("<Button-1>", self._limpiar_busqueda)
        Tooltip(btn_clear, "Limpiar búsqueda")

        # ── Grupo de filtros ───────────────────────────────
        fw = tk.Frame(
            bar, bg=C["bg_card"],
            highlightbackground=C["border"],
            highlightthickness=1
        )
        fw.pack(side="left")

        filtros = [
            ("Todas",        "todas"),
            ("Aula",         "aula"),
            ("Laboratorio",  "laboratorio"),
            ("Sala",         "sala"),
        ]
        for label, valor in filtros:
            btn = tk.Label(fw, text=label, font=F_SMALL, padx=14, pady=11, cursor="hand2")
            btn.pack(side="left")
            self._filtro_btns[valor] = btn
            btn.bind("<Button-1>", lambda e, v=valor: self._set_filtro(v))

        self._refrescar_filtro_ui()

        # Contador de resultados
        self.lbl_conteo = tk.Label(
            bar, text="", font=F_SMALL,
            bg=C["bg_content"], fg=C["text_3"]
        )
        self.lbl_conteo.pack(side="right")

    def _set_filtro(self, valor):
        self._filtro_activo = valor
        self._refrescar_filtro_ui()
        self._on_filtro()

    def _refrescar_filtro_ui(self):
        for v, btn in self._filtro_btns.items():
            if v == self._filtro_activo:
                btn.config(bg=C["primary"], fg="white")
            else:
                btn.config(bg=C["bg_card"], fg=C["text_2"])

    # ════════════════════════════════════════════════════════
    #  TABLA PRINCIPAL
    # ════════════════════════════════════════════════════════
    def _construir_tabla(self, parent):
        wrap = tk.Frame(
            parent, bg=C["bg_card"],
            highlightbackground=C["border"],
            highlightthickness=1
        )
        wrap.pack(side="left", fill="both", expand=True)

        # Cabecera de la tarjeta-tabla
        ch = tk.Frame(wrap, bg=C["bg_card"], pady=14)
        ch.pack(fill="x", padx=18)
        tk.Label(
            ch, text="Salas registradas",
            font=F_HEADING, bg=C["bg_card"], fg=C["text_1"]
        ).pack(side="left")
        self.lbl_pie = tk.Label(
            ch, text="", font=F_SMALL, bg=C["bg_card"], fg=C["text_3"]
        )
        self.lbl_pie.pack(side="right")

        # Línea divisoria
        tk.Frame(wrap, bg=C["border"], height=1).pack(fill="x")

        # Treeview
        cols = ("id", "nombre", "codigo", "tipo", "estado")
        self.tree = ttk.Treeview(
            wrap, columns=cols, show="headings",
            style="Pro.Treeview", selectmode="browse"
        )

        columnas_cfg = [
            ("id",     "#",                  50,  "center", False),
            ("nombre", "Nombre de la sala",  310, "w",      True),
            ("codigo", "Código",             120, "center", False),
            ("tipo",   "Tipo",               130, "center", False),
            ("estado", "Estado",             150, "center", False),
        ]
        for col, txt, ancho, ancla, stretch in columnas_cfg:
            self.tree.heading(col, text=txt,
                              command=lambda c=col: self._ordenar(c))
            self.tree.column(col, width=ancho, anchor=ancla, stretch=stretch)

        # Scrollbar vertical delgado
        sc = ttk.Scrollbar(
            wrap, orient="vertical",
            command=self.tree.yview,
            style="Thin.Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        # Tags de color semántico por estado
        self.tree.tag_configure("disponible", foreground=C["green"])
        self.tree.tag_configure("ocupada",    foreground=C["red"])
        # Fila impar con fondo ligeramente diferente (zebra striping)
        self.tree.tag_configure("impar",      background=C["bg_table_alt"])

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccion)
        self.tree.bind("<Motion>",
                       lambda e: self.tree.config(
                           cursor="hand2" if self.tree.identify_row(e.y) else ""))
    # ════════════════════════════════════════════════════════
    #  PANEL DETALLE LATERAL
    # ════════════════════════════════════════════════════════
    def _construir_panel_detalle(self, parent):
        self.panel = tk.Frame(
            parent, bg=C["bg_card"], width=295,
            highlightbackground=C["border"],
            highlightthickness=1
        )
        self.panel.pack(side="right", fill="y", padx=(14, 0))
        self.panel.pack_propagate(False)

        # Cabecera del panel
        ph = tk.Frame(self.panel, bg=C["bg_sidebar"], pady=14)
        ph.pack(fill="x")
        tk.Label(
            ph, text="Detalle de Sala",
            font=F_HEADING, bg=C["bg_sidebar"], fg=C["text_white"],
            padx=18
        ).pack(side="left")

        # Cuerpo dinámico
        self.det_body = tk.Frame(self.panel, bg=C["bg_card"])
        self.det_body.pack(fill="both", expand=True, padx=14, pady=12)
        self._det_vacio()

    def _det_vacio(self):
        """Muestra el estado vacío del panel de detalle."""
        for w in self.det_body.winfo_children():
            w.destroy()
        tk.Label(
            self.det_body,
            text="Selecciona una sala\npara ver sus detalles",
            font=F_BODY, bg=C["bg_card"], fg=C["text_3"],
            justify="center"
        ).pack(expand=True)

    def _det_sala(self, sala: dict):
        """Rellena el panel lateral con los datos de la sala seleccionada."""
        for w in self.det_body.winfo_children():
            w.destroy()

        disp      = bool(sala["disponible"])
        col_est   = C["green"]    if disp else C["red"]
        col_bg    = C["green_bg"] if disp else C["red_bg"]
        est_txt   = "Disponible"  if disp else "Ocupada"

        # Ícono grande
        ib = tk.Frame(self.det_body, bg=C["primary_glow"], width=56, height=56)
        ib.pack_propagate(False)
        ib.pack(pady=(0, 10))
        tk.Label(ib, text="🚪", font=("Segoe UI", 22), bg=C["primary_glow"]).pack(expand=True)

        # Nombre de la sala
        tk.Label(
            self.det_body, text=sala["nombre"],
            font=("Segoe UI", 11, "bold"),
            bg=C["bg_card"], fg=C["text_1"],
            wraplength=215, justify="center"
        ).pack()

        # Badge de estado
        tk.Label(
            self.det_body, text=f"  {est_txt}  ",
            font=F_SMALL, bg=col_bg, fg=col_est, pady=5
        ).pack(pady=(6, 10))

        # Separador
        tk.Frame(self.det_body, bg=C["border"], height=1).pack(fill="x", pady=(0, 10))

        # Campos de información
        estado_horario = "6:00 AM - 8:00 PM  ✅ Disponible" if disp else "6:00 AM - 8:00 PM  🔴 Ocupada"
        campos = [
            ("Código", sala["codigo"]),
            ("Tipo",   sala["tipo"].capitalize()),
            ("ID",     str(sala["id"])),
            ("Fecha",  estado_horario),
        ]
        for lbl, val in campos:
            fila = tk.Frame(self.det_body, bg=C["bg_card"])
            fila.pack(fill="x", pady=3)
            tk.Label(
                fila, text=lbl, font=F_SMALL,
                bg=C["bg_card"], fg=C["text_3"],
                width=7, anchor="w"
            ).pack(side="left")
            # Fecha lleva color semántico según disponibilidad
            fg_val = C["green"] if (lbl == "Fecha" and disp) else (
                     C["red"]   if (lbl == "Fecha" and not disp) else C["text_1"])
            tk.Label(
                fila, text=val, font=F_BOLD if lbl != "Fecha" else F_SMALL,
                bg=C["bg_card"], fg=fg_val,
                wraplength=175, justify="left"
            ).pack(side="left", padx=(6, 0))

        # Separador
        tk.Frame(self.det_body, bg=C["border"], height=1).pack(fill="x", pady=8)

        # Botón Reservar
        br = tk.Label(
            self.det_body, text="   📅  Reservar Sala   ",
            font=("Segoe UI", 9, "bold"),
            bg=C["primary"], fg="white",
            cursor="hand2", pady=10
        )
        br.pack(fill="x", pady=(0, 6))
        br.bind("<Enter>", lambda e: br.config(bg=C["primary_dark"]))
        br.bind("<Leave>", lambda e: br.config(bg=C["primary"]))
        Tooltip(br, "Crear una reserva para esta sala")

        # Botón Editar
        be = tk.Label(
            self.det_body, text="   ✏️  Editar Información   ",
            font=F_SMALL,
            bg=C["bg_content"], fg=C["text_2"],
            cursor="hand2", pady=10,
            highlightbackground=C["border"],
            highlightthickness=1
        )
        be.pack(fill="x")
        be.bind("<Enter>", lambda e: be.config(bg=C["border"]))
        be.bind("<Leave>", lambda e: be.config(bg=C["bg_content"]))
        Tooltip(be, "Editar los datos de esta sala")

    # ════════════════════════════════════════════════════════
    #  CARGA DE DATOS EN LA TABLA
    # ════════════════════════════════════════════════════════
    def _cargar_salas(self, salas: list):
        """Limpia la tabla y la rellena con la lista de salas recibida."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, s in enumerate(salas):
            est_txt = "✅  Disponible" if s["disponible"] else "🔴  Ocupada"
            t_est   = "disponible"    if s["disponible"] else "ocupada"
            t_fila  = "impar" if i % 2 != 0 else ""
            tags    = (t_est, t_fila) if t_fila else (t_est,)

            self.tree.insert(
                "", "end",
                values=(s["id"], s["nombre"], s["codigo"],
                        s["tipo"].capitalize(), est_txt),
                tags=tags
            )

        n = len(salas)
        txt = f"{n} sala{'s' if n != 1 else ''} encontrada{'s' if n != 1 else ''}"
        self.lbl_conteo.config(text=txt)
        self.lbl_pie.config(text=txt)
        self._det_vacio()

    # ════════════════════════════════════════════════════════
    #  MANEJADORES DE EVENTOS
    # ════════════════════════════════════════════════════════
    def _on_seleccion(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        # Obtener horario directo de la BD usando el código de la sala
        try:
            from consulta import obtener_sala_por_codigo
            sala_bd = obtener_sala_por_codigo(v[2])
            horario = sala_bd.get("horario", "6:00 AM - 8:00 PM")
        except Exception:
            horario = "6:00 AM - 8:00 PM"
        sala = {
            "id":         v[0],
            "nombre":     v[1],
            "codigo":     v[2],
            "tipo":       v[3].lower(),
            "disponible": 1 if "Disponible" in v[4] else 0,
            "horario":    horario,
        }
        self._det_sala(sala)

    def _on_busqueda(self, *_):
        t = self.var_busqueda.get()
        if t in ("", PLACEHOLDER):
            self._on_filtro()
            return
        self._cargar_salas(buscar_salas(t))

    def _on_filtro(self):
        f = self._filtro_activo
        if f == "todas":
            self._cargar_salas(obtener_todas_las_salas())
        else:
            self._cargar_salas(filtrar_por_tipo(f))

    def _limpiar_busqueda(self, _=None):
        self.var_busqueda.set("")
        self._ph_set()
        self._on_filtro()

    def _ordenar(self, col):
        """Ordena la tabla al hacer clic en el encabezado de columna."""
        desc = self._orden_desc.get(col, False)
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=desc)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self._orden_desc[col] = not desc

    # ── Placeholder helpers ──────────────────────────────────
    def _ph_set(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, PLACEHOLDER)
        self.entry.config(fg=C["text_3"])

    def _ph_clear(self, _=None):
        if self.entry.get() == PLACEHOLDER:
            self.entry.delete(0, "end")
            self.entry.config(fg=C["text_1"])

    def _ph_restore(self, _=None):
        if not self.entry.get():
            self._ph_set()