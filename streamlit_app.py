"""
🔥 Reinforced-Concrete Column Fire-Resistance Calculator
Complete Streamlit Application with Cross-Section Visualization
"""

import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="🔥 Гал эсэргүүцэх чадварын тооцоо",
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
        "subtitle": "Pure Python • ISO 834 Fire Curve",
        "btn_calculate": "Calculate Fire Resistance",
        "section1": "1. Column Geometry",
        "section2": "2. Materials",
        "section3": "3. Reinforcement & Load",
        "lbl_b": "b – Section width (mm)",
        "lbl_h": "h – Section height (mm)",
        "lbl_H0": "H₀ – Column height (mm)",
        "lbl_kL": "kL – Length factor (–)",
        "lbl_c1": "c₁ – Bottom axis (mm)",
        "lbl_c2": "c₂ – Top axis (mm)",
        "lbl_c3": "c₃ – Middle axis (mm)",
        "lbl_Rbn": "Rbn – Concrete (MPa)",
        "lbl_Rsn": "Rsn – Steel (MPa)",
        "lbl_rho": "ρ – Density (kg/m³)",
        "lbl_W": "W – Moisture (%)",
        "lbl_tb": "tb – Concrete T (°C)",
        "lbl_t0": "t₀ – Initial T (°C)",
        "lbl_As1": "As1 – Bottom (mm²)",
        "lbl_As2": "As2 – Top (mm²)",
        "lbl_As3": "As3 – Middle (mm²)",
        "lbl_Np": "Np – Load (kN)",
        "thermal_params": "Thermal Parameters",
        "static_check": "Static Check",
        "fire_curve": "Capacity vs Time",
        "chart_capacity": "Capacity",
        "chart_load": "Applied Load",
        "ok": "✓ PASS",
        "bad": "✗ FAIL",
        "pf": "Fire Rating",
        "n0": "Capacity",
        "load": "Load",
        "status": "Status",
    },
    "ru": {
        "title": "🔥 Расчет огнестойкости железобетонной колонны",
        "subtitle": "Pure Python • Кривая пожара ISO 834",
        "btn_calculate": "Рассчитать огнестойкость",
        "section1": "1. Геометрия сечения",
        "section2": "2. Материалы",
        "section3": "3. Арматура и нагрузка",
        "lbl_b": "b – ширина (мм)",
        "lbl_h": "h – высота (мм)",
        "lbl_H0": "H₀ – колонна (мм)",
        "lbl_kL": "kL – коэфф (–)",
        "lbl_c1": "c₁ – доод (мм)",
        "lbl_c2": "c₂ – дээд (мм)",
        "lbl_c3": "c₃ – дунд (мм)",
        "lbl_Rbn": "Rbn – бетон (МПа)",
        "lbl_Rsn": "Rsn – сталь (МПа)",
        "lbl_rho": "ρ – плотность (кг/м³)",
        "lbl_W": "W – влажность (%)",
        "lbl_tb": "tb – T бетона (°C)",
        "lbl_t0": "t₀ – T нач (°C)",
        "lbl_As1": "As1 – дод (мм²)",
        "lbl_As2": "As2 – деед (мм²)",
        "lbl_As3": "As3 – дунд (мм²)",
        "lbl_Np": "Np – нагруз (кН)",
        "thermal_params": "Тепловые параметры",
        "static_check": "Статическая проверка",
        "fire_curve": "Несущая способность",
        "chart_capacity": "Несущая",
        "chart_load": "Нагруз",
        "ok": "✓ ЗОВ",
        "bad": "✗ НЕ ЗОВ",
        "pf": "Огнестойк",
        "n0": "Несущая",
        "load": "Нагруз",
        "status": "Статус",
    },
    "mn": {
        "title": "🔥 Төмөр бетон баганын гал эсэргүүцэх чадварын тооцоо",
        "subtitle": "Pure Python • ISO 834 Галын муруй",
        "btn_calculate": "Тооцоо хийх",
        "section1": "1. Баганын геометри",
        "section2": "2. Материалууд",
        "section3": "3. Арматур ба ачаал",
        "lbl_b": "b – өргөн (мм)",
        "lbl_h": "h – өндөр (мм)",
        "lbl_H0": "H₀ – баган (мм)",
        "lbl_kL": "kL – коэфф (–)",
        "lbl_c1": "c₁ – доод (мм)",
        "lbl_c2": "c₂ – дээд (мм)",
        "lbl_c3": "c₃ – дунд (мм)",
        "lbl_Rbn": "Rbn – бетон (МПа)",
        "lbl_Rsn": "Rsn – ган (МПа)",
        "lbl_rho": "ρ – нягтрал (кг/м³)",
        "lbl_W": "W – чийг (%)",
        "lbl_tb": "tb – T (°C)",
        "lbl_t0": "t₀ – T (°C)",
        "lbl_As1": "As1 – доод (мм²)",
        "lbl_As2": "As2 – дээд (мм²)",
        "lbl_As3": "As3 – дунд (мм²)",
        "lbl_Np": "Np – ачаал (кН)",
        "thermal_params": "Дулааны параметр",
        "static_check": "Статик шалгалт",
        "fire_curve": "Дамжуулах чадвар",
        "chart_capacity": "Дамж",
        "chart_load": "Ачаал",
        "ok": "✓ ЗОВ",
        "bad": "✗ МУУГҮЙ",
        "pf": "Гал эс",
        "n0": "Дамж",
        "load": "Ачаал",
        "status": "Статус",
    }
}

