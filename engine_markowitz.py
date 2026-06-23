import os
import numpy as np
import pandas as pd
import cvxpy as cp

from pypfopt import EfficientFrontier, risk_models


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_MARKOWITZ_DIR = os.path.join(
    BASE_DIR,
    "inputs",
    "Markowitz"
)

OUTPUT_MARKOWITZ_DIR = os.path.join(
    BASE_DIR,
    "outputs",
    "Markowitz"
)

CATALOGO_UNIVERSOS = os.path.join(
    INPUT_MARKOWITZ_DIR,
    "CatalogoUniversos.xlsx"
)

os.makedirs(OUTPUT_MARKOWITZ_DIR, exist_ok=True)

# =========================================================
# FINANCIAL ENGINE
# =========================================================

def load_catalogo_universos():
    catalogo = pd.read_excel(
        CATALOGO_UNIVERSOS,
        sheet_name="Universos"
    )

    catalogo.columns = (
        catalogo.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    catalogo = catalogo[catalogo["activo"] == 1].copy()

    return catalogo


def get_default_universe_file(catalogo):
    default_rows = catalogo[catalogo["default"] == 1]

    if not default_rows.empty:
        archivo = default_rows.iloc[0]["archivo"]
    else:
        archivo = catalogo.iloc[0]["archivo"]

    return os.path.join(INPUT_MARKOWITZ_DIR, archivo)

def load_input_excel(path):
    universo_df = pd.read_excel(path, sheet_name="Activos")
    universo_df.columns = (
        universo_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    universo_df["alias"] = universo_df["alias"].astype(str).str.strip()

    required = [
        "categoria_general",
        "subcategoria",
        "alias",
        "nombre_formal",
        "retorno_default",
        "min_default",
        "max_default",
        "volatilidad_default",
        "default"
    ]

    missing = [c for c in required if c not in universo_df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en Activos: {missing}")

    for col in ["vehiculo_sugerido", "fee", "taxes", "alpha"]:
        if col not in universo_df.columns:
            universo_df[col] = ""

    corr = pd.read_excel(path, sheet_name="Correlacion", index_col=0)
    corr.index = corr.index.astype(str).str.strip()
    corr.columns = corr.columns.astype(str).str.strip()

    aliases = universo_df["alias"].tolist()

    missing_rows = [a for a in aliases if a not in corr.index]
    missing_cols = [a for a in aliases if a not in corr.columns]

    if missing_rows:
        raise ValueError(f"Faltan filas en Correlacion: {missing_rows}")
    if missing_cols:
        raise ValueError(f"Faltan columnas en Correlacion: {missing_cols}")

    selected = universo_df.loc[
        universo_df["default"] == 1,
        "alias"
    ].tolist()

    groups = []

    try:
        grupos_df = pd.read_excel(path, sheet_name="Grupos_Default")
        grupos_df.columns = (
            grupos_df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        temp = {}

        for _, row in grupos_df.iterrows():
            nombre = str(row["nombre_grupo"]).strip()
            alias_activo = str(row["alias_activo"]).strip()

            if alias_activo not in aliases:
                continue

            if nombre not in temp:
                temp[nombre] = {
                    "nombre": nombre,
                    "activos": [],
                    "min": float(row["min_grupo_%"]) / 100,
                    "max": float(row["max_grupo_%"]) / 100
                }

            temp[nombre]["activos"].append(alias_activo)

        groups = list(temp.values())

    except Exception:
        groups = []

    return universo_df, corr, selected, groups


def build_covariance(corr_master, activos, sigmas):
    corr_sub = corr_master.loc[activos, activos].astype(float)
    corr_sub = (corr_sub + corr_sub.T) / 2
    np.fill_diagonal(corr_sub.values, 1.0)

    sigma_vec = pd.Series(
        {a: sigmas[a] for a in activos},
        index=activos
    )

    D = np.diag(sigma_vec.values)
    cov = D @ corr_sub.values @ D

    S = pd.DataFrame(cov, index=activos, columns=activos)

    S = risk_models.fix_nonpositive_semidefinite(
        S,
        fix_method="spectral"
    )

    return S


def calculate_frontier(mu, S, nombre, minimos, maximos, grupos, activos, tipo_curva):
    n_points = 100

    max_ret = mu.max()
    min_ret = mu.min()

    if max_ret <= min_ret:
        raise ValueError("Los retornos esperados no permiten construir una frontera.")

    target_returns = np.linspace(min_ret, max_ret - 0.0001, n_points)

    rendimientos = []
    desviaciones = []
    pesos = []

    bounds = [(minimos[a], maximos[a]) for a in activos]

    for target in target_returns:
        try:
            ef = EfficientFrontier(mu, S, weight_bounds=bounds)

            for grupo in grupos:
                activos_grupo = [a for a in grupo["activos"] if a in activos]

                if not activos_grupo:
                    continue

                idx = [activos.index(a) for a in activos_grupo]

                ef.add_constraint(
                    lambda w, idx=idx, min_g=grupo["min"]: cp.sum(w[idx]) >= min_g
                )
                ef.add_constraint(
                    lambda w, idx=idx, max_g=grupo["max"]: cp.sum(w[idx]) <= max_g
                )

            ef.efficient_return(target_return=target)

            w = ef.clean_weights()
            ret, vol, _ = ef.portfolio_performance()

            rendimientos.append(ret)
            desviaciones.append(vol)
            pesos.append(w)

        except Exception:
            continue

    if not pesos:
        raise ValueError("No se pudo construir la frontera con esos supuestos/restricciones.")

    pesos_df = pd.DataFrame(pesos, columns=activos) * 100

    frontera = pesos_df.copy()
    frontera.insert(0, "Alpha_Ponderado_%", 0.0)
    frontera.insert(0, "Taxes_Ponderado_%", 0.0)
    frontera.insert(0, "Fee_Ponderado_%", 0.0)
    frontera.insert(0, "Impacto_Neto_%", 0.0)
    frontera.insert(0, "Rendimiento_Neto_%", np.array(rendimientos) * 100)
    frontera.insert(0, "Rendimiento_Bruto_%", np.array(rendimientos) * 100)
    frontera.insert(0, "Rendimiento_Grafica_%", np.array(rendimientos) * 100)
    frontera.insert(0, "Desviacion_Estandar_%", np.array(desviaciones) * 100)
    frontera.insert(0, "Tipo_Curva", tipo_curva)
    frontera.insert(0, "Optimizacion", nombre)

    frontera["Asset_Allocation"] = frontera.apply(
        lambda row: "<br>".join([
            f"{asset}: {row[asset]:.2f}%"
            for asset in activos
        ]),
        axis=1
    )

    return frontera


def translate_frontier_to_vehicles(frontera_base, nombre, activos, vehiculos, fee, taxes, alpha):
    rows = []

    for _, row in frontera_base.iterrows():
        fee_p = 0.0
        taxes_p = 0.0
        alpha_p = 0.0

        for asset in activos:
            peso = row[asset] / 100
            fee_p += peso * fee[asset]
            taxes_p += peso * taxes[asset]
            alpha_p += peso * alpha[asset]

        impacto = -fee_p - taxes_p + alpha_p
        ret_bruto = row["Rendimiento_Bruto_%"] / 100
        ret_neto = ret_bruto + impacto

        nueva = row.copy()
        nueva["Optimizacion"] = nombre
        nueva["Tipo_Curva"] = "Vehiculos"
        nueva["Rendimiento_Grafica_%"] = ret_neto * 100
        nueva["Rendimiento_Neto_%"] = ret_neto * 100
        nueva["Fee_Ponderado_%"] = fee_p * 100
        nueva["Taxes_Ponderado_%"] = taxes_p * 100
        nueva["Alpha_Ponderado_%"] = alpha_p * 100
        nueva["Impacto_Neto_%"] = impacto * 100

        nueva["Asset_Allocation"] = "<br>".join([
            f"{vehiculos.get(asset, asset)}: {nueva[asset]:.2f}%"
            for asset in activos
        ])

        rows.append(nueva)

    return pd.DataFrame(rows)


def add_vehicle_metrics_to_reopt(frontera, activos, vehiculos, fee, taxes, alpha):
    rows = []

    for _, row in frontera.iterrows():
        fee_p = 0.0
        taxes_p = 0.0
        alpha_p = 0.0

        for asset in activos:
            peso = row[asset] / 100
            fee_p += peso * fee[asset]
            taxes_p += peso * taxes[asset]
            alpha_p += peso * alpha[asset]

        impacto = -fee_p - taxes_p + alpha_p

        nueva = row.copy()
        nueva["Fee_Ponderado_%"] = fee_p * 100
        nueva["Taxes_Ponderado_%"] = taxes_p * 100
        nueva["Alpha_Ponderado_%"] = alpha_p * 100
        nueva["Impacto_Neto_%"] = impacto * 100
        nueva["Rendimiento_Neto_%"] = nueva["Rendimiento_Grafica_%"]

        nueva["Asset_Allocation"] = "<br>".join([
            f"{vehiculos.get(asset, asset)}: {nueva[asset]:.2f}%"
            for asset in activos
        ])

        rows.append(nueva)

    return pd.DataFrame(rows)

