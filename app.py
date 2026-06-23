import os

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from engine_markowitz import *


PIE_COLORS = [
    "#FF6B00", "#00D4FF", "#00C853", "#9C27B0", "#FFD600",
    "#FF4081", "#26A69A", "#5C6BC0", "#8D6E63", "#42A5F5",
    "#EC407A", "#7CB342", "#FFA726", "#AB47BC", "#78909C"
]

BBG_ORANGE = "#FF6B00"
BBG_BLUE = "#00D4FF"
BBG_GREEN = "#00C853"
BBG_GRAY = "#94A3B8"

BG_MAIN = "#0E1116"
BG_PANEL = "#161B22"
TEXT_PRIMARY = "#F3F4F6"
TEXT_SECONDARY = "#9CA3AF"
GRID = "#2D333B"
logo_path = os.path.join("assets", "opt_logo2.png")

st.set_page_config(
    page_title="OptymaR",
    layout="wide"
)
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
    }}

    h1, h2, h3 {{
        color: {BBG_ORANGE};
    }}

    section[data-testid="stSidebar"] {{
        background-color: #0B0F14;
        border-right: 1px solid {GRID};
    }}

    section[data-testid="stSidebar"] * {{
        color: {TEXT_PRIMARY};
    }}
    section[data-testid="stSidebar"] .optymar-title {{
        color: #FF6B00 !important;
        font-size: 50px;
        font-weight: 800;
        display: flex;
        align-items: center;
    
        height: 220px;
    }}
    input, textarea, select {{
        background-color: {BG_PANEL} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {GRID} !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: {BG_PANEL} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {GRID} !important;
    }}

    div[data-testid="stExpander"] {{
        background-color: {BG_PANEL};
        border: 1px solid {GRID};
        border-radius: 8px;
    }}

    details[data-testid="stExpander"] > summary {{
        background-color: {BG_PANEL} !important;
        border-radius: 8px !important;
    }}

    details[data-testid="stExpander"] > summary:hover {{
        background-color: #1F2937 !important;
    }}

    details[data-testid="stExpander"] summary * {{
        color: {TEXT_PRIMARY} !important;
    }}

    .stButton > button {{
        background-color: {BBG_ORANGE};
        color: white !important;
        border: 1px solid {BBG_ORANGE};
        border-radius: 6px;
        font-weight: 700;
    }}

    .stButton > button:hover {{
        background-color: #FF8C2B;
        border-color: #FF8C2B;
        color: white !important;
    }}

    .stButton > button[kind="secondary"] {{
        background-color: {BG_PANEL};
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {GRID};
    }}

    .stButton > button[kind="secondary"]:hover {{
        background-color: #1F2937;
        color: {BBG_ORANGE} !important;
        border-color: {BBG_ORANGE};
    }}

    div[data-testid="stDataFrame"] {{
        background-color: {BG_PANEL};
        border: 1px solid {GRID};
        border-radius: 8px;
    }}

    div[data-testid="stDataFrame"] div[role="grid"] {{
        background-color: {BG_PANEL};
        color: {TEXT_PRIMARY};
    }}

    div[data-testid="stDataFrame"] div[role="columnheader"] {{
        background-color: #0B0F14;
        color: {BBG_ORANGE};
        font-weight: 700;
        border-bottom: 1px solid {GRID};
    }}

    div[data-testid="stDataFrame"] div[role="gridcell"] {{
        background-color: {BG_PANEL};
        color: {TEXT_PRIMARY};
        border-color: {GRID};
    }}

    div[data-testid="stDataFrame"] div[role="row"]:hover div[role="gridcell"] {{
        background-color: #1F2937;
    }}


    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SESSION STATE
# =========================================================

if "optimizaciones" not in st.session_state:
    st.session_state.optimizaciones = []

if "clicked_points" not in st.session_state:
    st.session_state.clicked_points = []

if "opt_counter" not in st.session_state:
    st.session_state.opt_counter = 1

if "ignore_chart_event" not in st.session_state:
    st.session_state.ignore_chart_event = False

if "current_universe" not in st.session_state:
    st.session_state.current_universe = None

if "selected_assets" not in st.session_state:
    st.session_state.selected_assets = []

if "groups" not in st.session_state:
    st.session_state.groups = []

if "show_add_asset" not in st.session_state:
    st.session_state.show_add_asset = False

