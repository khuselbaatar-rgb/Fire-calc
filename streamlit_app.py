"""
Reinforced-Concrete Column Fire-Resistance Calculator
Streamlit Web Application (replaces Flask)

Run locally:
    streamlit run streamlit_app.py

Deploy to Streamlit Cloud:
    1. Push code to GitHub
    2. Connect repo at https://share.streamlit.io
"""

import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# =====================================================================
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="🔥 Fire Resistance Calculator",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# TRANSLATIONS (Russian, English, Mongolian)
# =====================================================================
LANG_TEXT = {
    "en": {
        "title": "🔥 Reinforced-Concrete Column Fire-Resistance Calculator",
        "subtitle": "Pure Streamlit Frontend · ISO 834 Fire Curve",
        "btn_load_example": "Load Example",
        "btn_calculate": "Calculate Fire Resistance",
        "section1": "1. Column Geometry",
        "section2": "2. Materials",
        "section3": "3. Reinforcement & Load",
        "section4": "Calculation Parameters",
        "lbl_b": "b – Section width (mm)",
        "lbl_h": "h – Section height (mm)",
        "lbl_H0": "H₀ – Column height (mm)",
        "lbl_kL": "kL – Length factor (–)",
        "lbl_c1": "c₁ – Axis distance for As1 (mm)",
        "lbl_c2": "c₂ – Axis distance for As2 (mm)",
        "lbl_Rbn": "Rbn – Concrete strength (MPa)",
        "lbl_Rsn": "Rsn – Steel strength (MPa)",
        "lbl_rho": "ρ – Concrete density (kg/m³)",
        "lbl_W": "W – Moisture content (%)",
        "lbl_tb": "tb – Mean concrete temp (°C)",
        "lbl_t0": "t₀ – Initial temperature (°C)",
        "lbl_As1": "As1 – Corner reinforcement (mm²)",
        "lbl_As2": "As2 – Mid-edge reinforcement (mm²)",
        "lbl_Np": "Np – Design load (kN)",
        "lbl_step": "Time step (min)",
        "lbl_tmax": "Max time (min)",
        "lbl_phi": "φ (manual, leave empty for auto)",
        "thermal_params": "Thermal Parameters",
        "static_check": "Static Check (τ = 0)",
        "fire_rating": "Fire Rating Result",
        "capacity_table": "Capacity vs Time",
        "fire_curve": "Fire Curve (ISO 834)",
        "chart_capacity": "Capacity",
        "chart_load": "Applied Load",
        "ok": "PASS",
        "bad": "FAIL",
        "pf": "Fire Rating",
        "n0": "Initial Capacity",
        "load": "Applied Load",
        "status": "Status",
    },
    "ru": {
        "title": "🔥 Расчет огнестойкости железобетонной колонны",
        "subtitle": "Streamlit Приложение · Кривая пожара ISO 834",
        "btn_load_example": "Загрузить пример",
        "btn_calculate": "Рассчитать огнестойкость",
        "section1": "1. Геометрия сечения",
        "section2": "2. Материалы",
        "section3": "3. Арматура и нагрузка",
        "section4": "Параметры расчета",
        "lbl_b": "b – ширина сечения (мм)",
        "lbl_h": "h – высота сечения (мм)",
        "lbl_H0": "H₀ – высота колонны (мм)",
        "lbl_kL": "kL – коэффициент длины (–)",
        "lbl_c1": "c₁ – расстояние до оси As1 (мм)",
        "lbl_c2": "c₂ – расстояние до оси As2 (мм)",
        "lbl_Rbn": "Rbn – прочность бетона (МПа)",
        "lbl_Rsn": "Rsn – прочность стали (МПа)",
        "lbl_rho": "ρ – плотность бетона (кг/м³)",
        "lbl_W": "W – влажность (%)",
        "lbl_tb": "tb – средняя t бетона (°C)",
        "lbl_t0": "t₀ – начальная t (°C)",
        "lbl_As1": "As1 – арматура у грани (мм²)",
        "lbl_As2": "As2 – арматура в середине (мм²)",
        "lbl_Np": "Np – расчетная нагрузка (кН)",
        "lbl_step": "Шаг времени (мин)",
        "lbl_tmax": "Максимум времени (мин)",
        "lbl_phi": "φ (вручную, пусто = авто)",
        "thermal_params": "Теплотехнические параметры",
        "static_check": "Статическая проверка (τ = 0)",
        "fire_rating": "Результат предела огнестойкости",
        "capacity_table": "Несущая способность по времени",
        "fire_curve": "Кривая пожара (ISO 834)",
        "chart_capacity": "Несущая способность",
        "chart_load": "Приложенная нагрузка",
        "ok": "ПОДХОДИТ",
        "bad": "НЕ ПОДХОДИТ",
        "pf": "Предел огнестойкости",
        "n0": "Начальная несущая способность",
        "load": "Приложенная нагрузка",
        "status": "Статус",
    }
}