# =====================================================================
# MATH FUNCTIONS
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

def temp_color(t):
    """Temperature → color mapping."""
    if t < 100: return '#5aa9ff'   # Blue
    if t < 300: return '#3ddc84'   # Green
    if t < 500: return '#ffd166'   # Yellow
    if t < 700: return '#ff9957'   # Orange
    return '#ff5c5c'               # Red

def gamma_steel(t):
    """Steel strength reduction factor."""
    pts = [(20, 1.0), (300, 0.97), (400, 0.85), (500, 0.544), (600, 0.37),
           (700, 0.22), (800, 0.12), (900, 0.06), (1000, 0.03)]
    return interp(t, pts)

def phi_by_lambda(lam):
    """Stability factor by slenderness."""
    pts = [(8, 0.98), (10, 0.973), (11.5, 0.965), (15, 0.95),
           (20, 0.90), (30, 0.80), (40, 0.70), (50, 0.60)]
    return interp(lam, pts)

def draw_cross_section_svg(b, h, c1, c2, c3, As1, As2, As3, delta, ts1, ts2, ts3, tau):
    """Draw column cross-section with temperature colors and 3 reinforcement types."""
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

def compute_step(tau, b, h, c1, c2, c3, Rbn, Rsn, As1, As2, As3, t0, Np, phi, aRed, kbS):
    """Compute one time step with 3 reinforcement types."""
    root = 0 if tau == 0 else 2.0 * math.sqrt(max(aRed, 0) * tau * 60.0)
    ts1 = ts2 = ts3 = t0
    g1 = g2 = g3 = 1.0
    delta = 0.0

    if tau > 0:
        clamp = lambda v: max(0, min(1, v))
        
        # As1 - bottom
        theta_x1 = clamp(erf_approx((kbS + c1)/root) + erf_approx((kbS + b - c1)/root) - 1.0)
        theta_y1 = clamp(erf_approx((kbS + c1)/root) + erf_approx((kbS + h - c1)/root) - 1.0)
        ts1 = 1250.0 - (1250.0 - t0) * theta_x1 * theta_y1
        g1 = gamma_steel(ts1)
        
        # As2 - top
        if As2 > 0:
            theta_x2 = clamp(erf_approx((kbS + c2)/root) + erf_approx((kbS + b - c2)/root) - 1.0)
            theta_y2 = clamp(erf_approx((kbS + c2)/root) + erf_approx((kbS + h - c2)/root) - 1.0)
            ts2 = 1250.0 - (1250.0 - t0) * theta_x2 * theta_y2
            g2 = gamma_steel(ts2)
        
        # As3 - middle
        if As3 > 0:
            theta_x3 = clamp(erf_approx((kbS + c3)/root) + erf_approx((kbS + b - c3)/root) - 1.0)
            theta_y3 = clamp(erf_approx((kbS + c3)/root) + erf_approx((kbS + h - c3)/root) - 1.0)
            ts3 = 1250.0 - (1250.0 - t0) * theta_x3 * theta_y3
            g3 = gamma_steel(ts3)
        
        delta = max(0, min(min(b, h)/2.0 - 1.0, 0.3807 * root - kbS))
    
    bb = max(1.0, b - 2.0 * delta)
    hh = max(1.0, h - 2.0 * delta)
    Nu = phi * (Rbn*bb*hh + (g1*Rsn)*As1 + (g2*Rsn)*As2 + (g3*Rsn)*As3) * 1.0e-3
    ok = Nu >= Np
    
    return {"tau": tau, "ts1": ts1, "ts2": ts2, "ts3": ts3, "g1": g1, "g2": g2, "g3": g3, "delta": delta, "Nu": Nu, "ok": ok}

