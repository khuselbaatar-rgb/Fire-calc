# 🔥 Reinforced-Concrete Column Fire-Resistance Calculator

**Streamlit Version** · Python-Only · Free Cloud Hosting

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red) ![License](https://img.shields.io/badge/License-Proprietary-green)

---

## 📖 Overview

A professional web application for calculating fire-resistance ratings of reinforced-concrete columns according to ISO 834 fire curve. Originally a Flask app with C++ backend, now refactored as a **pure Python Streamlit application** for easier deployment and maintenance.

**Features:**
- ✅ Real-time calculations (no page reload)
- ✅ Interactive plots with Plotly
- ✅ Multi-language support (English, Russian, Mongolian)
- ✅ Responsive design (desktop & mobile)
- ✅ Export results as tables
- ✅ Free cloud hosting

---

## 🚀 Quick Start

### Local Development (60 seconds)

```bash
# 1. Clone or download this repo
git clone https://github.com/your-username/fire-calc.git
cd fire-calc

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run streamlit_app.py
```

App opens at: **http://localhost:8501**

---

## ☁️ Deploy to Internet (5 minutes)

### Option 1: Streamlit Cloud (RECOMMENDED - FREE)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Go to Streamlit Cloud:**
   - Visit https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repo and branch
   - Main file: `streamlit_app.py`
   - Click "Deploy"

3. **Share your app URL:**
   ```
   https://fire-calc-USERNAME.streamlit.app
   ```

✅ **Done!** Your app is live and updates automatically with every git push.

### Option 2: Other Platforms

| Platform | Cost | Link |
|----------|------|------|
| **Streamlit Cloud** | FREE | https://share.streamlit.io |
| **Railway** | FREE-$5/mo | https://railway.app |
| **Render** | FREE-$7/mo | https://render.com |
| **Heroku** | $5-50/mo | https://heroku.com |

---

## 📁 Project Structure

```
fire-calc/
├── streamlit_app.py       # Main application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── .streamlit/
│   └── config.toml       # Streamlit configuration (optional)
└── README.md             # This file
```

---

## 🎯 Usage

### Input Parameters

**Column Geometry:**
- `b` – Cross-section width (mm)
- `h` – Cross-section height (mm)  
- `H₀` – Column height (mm)
- `kL` – Length reduction factor (0.5–2.0)
- `c₁`, `c₂` – Rebar axis distances (mm)

**Materials:**
- `Rbn` – Concrete strength (MPa)
- `Rsn` – Steel strength (MPa)
- `ρ` – Concrete density (kg/m³)
- `W` – Moisture content (%)
- `tb` – Mean concrete temp (°C)

**Loading:**
- `As1` – Corner reinforcement (mm²)
- `As2` – Mid-edge reinforcement (mm²)
- `Np` – Design load (kN)

### Output

- **Fire Rating**: Minutes of fire resistance
- **Capacity vs Time**: Interactive chart showing capacity decay
- **Detailed Table**: Thermal & structural parameters at each time step
- **Thermal Parameters**: λ_tem, c_tem, a_red, k_bS
- **Static Check**: Slenderness, stability factor φ, initial capacity N₀

---

## 📊 Calculation Model

The calculator implements:

1. **Thermal Diffusivity** (ISO 834):
   ```
   a_red = λ_tem / [(c_tem + 50W) · ρ]
   ```

2. **Temperature Distribution** (erf approximation):
   ```
   t_s = 1250 − (1250 − t₀) · Θ_x · Θ_y
   ```

3. **Steel Strength Reduction** (γ-steel tables)

4. **Sectional Capacity**:
   ```
   N_p,tem = φ · [R_bn(b−2δ)(h−2δ) + γ_s·R_sn·A_s] × 10⁻³
   ```

5. **Verdict**:
   - **✓ PASS**: Capacity > Load for entire duration
   - **✗ FAIL**: Capacity drops below load before t_max

---

## 🔧 Configuration

### Change Language

Edit `LANG_TEXT` dictionary in `streamlit_app.py`:

```python
LANG_TEXT = {
    "en": { ... },
    "ru": { ... },
    "mn": { ... },
}
```

### Customize Theme

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#ff7a1a"
backgroundColor = "#0b0f14"
secondaryBackgroundColor = "#141a22"
textColor = "#e7edf5"
font = "sans serif"
```

### Adjust Cache

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def expensive_calc():
    return result
```

---

## 🚀 Development

### Local Testing

```bash
# Run with cache clearing
streamlit run streamlit_app.py --logger.level=debug

# Profile performance
python -m cProfile -s cumtime streamlit_app.py
```

### Adding Features

Example: Add custom export to PDF

```python
import pdfkit

if st.button("Export to PDF"):
    html = f"<h1>Results</h1><p>{result}</p>"
    pdfkit.from_string(html, "results.pdf")
    st.success("PDF saved!")
```

---

## 🔐 Security

1. **Never commit secrets:**
   ```bash
   echo ".streamlit/secrets.toml" >> .gitignore
   ```

2. **Use Streamlit Secrets** (on Streamlit Cloud):
   - Go to App Settings → Secrets
   - Add TOML format:
     ```toml
     [credentials]
     email = "your@email.com"
     ```

3. **Enable GitHub 2FA** before connecting to Streamlit Cloud

---

## 📈 Performance

- **Calculation time**: <100ms (pure Python)
- **Chart rendering**: <500ms
- **Page load**: <2 seconds

Optimizations used:
- ✅ `@st.cache_data` for static lookups
- ✅ Vectorized calculations
- ✅ Lazy imports

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| App shows "Loading..." forever | Check for infinite loops, use `@st.cache_data` |
| "ModuleNotFoundError" | Add package to `requirements.txt`, redeploy |
| Slow calculations | Profile with cProfile, use numba for loops |
| CORS errors (external API) | Use backend proxy or HTTPS-only endpoints |

---

## 📝 Changelog

### v2.0 (2025-01)
- ✅ Converted from Flask+C++ to pure Streamlit
- ✅ Eliminated C++ dependency
- ✅ Added Plotly interactive charts
- ✅ Multi-language support
- ✅ Free cloud hosting via Streamlit Cloud

### v1.0 (Original)
- Flask backend with C++ computational engine
- Custom HTML/JS frontend

---

## 📞 Support & Contact

- **Email**: info@OnlineCalculatorJBK.com
- **Phone**: +7 929 905 62 05
- **GitHub Issues**: [Open an issue](https://github.com/your-username/fire-calc/issues)
- **Streamlit Docs**: https://docs.streamlit.io

---

## 📜 License

Proprietary. © 2025 OnlineCalculatorJBK. All rights reserved.

---

## 🙋 Contributing

Want to improve this calculator? 

1. Fork the repo
2. Create a feature branch
3. Make changes
4. Submit a pull request

---

## 🎉 What's Next?

After deploying:
1. ✅ Test on different browsers
2. ✅ Share the URL with colleagues
3. ✅ Collect feedback
4. ✅ Iterate & improve
5. ✅ Consider adding more features (PDF export, batch calculations, etc.)

---

**Made with ❤️ by OnlineCalculatorJBK**

Live Demo: https://fire-calc.streamlit.app *(coming soon)*
