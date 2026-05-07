import sys
import os
import json
import math
import io
import pandas as pd
import altair as alt
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.utils import (
    calc_section, calc_capacity, discretize_concrete_core_into_rings,
    steel_ring_area, steel_working_condition_coeff,
    concrete_working_condition_coeff, concrete_strain_by_temp,
)
from app.config import (
    GEOMETRY_LIMITS, MATERIAL_CONSTANTS, CALCULATION_CONFIG, DEFAULT_VALUES
)
from app.validation import validate_all_inputs
from app.calculations import (
    calculate_final_capacity, calculate_capacity_for_time,
    calculate_stiffness_for_time, get_reduction_coeff,
    get_thermal_record_for_time, calculate_time_series,
    calculate_detailed_ring_data, find_fire_resistance_limit
)

# === Общие CSS-стили ===
COMMON_CSS = """
<style>
.rings-table-wrapper { overflow-x: auto; }
.rings-table {
    min-width: 900px;
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 6px 0 rgba(0,0,0,0.04);
    border: 1px solid #e0e0e0;
    font-size: 0.88em;
    table-layout: fixed;
}
.rings-table th {
    background: #f6f8fa;
    color: #222;
    font-weight: 600;
    padding: 10px 12px;
    border-bottom: 1.5px solid #eaecef;
    border-right: 1px solid #e0e0e0;
    white-space: normal;
    word-wrap: break-word;
}
.rings-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #f0f0f0;
    color: #222;
    border-right: 1px solid #e0e0e0;
    text-align: center;
    white-space: normal;
    word-wrap: break-word;
}
.rings-table th:first-child,
.rings-table td:first-child {
    width: 75px;
}
.summary-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 6px 0 rgba(0,0,0,0.04);
    border: 1px solid #e0e0e0;
    font-size: 1.08em;
}
.summary-table th {
    background: #f6f8fa;
    color: #222;
    font-weight: 600;
    padding: 12px 18px;
    border-bottom: 1.5px solid #eaecef;
    border-right: 1px solid #e0e0e0;
}
.summary-table th:last-child { border-right: none; }
.summary-table td {
    padding: 10px 18px;
    border-bottom: 1px solid #f0f0f0;
    color: #222;
    border-right: 1px solid #e0e0e0;
}
.summary-table td:last-child { border-right: none; }
.summary-table tr:last-child td { border-bottom: none; }
.summary-table tr:first-child th:first-child { border-top-left-radius: 8px; }
.summary-table tr:first-child th:last-child { border-top-right-radius: 8px; }
.summary-table tr:last-child td:first-child { border-bottom-left-radius: 8px; }
.summary-table tr:last-child td:last-child { border-bottom-right-radius: 8px; }
.summary-table tr:hover td { background: #f0f6ff; transition: background 0.2s; }
</style>
"""

HEADER_MAP = {
    "No": ("No<br>кольца", ""),
    "R_out": ("Наружный<br>радиус", "R<sub>нар</sub>, мм"),
    "R_in": ("Внутренний<br>радиус", "R<sub>вн</sub>, мм"),
    "area": ("Площадь<br>сечения", "A, мм\u00b2"),
    "temp": ("Температура", "T, \u00b0C"),
    "gamma_bt": ("Коэффициент<br>условий работы<br>бетона", "\u03b3<sub>bt</sub>"),
    "f_bt": ("Расчётное<br>сопротивление<br>бетона", "R<sub>bu</sub>, МПа"),
    "strain": ("Деформация<br>бетона", "\u03b5<sub>yn,t</sub>"),
    "E_bt": ("Модуль<br>деформации<br>бетона", "E<sub>b,t</sub>, МПа"),
    "gamma_st": ("Коэффициент<br>условий работы<br>стали", "\u03b3<sub>st</sub>"),
    "f_st": ("Расчётное<br>сопротивление<br>стали", "R<sub>su</sub>, МПа"),
    "E_st": ("Модуль<br>упругости<br>стали", "E<sub>s,t</sub>, МПа"),
    "I": ("Момент<br>инерции", "I, м\u2074"),
    "N": ("Несущая<br>способность<br>кольца", "N<sub>p,t</sub>, кН"),
    "EI": ("Жёсткость<br>кольца", "EI, кН\u00b7м\u00b2"),
}

TABLE_TITLE_STYLE = 'style="text-align:center; font-size:1.25em; font-weight:700; font-family:Segoe UI, Arial, sans-serif; margin-bottom:0.5em; margin-top:0.5em;"'


# === Вспомогательные функции ===

def fmt_sci_html(val):
    if val is None:
        return "N/A"
    s = f"{val:.2e}"
    if "e" in s:
        base, exponent = s.split("e")
        return f"{base} \u00b7 10<sup>{int(exponent)}</sup>"
    return s


def fmt_sci_latex(val):
    s = f"{val:.2e}"
    if "e" in s:
        base, exponent = s.split("e")
        return f"{base} \\cdot 10^{{{int(exponent)}}}"
    return s


def fmt(val, fmt_str=".1f"):
    return f"{val:{fmt_str}}" if val is not None else "N/A"


def render_html_table(columns, header_map, rows):
    """Рендер HTML-таблицы с заданными столбцами и строками."""
    html = '<div class="rings-table-wrapper"><table class="rings-table"><tr>'
    for col in columns:
        top, bottom = header_map.get(col, (col, ""))
        html += '<th style="vertical-align:middle; padding-bottom:2px; text-align:center;">'
        html += f'<div style="font-weight:600; text-align:center;">{top}</div>'
        if bottom:
            html += f'<div style="font-size:0.92em; color:#888; font-weight:400; text-align:center;">{bottom}</div>'
        html += '</th>'
    html += '</tr>'
    for row in rows:
        html += '<tr>'
        for col in columns:
            html += f'<td>{row.get(col, "N/A")}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html


def build_concrete_row(d):
    return {
        "No": d['label'],
        "R_out": fmt(d['R_out_mm']),
        "R_in": fmt(d['R_in_mm']),
        "area": fmt(d['area_mm2']),
        "temp": fmt(d['temp_celsius']),
        "gamma_bt": fmt(d['gamma'], ".3f"),
        "f_bt": fmt(d['f_fire_mpa']),
        "strain": fmt(d['strain'], ".2f"),
        "E_bt": fmt(d['E_fire_mpa'], ".0f"),
        "I": fmt_sci_html(d['I_m4']),
        "N": fmt(d['N_kn']),
        "EI": fmt(d['EI_knm2']),
    }