# =====================================================================
# BACKEND CALCULATION ENGINE (PURE PYTHON)
# =====================================================================

def erf_approx(x):
    """Error function approximation."""
    a1, a2, a3 = 0.254829592, -0.284496736, 1.421413741
    a4, a5, p = -1.453152027, 1.061405429, 0.3275911
    s = 1 if x >= 0 else -1
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1) * t * math.exp(-x*x)
    return s * y

def interp(x, pts):
    """Linear interpolation."""
    if x <= pts[0][0]: return pts[0][1]
    for i in range(1, len(pts)):
        if x <= pts[i][0]:
            x0, y0 = pts[i-1]
            x1, y1 = pts[i]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]
def draw_cross_section_svg(b, h, c1, c2, c3, As1, As2, As3, delta, ts1, ts2, ts3, tau):
    """Draw column cross-section with temperature colors."""
    W = 500
    padding = 50
    scale = (W - 2*padding) / max(b, h)
    
    bs = b * scale
    hs = h * scale
    ox = (W - bs) / 2
    oy = (W - hs) / 2
    ds = min(delta * scale, min(bs, hs) / 2 - 2) if delta > 0 else 0
    
    # Rebar radii
    r1 = max(5, min(18, math.sqrt(max(As1, 0) / 4 / math.pi) * scale))
    r2 = max(4, min(14, math.sqrt(max(As2, 0) / 4 / math.pi) * scale))
    r3 = max(4, min(12, math.sqrt(max(As3, 0) / 4 / math.pi) * scale))
    
    c1s, c2s, c3s = c1 * scale, c2 * scale, c3 * scale
    
    # As1 - 2 bottom
    as1_pos = [(ox + c1s, oy + hs - c1s), (ox + bs - c1s, oy + hs - c1s)]
    
    # As2 - 2 top
    as2_pos = [(ox + c2s, oy + c2s), (ox + bs - c2s, oy + c2s)]
    
    # As3 - 3 middle vertical
    as3_pos = [(ox + bs/2, oy + c3s), (ox + bs/2, oy + hs/2), (ox + bs/2, oy + hs - c3s)]
    
    col1 = temp_color(ts1)
    col2 = temp_color(ts2)
    col3 = temp_color(ts3)
    
    circles1 = ''.join(f'<circle cx="{x}" cy="{y}" r="{r1}" fill="{col1}" stroke="#000" stroke-width="1"/>' for x,y in as1_pos)
    circles2 = ''.join(f'<circle cx="{x}" cy="{y}" r="{r2}" fill="{col2}" stroke="#000" stroke-width="1"/>' for x,y in as2_pos)
    circles3 = ''.join(f'<circle cx="{x}" cy="{y}" r="{r3}" fill="{col3}" stroke="#000" stroke-width="1"/>' for x,y in as3_pos)
    
    delta_line = f'<line x1="{ox}" y1="{oy-12}" x2="{ox+ds}" y2="{oy-12}" stroke="#ff7a1a" stroke-width="2"/><text x="{ox+ds/2}" y="{oy-16}" text-anchor="middle" font-size="10" fill="#ff9957">δ={delta:.1f}</text>' if delta > 0.5 else ''
    
    svg = f'''<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ddd;border-radius:8px;background:#f5f5f5">
    <defs><pattern id="burnt" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)"><rect width="8" height="8" fill="#ff7a1a"/><rect width="4" height="8" fill="#5a2a08"/></pattern></defs>
    <rect x="{ox}" y="{oy}" width="{bs}" height="{hs}" fill="url(#burnt)" stroke="#999" stroke-width="1.2" opacity="0.8"/>
    {f'<rect x="{ox+ds}" y="{oy+ds}" width="{max(1,bs-2*ds)}" height="{max(1,hs-2*ds)}" fill="#3a3a3a" stroke="#555" stroke-width="1"/>' if ds > 1 else ''}
    <text x="{ox+bs/2}" y="{oy+hs+28}" text-anchor="middle" font-size="12" font-family="monospace" fill="#333" font-weight="bold">b={b:.0f}</text>
    <text x="{ox-35}" y="{oy+hs/2+4}" text-anchor="middle" font-size="12" font-family="monospace" fill="#333" font-weight="bold" transform="rotate(-90 {ox-35} {oy+hs/2})">h={h:.0f}</text>
    {circles1}{circles2}{circles3}{delta_line}
    <text x="14" y="20" font-size="13" font-weight="bold" fill="#ff9957" font-family="monospace">τ={tau:.0f}мин</text>
    <text x="14" y="38" font-size="10" fill="#444" font-family="monospace">As1:{ts1:.0f}°C</text>
    <text x="14" y="52" font-size="10" fill="#444" font-family="monospace">As2:{ts2:.0f}°C</text>
    <text x="14" y="66" font-size="10" fill="#444" font-family="monospace">As3:{ts3:.0f}°C</text>
    </svg>'''
    return svg
