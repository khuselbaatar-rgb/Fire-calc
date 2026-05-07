# 🔥 Fire-Resistance Calculator - Streamlit Deployment Guide

## Convert Flask → Streamlit

Your Flask calculator has been converted to **pure Streamlit** with **NO C++ dependency**. The C++ physics engine is now implemented directly in Python.

---

## 📁 File Structure

```
your-repo/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .gitignore               # Ignore cache/secrets
└── README.md                # This guide
```

---

## 🚀 Quick Start (Local)

### 1. Install Streamlit

```bash
pip install streamlit plotly pandas
```

### 2. Run the App

```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Cloud (FREE)

### Step 1: Push Code to GitHub

```bash
git init
git add .
git commit -m "Convert to Streamlit"
git remote add origin https://github.com/YOUR_USERNAME/fire-calc.git
git push -u origin main
```

### Step 2: Connect to Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository and branch
5. Set the main file path: `streamlit_app.py`
6. Click **"Deploy"**

Your app is now live! **Streamlit Cloud gives you:**
- ✅ **FREE hosting** (no credit card)
- ✅ **Auto-deploy** on every git push
- ✅ **SSL certificate** included
- ✅ **Custom domain** support

**Example URL:** `https://fire-calc.streamlit.app`

---

## 📋 requirements.txt

```
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
```

---

## 🎯 Deployment Steps (One-by-One)

### Step 1: Create GitHub Repo
```bash
# Go to github.com/new and create "fire-calc"
# Clone it locally:
git clone https://github.com/YOUR_USERNAME/fire-calc.git
cd fire-calc
```

### Step 2: Add Files
```bash
# Copy these files to the repo:
# - streamlit_app.py
# - requirements.txt
# - README.md
# - .gitignore

git add .
git commit -m "Initial commit: Streamlit fire-resistance calculator"
git push origin main
```

### Step 3: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. **Sign in** with GitHub (authorize if needed)
3. Click **"New app"**
   - Repository: `YOUR_USERNAME/fire-calc`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
4. Click **"Deploy"**
5. Wait 1-2 minutes for deployment
6. Your app is live!

---

## 🔗 Share Your App

Your app URL: `https://fire-calc-YOUR_USERNAME.streamlit.app`

Share this link with colleagues, students, or the world!

---

## 🔄 Updates & Maintenance

Every time you push to GitHub, Streamlit Cloud auto-redeploys:

```bash
# Make changes locally
nano streamlit_app.py

# Push to GitHub
git add streamlit_app.py
git commit -m "Fix bug in calculations"
git push origin main

# Streamlit Cloud auto-deploys in 1-2 minutes!
```

---

## ☁️ Alternative Hosting (if you want to)

| Platform | Cost | Setup |
|----------|------|-------|
| **Streamlit Cloud** | FREE | 5 min ⭐ |
| **Railway** | FREE-$5/mo | 10 min |
| **Render** | FREE-$7/mo | 15 min |
| **Heroku** | $5-50/mo | 15 min |

**We recommend Streamlit Cloud** – it's built for Streamlit apps.

---

## 📞 Support

- **Streamlit Docs:** https://docs.streamlit.io
- **GitHub Issues:** https://github.com/streamlit/streamlit/issues
- **Community Forum:** https://discuss.streamlit.io

---

## ✨ What You Now Have

✅ **Pure Python** – No C++ needed
✅ **Modern UI** – Streamlit auto-generates interface
✅ **Free hosting** – Streamlit Cloud
✅ **Live updates** – Auto-redeploy on push
✅ **Mobile-friendly** – Works on phones
✅ **Shareable** – One URL for everyone

---

**That's it! Your app is live on the internet!** 🚀