def build_steel_row(d):
    return {
        "No": d['label'],
        "R_out": fmt(d['R_out_mm']),
        "R_in": fmt(d['R_in_mm']),
        "area": fmt(d['area_mm2']),
        "temp": fmt(d['temp_celsius']),
        "gamma_st": fmt(d['gamma'], ".3f"),
        "f_st": fmt(d['f_fire_mpa']),
        "E_st": fmt(d['E_fire_mpa'], ".0f"),
        "I": fmt_sci_html(d['I_m4']),
        "N": fmt(d['N_kn']),
        "EI": fmt(d['EI_knm2']),
    }


CONCRETE_COLUMNS = ["No", "R_out", "R_in", "area", "temp", "gamma_bt", "f_bt", "strain", "E_bt", "I", "N", "EI"]
STEEL_COLUMNS = ["No", "R_out", "R_in", "area", "temp", "gamma_st", "f_st", "E_st", "I", "N", "EI"]
REBAR_COLUMNS = ["No", "area", "temp", "gamma_st", "f_st", "E_st", "I", "N", "EI"]


# === Загрузка данных ===

def parse_thermal_filename(name: str):
    name_clean = name.replace('\u0445', 'x').replace('\u0425', 'x')
    parts = name_clean.split('x') if 'x' in name_clean else name_clean.split(',')
    if len(parts) < 2:
        return None
    try:
        diameter_val = float(parts[0].replace(',', '.'))
        thickness_val = float(parts[1].replace(',', '.'))
        rebar_val = float(parts[2].replace(',', '.')) if len(parts) >= 3 else None
        return diameter_val, thickness_val, rebar_val
    except ValueError:
        return None


@st.cache_data(show_spinner="Загрузка температурных данных...")
def load_thermal_data():
    thermal_dir = Path(PROJECT_ROOT) / "thermal_data"
    if not thermal_dir.exists():
        st.error(f"Директория {thermal_dir} не найдена!")
        return {}
    thermal_files = list(thermal_dir.glob("*.json"))
    if not thermal_files:
        st.error(f"JSON файлы не найдены в директории {thermal_dir}!")
        return {}
    thermal_data = {}
    for file in thermal_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            geometry = parse_thermal_filename(file.stem)
            if geometry is None:
                continue
            diameter_val, thickness_val, rebar_val = geometry
            thermal_data[(diameter_val, thickness_val, rebar_val)] = data
        except Exception as e:
            st.error(f"Ошибка при загрузке файла {file.name}: {str(e)}")
    return thermal_data


def get_closest_thermal_data(thermal_data, diameter, thickness, use_reinforcement, rebar_diameter=None):
    if not thermal_data:
        st.error("Нет доступных температурных данных!")
        return None

    key_data = []
    for key, data in thermal_data.items():
        if len(key) == 2:
            diameter_val, thickness_val = key
            rebar_val = None
        else:
            diameter_val, thickness_val, rebar_val = key
        key_data.append((diameter_val, thickness_val, rebar_val, data))

    if use_reinforcement:
        candidates = [k for k in key_data if k[2] is not None]
        if not candidates:
            candidates = key_data
    else:
        candidates = [k for k in key_data if k[2] is None]
        if not candidates:
            candidates = key_data

    if not candidates:
        st.error("Нет доступных размеров в температурных данных!")
        return None

    def distance(item):
        d_val, t_val, r_val, _ = item
        dist = (d_val - diameter) ** 2 + (t_val - thickness) ** 2
        if use_reinforcement and r_val is not None and rebar_diameter is not None:
            dist += (r_val - rebar_diameter) ** 2
        return dist

    closest_diameter, closest_thickness, closest_rebar, closest_data = min(candidates, key=distance)

    if closest_rebar is not None:
        if use_reinforcement:
            st.info(
                f"Температурные данные приняты для диаметра {closest_diameter} мм, "
                f"толщины {closest_thickness} мм и диаметра арматуры {closest_rebar} мм"
            )
        else:
            st.info(
                f"Температурные данные приняты для диаметра {closest_diameter} мм "
                f"и толщины {closest_thickness} мм (файл содержит данные арматуры, но они игнорируются)"
            )
    else:
        st.info(
            f"Температурные данные приняты для диаметра {closest_diameter} мм "
            f"и толщины {closest_thickness} мм (без учета арматуры)"
        )

    return closest_data


# === Функция экспорта в Excel ===