def gamma_steel(t):
    """Steel strength reduction factor."""
    pts = [
        (20, 1.0), (300, 0.97), (400, 0.85), (500, 0.544), (600, 0.37),
        (700, 0.22), (800, 0.12), (900, 0.06), (1000, 0.03)
    ]
    return interp(t, pts)

def phi_by_lambda(lam):
    """Stability factor by slenderness."""
    pts = [
        (8, 0.98), (10, 0.973), (11.5, 0.965), (15, 0.95),
        (20, 0.90), (30, 0.80), (40, 0.70), (50, 0.60)
    ]
    return interp(lam, pts)

def iso834_temp(tau_min):
    """ISO 834 fire curve: temperature vs time (minutes)."""
    if tau_min <= 0: return 20
    return 345 * math.log10(8 * tau_min + 1) + 20

def compute_step(tau, b, h, c1, c2, Rbn, Rsn, As1, As2, t0, Np, phi, aRed, kbS):
    """Compute one time step."""
    root = 0 if tau == 0 else 2.0 * math.sqrt(max(aRed, 0) * tau * 60.0)
    ts1 = t0
    ts2 = t0
    g1 = 1.0
    g2 = 1.0
    delta = 0.0

    if tau > 0:
        clamp = lambda v: max(0, min(1, v))
        theta_x1 = clamp(erf_approx((kbS + c1)/root) + erf_approx((kbS + b - c1)/root) - 1.0)
        theta_y1 = clamp(erf_approx((kbS + c1)/root) + erf_approx((kbS + h - c1)/root) - 1.0)
        
        ts1 = 1250.0 - (1250.0 - t0) * theta_x1 * theta_y1
        g1 = gamma_steel(ts1)
        
        if As2 > 0:
            theta_x2 = clamp(erf_approx((kbS + c2)/root) + erf_approx((kbS + b - c2)/root) - 1.0)
            theta_y2 = clamp(erf_approx((kbS + c2)/root) + erf_approx((kbS + h - c2)/root) - 1.0)
            ts2 = 1250.0 - (1250.0 - t0) * theta_x2 * theta_y2
            g2 = gamma_steel(ts2)
        
        delta = max(0, min(min(b, h)/2.0 - 1.0, 0.3807 * root - kbS))
    
    bb = max(1.0, b - 2.0 * delta)
    hh = max(1.0, h - 2.0 * delta)
    Nu = phi * (Rbn*bb*hh + (g1*Rsn)*As1 + (g2*Rsn)*As2) * 1.0e-3
    ok = Nu >= Np
    
    return {
        "tau": tau, "root": root, "ts1": ts1, "ts2": ts2,
        "g1": g1, "g2": g2, "delta": delta, "Nu": Nu, "ok": ok
    }

