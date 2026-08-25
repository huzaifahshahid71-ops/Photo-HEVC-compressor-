# HEIC Drop Converter

A fast, lightweight Windows desktop application for converting common image formats to **HEIC/HEIF using HEVC compression** while preserving important photo metadata.

**App Developer: Huzaifah**

## ✨ Features

- 🖼️ Convert images to **HEIC**
- 🚀 HEVC-based HEIC compression
- 🎚️ Adjustable quality from **10% to 100%**
- 📁 Drag-and-drop support
- 📂 Add individual files or entire folders
- 🔄 Batch conversion
- 📊 Live conversion progress
- 💾 Displays original size, output size, and space saved
- 📍 Preserves EXIF metadata
- 📅 Preserves date-taken metadata when available
- 🌍 Preserves GPS metadata when available
- 🔄 Preserves image orientation
- 📐 Preserves original pixel resolution
- 🎨 Preserves ICC color profiles when available
- 📂 Save beside the original files or to a custom folder
- 📝 Automatically avoids overwriting existing files
- 🧵 Conversion runs in the background so the interface remains responsive
- 🖥️ Modern dark PySide6 desktop interface

## 📸 Supported Input Formats

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.tif`
- `.tiff`
- `.bmp`

All supported formats are converted to `.heic`.

## 🎚️ Quality Settings

The converter provides a continuous quality slider from **10% to 100%**.

| Quality | Intended Use |
|---:|---|
| 10–35% | Maximum compression / smallest files |
| 36–55% | Strong compression |
| 56–75% | Everyday storage and sharing |
| 76–90% | High quality / recommended balance |
| 91–100% | Near-original visual quality |

The default quality is **85%**.

> Higher quality generally produces larger files, while lower quality prioritizes file-size reduction.

## 🧾 Metadata Preservation

The app is designed to retain important photo information during conversion:

- EXIF metadata
- Camera date/time
- GPS information
- Orientation
- Original pixel dimensions
- ICC color profile when available

The converter preserves the stored orientation rather than physically rotating the image.

## 📂 Output Options

Choose either:

- **Same folder as source** — places the new `.heic` beside the original image.
- **Custom folder** — sends all converted images to a destination you choose.

Existing files are never overwritten. If a filename already exists, the app automatically creates a unique name such as:

```text
IMG_0001.heic
IMG_0001 (1).heic
IMG_0001 (2).heic
```

## 🖱️ How to Use

1. Drag photos into the application, click **Add Files**, or click **Add Folder**.
2. Set the desired **HEIC Quality**.
3. Choose the output location.
4. Click **Start Conversion**.
5. Follow the live progress and storage-saving statistics in the interface.

Folders are searched recursively for supported images.

## 🏗️ Build the Windows EXE

This repository contains everything needed to build the application yourself on Windows.

### Requirements

- Windows 10 or Windows 11
- Python 3.x from [python.org](https://www.python.org/)
- The Python launcher (`py`) enabled during Python installation
- Internet access during the first build so Python packages can be installed

### Easiest method

1. Download or clone this repository.
2. Keep these files together in the same folder:

```text
heic_drop_converter.py
generate_icon.py
Build_HEIC_Drop_Converter.bat
```

If the artwork/icon files are missing, the builder automatically generates `HEIC-Drop-Converter.ico` and `HEIC-Drop-Converter.png` using `generate_icon.py`.

3. Double-click:

```text
Build_HEIC_Drop_Converter.bat
```

4. The builder automatically installs/updates:
   - PySide6
   - Pillow
   - pillow-heif
   - PyInstaller
5. When the build completes, the finished application will be located at:

```text
dist\HEIC-Drop-Converter.exe
```

The script also opens the `dist` folder automatically after a successful build.

### Manual build

Install the dependencies:

```powershell
py -3 -m pip install --upgrade PySide6 Pillow pillow-heif pyinstaller
```

Generate the application artwork and Windows icon:

```powershell
py -3 generate_icon.py
```

Then build the executable:

```powershell
py -3 -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name "HEIC-Drop-Converter" `
  --icon "HEIC-Drop-Converter.ico" `
  --add-data "HEIC-Drop-Converter.ico;." `
  --collect-all pillow_heif `
  "heic_drop_converter.py"
```

## 📦 Why the EXE Is Relatively Large

The standalone executable contains the Python runtime together with **PySide6/Qt**, **Pillow**, and the **pillow-heif / HEIF-HEVC libraries**. This allows the application to run on another Windows PC without requiring the user to install Python or those dependencies separately.

Normal ZIP/7Z compression may reduce the executable only slightly because a PyInstaller one-file build already contains compressed application data.

## 🧰 Project Files

| File | Purpose |
|---|---|
| `heic_drop_converter.py` | Main application source code |
| `Build_HEIC_Drop_Converter.bat` | One-click Windows EXE builder |
| `generate_icon.py` | Generates the project artwork and Windows icon |
| `HEIC-Drop-Converter.ico` | Generated Windows executable/application icon |
| `HEIC-Drop-Converter.png` | Generated project artwork / icon image |
| `requirements.txt` | Python dependencies |

## 🛠️ Built With

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop GUI |
| Pillow | Image processing |
| pillow-heif | HEIF/HEIC encoding |
| HEVC | Image compression codec |
| PyInstaller | Standalone Windows executable packaging |

## 📌 Version

**HEIC Drop Converter v3.0**

## 👨‍💻 Developer

**Huzaifah**