def export_to_excel(ring_data, summary_data, times, N_final_list, normative_load, params):
    """Экспорт результатов расчёта в Excel-файл."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Лист 1: Параметры расчёта
        params_df = pd.DataFrame([
            {"Параметр": "Диаметр, мм", "Значение": params['diameter']},
            {"Параметр": "Толщина стенки, мм", "Значение": params['thickness']},
            {"Параметр": "Высота, м", "Значение": params['height']},
            {"Параметр": "Коэфф. расч. длины", "Значение": params['eff_length_coeff']},
            {"Параметр": "Ryn стали, МПа", "Значение": params['steel_strength']},
            {"Параметр": "E стали, МПа", "Значение": params['steel_E']},
            {"Параметр": "Rbn бетона, МПа", "Значение": params['concrete_strength']},
            {"Параметр": "Нагрузка, кН", "Значение": normative_load},
            {"Параметр": "Армирование", "Значение": "Да" if params['use_reinforcement'] else "Нет"},
        ])
        if params['use_reinforcement']:
            params_df = pd.concat([params_df, pd.DataFrame([
                {"Параметр": "Кол-во стержней", "Значение": params['rebar_count']},
                {"Параметр": "Диаметр стержня, мм", "Значение": params['rebar_diameter']},
                {"Параметр": "Ryn арматуры, МПа", "Значение": params['rebar_strength']},
            ])], ignore_index=True)
        params_df.to_excel(writer, sheet_name="Параметры", index=False)

        # Лист 2: Детальный расчёт по кольцам
        rows = []
        for d in ring_data:
            rows.append({
                "Элемент": d['label'],
                "Тип": {"concrete": "Бетон", "steel": "Сталь", "rebar": "Арматура"}[d['type']],
                "R_нар, мм": d['R_out_mm'],
                "R_вн, мм": d['R_in_mm'],
                "A, мм\u00b2": d['area_mm2'],
                "T, \u00b0C": d['temp_celsius'],
                "\u03b3": d['gamma'],
                "R_fire, МПа": d['f_fire_mpa'],
                "\u03b5": d['strain'],
                "E_fire, МПа": d['E_fire_mpa'],
                "I, м\u2074": d['I_m4'],
                "N, кН": d['N_kn'],
                "EI, кН\u00b7м\u00b2": d['EI_knm2'],
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Кольца", index=False)

        # Лист 3: Сводные результаты
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Результаты", index=False)

        # Лист 4: Несущая способность по времени
        if times and N_final_list:
            n_safety = [N / normative_load if normative_load > 0 else 0 for N in N_final_list]
            ts_df = pd.DataFrame({
                "Время, мин": times,
                "N, кН": [round(n, 1) for n in N_final_list],
                "Коэфф. запаса": [round(n, 3) for n in n_safety],
            })
            ts_df.to_excel(writer, sheet_name="Временной ряд", index=False)

    output.seek(0)
    return output


# === UI: Конфигурация и ввод данных ===

st.set_page_config(page_title="Расчёт огнестойкости сталетрубобетонной колонны", page_icon="🔥", layout="wide")
st.markdown(COMMON_CSS, unsafe_allow_html=True)
st.markdown('<div style="text-align:center; font-size:2em; font-weight:700; font-family:Segoe UI, Arial, sans-serif; margin-bottom:0.7em; margin-top:0.2em;">🔥 Расчёт огнестойкости сталетрубобетонной колонны</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Ввод данных")

    with st.expander("📏 Геометрия", expanded=True):
        diameter = st.number_input(
            "Наружный диаметр, мм",
            min_value=GEOMETRY_LIMITS.MIN_DIAMETER_MM,
            max_value=GEOMETRY_LIMITS.MAX_DIAMETER_MM,
            value=DEFAULT_VALUES.DIAMETER_MM,
            step=0.1
        )
        thickness = st.number_input(
            "Толщина стенки, мм",
            min_value=GEOMETRY_LIMITS.MIN_THICKNESS_MM,
            max_value=GEOMETRY_LIMITS.MAX_THICKNESS_MM,
            value=DEFAULT_VALUES.THICKNESS_MM,
            step=0.1
        )
        height = st.number_input(
            "Высота колонны, м",
            min_value=GEOMETRY_LIMITS.MIN_HEIGHT_M,
            max_value=GEOMETRY_LIMITS.MAX_HEIGHT_M,
            value=DEFAULT_VALUES.HEIGHT_M,
            step=0.1
        )
        effective_length_coefficient = st.number_input(
            "Коэфф. расч. длины",
            min_value=0.1,
            max_value=5.0,
            value=DEFAULT_VALUES.EFFECTIVE_LENGTH_COEFF,
            step=0.1
        )

    with st.expander("🧱 Материалы", expanded=True):
        steel_strength_normative = st.number_input(
            "Ryn стали, МПа",
            min_value=200,
            max_value=1000,
            value=DEFAULT_VALUES.STEEL_STRENGTH_MPA
        )
        steel_elastic_modulus = st.number_input(
            "E стали, МПа",
            min_value=150000,
            max_value=250000,
            value=DEFAULT_VALUES.STEEL_ELASTIC_MODULUS_MPA
        )
        concrete_strength_normative = st.number_input(
            "Rbn бетона, МПа",
            min_value=5.0,
            max_value=120.0,
            value=DEFAULT_VALUES.CONCRETE_STRENGTH_MPA,
            step=0.1
        )

    with st.expander("🔥 Нагрузка и Огонь", expanded=True):
        normative_load = st.number_input(
            "Нагрузка, кН",
            min_value=0.0,
            max_value=50000.0,
            value=DEFAULT_VALUES.NORMATIVE_LOAD_KN,
            step=10.0
        )
        fire_exposure_time = st.number_input(
            "Время пожара, мин",
            min_value=0,
            max_value=360,
            value=DEFAULT_VALUES.FIRE_EXPOSURE_TIME_MIN,
            step=5
        )

    with st.expander("🏗️ Армирование"):
        use_reinforcement = st.checkbox("Учитывать армирование", value=True)
        rebar_count = st.number_input(
            "Кол-во стержней",
            min_value=0,
            max_value=40,
            value=MATERIAL_CONSTANTS.DEFAULT_REBAR_COUNT,
            step=1
        )
        rebar_diameter = st.number_input(
            "Диаметр стержня, мм",
            min_value=4,
            max_value=60,
            value=MATERIAL_CONSTANTS.DEFAULT_REBAR_DIAMETER_MM,
            step=1
        )
        rebar_strength_normative = st.number_input(
            "Ryn арматуры, МПа",
            min_value=200,
            max_value=1000,
            value=DEFAULT_VALUES.REBAR_STRENGTH_MPA,
            help="Нормативное сопротивление стали арматуры."
        )

# === Валидация ===
is_valid, error_message = validate_all_inputs(
    diameter, thickness, height,
    steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
    normative_load, fire_exposure_time,
    use_reinforcement, rebar_count, rebar_diameter
)
if not is_valid:
    st.error(error_message)
    st.stop()

# === Загрузка данных ===
thermal_data = load_thermal_data()
closest_data = get_closest_thermal_data(thermal_data, diameter, thickness, use_reinforcement, rebar_diameter)

if not closest_data:
    st.error("Данные не найдены")
    st.stop()

# === Общие параметры расчёта ===
fire_exposure_time_sec = fire_exposure_time * 60
ring_thicknesses = [10, 20, 20, 20, 20, 20, None]
num_rings = 7

# === Основной расчёт для текущего времени ===
N_final, N_total, N_cr, slenderness, reduction_coeff = calculate_final_capacity(
    diameter, thickness, height, effective_length_coefficient,
    closest_data, fire_exposure_time_sec,
    steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
    use_reinforcement, rebar_diameter, rebar_count,
    num_rings, ring_thicknesses, rebar_strength_normative
)

total_stiffness = calculate_stiffness_for_time(
    diameter, thickness, closest_data, fire_exposure_time_sec,
    concrete_strength_normative, steel_elastic_modulus,
    use_reinforcement, rebar_diameter, rebar_count,
    num_rings, ring_thicknesses
)

# === Детальные данные по кольцам ===
ring_data = calculate_detailed_ring_data(
    diameter, thickness, closest_data, fire_exposure_time_sec,
    steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
    use_reinforcement, rebar_diameter, rebar_count, rebar_strength_normative,
    num_rings, ring_thicknesses
)

# === Расчёт по всем временам для графиков ===
times, N_final_list = calculate_time_series(
    diameter, thickness, height, effective_length_coefficient,
    closest_data,
    steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
    use_reinforcement, rebar_diameter, rebar_count,
    num_rings, ring_thicknesses, rebar_strength_normative
)

n_safety_list = [N / normative_load if normative_load > 0 else 0 for N in N_final_list]

# === Метрики (Dashboard) ===
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    delta_color = "normal"
    if N_final < normative_load:
        delta_color = "inverse"
    st.metric("Несущая способность", f"{N_final:.0f} кН",
              f"{N_final - normative_load:.0f} кН запас", delta_color=delta_color)

with col_m2:
    st.metric("Действующая нагрузка", f"{normative_load:.0f} кН")

with col_m3:
    if total_stiffness > 0:
        st.metric("Жесткость (EI)", f"{total_stiffness/1000:.1f} МН·м\u00b2")
    else:
        st.metric("Жесткость (EI)", "N/A")

with col_m4:
    if N_final > 0:
        util = normative_load / N_final
        st.metric("Коэффициент надежности", f"{util:.2f}")
    else:
        st.metric("Коэффициент надежности", "N/A")

st.divider()

# === Вкладки ===
tab1, tab2, tab3, tab_walkthrough, tab4, tab5, tab_compare, tab_export, tab6 = st.tabs([
    "🧮 Детальный расчёт",
    "📈 График (N)",
    "📊 Запас прочности",
    "📝 Ход решения",
    "🌡️ График (T)",
    "📐 Сечение",
    "⚖️ Сравнение сечений",
    "📥 Экспорт",
    "ℹ️ О проекте"
])

# ==================== ВКЛАДКА 1: Детальный расчёт ====================
with tab1:
    # Таблица бетонных колец
    concrete_data = [d for d in ring_data if d['type'] == 'concrete']
    steel_data = [d for d in ring_data if d['type'] == 'steel']
    rebar_data = [d for d in ring_data if d['type'] == 'rebar']

    if concrete_data:
        st.markdown(f'<div {TABLE_TITLE_STYLE}>Расчёт бетонного сечения</div>', unsafe_allow_html=True)
        rows = [build_concrete_row(d) for d in concrete_data]
        st.markdown(render_html_table(CONCRETE_COLUMNS, HEADER_MAP, rows), unsafe_allow_html=True)

    if steel_data:
        st.markdown(f'<div {TABLE_TITLE_STYLE}>Расчёт стального кольца</div>', unsafe_allow_html=True)
        rows = [build_steel_row(d) for d in steel_data]
        st.markdown(render_html_table(STEEL_COLUMNS, HEADER_MAP, rows), unsafe_allow_html=True)

    if rebar_data:
        st.markdown(f'<div {TABLE_TITLE_STYLE}>Расчёт арматуры</div>', unsafe_allow_html=True)
        rows = [build_steel_row(d) for d in rebar_data]
        st.markdown(render_html_table(REBAR_COLUMNS, HEADER_MAP, rows), unsafe_allow_html=True)

    # Сводная таблица
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Результаты расчёта</div>', unsafe_allow_html=True)

    total_EI_from_rings = sum(d['EI_knm2'] or 0 for d in ring_data)

    summary_items = [
        ("Несущая способность колонны", f"{N_final:.1f} кН"),
        ("Полная жесткость сечения (EI)", f"{total_EI_from_rings:.1f} кН\u00b7м\u00b2"),
        ("Критическая сила", f"{N_cr:.1f} кН" if N_cr > 0 else "N/A"),
        ("Понижающий коэффициент", f"{reduction_coeff:.3f}"),
        ("Условная гибкость", f"{slenderness:.3f}"),
    ]

    summary_html = '<table class="summary-table"><tr><th>Показатель</th><th>Значение</th></tr>'
    for name, val in summary_items:
        summary_html += f'<tr><td>{name}</td><td>{val}</td></tr>'
    summary_html += '</table>'
    st.markdown(summary_html, unsafe_allow_html=True)


# ==================== ВКЛАДКА 2: График N(t) ====================
with tab2:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>График несущей способности от времени</div>', unsafe_allow_html=True)

    if times and N_final_list:
        chart_df = pd.DataFrame({"Время, мин": times, "Несущая способность, кН": N_final_list})

        fire_limit_time = find_fire_resistance_limit(times, N_final_list, normative_load)

        line = alt.Chart(chart_df).mark_line(point=True, color="#d62728", strokeWidth=3).encode(
            x=alt.X("Время, мин", axis=alt.Axis(title="Время огневого воздействия, мин", titleFontSize=16)),
            y=alt.Y("Несущая способность, кН", axis=alt.Axis(title="Несущая способность, кН", titleFontSize=16, format=".0f")),
            tooltip=["Время, мин", "Несущая способность, кН"]
        )
        norm_line = alt.Chart(pd.DataFrame({"y": [normative_load]})).mark_rule(
            color="#1f77b4", strokeDash=[2, 2], size=2
        ).encode(y="y")

        chart = line + norm_line
        if fire_limit_time is not None:
            fl_df = pd.DataFrame({"x": [fire_limit_time], "y1": [normative_load], "y0": [0]})
            chart = chart + alt.Chart(fl_df).mark_rule(color="#2ca02c", strokeDash=[1, 0], size=3).encode(x="x", y="y1", y2="y0")
            chart = chart + alt.Chart(fl_df).mark_point(filled=True, color="#2ca02c", size=80).encode(x="x", y="y1")

        st.altair_chart(chart.properties(height=800).interactive(), use_container_width=True)

        legend_html = f'''
        <div style="display:flex; flex-direction:column; align-items:center; margin-top:0.5em;">
            <div style="display:flex; align-items:center; gap:1em;">
                <span style="display:inline-block; width:24px; height:4px; background:#2ca02c; border-radius:2px;"></span>
                <span>Зелёная линия — предел огнестойкости{f': {fire_limit_time:.1f} мин' if fire_limit_time else ''}</span>
            </div>
            <div style="display:flex; align-items:center; gap:1em; margin-top:0.3em;">
                <span style="display:inline-block; width:24px; height:4px; background: repeating-linear-gradient(90deg, #1f77b4, #1f77b4 8px, transparent 8px, transparent 16px); border-radius:2px;"></span>
                <span>Синяя пунктирная линия — нормативная нагрузка: {normative_load} кН</span>
            </div>
        </div>
        '''
        st.markdown(legend_html, unsafe_allow_html=True)


# ==================== ВКЛАДКА 3: Запас прочности ====================
with tab3:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Коэффициент запаса прочности</div>', unsafe_allow_html=True)

    if times and N_final_list and normative_load > 0:
        df_safety = pd.DataFrame({'Время, мин': times, 'Коэффициент запаса n': n_safety_list})

        fire_resistance_limit_n = find_fire_resistance_limit(times, n_safety_list, 1.0)

        line = alt.Chart(df_safety).mark_line(point=True, color="#1f77b4", strokeWidth=3).encode(
            x=alt.X('Время, мин:Q', title='Время, мин'),
            y=alt.Y('Коэффициент запаса n:Q', title='Коэффициент запаса прочности n')
        )
        rule = alt.Chart(pd.DataFrame({'y': [1]})).mark_rule(
            color='red', strokeDash=[5, 5], strokeWidth=2
        ).encode(y='y:Q')

        chart = line + rule
        if fire_resistance_limit_n is not None:
            vline = alt.Chart(pd.DataFrame({'x': [fire_resistance_limit_n]})).mark_rule(
                color='green', strokeDash=[3, 3], strokeWidth=2
            ).encode(x='x:Q')
            chart = chart + vline

        st.altair_chart(chart.properties(height=400), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if fire_resistance_limit_n is not None:
                st.metric("Предел огнестойкости", f"{fire_resistance_limit_n:.1f} мин")
            else:
                st.info("Предел огнестойкости не достигнут в расчётном диапазоне")
        with col2:
            if n_safety_list:
                st.metric("Начальный запас прочности", f"{n_safety_list[0]:.2f}")
    else:
        st.warning("Недостаточно данных для построения графика. Убедитесь, что нагрузка > 0.")


# ==================== ВКЛАДКА 4: Ход решения ====================
with tab_walkthrough:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Подробный ход решения</div>', unsafe_allow_html=True)

    target_times = [0, 30, 60, 90, 120, 150, 180, 210, 240]

    for t_min in target_times:
        with st.expander(f"Время {t_min} мин", expanded=False):
            t_sec = t_min * 60

            current_record = get_thermal_record_for_time(closest_data, t_sec)
            if not current_record:
                st.warning(f"Нет температурных данных для времени {t_min} мин")
                continue

            st.markdown(f"**1. Определение температур в сечении для t = {t_min} мин**")
            st.markdown("Температуры определяются по теплотехническому расчёту (см. вкладку График (T)).")
            st.markdown(f"**2. Расчёт показателей для каждого элемента сечения**")

            # Расчёт детальных данных для этого времени
            step_ring_data = calculate_detailed_ring_data(
                diameter, thickness, closest_data, t_sec,
                steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
                use_reinforcement, rebar_diameter, rebar_count, rebar_strength_normative,
                num_rings, ring_thicknesses
            )

            N_calc_total = 0.0
            total_stiffness_calc = 0.0
            N_s_val = 0.0
            EI_s_val = 0.0
            N_a_val = 0.0
            EI_a_val = 0.0

            for d in step_ring_data:
                N_i = d['N_kn'] or 0
                EI_i = d['EI_knm2'] or 0
                N_calc_total += N_i
                total_stiffness_calc += EI_i

                if d['type'] == 'concrete':
                    temp_val = d['temp_celsius']
                    gamma_val = d['gamma'] or 1.0
                    f_val = d['f_fire_mpa'] or 0
                    strain_val = d['strain'] or 0
                    E_val = d['E_fire_mpa'] or 0
                    area_i = d['area_mm2'] or 0
                    I_i = d['I_m4'] or 0

                    with st.expander(f"Кольцо бетона {d['label']}"):
                        st.markdown(rf"Температура: $T = {temp_val:.1f}^\circ\text{{C}}$")
                        st.markdown(rf"Коэфф. условий работы: $\gamma_{{bt}} = {gamma_val:.2f}$")
                        st.markdown(rf"Сопротивление: $R_{{b,t}} = {concrete_strength_normative} \cdot {gamma_val:.2f} = {f_val:.1f}$ МПа")
                        if strain_val > 0:
                            st.markdown(rf"Модуль деформации: $E_{{b,t}} = \frac{{{f_val:.1f}}}{{{strain_val/1000:.4f}}} = {E_val:.0f}$ МПа")
                        else:
                            st.markdown(r"Модуль деформации: $E_{b,t} = 0$ МПа")
                        st.markdown(rf"Площадь кольца: $A = {area_i/100:.1f} \text{{ см}}^2$")
                        st.markdown(rf"Момент инерции: $I = {fmt_sci_latex(I_i)} \text{{ м}}^4$")
                        st.markdown(rf"Несущая способность: $N = {N_i:.1f}$ кН")
                        st.markdown(rf"Жесткость: $EI = {EI_i:.1f}$ кН·м²")

                elif d['type'] == 'steel':
                    N_s_val = N_i
                    EI_s_val = EI_i
                    temp_val = d['temp_celsius']
                    gamma_val = d['gamma'] or 1.0
                    f_val = d['f_fire_mpa'] or 0
                    E_val = d['E_fire_mpa'] or 0
                    area_s = d['area_mm2'] or 0
                    I_s = d['I_m4'] or 0

                    with st.expander("Стальная оболочка"):
                        st.markdown(rf"Температура: $T_{{s}} = {temp_val:.1f}^\circ\text{{C}}$")
                        st.markdown(rf"Коэфф. условий работы: $\gamma_{{st}} = {gamma_val:.2f}$")
                        st.markdown(rf"Сопротивление: $R_{{s,t}} = {steel_strength_normative} \cdot {gamma_val:.2f} = {f_val:.1f}$ МПа")
                        st.markdown(rf"Модуль упругости: $E_{{s,t}} = {steel_elastic_modulus} \cdot {gamma_val:.2f} = {E_val:.0f}$ МПа")
                        st.markdown(rf"Площадь оболочки: $A_{{s}} = {area_s/100:.1f} \text{{ см}}^2$")
                        st.markdown(rf"Момент инерции: $I_{{s}} = {fmt_sci_latex(I_s)} \text{{ м}}^4$")
                        st.markdown(rf"Несущая способность: $N_{{s}} = {N_s_val:.1f}$ кН")
                        st.markdown(rf"Жесткость: $EI_{{s}} = {EI_s_val:.1f}$ кН·м²")

                elif d['type'] == 'rebar':
                    N_a_val = N_i
                    EI_a_val = EI_i
                    temp_val = d['temp_celsius']
                    gamma_val = d['gamma'] or 1.0
                    f_val = d['f_fire_mpa'] or 0
                    E_val = d['E_fire_mpa'] or 0
                    area_a = d['area_mm2'] or 0
                    I_a = d['I_m4'] or 0

                    with st.expander(f"Арматура ({rebar_count}\u00d8{rebar_diameter})"):
                        st.markdown(rf"Температура: $T_{{a}} = {temp_val:.1f}^\circ\text{{C}}$")
                        st.markdown(rf"Коэфф. условий работы: $\gamma_{{st,a}} = {gamma_val:.2f}$")
                        st.markdown(rf"Сопротивление: $R_{{a,t}} = {rebar_strength_normative} \cdot {gamma_val:.2f} = {f_val:.1f}$ МПа")
                        st.markdown(rf"Модуль упругости: $E_{{a,t}} = {steel_elastic_modulus} \cdot {gamma_val:.2f} = {E_val:.0f}$ МПа")
                        st.markdown(rf"Площадь арматуры: $A_{{a}} = {area_a/100:.1f} \text{{ см}}^2$")
                        st.markdown(rf"Момент инерции: $I_{{a}} = {fmt_sci_latex(I_a)} \text{{ м}}^4$")
                        st.markdown(rf"Несущая способность: $N_{{a}} = {N_a_val:.1f}$ кН")
                        st.markdown(rf"Жесткость: $EI_{{a}} = {EI_a_val:.1f}$ кН·м²")

            # 3. Суммарная несущая способность
            n_conc_sum = N_calc_total - N_s_val - N_a_val
            st.markdown(f"**3. Суммарная несущая способность сечения** $N_{{total}}$")
            st.markdown(rf"$$N_{{total}} = \sum N_{{b,i}} + N_s + N_a = {n_conc_sum:.1f} + {N_s_val:.1f} + {N_a_val:.1f} = {N_calc_total:.1f}\text{{ кН}}$$")
            st.divider()

            # 4. Полная жесткость
            EI_conc = total_stiffness_calc - EI_s_val - EI_a_val
            st.markdown(f"**4. Полная жесткость сечения** $(EI)_{{total}}$")
            st.markdown(rf"$$(EI)_{{total}} = \sum (EI_{{b,i}}) + EI_s + EI_a = {EI_conc:.1f} + {EI_s_val:.1f} + {EI_a_val:.1f} = {total_stiffness_calc:.1f} \text{{ кН}}\cdot\text{{м}}^2$$")
            st.divider()

            # 5. Критическая сила
            l_eff = height * effective_length_coefficient
            N_cr_val = (math.pi ** 2) * total_stiffness_calc / (l_eff ** 2) if (l_eff > 0 and total_stiffness_calc > 0) else 0.0
            st.markdown(f"**5. Критическая сила** $N_{{cr}}$")
            st.markdown(rf"$$N_{{cr}} = \frac{{\pi^2 \cdot {total_stiffness_calc:.1f}}}{{({height} \cdot {effective_length_coefficient})^2}} = {N_cr_val:.1f} \text{{ кН}}$$")
            st.divider()

            # 6. Условная гибкость
            lambda_val = math.sqrt(N_calc_total / N_cr_val) if N_cr_val > 0 else 0.0
            st.markdown(r"**6. Условная гибкость** $\overline{\lambda}$")
            st.markdown(rf"$$\overline{{\lambda}} = \sqrt{{\frac{{{N_calc_total:.1f}}}{{{N_cr_val:.1f}}}}} = {lambda_val:.3f}$$")
            st.divider()

            # 7. Коэффициент продольного изгиба
            phi_val = get_reduction_coeff(lambda_val)
            st.markdown(r"**7. Коэффициент продольного изгиба** $\varphi$")
            st.markdown(rf"$$\varphi = {phi_val:.3f}$$")
            st.divider()

            # 8. Итоговая несущая способность
            N_final_val = N_calc_total * phi_val
            st.markdown(f"**8. Итоговая несущая способность** $N_{{u}}$")
            st.markdown(rf"$$N_{{u}} = {N_calc_total:.1f} \cdot {phi_val:.3f} = {N_final_val:.1f} \text{{ кН}}$$")


# ==================== ВКЛАДКА 5: График температур ====================
with tab4:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>График нагрева сечения</div>', unsafe_allow_html=True)

    if closest_data:
        temp_data_list = []
        for r in closest_data:
            t = r.get('time_minutes')
            if isinstance(t, (int, float)):
                item = {'Время, мин': t / 60.0}
                for k, label in [
                    ('temp_t1', 'Сталь (t1)'),
                    ('temp_t2', 'Б1 (t2)'),
                    ('temp_t3', 'Б2 (t3)'),
                    ('temp_t4', 'Арматура (t4)'),
                    ('temp_t5', 'Б3 (t5)'),
                    ('temp_t6', 'Б4 (t6)'),
                    ('temp_t7', 'Б5 (t7)'),
                    ('temp_t8', 'Б6 (t8)'),
                    ('temp_t9', 'Б7 (t9)'),
                ]:
                    val = r.get(k)
                    if val is not None:
                        item[label] = val
                temp_data_list.append(item)

        if temp_data_list:
            df_temps = pd.DataFrame(temp_data_list).sort_values('Время, мин')
            fig_temps = go.Figure()
            for col in df_temps.columns:
                if col == 'Время, мин':
                    continue
                fig_temps.add_trace(go.Scatter(
                    x=df_temps['Время, мин'], y=df_temps[col],
                    mode='lines', name=col
                ))
            fig_temps.update_layout(
                height=600,
                xaxis_title="Время, мин",
                yaxis_title="Температура, \u00b0C",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            st.plotly_chart(fig_temps, use_container_width=True)
    else:
        st.info("Нет данных для отображения графика прогрева.")


# ==================== ВКЛАДКА 6: Сечение ====================
def temp_to_color(temp, t_min=20, t_max=800):
    """Преобразование температуры в цвет: синий (холод) → жёлтый → красный (горяч)."""
    ratio = max(0.0, min(1.0, (temp - t_min) / (t_max - t_min))) if t_max > t_min else 0.0
    if ratio < 0.5:
        # Синий → Жёлтый
        r = int(2 * ratio * 255)
        g = int(2 * ratio * 255)
        b = int((1 - 2 * ratio) * 255)
    else:
        # Жёлтый → Красный
        r = 255
        g = int((1 - 2 * (ratio - 0.5)) * 255)
        b = 0
    return f'rgb({r},{g},{b})'

with tab5:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Сечение колонны — температурная карта</div>', unsafe_allow_html=True)

    # Определяем доступные временные точки
    available_times = sorted(set(
        int(r['time_minutes']) // 60
        for r in closest_data
        if isinstance(r.get('time_minutes'), (int, float))
    )) if closest_data else [0]
    max_time = max(available_times) if available_times else 240

    section_time = st.slider("Время огневого воздействия, мин", min_value=0, max_value=max_time, value=0, step=1, key="section_time_slider")

    # Получаем температуры для выбранного времени
    section_record = get_thermal_record_for_time(closest_data, section_time * 60)
    temp_keys_concrete = ['temp_t2', 'temp_t3', 'temp_t5', 'temp_t6', 'temp_t7', 'temp_t8', 'temp_t9']
    ring_temps = []
    for k in temp_keys_concrete:
        val = section_record.get(k) if section_record else None
        ring_temps.append(val if isinstance(val, (int, float)) else 20.0)
    temp_steel = section_record.get('temp_t1', 20.0) if section_record else 20.0
    temp_rebar = section_record.get('temp_t4') if section_record else None

    # Определяем диапазон температур для шкалы
    all_temps = [temp_steel] + ring_temps
    if temp_rebar is not None:
        all_temps.append(temp_rebar)
    t_max_color = max(max(all_temps), 100)

    radius = diameter / 2
    theta = np.linspace(0, 2 * np.pi, 100)

    # Вычисляем реальные радиусы колец из ring_thicknesses
    concrete_outer_r = radius - thickness
    actual_ring_radii = [radius, concrete_outer_r]

    current_r = concrete_outer_r
    for i, t_val in enumerate(ring_thicknesses):
        if t_val is None:
            current_r = 0.0
        else:
            current_r = max(0.0, current_r - t_val)
        actual_ring_radii.append(current_r)

    ring_labels = [
        f'Стальная стенка ({temp_steel:.0f} °C)',
    ] + [
        f'Б{i+1} ({ring_temps[i]:.0f} °C)' for i in range(len(ring_temps))
    ]

    fig = go.Figure()

    # Внешний круг — стальная оболочка с цветом по температуре
    x_outer = radius * np.cos(theta)
    y_outer = radius * np.sin(theta)
    steel_color = temp_to_color(temp_steel, 20, t_max_color)
    fig.add_trace(go.Scatter(x=x_outer, y=y_outer, fill='toself',
                             fillcolor=steel_color, line=dict(width=0), showlegend=False,
                             hoverinfo='text', text=f'Сталь: {temp_steel:.0f} °C'))

    # Бетонные кольца — заливка по температуре (от внешнего к внутреннему)
    for i in range(1, len(actual_ring_radii)):
        r = actual_ring_radii[i]
        if r <= 0:
            continue
        x_ring = r * np.cos(theta)
        y_ring = r * np.sin(theta)
        # i=1 — граница стали/бетона (кольцо Б1, temp index 0), i=2 — Б2 (temp index 1), ...
        if i - 1 < len(ring_temps):
            fill_color = temp_to_color(ring_temps[i - 1], 20, t_max_color)
            hover = f'Б{i}: {ring_temps[i - 1]:.0f} °C'
        else:
            fill_color = 'rgb(210,209,205)'
            hover = ''
        fig.add_trace(go.Scatter(x=x_ring, y=y_ring, fill='toself',
                                 fillcolor=fill_color, line=dict(width=0), showlegend=False,
                                 hoverinfo='text', text=hover))

    # Контуры колец (тонкие белые линии для разделения)
    for i in range(1, len(actual_ring_radii)):
        r = actual_ring_radii[i]
        if r <= 0:
            continue
        x_ring = r * np.cos(theta)
        y_ring = r * np.sin(theta)
        fig.add_trace(go.Scatter(x=x_ring, y=y_ring, mode='lines',
                                 line=dict(width=1.5, color='rgba(255,255,255,0.7)'), showlegend=False,
                                 hoverinfo='skip'))

    # Контур внешнего круга
    fig.add_trace(go.Scatter(x=x_outer, y=y_outer, mode='lines',
                             line=dict(width=2, color='black'), showlegend=False, hoverinfo='skip'))

    # Арматура
    if use_reinforcement:
        rebar_radius = radius - thickness - MATERIAL_CONSTANTS.REBAR_COVER_MM - rebar_diameter / 2
        rebar_theta = np.linspace(0, 2 * np.pi, rebar_count, endpoint=False)
        rebar_x = rebar_radius * np.cos(rebar_theta)
        rebar_y = rebar_radius * np.sin(rebar_theta)
        rebar_color = temp_to_color(temp_rebar, 20, t_max_color) if temp_rebar is not None else 'white'
        rebar_text = f'Арматура: {temp_rebar:.0f} °C' if temp_rebar is not None else 'Арматура: нет данных'
        fig.add_trace(go.Scatter(
            x=rebar_x, y=rebar_y, mode='markers',
            marker=dict(size=max(6, rebar_diameter * 0.8), color=rebar_color,
                        line=dict(width=1, color='black')),
            showlegend=False, hoverinfo='text', text=rebar_text
        ))

    axis_range = radius * 1.1
    fig.update_xaxes(range=[-axis_range, axis_range], title="X, мм")
    fig.update_yaxes(range=[-axis_range, axis_range], title="Y, мм")
    fig.update_layout(
        width=600, height=600,
        plot_bgcolor='white', showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showgrid=True, zeroline=True, showline=True, mirror=True,
                   scaleanchor="y", scaleratio=1, constrain="domain"),
        yaxis=dict(showgrid=True, zeroline=True, showline=True, mirror=True, constrain="domain")
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, use_container_width=True)

    # Цветовая шкала
    gradient_steps = 10
    gradient_divs = ''.join(
        f'<div style="flex:1; height:20px; background:{temp_to_color(20 + i * (t_max_color - 20) / gradient_steps, 20, t_max_color)};"></div>'
        for i in range(gradient_steps + 1)
    )
    scale_html = f'''
    <div style="max-width:500px; margin:0 auto; padding:10px;">
        <div style="display:flex; border-radius:4px; overflow:hidden; border:1px solid #ccc;">{gradient_divs}</div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#666; margin-top:4px;">
            <span>20 °C</span><span>{t_max_color:.0f} °C</span>
        </div>
    </div>
    '''
    st.markdown(scale_html, unsafe_allow_html=True)

    # Легенда с температурами
    legend_html = '<div style="display:flex; flex-wrap:wrap; justify-content:center; gap:15px; padding:10px; background:white; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1); margin-top:10px;">'
    legend_html += f'<div style="display:flex; align-items:center; gap:6px; font-size:13px;"><div style="width:16px; height:16px; border-radius:3px; background:{steel_color}; border:1px solid #999;"></div><span>{ring_labels[0]}</span></div>'
    for i in range(len(ring_temps)):
        c = temp_to_color(ring_temps[i], 20, t_max_color)
        legend_html += f'<div style="display:flex; align-items:center; gap:6px; font-size:13px;"><div style="width:16px; height:16px; border-radius:3px; background:{c}; border:1px solid #999;"></div><span>{ring_labels[i + 1]}</span></div>'
    if use_reinforcement and temp_rebar is not None:
        rc = temp_to_color(temp_rebar, 20, t_max_color)
        legend_html += f'<div style="display:flex; align-items:center; gap:6px; font-size:13px;"><div style="width:16px; height:16px; border-radius:50%; background:{rc}; border:1px solid #999;"></div><span>Арматура ({temp_rebar:.0f} °C)</span></div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)


# ==================== ВКЛАДКА 7: Сравнение сечений ====================
with tab_compare:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Параметрическое сравнение сечений</div>', unsafe_allow_html=True)
    st.markdown("Задайте до 5 вариантов сечений для сравнения их огнестойкости на одном графике.")

    num_variants = st.number_input("Количество вариантов", min_value=2, max_value=5, value=3, step=1)

    variants = []
    cols = st.columns(num_variants)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Вариант {i+1}**")
            d_var = st.number_input(f"D, мм", min_value=200.0, max_value=1200.0,
                                    value=float(200 + i * 50), step=10.0, key=f"cmp_d_{i}")
            t_var = st.number_input(f"t, мм", min_value=3.0, max_value=30.0,
                                    value=6.0, step=0.5, key=f"cmp_t_{i}")
            variants.append((d_var, t_var))

    if st.button("Рассчитать сравнение"):
        compare_fig = go.Figure()
        colors = ['#d62728', '#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']

        for idx, (d_var, t_var) in enumerate(variants):
            var_data = get_closest_thermal_data(thermal_data, d_var, t_var, use_reinforcement, rebar_diameter)
            if not var_data:
                continue
            var_times, var_N = calculate_time_series(
                d_var, t_var, height, effective_length_coefficient,
                var_data,
                steel_strength_normative, steel_elastic_modulus, concrete_strength_normative,
                use_reinforcement, rebar_diameter, rebar_count,
                num_rings, ring_thicknesses, rebar_strength_normative
            )
            if var_times and var_N:
                fire_limit = find_fire_resistance_limit(var_times, var_N, normative_load)
                label = f"D={d_var}, t={t_var}"
                if fire_limit is not None:
                    label += f" (R{fire_limit:.0f})"
                compare_fig.add_trace(go.Scatter(
                    x=var_times, y=var_N, mode='lines+markers',
                    name=label,
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))

        # Линия нагрузки
        compare_fig.add_hline(y=normative_load, line_dash="dash", line_color="gray",
                              annotation_text=f"Нагрузка {normative_load} кН")

        compare_fig.update_layout(
            height=600,
            xaxis_title="Время, мин",
            yaxis_title="Несущая способность, кН",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(compare_fig, use_container_width=True)


# ==================== ВКЛАДКА 8: Экспорт ====================
with tab_export:
    st.markdown(f'<div {TABLE_TITLE_STYLE}>Экспорт результатов</div>', unsafe_allow_html=True)

    summary_export = [
        {"Показатель": name, "Значение": val}
        for name, val in summary_items
    ]

    params = {
        'diameter': diameter, 'thickness': thickness, 'height': height,
        'eff_length_coeff': effective_length_coefficient,
        'steel_strength': steel_strength_normative, 'steel_E': steel_elastic_modulus,
        'concrete_strength': concrete_strength_normative,
        'use_reinforcement': use_reinforcement, 'rebar_count': rebar_count,
        'rebar_diameter': rebar_diameter, 'rebar_strength': rebar_strength_normative,
    }

    excel_data = export_to_excel(ring_data, summary_export, times, N_final_list, normative_load, params)

    st.download_button(
        label="📥 Скачать отчёт в Excel",
        data=excel_data,
        file_name=f"fire_resistance_D{diameter}_t{thickness}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.info("Отчёт содержит: параметры расчёта, детальные данные по кольцам, сводные результаты и временной ряд несущей способности.")


# ==================== ВКЛАДКА 9: О проекте ====================
with tab6:
    st.markdown("""