def calculate(inputs):
    """Main calculation engine (pure Python)."""
    b = inputs["b"]
    h = inputs["h"]
    H0 = inputs["H0"]
    kL = inputs["kL"]
    c1 = inputs["c1"]
    c2 = inputs["c2"]
    Rbn = inputs["Rbn"]
    Rsn = inputs["Rsn"]
    rho = inputs["rho"]
    W = inputs["W"]
    tb = inputs["tb"]
    t0 = inputs["t0"]
    As1 = inputs["As1"]
    As2 = inputs["As2"]
    Np = inputs["Np"]
    step = inputs.get("step", 30)
    tmax = inputs.get("tmax", 180)
    phi_manual = inputs.get("phi_manual")

    # Thermal parameters
    lambda0, a_lambda = 1.14, -0.00055
    c0, ac = 710.0, 0.84
    lambdaTem = lambda0 + a_lambda * tb
    cTem = c0 + ac * tb
    aRed_m2s = lambdaTem / ((cTem + 50.0 * W) * rho)
    aRed = aRed_m2s * 1.0e6
    kb = 37.2
    kbS = kb * math.sqrt(max(aRed, 0))

    # Static check
    l0 = kL * H0
    lambda_val = l0 / min(b, h)
    phi = phi_manual if phi_manual else phi_by_lambda(lambda_val)
    N0 = phi * (Rbn*b*h + Rsn*As1 + Rsn*As2) * 1.0e-3
    N0_pass = N0 >= Np

    # Time series
    times = list(range(0, int(tmax) + 1, max(1, int(step))))
    if times[-1] != tmax:
        times.append(int(tmax))

    # Compute rows
    rows = []
    Nus = []
    fail_idx = -1

    for tau in times:
        r = compute_step(tau, b, h, c1, c2, Rbn, Rsn, As1, As2, t0, Np, phi, aRed, kbS)
        if not r["ok"] and fail_idx < 0:
            fail_idx = len(rows)
        Nus.append(r["Nu"])
        rows.append(r)

    # Verdict
    verdict = "more"
    t_exact = -1
    if fail_idx == 0:
        verdict = "zero"
    elif fail_idx > 0:
        prev_tau, prev_Nu = rows[fail_idx - 1]["tau"], Nus[fail_idx - 1]
        cur_tau, cur_Nu = rows[fail_idx]["tau"], Nus[fail_idx]
        if cur_Nu != prev_Nu:
            t_exact = prev_tau + (Np - prev_Nu) * (cur_tau - prev_tau) / (cur_Nu - prev_Nu)
        verdict = "approx"

    # 1-minute resolution for charts
    chart_rows = []
    for tau in range(0, int(tmax) + 1):
        r = compute_step(tau, b, h, c1, c2, Rbn, Rsn, As1, As2, t0, Np, phi, aRed, kbS)
        chart_rows.append(r)

    return {
        "lambdaTem": lambdaTem,
        "cTem": cTem,
        "aRed": aRed,
        "kbS": kbS,
        "l0": l0,
        "lambda": lambda_val,
        "phi": phi,
        "phi_manual": bool(phi_manual),
        "N0": N0,
        "N0_pass": N0_pass,
        "Np": Np,
        "rows": rows,
        "chart_rows": chart_rows,
        "verdict": verdict,
        "t_exact": t_exact,
        "tauLast": tmax,
    }

# =====================================================================
# STREAMLIT UI
# =====================================================================

def t(key):
    """Translate key using selected language."""
    lang = st.session_state.get("lang", "en")
    return LANG_TEXT.get(lang, LANG_TEXT["en"]).get(key, key)

# Sidebar: language selector
with st.sidebar:
    st.markdown("### 🌍 Language")
    lang = st.radio("Select language", ["en", "ru"], format_func=lambda x: {"en": "🇬🇧 English", "ru": "🇷🇺 Русский"}[x])
    st.session_state["lang"] = lang

# Header
st.markdown(f'# {t("title")}')
st.markdown(f'_{t("subtitle")}_')

# Main layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(t("section1"))
    b = st.number_input(t("lbl_b"), value=300, min_value=100)
    h = st.number_input(t("lbl_h"), value=300, min_value=100)
    H0 = st.number_input(t("lbl_H0"), value=4000, min_value=1000)
    kL = st.number_input(t("lbl_kL"), value=0.8, min_value=0.5, max_value=2.0, step=0.01)
    c1 = st.number_input(t("lbl_c1"), value=50, min_value=10)
    c2 = st.number_input(t("lbl_c2"), value=150, min_value=10)

    st.subheader(t("section2"))
    Rbn = st.number_input(t("lbl_Rbn"), value=22, min_value=5)
    Rsn = st.number_input(t("lbl_Rsn"), value=400, min_value=200)
    rho = st.number_input(t("lbl_rho"), value=2300, min_value=2000)
    W = st.number_input(t("lbl_W"), value=2.0, min_value=0.0, max_value=5.0, step=0.1)
    tb = st.number_input(t("lbl_tb"), value=450, min_value=20)
    t0 = st.number_input(t("lbl_t0"), value=20, min_value=20)

    st.subheader(t("section3"))
    As1 = st.number_input(t("lbl_As1"), value=5027, min_value=100)
    As2 = st.number_input(t("lbl_As2"), value=2513, min_value=0)
    Np = st.number_input(t("lbl_Np"), value=2354, min_value=100)

    st.subheader(t("section4"))
    step = st.selectbox(t("lbl_step"), [15, 30, 60], index=1)
    tmax = st.number_input(t("lbl_tmax"), value=180, min_value=60, step=30)
    phi_manual = st.number_input(t("lbl_phi"), value=0.0, step=0.001, format="%.3f")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_calc = st.button(t("btn_calculate"), use_container_width=True, type="primary")
    with col_btn2:
        btn_example = st.button(t("btn_load_example"), use_container_width=True)