def calculate(inputs):
    """Main calculation engine (pure Python)."""
    b, h, H0, kL = inputs["b"], inputs["h"], inputs["H0"], inputs["kL"]
    c1, c2, c3 = inputs["c1"], inputs["c2"], inputs["c3"]
    Rbn, Rsn, rho, W = inputs["Rbn"], inputs["Rsn"], inputs["rho"], inputs["W"]
    tb, t0 = inputs["tb"], inputs["t0"]
    As1, As2, As3, Np = inputs["As1"], inputs["As2"], inputs["As3"], inputs["Np"]
    step, tmax = inputs.get("step", 30), inputs.get("tmax", 180)
    phi_manual = inputs.get("phi_manual")

    # Thermal parameters
    lambdaTem = 1.14 + (-0.00055) * tb
    cTem = 710.0 + 0.84 * tb
    aRed_m2s = lambdaTem / ((cTem + 50.0 * W) * rho)
    aRed = aRed_m2s * 1.0e6
    kbS = 37.2 * math.sqrt(max(aRed, 0))

    # Static check
    l0 = kL * H0
    lambda_val = l0 / min(b, h)
    phi = phi_manual if phi_manual else phi_by_lambda(lambda_val)
    N0 = phi * (Rbn*b*h + Rsn*As1 + Rsn*As2 + Rsn*As3) * 1.0e-3
    N0_pass = N0 >= Np

    # Time series
    times = list(range(0, int(tmax) + 1, max(1, int(step))))
    if times[-1] != tmax:
        times.append(int(tmax))

    # Compute rows
    rows, Nus, fail_idx = [], [], -1
    for tau in times:
        r = compute_step(tau, b, h, c1, c2, c3, Rbn, Rsn, As1, As2, As3, t0, Np, phi, aRed, kbS)
        if not r["ok"] and fail_idx < 0:
            fail_idx = len(rows)
        Nus.append(r["Nu"])
        rows.append(r)

    # Verdict
    verdict, t_exact = "more", -1
    if fail_idx == 0:
        verdict = "zero"
    elif fail_idx > 0:
        prev_tau, prev_Nu = rows[fail_idx - 1]["tau"], Nus[fail_idx - 1]
        cur_tau, cur_Nu = rows[fail_idx]["tau"], Nus[fail_idx]
        if cur_Nu != prev_Nu:
            t_exact = prev_tau + (Np - prev_Nu) * (cur_tau - prev_tau) / (cur_Nu - prev_Nu)
        verdict = "approx"

    # 1-minute resolution for charts
    chart_rows = [compute_step(tau, b, h, c1, c2, c3, Rbn, Rsn, As1, As2, As3, t0, Np, phi, aRed, kbS) for tau in range(0, int(tmax) + 1)]

    return {
        "lambdaTem": lambdaTem, "cTem": cTem, "aRed": aRed, "kbS": kbS,
        "l0": l0, "lambda": lambda_val, "phi": phi, "N0": N0, "N0_pass": N0_pass,
        "Np": Np, "rows": rows, "chart_rows": chart_rows, "verdict": verdict, "t_exact": t_exact
    }

def t(key):
    """Translate key using selected language."""
    lang = st.session_state.get("lang", "en")
    return LANG_TEXT.get(lang, LANG_TEXT["en"]).get(key, key)

# =====================================================================
# STREAMLIT UI
# =====================================================================

with st.sidebar:
    st.markdown("### 🌍 Language | Язык | Хэл")
    lang = st.radio("Select", ["en", "ru", "mn"], format_func=lambda x: {"en": "🇬🇧 English", "ru": "🇷🇺 Русский", "mn": "🇲🇳 Монгол"}[x])
    st.session_state["lang"] = lang