### О проекте

Программа предназначена для расчёта огнестойкости сталетрубобетонных (трубобетонных) колонн
при воздействии стандартного температурного режима пожара.

#### Методика расчёта

Расчёт выполняется в соответствии с положениями **СП 468.1325800.2019** и включает следующие этапы:

**1. Определение температурного поля** — загрузка результатов теплотехнического расчёта
из JSON-файлов, полученных численным моделированием (ANSYS, ABAQUS, ELCUT и др.)

**2. Дискретизация сечения** — бетонное ядро разбивается на 7 концентрических колец
с толщинами [10, 20, 20, 20, 20, 20, остаток] мм. Для каждого кольца определяется
средняя температура по данным теплотехнического расчёта.

**3. Определение свойств материалов при повышенных температурах:**
    """)
    st.latex(r"""
    \gamma_{st}(T) \text{ — коэффициент условий работы стали}
    """)
    st.latex(r"""
    \gamma_{bt}(T) \text{ — коэффициент условий работы бетона}
    """)
    st.latex(r"""
    \varepsilon_{yn,t}(T) \text{ — деформация бетона при сжатии}
    """)
    st.latex(r"""
    E_{b,t} = \frac{R_{b,t}}{\varepsilon_{yn,t}} \text{ — модуль деформации бетона}
    """)

    st.markdown("""