if "show_add_group" not in st.session_state:
    st.session_state.show_add_group = False

if "show_vehicle_panel" not in st.session_state:
    st.session_state.show_vehicle_panel = False

if "assets_grid_version" not in st.session_state:
    st.session_state.assets_grid_version = 0

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:


    logo_col, title_col = st.columns([1, 2])

    with logo_col:
        st.image(
            logo_path,
            width=150
        )

    with title_col:
        st.markdown(
            f"""
            <div class="optymar-title">
                OptymaR
            </div>
            """,
            unsafe_allow_html=True
        )

    st.header("Configuración")

    catalogo = load_catalogo_universos()

    universo = st.selectbox(
        "Universo",
        catalogo["nombrevisible"]
    )

    row = catalogo.loc[
        catalogo["nombrevisible"] == universo
    ].iloc[0]

    input_file = os.path.join(
        INPUT_MARKOWITZ_DIR,
        row["archivo"]
    )

    universo_df, corr_master, selected_assets_default, groups_default = load_input_excel(
        input_file
    )

    if (
            not st.session_state.selected_assets
            or st.session_state.current_universe != universo
    ):
        st.session_state.current_universe = universo
        st.session_state.selected_assets = selected_assets_default.copy()
        st.session_state.groups = groups_default.copy()
        st.session_state.optimizaciones = []
        st.session_state.clicked_points = []
        st.session_state.opt_counter = 1
        st.session_state.show_vehicle_panel = False
        st.session_state.assets_grid_version += 1

    editable_df = universo_df[
        universo_df["alias"].isin(st.session_state.selected_assets)
    ][[
        "alias",
        "retorno_default",
        "volatilidad_default",
        "min_default",
        "max_default"
    ]].copy()

    if "show_assets_panel" not in st.session_state:
        st.session_state.show_assets_panel = False

    if st.button(
            "Activos y supuestos (%)",
            key="btn_toggle_assets_panel",
            type="secondary"
    ):
        st.session_state.show_assets_panel = not st.session_state.show_assets_panel

    if st.session_state.show_assets_panel:
        # aquí va TODO el contenido que antes estaba dentro del expander

        editable_df = universo_df[
            universo_df["alias"].isin(st.session_state.selected_assets)
        ][[
            "alias",
            "retorno_default",
            "volatilidad_default",
            "min_default",
            "max_default"
        ]].copy()

        editable_df["quitar"] = False

        gb_assets = GridOptionsBuilder.from_dataframe(editable_df)

        gb_assets.configure_default_column(
            editable=True,
            sortable=False,
            filter=False,
            resizable=True
        )

        gb_assets.configure_column(
            "alias",
            header_name="Activo",
            editable=False,
            width=150
        )

        gb_assets.configure_column(
            "retorno_default",
            header_name="Ret",
            type=["numericColumn"],
            width=70
        )

        gb_assets.configure_column(
            "volatilidad_default",
            header_name="Riesgo",
            type=["numericColumn"],
            width=75
        )

        gb_assets.configure_column(
            "min_default",
            header_name="Mín",
            type=["numericColumn"],
            width=65
        )

        gb_assets.configure_column(
            "max_default",
            header_name="Máx",
            type=["numericColumn"],
            width=65
        )

        gb_assets.configure_column(
            "quitar",
            header_name="✕",
            editable=True,
            width=55
        )


        grid_assets = AgGrid(
            editable_df,
            gridOptions=gb_assets.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED,
            theme="alpine-dark",
            height=220,
            columns_auto_size_mode=None,
            allow_unsafe_jscode=True,
            custom_css={
                ".ag-root-wrapper": {
                    "background-color": "#161B22",
                    "border": "1px solid #2D333B",
                    "border-radius": "8px"
                },
                ".ag-header": {
                    "background-color": "#0B0F14",
                    "color": "#FF6B00"
                },
                ".ag-row": {
                    "background-color": "#161B22",
                    "color": "#F3F4F6"
                },
                ".ag-cell": {
                    "border-color": "#2D333B"
                },
                ".ag-center-cols-viewport": {
                    "background-color": "#161B22"
                },
                ".ag-center-cols-container": {
                    "background-color": "#161B22"
                },
                ".ag-body-viewport": {
                    "background-color": "#161B22"
                },
                ".ag-root-wrapper": {
                    "background-color": "#161B22",
                    "border": "1px solid #2D333B",
                    "border-radius": "8px"
                },
                ".ag-header": {
                    "background-color": "#0B0F14",
                    "color": "#FF6B00",
                    "font-size": "13px",
                    "font-weight": "700"
                },
                ".ag-row": {
                    "background-color": "#161B22",
                    "color": "#F3F4F6",
                    "font-size": "13px"
                },
                ".ag-cell": {
                    "border-color": "#2D333B"
                }
            },
            key=f"activos_aggrid_{st.session_state.current_universe}_{st.session_state.assets_grid_version}_{len(editable_df)}"
        )


        editable_df = pd.DataFrame(grid_assets["data"])

        for col in [
            "retorno_default",
            "volatilidad_default",
            "min_default",
            "max_default"
        ]:
            editable_df[col] = pd.to_numeric(
                editable_df[col],
                errors="coerce"
            ).fillna(0.0)

        activos_a_quitar = editable_df.loc[
            editable_df["quitar"] == True,
            "alias"
        ].tolist()

        if activos_a_quitar:
            if st.button(
                    f"Eliminar {len(activos_a_quitar)} activo(s)",
                    key="btn_delete_selected_assets",
                    type="secondary"
            ):
                st.session_state.selected_assets = [
                    a for a in st.session_state.selected_assets
                    if a not in activos_a_quitar
                ]

                st.session_state.assets_grid_version += 1
                st.rerun()

        if st.button("➕ Agregar activo", key="btn_show_add_asset"):
            st.session_state.show_add_asset = not st.session_state.show_add_asset

        if st.session_state.show_add_asset:

            st.markdown("**Agregar activo**")

            cat_options = sorted(
                universo_df["categoria_general"].dropna().unique().tolist()
            )

            cat_sel = st.selectbox(
                "Categoría",
                cat_options,
                key="add_asset_category"
            )

            subcat_options = sorted(
                universo_df.loc[
                    universo_df["categoria_general"] == cat_sel,
                    "subcategoria"
                ].dropna().unique().tolist()
            )

            subcat_sel = st.selectbox(
                "Subcategoría",
                subcat_options,
                key="add_asset_subcategory"
            )

            candidatos = universo_df.loc[
                (universo_df["categoria_general"] == cat_sel) &
                (universo_df["subcategoria"] == subcat_sel) &
                (~universo_df["alias"].isin(st.session_state.selected_assets)),
                "alias"
            ].tolist()

            if candidatos:

                asset_sel = st.selectbox(
                    "Activo",
                    candidatos,
                    key="add_asset_alias"
                )

                if st.button("Agregar", key="btn_add_asset"):
                    if len(st.session_state.selected_assets) >= 15:
                        st.warning("Máximo 15 activos seleccionados.")
                    else:
                        st.session_state.selected_assets.append(asset_sel)
                        st.session_state.assets_grid_version += 1
                        st.session_state.show_add_asset = False
                        st.rerun()

            else:
                st.info("No hay activos disponibles para agregar en esta categoría.")

    with st.expander("Restricciones de grupo", expanded=False):

        grupos_editados = []

        if not st.session_state.groups:
            st.info("Este universo no tiene restricciones de grupo.")

        for i, grupo in enumerate(st.session_state.groups):

            activo_g = st.checkbox(
                f"{grupo['nombre']}",
                value=grupo.get("activo", True),
                key=f"group_active_{i}"
            )

            col_min, col_max = st.columns(2)

            with col_min:
                min_g = st.number_input(
                    "Min %",
                    value=float(grupo["min"] * 100),
                    step=1.0,
                    key=f"group_min_{i}"
                )

            with col_max:
                max_g = st.number_input(
                    "Max %",
                    value=float(grupo["max"] * 100),
                    step=1.0,
                    key=f"group_max_{i}"
                )

            st.caption(
                ", ".join(grupo["activos"])
            )

            if activo_g:
                grupos_editados.append(
                    {
                        "nombre": grupo["nombre"],
                        "activos": grupo["activos"],
                        "min": min_g / 100,
                        "max": max_g / 100,
                        "activo": True
                    }
                )

            st.divider()

        st.markdown("**Agregar restricción de grupo**")

        if st.button("➕ Agregar grupo"):
            st.session_state.show_add_group = not st.session_state.show_add_group

        if st.session_state.show_add_group:

            nuevo_nombre = st.text_input(
                "Nombre del grupo",
                key="new_group_name"
            )

            nuevos_activos = st.multiselect(
                "Activos del grupo",
                options=st.session_state.selected_assets,
                key="new_group_assets"
            )

            col_new_min, col_new_max = st.columns(2)

            with col_new_min:
                nuevo_min = st.number_input(
                    "Min nuevo %",
                    value=0.0,
                    step=1.0,
                    key="new_group_min"
                )

            with col_new_max:
                nuevo_max = st.number_input(
                    "Max nuevo %",
                    value=100.0,
                    step=1.0,
                    key="new_group_max"
                )

            if st.button("Guardar grupo"):
                if not nuevo_nombre.strip():
                    st.warning("El grupo necesita nombre.")
                elif not nuevos_activos:
                    st.warning("Selecciona al menos un activo.")
                elif nuevo_min > nuevo_max:
                    st.warning("El mínimo no puede exceder el máximo.")
                else:
                    st.session_state.groups.append(
                        {
                            "nombre": nuevo_nombre.strip(),
                            "activos": nuevos_activos,
                            "min": nuevo_min / 100,
                            "max": nuevo_max / 100,
                            "activo": True
                        }
                    )
                    st.session_state.show_add_group = False
                    st.rerun()

        groups = grupos_editados

    calcular = st.button("Calcular simulación",key="btn_calcular",type="primary")

    if st.button("Traducir última OPT a vehículos",key="btn_vehiculos",type="primary"):
        st.session_state.show_vehicle_panel = not st.session_state.show_vehicle_panel

    if st.button("Limpiar optimizaciones",key="btn_limpiar_opts",type="secondary"):
        st.session_state.optimizaciones = []
        st.session_state.clicked_points = []
        st.session_state.opt_counter = 1
        st.session_state.show_vehicle_panel = False
        st.rerun()


