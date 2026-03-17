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
    crear_sala,
    obtener_todas_las_reservas,
    buscar_reservas,
    filtrar_reservas_por_estado,
    obtener_estadisticas_reservas,
    crear_reserva,
    cancelar_reserva,
    obtener_salas_disponibles,
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
 
        # Estado interno — Salas
        self._filtro_activo   = "todas"
        self._filtro_btns     = {}
        self._orden_desc      = {}
 
        # Estado interno — Reservas
        self._rfiltro_activo  = "todas"
        self._rfiltro_btns    = {}
        self._rorden_desc     = {}
 
        # Vista activa: "salas" | "reservas"
        self._vista_activa    = "salas"
        self._nav_rows        = {}   # nombre → (row_frame, acento_frame)
 
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
 
        # Columna derecha
        self._frame_derecha = tk.Frame(self, bg=C["bg_content"])
        self._frame_derecha.pack(side="left", fill="both", expand=True)
 
        # Contenedor de vistas apiladas
        self._frame_vistas = tk.Frame(self._frame_derecha, bg=C["bg_content"])
        self._frame_vistas.pack(fill="both", expand=True)
 
        # Construir ambas vistas (solo una visible a la vez)
        self._frame_salas   = tk.Frame(self._frame_vistas, bg=C["bg_content"])
        self._frame_reservas = tk.Frame(self._frame_vistas, bg=C["bg_content"])
 
        self._construir_vista_salas(self._frame_salas)
        self._construir_vista_reservas(self._frame_reservas)
 
        # Mostrar vista inicial
        self._mostrar_vista("salas")
 
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
            ("🏠", "Dashboard",  None),
            ("🚪", "Salas",      "salas"),
            ("📅", "Reservas",   "reservas"),
            ("👥", "Usuarios",   None),
            ("📊", "Reportes",   None),
        ]
        for ico, nombre, vista in nav_items:
            self._nav_btn(sb, ico, nombre, vista)
 
        # Separador
        tk.Frame(sb, bg="#334155", height=1).pack(fill="x", padx=20, pady=14)
        tk.Label(
            sb, text="SISTEMA", font=F_MICRO,
            bg=C["bg_sidebar"], fg=C["text_3"], padx=20
        ).pack(anchor="w", pady=(0, 4))
 
        for ico, nombre in [("⚙️", "Configuración"), ("❓", "Ayuda")]:
            self._nav_btn(sb, ico, nombre, None)
 
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
 
    def _nav_btn(self, parent, ico, texto, vista):
        """Crea un ítem de navegación en el sidebar."""
        activo = (vista == "salas")   # Salas es la vista inicial
        bg = C["sid_active"] if activo else C["bg_sidebar"]
        fg = C["text_white"]  if activo else C["text_sidebar"]
 
        row = tk.Frame(parent, bg=bg, cursor="hand2" if vista else "arrow")
        row.pack(fill="x", padx=10, pady=1)
 
        acento = tk.Frame(row, bg="white" if activo else bg, width=4)
        acento.pack(side="left", fill="y")
 
        tk.Label(
            row, text=ico, font=("Segoe UI", 12),
            bg=bg, fg=fg, width=2
        ).pack(side="left", padx=(10, 6), pady=10)
 
        tk.Label(row, text=texto, font=F_NAV, bg=bg, fg=fg).pack(side="left")
 
        if vista:
            self._nav_rows[texto] = (row, acento)
            def on_click(e, v=vista):
                self._mostrar_vista(v)
            row.bind("<Button-1>", on_click)
 
        if not activo and vista:
            row.bind("<Enter>",
                     lambda e, r=row, a=acento:
                     (r.config(bg=C["sid_hover"]), a.config(bg=C["sid_hover"])))
            row.bind("<Leave>",
                     lambda e, r=row, a=acento, v=vista:
                     (r.config(bg=C["bg_sidebar"] if self._vista_activa != v else C["sid_active"]),
                      a.config(bg=C["bg_sidebar"] if self._vista_activa != v else "white")))
 
    def _mostrar_vista(self, nombre_vista: str):
        """Alterna entre la vista de Salas y Reservas."""
        self._vista_activa = nombre_vista
 
        # Ocultar todas y mostrar la activa
        self._frame_salas.pack_forget()
        self._frame_reservas.pack_forget()
 
        if nombre_vista == "salas":
            self._frame_salas.pack(fill="both", expand=True)
        else:
            self._frame_reservas.pack(fill="both", expand=True)
            self._cargar_reservas(obtener_todas_las_reservas())
            self._construir_kpis_reservas()
 
        # Actualizar estilos del sidebar
        mapa = {"Salas": "salas", "Reservas": "reservas"}
        for nombre, (row, acento) in self._nav_rows.items():
            vista = mapa.get(nombre)
            if vista == nombre_vista:
                row.config(bg=C["sid_active"])
                acento.config(bg="white")
                for child in row.winfo_children():
                    child.config(bg=C["sid_active"])
                    if isinstance(child, tk.Label):
                        child.config(fg=C["text_white"])
            else:
                row.config(bg=C["bg_sidebar"])
                acento.config(bg=C["bg_sidebar"])
                for child in row.winfo_children():
                    child.config(bg=C["bg_sidebar"])
                    if isinstance(child, tk.Label):
                        child.config(fg=C["text_sidebar"])
    # ════════════════════════════════════════════════════════
    #  VISTA SALAS
    # ════════════════════════════════════════════════════════
    def _construir_vista_salas(self, parent):
        self._construir_header(parent)
        self._construir_cuerpo(parent)
 
    # ════════════════════════════════════════════════════════
    #  VISTA RESERVAS
    # ════════════════════════════════════════════════════════
    def _construir_vista_reservas(self, parent):
        self._construir_header_reservas(parent)
        self._construir_cuerpo_reservas(parent)
 
    # ════════════════════════════════════════════════════════
    #  HEADER SUPERIOR — SALAS
    # ════════════════════════════════════════════════════════
    def _construir_header(self, parent):
        hdr = tk.Frame(parent, bg=C["bg_header"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")
 
        bc = tk.Frame(hdr, bg=C["bg_header"])
        bc.pack(side="left", padx=32, fill="y")
        tk.Label(bc, text="Inicio  ›  ", font=F_SMALL,
                 bg=C["bg_header"], fg=C["text_3"]).pack(side="left")
        tk.Label(bc, text="Salas", font=("Segoe UI", 9, "bold"),
                 bg=C["bg_header"], fg=C["primary"]).pack(side="left")
 
        ac = tk.Frame(hdr, bg=C["bg_header"])
        ac.pack(side="right", padx=28)
 
        btn_nueva = tk.Label(ac, text="   +  Nueva Sala   ",
                             font=("Segoe UI", 9, "bold"),
                             bg=C["primary"], fg="white",
                             cursor="hand2", pady=9)
        btn_nueva.pack(side="right", padx=(10, 0))
        btn_nueva.bind("<Enter>", lambda e: btn_nueva.config(bg=C["primary_dark"]))
        btn_nueva.bind("<Leave>", lambda e: btn_nueva.config(bg=C["primary"]))
        btn_nueva.bind("<Button-1>", lambda e: self._abrir_modal_crear_sala())
        Tooltip(btn_nueva, "Agregar una nueva sala al sistema")
 
        btn_exp = tk.Label(ac, text="   v  Exportar   ",
                           font=F_SMALL, bg=C["bg_content"], fg=C["text_2"],
                           cursor="hand2", pady=9,
                           highlightbackground=C["border"], highlightthickness=1)
        btn_exp.pack(side="right")
        btn_exp.bind("<Enter>", lambda e: btn_exp.config(bg=C["border"]))
        btn_exp.bind("<Leave>", lambda e: btn_exp.config(bg=C["bg_content"]))
        Tooltip(btn_exp, "Exportar listado de salas a archivo")
 
    # ════════════════════════════════════════════════════════
    #  HEADER SUPERIOR — RESERVAS
    # ════════════════════════════════════════════════════════
    def _construir_header_reservas(self, parent):
        hdr = tk.Frame(parent, bg=C["bg_header"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")
 
        bc = tk.Frame(hdr, bg=C["bg_header"])
        bc.pack(side="left", padx=32, fill="y")
        tk.Label(bc, text="Inicio  ›  ", font=F_SMALL,
                 bg=C["bg_header"], fg=C["text_3"]).pack(side="left")
        tk.Label(bc, text="Reservas", font=("Segoe UI", 9, "bold"),
                 bg=C["bg_header"], fg=C["primary"]).pack(side="left")
 
        ac = tk.Frame(hdr, bg=C["bg_header"])
        ac.pack(side="right", padx=28)
 
        btn_nueva = tk.Label(ac, text="   +  Nueva Reserva   ",
                             font=("Segoe UI", 9, "bold"),
                             bg=C["primary"], fg="white",
                             cursor="hand2", pady=9)
        btn_nueva.pack(side="right", padx=(10, 0))
        btn_nueva.bind("<Enter>", lambda e: btn_nueva.config(bg=C["primary_dark"]))
        btn_nueva.bind("<Leave>", lambda e: btn_nueva.config(bg=C["primary"]))
        btn_nueva.bind("<Button-1>", lambda e: self._abrir_modal_crear_reserva())
        Tooltip(btn_nueva, "Registrar una nueva reserva")
 
        btn_exp = tk.Label(ac, text="   v  Exportar   ",
                           font=F_SMALL, bg=C["bg_content"], fg=C["text_2"],
                           cursor="hand2", pady=9,
                           highlightbackground=C["border"], highlightthickness=1)
        btn_exp.pack(side="right")
        btn_exp.bind("<Enter>", lambda e: btn_exp.config(bg=C["border"]))
        btn_exp.bind("<Leave>", lambda e: btn_exp.config(bg=C["bg_content"]))
        Tooltip(btn_exp, "Exportar listado de reservas")
 
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
    #  CUERPO PRINCIPAL — RESERVAS
    # ════════════════════════════════════════════════════════
    def _construir_cuerpo_reservas(self, parent):
        pad = tk.Frame(parent, bg=C["bg_content"])
        pad.pack(fill="both", expand=True, padx=32, pady=28)
 
        # Título
        fila = tk.Frame(pad, bg=C["bg_content"])
        fila.pack(fill="x")
        tk.Label(fila, text="Listado de Reservas",
                 font=F_DISPLAY, bg=C["bg_content"], fg=C["text_1"]).pack(anchor="w")
        tk.Label(fila,
                 text="Gestiona y consulta todas las reservas de salas del sistema",
                 font=F_BODY, bg=C["bg_content"], fg=C["text_2"]).pack(anchor="w", pady=(3, 0))
 
        # KPI frame reservas
        self.frame_kpi_res = tk.Frame(pad, bg=C["bg_content"])
        self.frame_kpi_res.pack(fill="x", pady=(20, 22))
        self._construir_kpis_reservas()
 
        # Toolbar reservas
        self._construir_toolbar_reservas(pad)
 
        # Tabla + detalle
        cont = tk.Frame(pad, bg=C["bg_content"])
        cont.pack(fill="both", expand=True, pady=(14, 0))
        self._construir_tabla_reservas(cont)
        self._construir_panel_detalle_reservas(cont)
 
        # Carga inicial
        self._cargar_reservas(obtener_todas_las_reservas())
 
    # ── KPIs Reservas ─────────────────────────────────────────
    def _construir_kpis_reservas(self):
        for w in self.frame_kpi_res.winfo_children():
            w.destroy()
 
        stats = obtener_estadisticas_reservas()
        total = max(stats["total"], 1)
        pct   = int(stats["activas"] / total * 100)
 
        defs = [
            ("Total Reservas", str(stats["total"]),      "📅", C["primary"], C["primary_glow"]),
            ("Activas",        str(stats["activas"]),    "✅", C["green"],   C["green_bg"]),
            ("Canceladas",     str(stats["canceladas"]), "🔴", C["red"],     C["red_bg"]),
            ("Tasa activa",    f"{pct}%",                "📊", C["amber"],   C["amber_bg"]),
        ]
        for titulo, valor, ico, color, ico_bg in defs:
            card = tk.Frame(self.frame_kpi_res, bg=C["bg_card"],
                            highlightbackground=C["border"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 14))
            inner = tk.Frame(card, bg=C["bg_card"], padx=20, pady=18)
            inner.pack(fill="both", expand=True)
            top = tk.Frame(inner, bg=C["bg_card"])
            top.pack(fill="x")
            ib = tk.Frame(top, bg=ico_bg, width=50, height=50)
            ib.pack_propagate(False)
            ib.pack(side="right")
            tk.Label(ib, text=ico, font=("Segoe UI", 20), bg=ico_bg).pack(expand=True)
            tk.Label(top, text=valor, font=F_KPI,
                     bg=C["bg_card"], fg=color).pack(side="left", anchor="w")
            tk.Label(inner, text=titulo, font=F_BODY,
                     bg=C["bg_card"], fg=C["text_2"]).pack(anchor="w", pady=(8, 0))
            tk.Frame(card, bg=color, height=3).pack(fill="x", side="bottom")
 
    # ── Toolbar Reservas ──────────────────────────────────────
    def _construir_toolbar_reservas(self, parent):
        bar = tk.Frame(parent, bg=C["bg_content"])
        bar.pack(fill="x")
 
        sw = tk.Frame(bar, bg=C["bg_card"],
                      highlightbackground=C["border"], highlightthickness=1)
        sw.pack(side="left", fill="x", expand=True, padx=(0, 12))
 
        tk.Label(sw, text="🔍", font=("Segoe UI", 11),
                 bg=C["bg_card"], fg=C["text_3"], padx=10).pack(side="left")
 
        self.var_busqueda_res = tk.StringVar()
        self._ph_res = "Buscar por sala, responsable o fecha…"
        self.entry_res = tk.Entry(
            sw, textvariable=self.var_busqueda_res,
            font=F_BODY, bd=0, relief="flat",
            bg=C["bg_card"], fg=C["text_1"],
            insertbackground=C["primary"])
        self.entry_res.pack(side="left", fill="both", expand=True, pady=11, padx=(0, 8))
        self._ph_res_set()
        self.entry_res.bind("<FocusIn>",  self._ph_res_clear)
        self.entry_res.bind("<FocusOut>", self._ph_res_restore)
        self.var_busqueda_res.trace_add("write", self._on_busqueda_reservas)
 
        btn_clear = tk.Label(sw, text=" x ", font=F_SMALL,
                             bg=C["bg_card"], fg=C["text_3"], cursor="hand2", padx=6)
        btn_clear.pack(side="right")
        btn_clear.bind("<Button-1>", self._limpiar_busqueda_reservas)
 
        # Filtros de estado
        fw = tk.Frame(bar, bg=C["bg_card"],
                      highlightbackground=C["border"], highlightthickness=1)
        fw.pack(side="left")
        self._rfiltro_btns = {}
        for label, valor in [("Todas", "todas"), ("Activas", "activa"),
                              ("Canceladas", "cancelada"), ("Finalizadas", "finalizada")]:
            btn = tk.Label(fw, text=label, font=F_SMALL, padx=14, pady=11, cursor="hand2")
            btn.pack(side="left")
            self._rfiltro_btns[valor] = btn
            btn.bind("<Button-1>", lambda e, v=valor: self._set_rfiltro(v))
        self._refrescar_rfiltro_ui()
 
        self.lbl_conteo_res = tk.Label(
            bar, text="", font=F_SMALL, bg=C["bg_content"], fg=C["text_3"])
        self.lbl_conteo_res.pack(side="right")
 
    def _set_rfiltro(self, valor):
        self._rfiltro_activo = valor
        self._refrescar_rfiltro_ui()
        self._on_rfiltro()
 
    def _refrescar_rfiltro_ui(self):
        for v, btn in self._rfiltro_btns.items():
            if v == self._rfiltro_activo:
                btn.config(bg=C["primary"], fg="white")
            else:
                btn.config(bg=C["bg_card"], fg=C["text_2"])
 
    def _on_rfiltro(self):
        f = self._rfiltro_activo
        if f == "todas":
            self._cargar_reservas(obtener_todas_las_reservas())
        else:
            self._cargar_reservas(filtrar_reservas_por_estado(f))
 
    def _on_busqueda_reservas(self, *_):
        t = self.var_busqueda_res.get()
        if t in ("", self._ph_res):
            self._on_rfiltro()
            return
        self._cargar_reservas(buscar_reservas(t))
 
    def _limpiar_busqueda_reservas(self, _=None):
        self.var_busqueda_res.set("")
        self._ph_res_set()
        self._on_rfiltro()
 
    def _ph_res_set(self):
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, self._ph_res)
        self.entry_res.config(fg=C["text_3"])
 
    def _ph_res_clear(self, _=None):
        if self.entry_res.get() == self._ph_res:
            self.entry_res.delete(0, "end")
            self.entry_res.config(fg=C["text_1"])
 
    def _ph_res_restore(self, _=None):
        if not self.entry_res.get():
            self._ph_res_set()
 
    # ── Tabla Reservas ────────────────────────────────────────
    def _construir_tabla_reservas(self, parent):
        wrap = tk.Frame(parent, bg=C["bg_card"],
                        highlightbackground=C["border"], highlightthickness=1)
        wrap.pack(side="left", fill="both", expand=True)
 
        ch = tk.Frame(wrap, bg=C["bg_card"], pady=14)
        ch.pack(fill="x", padx=18)
        tk.Label(ch, text="Reservas registradas",
                 font=F_HEADING, bg=C["bg_card"], fg=C["text_1"]).pack(side="left")
        self.lbl_pie_res = tk.Label(
            ch, text="", font=F_SMALL, bg=C["bg_card"], fg=C["text_3"])
        self.lbl_pie_res.pack(side="right")
 
        tk.Frame(wrap, bg=C["border"], height=1).pack(fill="x")
 
        cols = ("id", "sala", "fecha", "hora", "responsable", "estado")
        self.tree_res = ttk.Treeview(
            wrap, columns=cols, show="headings",
            style="Pro.Treeview", selectmode="browse")
 
        cfg = [
            ("id",          "#",           45,  "center", False),
            ("sala",        "Sala",        180, "w",      True),
            ("fecha",       "Fecha",       110, "center", False),
            ("hora",        "Horario",     150, "center", False),
            ("responsable", "Responsable", 160, "w",      True),
            ("estado",      "Estado",      110, "center", False),
        ]
        for col, txt, ancho, ancla, stretch in cfg:
            self.tree_res.heading(col, text=txt,
                                  command=lambda c=col: self._ordenar_res(c))
            self.tree_res.column(col, width=ancho, anchor=ancla, stretch=stretch)
 
        sc = ttk.Scrollbar(wrap, orient="vertical",
                           command=self.tree_res.yview,
                           style="Thin.Vertical.TScrollbar")
        self.tree_res.configure(yscrollcommand=sc.set)
        self.tree_res.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")
 
        self.tree_res.tag_configure("activa",     foreground=C["green"])
        self.tree_res.tag_configure("cancelada",  foreground=C["red"])
        self.tree_res.tag_configure("finalizada", foreground=C["amber"])
        self.tree_res.tag_configure("impar",      background=C["bg_table_alt"])
 
        self.tree_res.bind("<<TreeviewSelect>>", self._on_seleccion_reserva)
        self.tree_res.bind("<Motion>",
                           lambda e: self.tree_res.config(
                               cursor="hand2" if self.tree_res.identify_row(e.y) else ""))
 
    # ── Panel detalle Reservas ────────────────────────────────
    def _construir_panel_detalle_reservas(self, parent):
        self.panel_res = tk.Frame(
            parent, bg=C["bg_card"], width=295,
            highlightbackground=C["border"], highlightthickness=1)
        self.panel_res.pack(side="right", fill="y", padx=(14, 0))
        self.panel_res.pack_propagate(False)
 
        ph = tk.Frame(self.panel_res, bg=C["bg_sidebar"], pady=14)
        ph.pack(fill="x")
        tk.Label(ph, text="Detalle de Reserva",
                 font=F_HEADING, bg=C["bg_sidebar"], fg=C["text_white"],
                 padx=18).pack(side="left")
 
        self.det_body_res = tk.Frame(self.panel_res, bg=C["bg_card"])
        self.det_body_res.pack(fill="both", expand=True, padx=14, pady=12)
        self._det_res_vacio()
 
    def _det_res_vacio(self):
        for w in self.det_body_res.winfo_children():
            w.destroy()
        tk.Label(self.det_body_res,
                 text="Selecciona una reserva\npara ver sus detalles",
                 font=F_BODY, bg=C["bg_card"], fg=C["text_3"],
                 justify="center").pack(expand=True)
 
    def _det_reserva(self, r: dict):
        for w in self.det_body_res.winfo_children():
            w.destroy()
 
        estado = r.get("estado", "activa")
        col_map = {"activa": C["green"], "cancelada": C["red"], "finalizada": C["amber"]}
        bg_map  = {"activa": C["green_bg"], "cancelada": C["red_bg"], "finalizada": C["amber_bg"]}
        col_est = col_map.get(estado, C["text_2"])
        col_bg  = bg_map.get(estado, C["border"])
 
        # Ícono
        ib = tk.Frame(self.det_body_res, bg=C["primary_glow"], width=56, height=56)
        ib.pack_propagate(False)
        ib.pack(pady=(0, 8))
        tk.Label(ib, text="📅", font=("Segoe UI", 22), bg=C["primary_glow"]).pack(expand=True)
 
        # Nombre sala
        tk.Label(self.det_body_res, text=r.get("sala_nombre", ""),
                 font=("Segoe UI", 11, "bold"), bg=C["bg_card"], fg=C["text_1"],
                 wraplength=215, justify="center").pack()
        tk.Label(self.det_body_res, text=r.get("sala_codigo", ""),
                 font=F_SMALL, bg=C["bg_card"], fg=C["text_3"]).pack()
 
        # Badge estado
        tk.Label(self.det_body_res, text=f"  {estado.capitalize()}  ",
                 font=F_SMALL, bg=col_bg, fg=col_est, pady=5).pack(pady=(6, 10))
 
        tk.Frame(self.det_body_res, bg=C["border"], height=1).pack(fill="x", pady=(0, 8))
 
        campos = [
            ("Fecha",       r.get("fecha", "")),
            ("Inicio",      r.get("hora_inicio", "")),
            ("Fin",         r.get("hora_fin", "")),
            ("Responsable", r.get("responsable", "")),
            ("Proposito",   r.get("descripcion", "") or "—"),
            ("ID",          str(r.get("id", ""))),
        ]
        for lbl, val in campos:
            fila = tk.Frame(self.det_body_res, bg=C["bg_card"])
            fila.pack(fill="x", pady=3)
            tk.Label(fila, text=lbl, font=F_SMALL, bg=C["bg_card"], fg=C["text_3"],
                     width=10, anchor="w").pack(side="left")
            tk.Label(fila, text=val, font=F_BOLD if lbl != "Proposito" else F_SMALL,
                     bg=C["bg_card"], fg=C["text_1"],
                     wraplength=155, justify="left").pack(side="left", padx=(4, 0))
 
        tk.Frame(self.det_body_res, bg=C["border"], height=1).pack(fill="x", pady=8)
 
        # Botón cancelar (solo si activa)
        if estado == "activa":
            rid = r.get("id")
            bc = tk.Label(self.det_body_res, text="   Cancelar Reserva   ",
                          font=("Segoe UI", 9, "bold"),
                          bg=C["red"], fg="white", cursor="hand2", pady=9)
            bc.pack(fill="x")
            bc.bind("<Button-1>", lambda e, rid=rid: self._confirmar_cancelar(rid))
            bc.bind("<Enter>", lambda e: bc.config(bg="#b91c1c"))
            bc.bind("<Leave>", lambda e: bc.config(bg=C["red"]))
 
    # ── Cargar datos en tabla reservas ────────────────────────
    def _cargar_reservas(self, reservas: list):
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
 
        for i, r in enumerate(reservas):
            horario = f"{r['hora_inicio']} - {r['hora_fin']}"
            estado  = r.get("estado", "activa")
            t_fila  = "impar" if i % 2 != 0 else ""
            tags    = (estado, t_fila) if t_fila else (estado,)
            self.tree_res.insert("", "end",
                iid=str(r["id"]),
                values=(r["id"], r["sala_nombre"], r["fecha"],
                        horario, r["responsable"], estado.capitalize()),
                tags=tags)
 
        n = len(reservas)
        txt = f"{n} reserva{'s' if n != 1 else ''} encontrada{'s' if n != 1 else ''}"
        self.lbl_conteo_res.config(text=txt)
        self.lbl_pie_res.config(text=txt)
        self._det_res_vacio()
 
    # ── Eventos tabla reservas ────────────────────────────────
    def _on_seleccion_reserva(self, _=None):
        sel = self.tree_res.selection()
        if not sel:
            return
        rid = int(sel[0])
        try:
            from consulta import obtener_reserva_por_id
            r = obtener_reserva_por_id(rid)
            self._det_reserva(r)
        except Exception:
            pass
 
    def _ordenar_res(self, col):
        desc  = self._rorden_desc.get(col, False)
        items = [(self.tree_res.set(k, col), k) for k in self.tree_res.get_children("")]
        items.sort(reverse=desc)
        for idx, (_, k) in enumerate(items):
            self.tree_res.move(k, "", idx)
        self._rorden_desc[col] = not desc
 
    def _confirmar_cancelar(self, reserva_id):
        """Cancela una reserva tras confirmación."""
        import tkinter.messagebox as mb
        if mb.askyesno("Cancelar Reserva",
                       "¿Estás seguro de que deseas cancelar esta reserva?",
                       icon="warning"):
            try:
                cancelar_reserva(reserva_id)
                self._on_rfiltro()
                self._construir_kpis_reservas()
                self._det_res_vacio()
            except ValueError as e:
                mb.showerror("Error", str(e))
 
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
 
    # ════════════════════════════════════════════════════════
    #  MODAL — CREAR NUEVA RESERVA
    # ════════════════════════════════════════════════════════
    def _abrir_modal_crear_reserva(self):
        """Abre un modal para registrar una nueva reserva."""
        modal = tk.Toplevel(self)
        modal.title("Nueva Reserva")
        modal.geometry("520x620")
        modal.resizable(False, False)
        modal.configure(bg=C["bg_card"])
        modal.grab_set()
        modal.transient(self)
 
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 620) // 2
        modal.geometry(f"+{x}+{y}")
 
        # Cabecera
        cab = tk.Frame(modal, bg=C["bg_sidebar"], pady=16)
        cab.pack(fill="x")
        tk.Label(cab, text="  +  Registrar Nueva Reserva",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["bg_sidebar"], fg=C["text_white"], padx=20).pack(side="left")
 
        # Cuerpo con scroll
        outer = tk.Frame(modal, bg=C["bg_card"])
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=C["bg_card"], bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        cuerpo = tk.Frame(canvas, bg=C["bg_card"])
        cuerpo_id = canvas.create_window((0, 0), window=cuerpo, anchor="nw")
 
        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cuerpo_id, width=canvas.winfo_width())
        cuerpo.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cuerpo_id, width=e.width))
 
        # Padding interno
        inner = tk.Frame(cuerpo, bg=C["bg_card"], padx=28, pady=16)
        inner.pack(fill="both", expand=True)
 
        # Helper entry
        def hacer_entry(parent, etiqueta, placeholder=""):
            tk.Label(parent, text=etiqueta, font=("Segoe UI", 10, "bold"),
                     bg=C["bg_card"], fg=C["text_2"], anchor="w").pack(anchor="w", pady=(10, 3))
            entry = tk.Entry(parent, font=("Segoe UI", 10),
                             relief="solid", bd=1, bg="#f8fafc",
                             fg=C["text_3"] if placeholder else C["text_1"],
                             insertbackground=C["primary"])
            entry.pack(fill="x", ipady=7)
            if placeholder:
                entry.insert(0, placeholder)
                def on_in(ev, e=entry, ph=placeholder):
                    if e.get() == ph:
                        e.delete(0, "end"); e.config(fg=C["text_1"])
                def on_out(ev, e=entry, ph=placeholder):
                    if not e.get().strip():
                        e.insert(0, ph); e.config(fg=C["text_3"])
                entry.bind("<FocusIn>",  on_in)
                entry.bind("<FocusOut>", on_out)
            return entry, placeholder
 
        # ── Selector de sala ──────────────────────────────
        tk.Label(inner, text="Sala *", font=("Segoe UI", 10, "bold"),
                 bg=C["bg_card"], fg=C["text_2"], anchor="w").pack(anchor="w", pady=(10, 3))
 
        salas_disp = obtener_todas_las_salas()
        nombres_salas = [f"{s['nombre']}  [{s['codigo']}]" for s in salas_disp]
        var_sala = tk.StringVar()
 
        combo_sala = ttk.Combobox(inner, textvariable=var_sala,
                                  values=nombres_salas,
                                  font=("Segoe UI", 10),
                                  state="readonly")
        combo_sala.pack(fill="x", ipady=4)
        if nombres_salas:
            combo_sala.current(0)
 
        # ── Fecha ─────────────────────────────────────────
        entry_fecha, ph_fecha = hacer_entry(inner, "Fecha *", "YYYY-MM-DD  (ej: 2026-04-15)")
 
        # ── Hora inicio / fin (en fila) ───────────────────
        tk.Label(inner, text="Horario *", font=("Segoe UI", 10, "bold"),
                 bg=C["bg_card"], fg=C["text_2"], anchor="w").pack(anchor="w", pady=(10, 3))
 
        fila_hora = tk.Frame(inner, bg=C["bg_card"])
        fila_hora.pack(fill="x")
 
        entry_inicio = tk.Entry(fila_hora, font=("Segoe UI", 10),
                                relief="solid", bd=1, bg="#f8fafc",
                                fg=C["text_3"], insertbackground=C["primary"])
        entry_inicio.pack(side="left", fill="x", expand=True, ipady=7)
        entry_inicio.insert(0, "HH:MM  (ej: 08:00)")
        def _in_inicio(ev):
            if entry_inicio.get() == "HH:MM  (ej: 08:00)":
                entry_inicio.delete(0, "end"); entry_inicio.config(fg=C["text_1"])
        def _out_inicio(ev):
            if not entry_inicio.get().strip():
                entry_inicio.insert(0, "HH:MM  (ej: 08:00)"); entry_inicio.config(fg=C["text_3"])
        entry_inicio.bind("<FocusIn>",  _in_inicio)
        entry_inicio.bind("<FocusOut>", _out_inicio)
 
        tk.Label(fila_hora, text="  hasta  ", font=F_SMALL,
                 bg=C["bg_card"], fg=C["text_3"]).pack(side="left")
 
        entry_fin = tk.Entry(fila_hora, font=("Segoe UI", 10),
                             relief="solid", bd=1, bg="#f8fafc",
                             fg=C["text_3"], insertbackground=C["primary"])
        entry_fin.pack(side="left", fill="x", expand=True, ipady=7)
        entry_fin.insert(0, "HH:MM  (ej: 10:00)")
        def _in_fin(ev):
            if entry_fin.get() == "HH:MM  (ej: 10:00)":
                entry_fin.delete(0, "end"); entry_fin.config(fg=C["text_1"])
        def _out_fin(ev):
            if not entry_fin.get().strip():
                entry_fin.insert(0, "HH:MM  (ej: 10:00)"); entry_fin.config(fg=C["text_3"])
        entry_fin.bind("<FocusIn>",  _in_fin)
        entry_fin.bind("<FocusOut>", _out_fin)
 
        # ── Responsable ───────────────────────────────────
        entry_resp, ph_resp = hacer_entry(inner, "Responsable *", "Nombre completo")
 
        # ── Descripción ───────────────────────────────────
        tk.Label(inner, text="Descripcion / Proposito",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["bg_card"], fg=C["text_2"], anchor="w").pack(anchor="w", pady=(10, 3))
        txt_desc = tk.Text(inner, font=("Segoe UI", 10),
                           relief="solid", bd=1, bg="#f8fafc",
                           fg=C["text_1"], height=4,
                           insertbackground=C["primary"], wrap="word")
        txt_desc.pack(fill="x")
 
        # ── Mensaje ───────────────────────────────────────
        lbl_msg = tk.Label(inner, text="", font=("Segoe UI", 9),
                           bg=C["bg_card"], fg=C["red"],
                           wraplength=440, justify="left")
        lbl_msg.pack(anchor="w", pady=(8, 0))
 
        # Pie
        pie = tk.Frame(modal, bg=C["bg_content"], pady=12, padx=24)
        pie.pack(fill="x", side="bottom")
 
        ph_inicio = "HH:MM  (ej: 08:00)"
        ph_fin    = "HH:MM  (ej: 10:00)"
 
        def _leer(entry, ph):
            v = entry.get().strip()
            return "" if v == ph else v
 
        def _guardar():
            # Leer sala
            idx = combo_sala.current()
            if idx < 0 or not salas_disp:
                lbl_msg.config(text="Selecciona una sala.", fg=C["red"])
                return
            sala = salas_disp[idx]
 
            fecha    = _leer(entry_fecha,  ph_fecha)
            inicio   = _leer(entry_inicio, ph_inicio)
            fin      = _leer(entry_fin,    ph_fin)
            resp     = _leer(entry_resp,   ph_resp)
            desc     = txt_desc.get("1.0", "end").strip()
 
            if not fecha:
                lbl_msg.config(text="La fecha es obligatoria.", fg=C["red"]); return
            if not inicio:
                lbl_msg.config(text="La hora de inicio es obligatoria.", fg=C["red"]); return
            if not fin:
                lbl_msg.config(text="La hora de fin es obligatoria.", fg=C["red"]); return
            if not resp:
                lbl_msg.config(text="El responsable es obligatorio.", fg=C["red"]); return
 
            try:
                crear_reserva(
                    sala_id=sala["id"],
                    sala_nombre=sala["nombre"],
                    sala_codigo=sala["codigo"],
                    fecha=fecha,
                    hora_inicio=inicio,
                    hora_fin=fin,
                    responsable=resp,
                    descripcion=desc,
                )
                self._construir_kpis_reservas()
                self._on_rfiltro()
                modal.destroy()
                self._mostrar_confirmacion_reserva(
                    sala_nombre=sala["nombre"],
                    sala_codigo=sala["codigo"],
                    fecha=fecha,
                    inicio=inicio,
                    fin=fin,
                    responsable=resp,
                )
            except ValueError as err:
                lbl_msg.config(text=str(err), fg=C["red"])
 
        btn_g = tk.Label(pie, text="  Guardar reserva  ",
                         font=("Segoe UI", 9, "bold"),
                         bg=C["primary"], fg="white", cursor="hand2", pady=8)
        btn_g.pack(side="right", padx=(10, 0))
        btn_g.bind("<Button-1>", lambda e: _guardar())
        btn_g.bind("<Enter>", lambda e: btn_g.config(bg=C["primary_dark"]))
        btn_g.bind("<Leave>", lambda e: btn_g.config(bg=C["primary"]))
        modal.bind("<Return>", lambda e: _guardar())
 
        btn_c = tk.Label(pie, text="  Cancelar  ",
                         font=("Segoe UI", 9), bg=C["bg_content"], fg=C["text_2"],
                         cursor="hand2", pady=8,
                         highlightbackground=C["border"], highlightthickness=1)
        btn_c.pack(side="right")
        btn_c.bind("<Button-1>", lambda e: modal.destroy())
        btn_c.bind("<Enter>", lambda e: btn_c.config(bg=C["border"]))
        btn_c.bind("<Leave>", lambda e: btn_c.config(bg=C["bg_content"]))
 
        combo_sala.focus_set()
 
    # ════════════════════════════════════════════════════════
    #  MODAL — CONFIRMACIÓN DE RESERVA REGISTRADA
    # ════════════════════════════════════════════════════════
    def _mostrar_confirmacion_reserva(self, sala_nombre: str, sala_codigo: str,
                                       fecha: str, inicio: str, fin: str,
                                       responsable: str):
        """
        Muestra un modal de éxito con los detalles de la reserva recién creada.
        Se cierra automáticamente después de 4 segundos o al presionar el botón.
        """
        confirm = tk.Toplevel(self)
        confirm.title("Reserva Confirmada")
        confirm.geometry("460x360")
        confirm.resizable(False, False)
        confirm.configure(bg=C["bg_card"])
        confirm.grab_set()
        confirm.transient(self)
 
        # Centrar en la ventana principal
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 460) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        confirm.geometry(f"+{x}+{y}")
 
        # ── Banda verde superior ──────────────────────────
        banda = tk.Frame(confirm, bg=C["green"], height=6)
        banda.pack(fill="x")
 
        # ── Ícono de éxito ────────────────────────────────
        tk.Frame(confirm, bg=C["bg_card"], height=24).pack(fill="x")
        circulo = tk.Frame(confirm, bg=C["green_bg"], width=72, height=72)
        circulo.pack_propagate(False)
        circulo.pack()
        tk.Label(
            circulo, text="✓", font=("Segoe UI", 28, "bold"),
            bg=C["green_bg"], fg=C["green"]
        ).pack(expand=True)
 
        # ── Título ────────────────────────────────────────
        tk.Label(
            confirm, text="¡Reserva Registrada!",
            font=("Segoe UI", 14, "bold"),
            bg=C["bg_card"], fg=C["text_1"]
        ).pack(pady=(14, 2))
        tk.Label(
            confirm, text="Los datos de tu reserva han sido guardados correctamente.",
            font=("Segoe UI", 9),
            bg=C["bg_card"], fg=C["text_2"],
            wraplength=380
        ).pack()
 
        # ── Tarjeta de detalles ───────────────────────────
        tarjeta = tk.Frame(
            confirm, bg=C["bg_content"],
            highlightbackground=C["border"], highlightthickness=1
        )
        tarjeta.pack(fill="x", padx=32, pady=(18, 0))
 
        detalles = [
            ("🚪  Sala",         f"{sala_nombre}  [{sala_codigo}]"),
            ("📅  Fecha",        fecha),
            ("🕐  Horario",      f"{inicio}  →  {fin}"),
            ("👤  Responsable",  responsable),
        ]
        for i, (etiqueta, valor) in enumerate(detalles):
            fila = tk.Frame(tarjeta, bg=C["bg_content"])
            fila.pack(fill="x", padx=16, pady=(10 if i == 0 else 6, 6 if i < len(detalles) - 1 else 10))
            tk.Label(
                fila, text=etiqueta,
                font=("Segoe UI", 9), width=16, anchor="w",
                bg=C["bg_content"], fg=C["text_2"]
            ).pack(side="left")
            tk.Label(
                fila, text=valor,
                font=("Segoe UI", 9, "bold"),
                bg=C["bg_content"], fg=C["text_1"], anchor="w"
            ).pack(side="left")
 
        # ── Barra de progreso de cierre automático ────────
        barra_frame = tk.Frame(confirm, bg=C["border"], height=4)
        barra_frame.pack(fill="x", padx=32, pady=(14, 0))
        barra_prog = tk.Frame(barra_frame, bg=C["green"], height=4)
        barra_prog.place(relwidth=1.0, relheight=1.0)
 
        # ── Botón Aceptar ─────────────────────────────────
        btn_ok = tk.Label(
            confirm, text="  Aceptar  ",
            font=("Segoe UI", 9, "bold"),
            bg=C["primary"], fg="white",
            cursor="hand2", pady=8, padx=6
        )
        btn_ok.pack(pady=(10, 20))
        btn_ok.bind("<Button-1>", lambda e: confirm.destroy())
        btn_ok.bind("<Enter>",    lambda e: btn_ok.config(bg=C["primary_dark"]))
        btn_ok.bind("<Leave>",    lambda e: btn_ok.config(bg=C["primary"]))
        confirm.bind("<Return>",  lambda e: confirm.destroy())
        confirm.bind("<Escape>",  lambda e: confirm.destroy())
 
        # ── Animación de barra + cierre automático (4 s) ──
        duracion_ms = 4000
        pasos       = 80
        intervalo   = duracion_ms // pasos
 
        def _animar(paso=0):
            if not confirm.winfo_exists():
                return
            fraccion = 1.0 - (paso / pasos)
            barra_prog.place(relwidth=max(fraccion, 0), relheight=1.0)
            if paso < pasos:
                confirm.after(intervalo, lambda: _animar(paso + 1))
            else:
                if confirm.winfo_exists():
                    confirm.destroy()
 
        confirm.after(intervalo, lambda: _animar(1))
        btn_ok.focus_set()
 
    # ════════════════════════════════════════════════════════
    #  MODAL — CREAR NUEVA SALA
    # ════════════════════════════════════════════════════════
    def _abrir_modal_crear_sala(self):
        """Abre una ventana modal para registrar una nueva sala."""
        modal = tk.Toplevel(self)
        modal.title("Nueva Sala")
        modal.geometry("480x500")
        modal.resizable(False, False)
        modal.configure(bg=C["bg_card"])
        modal.grab_set()
        modal.transient(self)
 
        # Centrar modal
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 500) // 2
        modal.geometry(f"+{x}+{y}")
 
        # ── Cabecera ──────────────────────────────────────
        cab = tk.Frame(modal, bg=C["bg_sidebar"], pady=16)
        cab.pack(fill="x")
        tk.Label(
            cab, text="  +  Registrar Nueva Sala",
            font=("Segoe UI", 11, "bold"),
            bg=C["bg_sidebar"], fg=C["text_white"],
            padx=20
        ).pack(side="left")
 
        # ── Cuerpo ────────────────────────────────────────
        cuerpo = tk.Frame(modal, bg=C["bg_card"])
        cuerpo.pack(fill="both", expand=True, padx=28, pady=16)
 
        # ── Helper para crear campo de texto ──────────────
        def hacer_entry(parent, etiqueta, ph_texto):
            """Crea label + Entry con placeholder manual (sin StringVar para evitar conflictos)."""
            tk.Label(
                parent, text=etiqueta,
                font=("Segoe UI", 10, "bold"),
                bg=C["bg_card"], fg=C["text_2"], anchor="w"
            ).pack(anchor="w", pady=(10, 3))
 
            entry = tk.Entry(
                parent,
                font=("Segoe UI", 10),
                relief="solid", bd=1,
                bg="#f8fafc", fg=C["text_3"],
                insertbackground=C["primary"],
            )
            entry.pack(fill="x", ipady=7)
            entry.insert(0, ph_texto)
 
            def on_focus_in(ev):
                if entry.get() == ph_texto:
                    entry.delete(0, "end")
                    entry.config(fg=C["text_1"])
 
            def on_focus_out(ev):
                if not entry.get().strip():
                    entry.insert(0, ph_texto)
                    entry.config(fg=C["text_3"])
 
            entry.bind("<FocusIn>",  on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)
            return entry, ph_texto
 
        entry_nombre, ph_nombre = hacer_entry(cuerpo, "Nombre de la sala *",
                                               "Ej: Laboratorio de Computo 3")
        entry_codigo, ph_codigo = hacer_entry(cuerpo, "Codigo unico *", "Ej: LAB03")
 
        # ── Tipo ──────────────────────────────────────────
        tk.Label(
            cuerpo, text="Tipo *",
            font=("Segoe UI", 10, "bold"),
            bg=C["bg_card"], fg=C["text_2"], anchor="w"
        ).pack(anchor="w", pady=(12, 4))
 
        var_tipo  = tk.StringVar(value="aula")
        f_tipo    = tk.Frame(cuerpo, bg=C["bg_card"])
        f_tipo.pack(anchor="w")
        for val, lbl in [("aula", "Aula"), ("laboratorio", "Laboratorio"), ("sala", "Sala")]:
            tk.Radiobutton(
                f_tipo, text=lbl, variable=var_tipo, value=val,
                font=("Segoe UI", 10),
                bg=C["bg_card"], fg=C["text_1"],
                activebackground=C["bg_card"],
                selectcolor=C["primary_glow"],
                cursor="hand2"
            ).pack(side="left", padx=(0, 18))
 
        # ── Estado inicial ────────────────────────────────
        tk.Label(
            cuerpo, text="Estado inicial *",
            font=("Segoe UI", 10, "bold"),
            bg=C["bg_card"], fg=C["text_2"], anchor="w"
        ).pack(anchor="w", pady=(12, 4))
 
        var_disp  = tk.IntVar(value=1)
        f_disp    = tk.Frame(cuerpo, bg=C["bg_card"])
        f_disp.pack(anchor="w")
        for val, lbl in [(1, "Disponible"), (0, "Ocupada")]:
            tk.Radiobutton(
                f_disp, text=lbl, variable=var_disp, value=val,
                font=("Segoe UI", 10),
                bg=C["bg_card"], fg=C["text_1"],
                activebackground=C["bg_card"],
                selectcolor=C["primary_glow"],
                cursor="hand2"
            ).pack(side="left", padx=(0, 18))
 
        # ── Mensaje de error/éxito ────────────────────────
        lbl_msg = tk.Label(
            cuerpo, text="",
            font=("Segoe UI", 9),
            bg=C["bg_card"], fg=C["red"],
            wraplength=400, justify="left"
        )
        lbl_msg.pack(anchor="w", pady=(10, 0))
 
        # ── Pie de botones ────────────────────────────────
        pie = tk.Frame(modal, bg=C["bg_content"], pady=12, padx=24)
        pie.pack(fill="x", side="bottom")
 
        def _leer_campo(entry, placeholder):
            """Lee el Entry y devuelve '' si contiene el placeholder."""
            val = entry.get().strip()
            return "" if val == placeholder else val
 
        def _guardar():
            nombre = _leer_campo(entry_nombre, ph_nombre)
            codigo = _leer_campo(entry_codigo, ph_codigo)
            tipo   = var_tipo.get()
            disp   = var_disp.get()
 
            if not nombre:
                lbl_msg.config(text="El nombre de la sala es obligatorio.", fg=C["red"])
                entry_nombre.focus_set()
                return
            if not codigo:
                lbl_msg.config(text="El codigo de la sala es obligatorio.", fg=C["red"])
                entry_codigo.focus_set()
                return
 
            try:
                crear_sala(nombre, codigo, tipo, disp)
                self._construir_kpis()
                self._on_filtro()
                lbl_msg.config(
                    text=f"Sala '{nombre}' creada correctamente.",
                    fg=C["green"]
                )
                modal.after(1400, modal.destroy)
 
            except ValueError as err:
                lbl_msg.config(text=str(err), fg=C["red"])
 
        btn_g = tk.Label(
            pie, text="  Guardar sala  ",
            font=("Segoe UI", 9, "bold"),
            bg=C["primary"], fg="white",
            cursor="hand2", pady=8
        )
        btn_g.pack(side="right", padx=(10, 0))
        btn_g.bind("<Button-1>", lambda e: _guardar())
        btn_g.bind("<Enter>", lambda e: btn_g.config(bg=C["primary_dark"]))
        btn_g.bind("<Leave>", lambda e: btn_g.config(bg=C["primary"]))
 
        # Permitir guardar con Enter
        modal.bind("<Return>", lambda e: _guardar())
 
        btn_c = tk.Label(
            pie, text="  Cancelar  ",
            font=("Segoe UI", 9),
            bg=C["bg_content"], fg=C["text_2"],
            cursor="hand2", pady=8,
            highlightbackground=C["border"],
            highlightthickness=1
        )
        btn_c.pack(side="right")
        btn_c.bind("<Button-1>", lambda e: modal.destroy())
        btn_c.bind("<Enter>", lambda e: btn_c.config(bg=C["border"]))
        btn_c.bind("<Leave>", lambda e: btn_c.config(bg=C["bg_content"]))
 
        # Poner foco en el primer campo
        entry_nombre.focus_set()
        # En visualizacion.py dentro de la clase VentanaPrincipal
 
    def _verificacion_periodica(self):
        """Refresca los estados de salas y reservas automáticamente."""
        from consulta import actualizar_estado_salas_y_reservas
        actualizar_estado_salas_y_reservas()
    
    # Refrescar la vista actual para mostrar cambios
        if self._vista_activa == "salas":
            self._on_filtro()
        else:
            self._on_rfiltro()
        
        self._construir_kpis()
        self._construir_kpis_reservas()
    
    #    Programar siguiente ejecución en 60 segundos
        self.after(60000, self._verificacion_periodica)
 
# En el __init__ de VentanaPrincipal, inicia el ciclo:
# self._verificacion_periodica()