**4. Расчёт несущей способности** — суммирование вкладов бетонных колец,
стальной оболочки и арматуры (при наличии):
    """)
    st.latex(r"N_{total} = \sum N_{b,i} + N_s + N_a")

    st.markdown("""
**5. Расчёт жёсткости сечения** — суммирование жёсткостей всех элементов:
    """)
    st.latex(r"(EI)_{total} = \sum (EI)_{b,i} + (EI)_s + (EI)_a")

    st.markdown("""
**6. Учёт продольного изгиба** — определение критической силы по Эйлеру,
условной гибкости и понижающего коэффициента:
    """)
    st.latex(r"N_{cr} = \frac{\pi^2 \cdot (EI)_{total}}{(\mu \cdot l)^2}")
    st.latex(r"\overline{\lambda} = \sqrt{\frac{N_{total}}{N_{cr}}}")
    st.latex(r"N_u = \varphi \cdot N_{total}")

    st.markdown("""
#### Особенности реализации

- Поддержка армированных колонн с произвольным числом стержней
- Момент инерции арматуры рассчитывается по теореме Штейнера:
    """)
    st.latex(r"I_a = n \cdot I_0 + \frac{n}{2} \cdot A \cdot R^2")
    st.markdown("""
- Параметрическое сравнение нескольких типоразмеров колонн
- Экспорт результатов в формате Excel
- Интерполяция предела огнестойкости по пересечению кривой N(t) с уровнем нагрузки
- [Streamlit](https://streamlit.io/) — фреймворк для визуализации инженерных расчётов
    """)
    st.info("Данный расчёт является демонстрационным и не заменяет нормативный расчёт по СП или другим стандартам.")