with col2:
    if btn_calc or btn_example:
        # Prepare inputs
        inputs = {
            "b": b, "h": h, "H0": H0, "kL": kL, "c1": c1, "c2": c2,
            "Rbn": Rbn, "Rsn": Rsn, "rho": rho, "W": W, "tb": tb, "t0": t0,
            "As1": As1, "As2": As2, "Np": Np, "step": step, "tmax": int(tmax),
            "phi_manual": phi_manual if phi_manual > 0 else None,
        }

        # Calculate
        with st.spinner("Calculating..."):
            result = calculate(inputs)

        # Display results
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        with col_res1:
            st.metric(t("pf"), f"{result['t_exact']:.0f} min" if result['verdict'] == 'approx' else f"> {int(tmax)} min")
        with col_res2:
            st.metric(t("n0"), f"{result['N0']:.0f} kN")
        with col_res3:
            st.metric(t("load"), f"{result['Np']:.0f} kN")
        with col_res4:
            status_text = t("ok") if result["N0_pass"] else t("bad")
            st.metric(t("status"), status_text)

        # Thermal parameters
        st.subheader(t("thermal_params"))
        col_tp1, col_tp2, col_tp3, col_tp4 = st.columns(4)
        with col_tp1:
            st.metric("λ_tem", f"{result['lambdaTem']:.4f}")
        with col_tp2:
            st.metric("c_tem", f"{result['cTem']:.0f}")
        with col_tp3:
            st.metric("a_red", f"{result['aRed']:.4f}")
        with col_tp4:
            st.metric("k_bS", f"{result['kbS']:.2f}")

        # Static check
        st.subheader(t("static_check"))
        col_sc1, col_sc2, col_sc3 = st.columns(3)
        with col_sc1:
            st.metric("l₀", f"{result['l0']:.0f} mm")
        with col_sc2:
            st.metric("λ", f"{result['lambda']:.2f}")
        with col_sc3:
            st.metric("φ", f"{result['phi']:.3f}")

        # Table
        st.subheader(t("capacity_table"))
        df_rows = []
        for row in result["rows"]:
            df_rows.append({
                "τ (min)": int(row["tau"]),
                "√(a·τ) (mm)": f"{row['root']:.0f}",
                "ts1 (°C)": f"{row['ts1']:.0f}",
                "ts2 (°C)": f"{row['ts2']:.0f}",
                "γs1": f"{row['g1']:.3f}",
                "γs2": f"{row['g2']:.3f}",
                "δ (mm)": f"{row['delta']:.1f}",
                "Nu (kN)": f"{row['Nu']:.0f}",
                "OK": "✓" if row["ok"] else "✗"
            })
        st.dataframe(pd.DataFrame(df_rows), use_container_width=True)

        # Chart
        st.subheader(t("fire_curve"))
        
        chart_times = [r["tau"] for r in result["chart_rows"]]
        chart_Nus = [r["Nu"] for r in result["chart_rows"]]
        chart_loads = [result["Np"] for _ in chart_times]

        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_times, y=chart_Nus,
            name=t("chart_capacity"),
            mode="lines",
            line=dict(color="#ff7a1a", width=3),
            fill="tozeroy",
            fillcolor="rgba(255, 122, 26, 0.2)"
        ))

        fig.add_trace(go.Scatter(
            x=chart_times, y=chart_loads,
            name=t("chart_load"),
            mode="lines",
            line=dict(color="#5aa9ff", width=2, dash="dash")
        ))

        fig.update_layout(
            title="Capacity vs Time",
            xaxis_title="Time τ (minutes)",
            yaxis_title="Capacity (kN)",
            hovermode="x unified",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Verdict
        st.markdown("---")
        if result["verdict"] == "more":
            st.success(f"✓ Fire rating > {int(tmax)} minutes")
        elif result["verdict"] == "zero":
            st.error("✗ No fire resistance")
        else:
            st.warning(f"⚠ Fire rating ≈ {result['t_exact']:.0f} minutes")

# Footer
st.markdown("---")
col_ft1, col_ft2, col_ft3 = st.columns(3)
with col_ft1:
    st.caption("📧 Khuselbaatar.com")
with col_ft2:
    st.caption("📱 +7 929 905 62 05")
with col_ft3:
    st.caption(f"© {datetime.now().year} OnlineCalculatorJBK")

