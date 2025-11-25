# SharpDecimate

Free Blender add-on for hard-surface lowpoly modeling with **sharp edges preservation**.  
Preserve hard-surface details while decimating — no "soapiness", no lost geometry.

> "Geometry without grace." — NEFAS

---

## ✨ Features

- **Preserves sharp edges** by angle threshold (70°–85°)
- Respects **manually marked Sharp edges** (`Edge → Mark Sharp`)
- Supports **Edge Crease** values (for Subdivision workflows)
- **Material-Based Decimation**: assign `HighDetail`/`LowDetail` materials to control poly reduction per area
- Real-time statistics: current vs target polycount
- **Multi-language UI**: English, Russian, German, Spanish (auto-detected)
- **No external dependencies** — works in Blender 3.6.23+

---

## 📦 Installation

1. Download [`SharpDecimate.zip`](https://github.com/sergan-vyatka/SharpDecimate/releases/latest)
2. In Blender:  
   **Edit → Preferences → Add-ons → Install...**  
   Select the downloaded `.zip` file
3. Enable **"Sharp Decimate"**
4. Use in **3D View > Sidebar > Tool > Sharp Decimate**

> 💡 Tip: Click **"Setup Smart Materials"** to auto-create `HighDetail` (red) and `LowDetail` (gray) materials.

---

## 🎛️ Modes

### Standard Mode
- Uniform decimation with sharp edge preservation
- Ideal for simple objects and quick cleanup

### Smart Mode (Material-Based)
- Assign **HighDetail** material to important areas (e.g., weapon edges, face)
- Assign **LowDetail** to background areas (e.g., back, interior)
- Set different reduction ratios for each
- SharpDecimate preserves detail **exactly where you need it**

---

## 🔒 License

- **Free version**: [GNU GPL v3](LICENSE.txt) — free for personal and commercial use
- **Pro version**: available on [Boosty](https://boosty.to/cmapnep)  
  → LOD chains, Batch processing, Presets (Diablo, 3D Print, Mobile), Auto UV

---

## 🌐 Translations

- [Русская версия (README_RUS.md)](README_RUS.md)

---

by **[NEFAS](https://boosty.to/cmapnep)** — tools for those who value substance over noise.