# =========================================================
# CALCULAR OPTIMIZACIÓN
# =========================================================

if calcular:

    activos = editable_df["alias"].tolist()

    mu = pd.Series(
        editable_df["retorno_default"].values / 100,
        index=activos
    )

    sigmas = dict(
        zip(
            activos,
            editable_df["volatilidad_default"] / 100
        )
    )

    minimos = dict(
        zip(
            activos,
            editable_df["min_default"] / 100
        )
    )

    maximos = dict(
        zip(
            activos,
            editable_df["max_default"] / 100
        )
    )

    S = build_covariance(
        corr_master,
        activos,
        sigmas
    )

    nombre_opt = f"OPT {st.session_state.opt_counter}"

    frontera = calculate_frontier(
        mu,
        S,
        nombre_opt,
        minimos,
        maximos,
        groups,
        activos,
        "OPT"
    )

    st.session_state.optimizaciones.append(
        {
            "nombre": nombre_opt,
            "tipo": "OPT",
            "df": frontera,
            "activos": activos,
            "labels": {a: a for a in activos},
            "mu": mu,
            "S": S,
            "minimos": minimos,
            "maximos": maximos,
            "groups": groups,
            "frontera_base": frontera.copy()
        }
    )

    st.session_state.opt_counter += 1
    st.session_state.clicked_points = []

    # Corrige el bug: permite que el panel de vehículos vea la OPT recién creada.
    st.rerun()


