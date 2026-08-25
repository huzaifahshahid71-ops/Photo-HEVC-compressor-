# HEIC Drop Converter

A fast, lightweight Windows desktop application for converting common image formats to **HEIC/HEIF using HEVC compression** while preserving important photo metadata.

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
- 🖥️ Modern dark desktop interface

---

## 📸 Supported Input Formats

HEIC Drop Converter supports:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.tif`
- `.tiff`
- `.bmp`

All supported formats are converted to `.heic`.

---

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

---

## 🧾 Metadata Preservation

HEIC Drop Converter is designed to retain important photo information during conversion.

### Preserved

- EXIF metadata
- Camera date/time
- GPS information
- Orientation
- Original pixel dimensions
- ICC color profile when available

The converter preserves the stored orientation rather than physically rotating the image.

---

## 📂 Output Options

You can choose between two output modes.

### Same Folder

Converted `.heic` files are placed beside their original images.

```text
Photos/
├── IMG_0001.jpg
├── IMG_0001.heic
├── IMG_0002.jpg
└── IMG_0002.heic
```

### Custom Folder

Choose a separate destination for all converted files.

Existing files are not overwritten. If a filename already exists, the converter automatically creates a unique filename:

```text
IMG_0001.heic
IMG_0001 (1).heic
IMG_0001 (2).heic
```

---

## 🖱️ How to Use

### 1. Add Images

You can either:

- Drag and drop photos into the application
- Click **Add Files**
- Click **Add Folder**

Folders are searched recursively for supported image files.

### 2. Select Quality

Use the **HEIC Quality** slider to choose your desired compression level.

### 3. Select Output Location

Choose:

- **Same folder as source**, or
- **Custom folder**

### 4. Start Conversion

Click **Start Conversion**.

The application displays:

- Current file
- Original size
- Conversion status
- HEIC size
- Overall progress
- Total space saved

---

## 📊 Conversion Statistics

After conversion, the application reports the total results:

```text
Converted: 100
Failed: 0

Original: 1.2 GB
HEIC: 420 MB
Space saved: 65.0%
```

The application calculates the total output size and percentage of storage saved.

---

## 🧵 Batch Processing

Multiple images can be added to the conversion queue and processed in one operation.

The application provides live progress updates and reports successful and failed conversions individually.

---

## ⚠️ Notes

- HEIC encoding quality and resulting file size depend on the source image and selected quality setting.
- A lower quality setting does **not** guarantee a specific percentage reduction in file size.
- Metadata preservation depends on metadata being present in the original file.
- Original pixel dimensions are retained during conversion.

---

## 📥 Download

Download the latest **HEIC Drop Converter `.exe`** from the Releases section of this repository.

No Python installation or additional dependencies are required.

Simply download the executable and run it.

---

## 🏗️ Built With

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop GUI |
| Pillow | Image processing |
| pillow-heif | HEIF/HEIC encoding |
| HEVC | Image compression codec |

---

## 📌 Version

**HEIC Drop Converter v3.0**

---

## 📄 License

Add your preferred license here.

If this project is intended to remain personal/private, a license can be omitted.