st.markdown(f'# {t("title")}')
st.markdown(f'_{t("subtitle")}_')

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(t("section1"))
    b = st.number_input(t("lbl_b"), value=300, min_value=100)
    h = st.number_input(t("lbl_h"), value=300, min_value=100)
    H0 = st.number_input(t("lbl_H0"), value=4000, min_value=1000)
    kL = st.number_input(t("lbl_kL"), value=0.8, min_value=0.5, max_value=2.0, step=0.01)
    c1 = st.number_input(t("lbl_c1"), value=50, min_value=10)
    c2 = st.number_input(t("lbl_c2"), value=150, min_value=10)
    c3 = st.number_input(t("lbl_c3"), value=150, min_value=10)
    
    st.subheader(t("section2"))
    Rbn = st.number_input(t("lbl_Rbn"), value=22, min_value=5)
    Rsn = st.number_input(t("lbl_Rsn"), value=400, min_value=200)
    rho = st.number_input(t("lbl_rho"), value=2300, min_value=2000)
    W = st.number_input(t("lbl_W"), value=2.0, min_value=0.0, max_value=5.0, step=0.1)
    tb = st.number_input(t("lbl_tb"), value=450, min_value=20)
    t0 = st.number_input(t("lbl_t0"), value=20, min_value=20)
    
    st.subheader(t("section3"))
    As1 = st.number_input(t("lbl_As1"), value=1256, min_value=100)
    As2 = st.number_input(t("lbl_As2"), value=1256, min_value=0)
    As3 = st.number_input(t("lbl_As3"), value=1500, min_value=0)
    Np = st.number_input(t("lbl_Np"), value=2400, min_value=100)
    step = st.selectbox("Step (min)", [15, 30, 60], index=1)
    tmax = st.number_input("Max (min)", value=180, min_value=60, step=30)
    phi_manual = st.number_input("φ", value=0.0, step=0.001, format="%.3f")
    
    if st.button(t("btn_calculate"), use_container_width=True, type="primary"):
        inputs = {"b": b, "h": h, "H0": H0, "kL": kL, "c1": c1, "c2": c2, "c3": c3,
                  "Rbn": Rbn, "Rsn": Rsn, "rho": rho, "W": W, "tb": tb, "t0": t0,
                  "As1": As1, "As2": As2, "As3": As3, "Np": Np, "step": step, "tmax": int(tmax),
                  "phi_manual": phi_manual if phi_manual > 0 else None}
        
        with st.spinner("Calculating..."):
            result = calculate(inputs)
        
        with col2:
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: st.metric(t("pf"), f"{result['N0']:.0f}kN")
            with col_m2: st.metric(t("load"), f"{result['Np']:.0f}kN")
            with col_m3: st.metric(t("status"), t("ok") if result["N0_pass"] else t("bad"))
            with col_m4:
                util = result['Np'] / result['N0'] if result['N0'] > 0 else 0
                st.metric("Ratio", f"{util:.2f}")
            
            st.divider()
            
            st.subheader("🔥 Cross-Section")
            if len(result["chart_rows"]) > 0:
                cr = result["chart_rows"][0]
                col_sec1, col_sec2 = st.columns([2, 1])
                
                with col_sec1:
                    svg_html = draw_cross_section_svg(b, h, c1, c2, c3, As1, As2, As3,
                                                       cr["delta"], cr["ts1"], cr["ts2"], cr["ts3"], cr["tau"])
                    st.markdown(svg_html, unsafe_allow_html=True)
                
                with col_sec2:
                    st.markdown("**Color Legend:**\n- 🔵 <100°C\n- 🟢 100-300°C\n- 🟡 300-500°C\n- 🟠 500-700°C\n- 🔴 >700°C")
                    
                    if len(result["chart_rows"]) > 1:
                        max_tau = int(result["chart_rows"][-1]["tau"])
                        selected_tau = st.slider("Time", 0, max_tau, 0)
                        closest_idx = min(range(len(result["chart_rows"])),
                                        key=lambda i: abs(result["chart_rows"][i]["tau"] - selected_tau))
                        cr = result["chart_rows"][closest_idx]
                        svg_html = draw_cross_section_svg(b, h, c1, c2, c3, As1, As2, As3,
                                                           cr["delta"], cr["ts1"], cr["ts2"], cr["ts3"], cr["tau"])
                        st.markdown(svg_html, unsafe_allow_html=True)
            
            st.divider()
            
            st.subheader(t("thermal_params"))
            col_tp1, col_tp2, col_tp3, col_tp4 = st.columns(4)
            with col_tp1: st.metric("λ", f"{result['lambdaTem']:.4f}")
            with col_tp2: st.metric("c", f"{result['cTem']:.0f}")
            with col_tp3: st.metric("a", f"{result['aRed']:.4f}")
            with col_tp4: st.metric("k", f"{result['kbS']:.2f}")
            
            st.divider()
            
            st.subheader(t("static_check"))
            col_sc1, col_sc2, col_sc3 = st.columns(3)
            with col_sc1: st.metric("l₀", f"{result['l0']:.0f}mm")
            with col_sc2: st.metric("λ", f"{result['lambda']:.2f}")
            with col_sc3: st.metric("φ", f"{result['phi']:.3f}")
            
            st.divider()
            
            st.subheader(t("fire_curve"))
            chart_times = [r["tau"] for r in result["chart_rows"]]
            chart_Nus = [r["Nu"] for r in result["chart_rows"]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_times, y=chart_Nus, name=t("chart_capacity"),
                                    mode="lines", line=dict(color="#ff7a1a", width=3), fill="tozeroy"))
            fig.add_trace(go.Scatter(x=chart_times, y=[result["Np"]]*len(chart_times), name=t("chart_load"),
                                    mode="lines", line=dict(color="#5aa9ff", width=2, dash="dash")))
            fig.update_layout(height=400, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
st.markdown("---")
col_ft1, col_ft2, col_ft3 = st.columns(3)
with col_ft1:
    st.caption("📧 Khuselbaatar.com")
with col_ft2:
    st.caption("📱 +7 929 905 62 05")
with col_ft3:
    st.caption(f"© {datetime.now().year} OnlineCalculatorJBK")