# =========================================================
# MAIN LAYOUT
# =========================================================

if st.session_state.show_vehicle_panel and st.session_state.optimizaciones:
    main_col, vehicle_col = st.columns([5, 1.6])
else:
    main_col = st.container()
    vehicle_col = None


with main_col:

    if st.session_state.optimizaciones:

        opt_actual = st.session_state.optimizaciones[-1]
        frontera = opt_actual["df"]
        activos = opt_actual["activos"]

        fig = go.Figure()

        for curve_idx, opt_i in enumerate(st.session_state.optimizaciones):

            frontera_i = opt_i["df"]
            nombre_i = opt_i["nombre"]

            tipo_i = opt_i.get("tipo", "OPT")

            if tipo_i == "OPT":
                line_color = BBG_ORANGE
                line_dash = "dot"
                line_width = 3
            elif tipo_i == "Vehiculos":
                line_color = BBG_BLUE
                line_dash = "solid"
                line_width = 2
            else:
                line_color = BBG_GREEN
                line_dash = "solid"
                line_width = 2

            selected_points_curve = {
                p["point"]
                for p in st.session_state.clicked_points
                if p["curve"] == curve_idx
            }

            marker_colors = [
                "#FFFFFF" if i in selected_points_curve else line_color
                for i in range(len(frontera_i))
            ]

            marker_sizes = [
                13 if i in selected_points_curve else 5
                for i in range(len(frontera_i))
            ]

            fig.add_trace(
                go.Scatter(
                    x=frontera_i["Desviacion_Estandar_%"],
                    y=frontera_i["Rendimiento_Grafica_%"],
                    customdata=list(range(len(frontera_i))),
                    mode="lines+markers",
                    name=nombre_i,
                    line=dict(
                        color=line_color,
                        width=line_width,
                        dash=line_dash
                    ),
                    marker=dict(
                        color=marker_colors,
                        size=marker_sizes
                    ),
                    hovertemplate=(
                        "<b>%{fullData.name}</b><br>"
                        "Punto %{customdata}<br>"
                        "Volatilidad: %{x:.2f}%<br>"
                        "Retorno: %{y:.2f}%"
                        "<extra></extra>"
                    )
                )
            )

        fig.update_layout(
            template="plotly_dark",
            title="Optimización",
            xaxis_title="Desviación estándar anual (%)",
            yaxis_title="Rendimiento esperado anual (%)",
            height=650,
            margin=dict(l=60, r=30, t=60, b=60),
            paper_bgcolor=BG_MAIN,
            plot_bgcolor=BG_PANEL,
            font=dict(color=TEXT_PRIMARY)
        )

        event = st.plotly_chart(
            fig,
            use_container_width=True,
            theme=None,
            on_select="rerun",
            selection_mode="points",
            key="frontier_chart"
        )

        if st.session_state.ignore_chart_event:
            st.session_state.ignore_chart_event = False
        else:
            try:
                points = event["selection"]["points"]

                if points:
                    clicked_idx = int(points[0]["point_index"])
                    curve_idx = int(points[0]["curve_number"])

                    clicked_key = {
                        "curve": curve_idx,
                        "point": clicked_idx
                    }

                    if clicked_key not in st.session_state.clicked_points:
                        st.session_state.clicked_points.append(clicked_key)
                        st.rerun()

            except Exception:
                pass

        if st.session_state.clicked_points:

            max_pie_cols = min(
                max(len(st.session_state.clicked_points), 2),
                4
            )

            legend_col, *pie_cols = st.columns(
                [0.8] + [1] * max_pie_cols
            )

            with legend_col:

                st.subheader("Comparar mezclas")
                st.markdown("### Leyenda")

                for i, asset in enumerate(activos):
                    st.markdown(
                        f"""
                        <div style="
                            font-size:14px;
                            margin-bottom:8px;
                            color:{PIE_COLORS[i % len(PIE_COLORS)]};
                            font-weight:600;
                        ">
                            ■ {asset}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            for j, selected in enumerate(st.session_state.clicked_points):

                curve_idx = selected["curve"]
                punto_idx = selected["point"]


                opt_sel = st.session_state.optimizaciones[curve_idx]
                tipo_sel = opt_sel.get("tipo", "OPT")
                frontera_sel = opt_sel["df"]
                activos_sel = opt_sel["activos"]
                nombre_sel = opt_sel["nombre"]

                punto = frontera_sel.iloc[punto_idx]

                impacto_fee = -punto.get("Fee_Ponderado_%", 0.0)
                impacto_tax = -punto.get("Taxes_Ponderado_%", 0.0)
                impacto_alpha = punto.get("Alpha_Ponderado_%", 0.0)
                impacto_neto = punto.get("Impacto_Neto_%", 0.0)

                col = pie_cols[j % max_pie_cols]

                with col:

                    header_left, header_right = st.columns([5, 1])
                    tipo_sel = opt_sel.get("tipo", "OPT")

                    if tipo_sel == "OPT":
                        header_color = BBG_ORANGE
                    elif tipo_sel == "Vehiculos":
                        header_color = BBG_BLUE
                    else:
                        header_color = BBG_GREEN

                    with header_left:
                        st.markdown(
                            f"""
                            <div style="
                                color:{header_color};
                                border:2px solid {header_color};
                                border-radius:8px;
                                background-color:{BG_PANEL};
                                font-weight:700;
                                font-size:13px;
                                padding:6px 10px;
                                margin-bottom:6px;
                                text-align:center;
                            ">
                                {nombre_sel} | P{punto_idx}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with header_right:
                        if st.button(
                            "✕",
                            key=f"remove_pie_{curve_idx}_{punto_idx}_{j}"
                        ):
                            st.session_state.clicked_points = [
                                p for p in st.session_state.clicked_points
                                if not (
                                    p["curve"] == curve_idx
                                    and p["point"] == punto_idx
                                )
                            ]
                            st.session_state.ignore_chart_event = True
                            st.rerun()

                    pesos = punto[activos_sel]

                    pie_left, pie_right = st.columns([2.2, 0.9])
                    pie_fig = go.Figure(
                        data=[
                            go.Pie(
                                labels=activos_sel,
                                values=pesos,
                                hole=0.45,
                                textinfo="percent",
                                marker=dict(
                                    colors=PIE_COLORS[:len(activos_sel)]
                                )
                            )
                        ]
                    )

                    pie_fig.update_layout(
                        template="plotly_dark",
                        height=280,
                        margin=dict(l=5, r=5, t=5, b=5),
                        showlegend=False,
                        paper_bgcolor="#0E1116",
                        plot_bgcolor="#161B22",
                        font=dict(
                            color="#F3F4F6",
                            size=14
                        ),
                        annotations=[
                            dict(
                                text=(
                                    f"Ret {punto['Rendimiento_Grafica_%']:.2f}%<br>"
                                    f"Vol {punto['Desviacion_Estandar_%']:.2f}%"
                                ),
                                x=0.5,
                                y=0.5,
                                font=dict(
                                    size=17,
                                    color="#F3F4F6"
                                ),
                                showarrow=False
                            )
                        ]
                    )
                    with pie_left:
                        st.plotly_chart(
                            pie_fig,
                            use_container_width=True,
                            theme=None
                        )
                    with pie_right:
                        if tipo_sel == "OPT":
                            st.markdown(
                                """
                                <div style="
                                    font-size:12px;
                                    line-height:1.6;
                                    padding-top:52px;
                                    color:#9CA3AF;
                                ">
                                    <b></b><br>
                                    <br>
                                    
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                           <div style="
                                               font-size:16px;
                                               line-height:1.6;
                                               padding-top:38px;
                                           ">
                                               <b>Impacto</b><br>
                                               Com&nbsp;&nbsp; {impacto_fee:.2f}%<br>
                                               Imp&nbsp;&nbsp; {impacto_tax:.2f}%<br>
                                               α&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {impacto_alpha:.2f}%<br>
                                               <b>Neto {impacto_neto:.2f}%</b>
                                           </div>
                                           """,
                                unsafe_allow_html=True
                            )
            if st.button("Limpiar puntos seleccionados"):
                st.session_state.clicked_points = []
                st.session_state.ignore_chart_event = True
                st.rerun()

    else:
        #st.info("Configura los activos y presiona **Calcular simulación**.")
        st.image(
            logo_path,
            width=1000
        )


# =========================================================
# RIGHT VEHICLE PANEL
# =========================================================

    if vehicle_col is not None:

        with vehicle_col:

            st.subheader("Vehículos")

            if st.button("Cerrar panel", key="close_vehicle_panel"):
                st.session_state.show_vehicle_panel = False
                st.rerun()

            opts_base = [
                opt for opt in st.session_state.optimizaciones
                if opt.get("tipo") == "OPT"
            ]

            if not opts_base:
                st.info("Primero calcula una optimización base.")
                st.stop()

            ultima = opts_base[-1]
            activos_ult = ultima["activos"]

            veh_df = universo_df[
                universo_df["alias"].isin(activos_ult)
            ][[
                "alias",
                "vehiculo_sugerido",
                "fee",
                "taxes",
                "alpha"
            ]].copy()

            for col in ["fee", "taxes", "alpha"]:
                veh_df[col] = pd.to_numeric(
                    veh_df[col],
                    errors="coerce"
                ).fillna(0.0)

            veh_df["display_name"] = (
                    veh_df["vehiculo_sugerido"].fillna("")
                    + " | "
                    + veh_df["alias"]
            )

            veh_left_col, veh_right_col = st.columns([5, 1])

            with veh_left_col:

                for col in ["fee", "taxes", "alpha"]:
                    veh_df[col] = veh_df[col].round(2)

                veh_edit_df = veh_df[
                    [
                        "display_name",
                        "fee",
                        "taxes",
                        "alpha",
                        "alias",
                        "vehiculo_sugerido"
                    ]
                ].copy()

                gb = GridOptionsBuilder.from_dataframe(veh_edit_df)

                gb.configure_default_column(
                    editable=True,
                    sortable=False,
                    filter=False,
                    resizable=True
                )

                gb.configure_column(
                    "display_name",
                    header_name="Vehículo",
                    editable=False,
                    width=280
                )

                gb.configure_column(
                    "fee",
                    header_name="Com",
                    type=["numericColumn"],
                    width=80
                )

                gb.configure_column(
                    "taxes",
                    header_name="Imp",
                    type=["numericColumn"],
                    width=80
                )

                gb.configure_column(
                    "alpha",
                    header_name="α",
                    type=["numericColumn"],
                    width=80
                )

                gb.configure_column("alias", hide=True)
                gb.configure_column("vehiculo_sugerido", hide=True)

                grid_response = AgGrid(
                    veh_edit_df,
                    gridOptions=gb.build(),
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    theme="alpine-dark",
                    height=250,
                    allow_unsafe_jscode=True,
                    custom_css={
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },
                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00"
                        },
                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6"
                        },
                        ".ag-center-cols-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-center-cols-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },

                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00",
                            "font-size": "13px",
                            "font-weight": "700"
                        },

                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6",
                            "font-size": "13px"
                        },

                        ".ag-cell": {
                            "border-color": "#2D333B"
                        }
                    },
                    key="vehiculos_aggrid"
                )

                veh_df = pd.DataFrame(grid_response["data"])

            for col in ["fee", "taxes", "alpha"]:
                veh_df[col] = pd.to_numeric(
                    veh_df[col],
                    errors="coerce"
                ).fillna(0.0)

            veh_df["rend_final"] = veh_df.apply(
                lambda row: (
                        ultima["mu"][row["alias"]] * 100
                        - row["fee"]
                        - row["taxes"]
                        + row["alpha"]
                ),
                axis=1
            ).round(2)

            with veh_right_col:

                rend_df = veh_df[["rend_final"]].copy()
                rend_df.columns = ["Rend"]

                gb_r = GridOptionsBuilder.from_dataframe(rend_df)

                gb_r.configure_default_column(
                    editable=False,
                    sortable=False,
                    filter=False,
                    resizable=False
                )

                AgGrid(
                    rend_df,
                    gridOptions=gb_r.build(),
                    theme="alpine-dark",
                    height=250,
                    allow_unsafe_jscode=True,
                    custom_css={
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },
                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00"
                        },
                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6"
                        },
                        ".ag-center-cols-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-center-cols-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },
                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00",
                            "font-size": "13px",
                            "font-weight": "700"
                        },
                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6",
                            "font-size": "13px"
                        },
                        ".ag-cell": {
                            "border-color": "#2D333B"
                        }
                    },
                    key="rend_aggrid"
                )

            st.divider()

            if st.button(
                    "Aplicar vehículos",
                    key="apply_vehicles_btn",
                    type="primary"
            ):

                fee = dict(zip(veh_df["alias"], veh_df["fee"] / 100))
                taxes = dict(zip(veh_df["alias"], veh_df["taxes"] / 100))
                alpha = dict(zip(veh_df["alias"], veh_df["alpha"] / 100))

                vehiculos = dict(
                    zip(
                        veh_df["alias"],
                        veh_df["vehiculo_sugerido"].fillna(veh_df["alias"])
                    )
                )

                mu_neto = {}

                for asset in activos_ult:
                    mu_neto[asset] = (
                            ultima["mu"][asset]
                            - fee[asset]
                            - taxes[asset]
                            + alpha[asset]
                    )

                mu_neto = pd.Series(mu_neto, index=activos_ult)

                nombre_base = ultima["nombre"]

                frontera_vehiculos = translate_frontier_to_vehicles(
                    ultima["frontera_base"],
                    f"{nombre_base} - Vehículos",
                    activos_ult,
                    vehiculos,
                    fee,
                    taxes,
                    alpha
                )

                frontera_vopt = calculate_frontier(
                    mu_neto,
                    ultima["S"],
                    f"{nombre_base} - V.OPT",
                    ultima["minimos"],
                    ultima["maximos"],
                    ultima["groups"],
                    activos_ult,
                    "V.OPT"
                )

                frontera_vopt = add_vehicle_metrics_to_reopt(
                    frontera_vopt,
                    activos_ult,
                    vehiculos,
                    fee,
                    taxes,
                    alpha
                )

                impacto_resumen = pd.DataFrame(
                    {
                        "Concepto": [
                            "Comisión",
                            "Impuestos",
                            "Alpha",
                            "Neto"
                        ],
                        "Vehículos": [
                            -frontera_vehiculos["Fee_Ponderado_%"].mean(),
                            -frontera_vehiculos["Taxes_Ponderado_%"].mean(),
                            frontera_vehiculos["Alpha_Ponderado_%"].mean(),
                            frontera_vehiculos["Impacto_Neto_%"].mean()
                        ],
                        "V.OPT": [
                            -frontera_vopt["Fee_Ponderado_%"].mean(),
                            -frontera_vopt["Taxes_Ponderado_%"].mean(),
                            frontera_vopt["Alpha_Ponderado_%"].mean(),
                            frontera_vopt["Impacto_Neto_%"].mean()
                        ]
                    }
                ).round(2)

                st.session_state.impacto_vehiculos = impacto_resumen

                st.session_state.optimizaciones.append(
                    {
                        "nombre": f"{nombre_base} - Vehículos",
                        "tipo": "Vehiculos",
                        "df": frontera_vehiculos,
                        "activos": activos_ult,
                        "labels": vehiculos
                    }
                )

                st.session_state.optimizaciones.append(
                    {
                        "nombre": f"{nombre_base} - V.OPT",
                        "tipo": "V.OPT",
                        "df": frontera_vopt,
                        "activos": activos_ult,
                        "labels": vehiculos
                    }
                )

                st.session_state.clicked_points = []
                st.rerun()

            if "impacto_vehiculos" in st.session_state:
                st.divider()
                st.markdown("**Impacto promedio**")

                impacto_df = st.session_state.impacto_vehiculos.copy()

                gb_imp = GridOptionsBuilder.from_dataframe(impacto_df)

                gb_imp.configure_default_column(
                    editable=False,
                    sortable=False,
                    filter=False,
                    resizable=True
                )

                gb_imp.configure_column(
                    "Concepto",
                    header_name="Concepto",
                    width=130
                )

                gb_imp.configure_column(
                    "Vehículos",
                    header_name="Vehículos",
                    type=["numericColumn"],
                    width=100
                )

                gb_imp.configure_column(
                    "V.OPT",
                    header_name="V.OPT",
                    type=["numericColumn"],
                    width=100
                )

                AgGrid(
                    impacto_df,
                    gridOptions=gb_imp.build(),
                    theme="alpine-dark",
                    fit_columns_on_grid_load=False,
                    height=160,
                    allow_unsafe_jscode=True,
                    custom_css={
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },
                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00"
                        },
                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6"
                        },
                        ".ag-center-cols-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-center-cols-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-viewport": {
                            "background-color": "#161B22"
                        },
                        ".ag-body-horizontal-scroll-container": {
                            "background-color": "#161B22"
                        },
                        ".ag-root-wrapper": {
                            "background-color": "#161B22",
                            "border": "1px solid #2D333B",
                            "border-radius": "8px"
                        },
                        ".ag-header": {
                            "background-color": "#0B0F14",
                            "color": "#FF6B00",
                            "font-size": "13px",
                            "font-weight": "700"
                        },
                        ".ag-row": {
                            "background-color": "#161B22",
                            "color": "#F3F4F6",
                            "font-size": "13px"
                        },
                        ".ag-cell": {
                            "border-color": "#2D333B"
                        }
                    },
                    key="impacto_aggrid"
                )
            st.markdown("<br><br>", unsafe_allow_html=True)

            logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])

            with logo_col2:
                st.image(
                    logo_path,
                    width=2400
                )
