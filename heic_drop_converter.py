import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QFrame,
    QSlider,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QRadioButton,
    QButtonGroup,
    QSizePolicy,
    QAbstractItemView,
)
from PIL import Image
import pillow_heif


pillow_heif.register_heif_opener()

APP_TITLE = "HEIC Drop Converter"
APP_VERSION = "3.0"
ICON_NAME = "HEIC-Drop-Converter.ico"
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def resource_path(name: str) -> Path:
    """Return a bundled PyInstaller resource or a file beside the script."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def format_bytes(value: int) -> str:
    value = int(value)
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path

    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def convert_one(src: Path, out_dir: Path, quality: int):
    """
    Convert one image to HEIC while retaining the original pixel dimensions
    and EXIF metadata (including camera date/GPS/orientation when present).
    """
    with Image.open(src) as im:
        exif = im.getexif()
        exif_bytes = exif.tobytes() if exif else None

        # Preserve the image's stored orientation instead of physically rotating it.
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")

        out_dir.mkdir(parents=True, exist_ok=True)
        dst = unique_output_path(out_dir / f"{src.stem}.heic")

        save_kwargs = {
            "format": "HEIF",
            "quality": int(quality),
            "compression": "HEVC",
        }
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes

        # Preserve ICC profile when available.
        icc_profile = im.info.get("icc_profile")
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile

        im.save(dst, **save_kwargs)

    return dst, src.stat().st_size, dst.stat().st_size


class WorkerSignals(QObject):
    file_done = Signal(str, int, int, bool, str)
    progress = Signal(int, int, str)
    finished = Signal(list, list)


def process_files(files, custom_out_dir, same_folder, quality, signals):
    ok = []
    failed = []
    total = len(files)

    for index, src in enumerate(files, 1):
        try:
            out_dir = src.parent if same_folder else custom_out_dir
            dst, old_size, new_size = convert_one(src, out_dir, quality)
            ok.append((src, dst, old_size, new_size))
            signals.file_done.emit(str(src), old_size, new_size, True, "")
        except Exception as exc:
            failed.append((src, str(exc)))
            signals.file_done.emit(str(src), src.stat().st_size if src.exists() else 0, 0, False, str(exc))

        signals.progress.emit(index, total, src.name)

    signals.finished.emit(ok, failed)


class DropZone(QFrame):
    filesDropped = Signal(list)

    def __init__(self, icon_path: Path, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self.setMinimumHeight(310)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo = QLabel()
        self.logo.setObjectName("dropLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.logo.setPixmap(icon.pixmap(112, 112))
        else:
            self.logo.setText("⇩")

        title = QLabel("Drop photos here")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        or_label = QLabel("or")
        or_label.setObjectName("muted")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.add_files_btn = QPushButton("  Add Files")
        self.add_files_btn.setObjectName("primarySmall")

        self.add_folder_btn = QPushButton("  Add Folder")
        self.add_folder_btn.setObjectName("secondarySmall")

        buttons.addStretch()
        buttons.addWidget(self.add_files_btn)
        buttons.addWidget(self.add_folder_btn)
        buttons.addStretch()

        subtitle = QLabel("Supports JPG, JPEG, PNG, WEBP, TIFF and BMP")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.logo)
        layout.addWidget(title)
        layout.addWidget(or_label)
        layout.addLayout(buttons)
        layout.addWidget(subtitle)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        paths = []

        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())

            if path.is_dir():
                paths.extend(
                    file
                    for file in path.rglob("*")
                    if file.is_file() and file.suffix.lower() in SUPPORTED
                )
            elif path.is_file() and path.suffix.lower() in SUPPORTED:
                paths.append(path)

        seen = set()
        unique_files = []

        for path in paths:
            try:
                key = str(path.resolve()).lower()
            except OSError:
                key = str(path).lower()

            if key not in seen:
                seen.add(key)
                unique_files.append(path)

        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

        if unique_files:
            self.filesDropped.emit(unique_files)

        event.acceptProposedAction()


class StatCard(QFrame):
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")

        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")

        layout.addWidget(self.value_label)
        layout.addWidget(label_widget)


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.icon_path = resource_path(ICON_NAME)
        self.files = []
        self.items = {}
        self.processing = False
        self.output_dir = None
        self.total_output_bytes = 0

        self.setObjectName("root")
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1050, 700)
        self.resize(1260, 800)

        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))

        self.build_ui()
        self.apply_styles()
        self.update_quality_text(self.quality_slider.value())

    def build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- Sidebar ----------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 24, 20, 20)
        side.setSpacing(14)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        logo = QLabel()
        logo.setFixedSize(46, 46)
        if self.icon_path.exists():
            logo.setPixmap(QIcon(str(self.icon_path)).pixmap(46, 46))

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)

        name = QLabel("HEIC Drop\nConverter")
        name.setObjectName("brandName")

        tagline = QLabel("Smaller files.\nSame quality.")
        tagline.setObjectName("brandTagline")

        brand_text.addWidget(name)
        brand_text.addWidget(tagline)

        brand_row.addWidget(logo)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()

        side.addLayout(brand_row)
        side.addSpacing(14)

        active = QPushButton("  Convert")
        active.setObjectName("navActive")
        active.setEnabled(False)

        queue_hint = QPushButton("  Queue")
        queue_hint.setObjectName("navGhost")
        queue_hint.setEnabled(False)

        settings_hint = QPushButton("  Settings")
        settings_hint.setObjectName("navGhost")
        settings_hint.setEnabled(False)

        side.addWidget(active)
        side.addWidget(queue_hint)
        side.addWidget(settings_hint)
        side.addStretch()

        preserved = QLabel("✓ EXIF preserved\n✓ GPS preserved\n✓ Original resolution")
        preserved.setObjectName("sideFeature")
        side.addWidget(preserved)

        developer = QLabel("App Developer: Huzaifah")
        developer.setObjectName("developer")
        side.addWidget(developer)

        version = QLabel(f"HEIC Drop Converter  v{APP_VERSION}")
        version.setObjectName("version")
        side.addWidget(version)

        root.addWidget(sidebar)

        # ---------------- Main content ----------------
        content = QFrame()
        content.setObjectName("content")

        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(2)

        title = QLabel("HEIC Drop Converter")
        title.setObjectName("title")

        subtitle = QLabel("Fast HEVC photo compression with metadata and resolution preserved")
        subtitle.setObjectName("subtitle")

        titles.addWidget(title)
        titles.addWidget(subtitle)

        header.addLayout(titles)
        header.addStretch()

        self.header_count = QLabel("0 photos")
        self.header_count.setObjectName("countPill")
        header.addWidget(self.header_count)

        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ---------------- Left column ----------------
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        self.drop = DropZone(self.icon_path)
        self.drop.filesDropped.connect(self.add_files)
        self.drop.add_files_btn.clicked.connect(self.pick_files)
        self.drop.add_folder_btn.clicked.connect(self.pick_folder)
        left_col.addWidget(self.drop)

        queue_card = QFrame()
        queue_card.setObjectName("card")

        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(14, 12, 14, 12)
        queue_layout.setSpacing(10)

        queue_header = QHBoxLayout()
        queue_title = QLabel("Conversion Queue")
        queue_title.setObjectName("sectionTitle")
        queue_header.addWidget(queue_title)

        self.queue_count = QLabel("0")
        self.queue_count.setObjectName("miniPill")
        queue_header.addWidget(self.queue_count)

        queue_header.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("textButton")
        self.clear_btn.clicked.connect(self.clear_files)
        queue_header.addWidget(self.clear_btn)

        queue_layout.addLayout(queue_header)

        self.queue = QTreeWidget()
        self.queue.setObjectName("queue")
        self.queue.setColumnCount(4)
        self.queue.setHeaderLabels(["Photo", "Original", "Status", "HEIC"])
        self.queue.setRootIsDecorated(False)
        self.queue.setAlternatingRowColors(False)
        self.queue.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.queue.setMinimumHeight(205)
        self.queue.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header_view = self.queue.header()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        queue_layout.addWidget(self.queue)
        left_col.addWidget(queue_card, 1)

        body.addLayout(left_col, 3)

        # ---------------- Right column ----------------
        right = QVBoxLayout()
        right.setSpacing(14)

        compression_card = QFrame()
        compression_card.setObjectName("card")

        compression = QVBoxLayout(compression_card)
        compression.setContentsMargins(16, 15, 16, 16)
        compression.setSpacing(9)

        compression_title = QLabel("Compression")
        compression_title.setObjectName("sectionTitle")
        compression.addWidget(compression_title)

        top_quality = QHBoxLayout()
        quality_label = QLabel("HEIC quality")
        quality_label.setObjectName("labelStrong")

        self.quality_value = QLabel("85%")
        self.quality_value.setObjectName("qualityValue")

        top_quality.addWidget(quality_label)
        top_quality.addStretch()
        top_quality.addWidget(self.quality_value)

        compression.addLayout(top_quality)

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setSingleStep(1)
        self.quality_slider.setPageStep(5)
        self.quality_slider.valueChanged.connect(self.update_quality_text)
        compression.addWidget(self.quality_slider)

        scale = QHBoxLayout()
        low = QLabel("10")
        mid = QLabel("55")
        high = QLabel("100")
        for widget in (low, mid, high):
            widget.setObjectName("scaleLabel")

        scale.addWidget(low)
        scale.addStretch()
        scale.addWidget(mid)
        scale.addStretch()
        scale.addWidget(high)
        compression.addLayout(scale)

        self.quality_hint = QLabel()
        self.quality_hint.setObjectName("hintBox")
        self.quality_hint.setWordWrap(True)
        compression.addWidget(self.quality_hint)

        right.addWidget(compression_card)

        output_card = QFrame()
        output_card.setObjectName("card")
        output = QVBoxLayout(output_card)
        output.setContentsMargins(16, 15, 16, 16)
        output.setSpacing(10)

        output_title = QLabel("Output Folder")
        output_title.setObjectName("sectionTitle")
        output.addWidget(output_title)

        self.same_folder_radio = QRadioButton("Same folder as source")
        self.custom_folder_radio = QRadioButton("Custom folder")
        self.same_folder_radio.setChecked(True)

        self.output_group = QButtonGroup(self)
        self.output_group.addButton(self.same_folder_radio)
        self.output_group.addButton(self.custom_folder_radio)

        self.same_folder_radio.toggled.connect(self.output_mode_changed)
        self.custom_folder_radio.toggled.connect(self.output_mode_changed)

        output.addWidget(self.same_folder_radio)
        output.addWidget(self.custom_folder_radio)

        self.output_btn = QPushButton("Choose custom folder")
        self.output_btn.setObjectName("secondaryButton")
        self.output_btn.setEnabled(False)
        self.output_btn.clicked.connect(self.choose_output)
        output.addWidget(self.output_btn)

        right.addWidget(output_card)

        preserve_card = QFrame()
        preserve_card.setObjectName("card")
        preserve = QVBoxLayout(preserve_card)
        preserve.setContentsMargins(16, 14, 16, 14)
        preserve.setSpacing(7)

        preserve_title = QLabel("Preservation")
        preserve_title.setObjectName("sectionTitle")
        preserve.addWidget(preserve_title)

        for text in (
            "✓ EXIF metadata",
            "✓ Date taken & GPS",
            "✓ Orientation",
            "✓ Original pixel resolution",
        ):
            item = QLabel(text)
            item.setObjectName("preserveItem")
            preserve.addWidget(item)

        right.addWidget(preserve_card)

        self.convert_btn = QPushButton("Start Conversion")
        self.convert_btn.setObjectName("convert")
        self.convert_btn.setMinimumHeight(52)
        self.convert_btn.clicked.connect(self.start_conversion)
        right.addWidget(self.convert_btn)

        stats = QHBoxLayout()
        stats.setSpacing(8)

        self.original_stat = StatCard("Original", "0 B")
        self.output_stat = StatCard("HEIC", "—")
        self.saved_stat = StatCard("Saved", "—")

        stats.addWidget(self.original_stat)
        stats.addWidget(self.output_stat)
        stats.addWidget(self.saved_stat)

        right.addLayout(stats)
        right.addStretch()

        body.addLayout(right, 2)

        outer.addLayout(body, 1)

        # ---------------- Footer ----------------
        footer = QFrame()
        footer.setObjectName("footerCard")

        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 9, 12, 9)
        footer_layout.setSpacing(5)

        row = QHBoxLayout()

        self.status = QLabel("Ready — add photos to begin.")
        self.status.setObjectName("status")
        row.addWidget(self.status)
        row.addStretch()

        self.footer_saved = QLabel("")
        self.footer_saved.setObjectName("savedText")
        row.addWidget(self.footer_saved)

        footer_layout.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        footer_layout.addWidget(self.progress)

        outer.addWidget(footer)

        root.addWidget(content, 1)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget#root {
                background: #08111f;
                color: #f6f8ff;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QFrame#content {
                background: #0b1424;
            }

            QFrame#sidebar {
                background: #07101d;
                border-right: 1px solid #1b2d49;
            }

            QLabel#brandName {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#brandTagline,
            QLabel#version {
                color: #7285a3;
                font-size: 10px;
            }

            QLabel#developer {
                color: #9ccaff;
                font-size: 10px;
                font-weight: 600;
            }

            QLabel#sideFeature {
                color: #8da5c8;
                line-height: 1.5;
                font-size: 11px;
                background: #0b1627;
                border: 1px solid #172b49;
                border-radius: 10px;
                padding: 10px;
            }

            QPushButton#navActive {
                text-align: left;
                color: #ffffff;
                background: #0d6efd;
                border: 1px solid #2d8cff;
                border-radius: 10px;
                padding: 10px 12px;
                font-weight: 650;
            }

            QPushButton#navActive:disabled {
                color: #ffffff;
                background: #0d6efd;
            }

            QPushButton#navGhost {
                text-align: left;
                color: #7e91af;
                background: transparent;
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 10px 12px;
            }

            QPushButton#navGhost:disabled {
                color: #6f829f;
                background: transparent;
            }

            QLabel#title {
                font-size: 26px;
                font-weight: 750;
                color: #ffffff;
            }

            QLabel#subtitle,
            QLabel#muted {
                color: #7f92b0;
            }

            QLabel#countPill {
                color: #9ccaff;
                background: #0e1f38;
                border: 1px solid #1d4776;
                border-radius: 12px;
                padding: 6px 11px;
                font-weight: 600;
            }

            QFrame#dropZone {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0c1729,
                    stop:1 #0a1322
                );
                border: 1px dashed #2679da;
                border-radius: 18px;
            }

            QFrame#dropZone[dragging="true"] {
                background: #0c203a;
                border: 2px dashed #42a5ff;
            }

            QLabel#dropTitle {
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
            }

            QPushButton#primarySmall,
            QPushButton#secondarySmall,
            QPushButton#secondaryButton,
            QPushButton#textButton {
                border-radius: 9px;
                padding: 9px 14px;
                font-weight: 600;
            }

            QPushButton#primarySmall {
                color: #ffffff;
                background: #087cff;
                border: 1px solid #32a1ff;
                min-width: 130px;
            }

            QPushButton#primarySmall:hover {
                background: #168cff;
            }

            QPushButton#secondarySmall,
            QPushButton#secondaryButton {
                color: #dbe8ff;
                background: #121f34;
                border: 1px solid #253a59;
                min-width: 130px;
            }

            QPushButton#secondarySmall:hover,
            QPushButton#secondaryButton:hover {
                background: #182943;
                border-color: #35547e;
            }

            QPushButton#secondaryButton:disabled {
                color: #53637d;
                background: #0d1726;
                border-color: #1a2a42;
            }

            QPushButton#textButton {
                color: #8da5c8;
                background: transparent;
                border: none;
                padding: 5px 8px;
            }

            QPushButton#textButton:hover {
                color: #ffffff;
                background: #13233a;
            }

            QFrame#card,
            QFrame#footerCard {
                background: #0c1728;
                border: 1px solid #182b48;
                border-radius: 14px;
            }

            QLabel#sectionTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#labelStrong {
                color: #dfe9f8;
                font-weight: 650;
            }

            QLabel#qualityValue {
                color: #ffffff;
                font-size: 29px;
                font-weight: 800;
            }

            QLabel#scaleLabel {
                color: #5f7494;
                font-size: 10px;
            }

            QLabel#hintBox {
                color: #8fa7c8;
                background: #0a1322;
                border: 1px solid #152945;
                border-radius: 9px;
                padding: 9px;
            }

            QLabel#preserveItem {
                color: #9fd6b8;
                padding: 2px 0;
            }

            QRadioButton {
                color: #d6e2f3;
                spacing: 8px;
            }

            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }

            QRadioButton::indicator:unchecked {
                border: 1px solid #496482;
                border-radius: 8px;
                background: #0a1423;
            }

            QRadioButton::indicator:checked {
                border: 4px solid #2287ff;
                border-radius: 8px;
                background: #dcecff;
            }

            QSlider::groove:horizontal {
                height: 7px;
                border-radius: 3px;
                background: #1a2c49;
            }

            QSlider::sub-page:horizontal {
                border-radius: 3px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #20d67a,
                    stop:0.45 #15bce9,
                    stop:1 #1d7cff
                );
            }

            QSlider::handle:horizontal {
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
                background: #ffffff;
                border: 2px solid #1589ff;
            }

            QTreeWidget#queue {
                background: #091321;
                alternate-background-color: #0b1627;
                color: #dfe8f8;
                border: 1px solid #142742;
                border-radius: 10px;
                outline: none;
                padding: 2px;
            }

            QTreeWidget#queue::item {
                border-bottom: 1px solid #12233b;
                padding: 8px 4px;
            }

            QTreeWidget#queue::item:selected {
                background: #12315a;
                color: #ffffff;
            }

            QHeaderView::section {
                color: #7f95b6;
                background: #0c1728;
                border: none;
                border-bottom: 1px solid #1c304f;
                padding: 7px 5px;
                font-weight: 600;
            }

            QLabel#miniPill {
                color: #9ecbff;
                background: #112642;
                border-radius: 9px;
                padding: 2px 7px;
            }

            QPushButton#convert {
                color: #ffffff;
                font-size: 15px;
                font-weight: 750;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #087cff,
                    stop:0.6 #166dff,
                    stop:1 #7047ff
                );
                border: 1px solid #2b8bff;
                border-radius: 12px;
                padding: 12px 18px;
            }

            QPushButton#convert:hover {
                border-color: #73b9ff;
            }

            QPushButton#convert:disabled {
                color: #75849b;
                background: #16243a;
                border-color: #243852;
            }

            QFrame#statCard {
                background: #091321;
                border: 1px solid #172a46;
                border-radius: 10px;
            }

            QLabel#statValue {
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#statLabel {
                color: #6f86a7;
                font-size: 10px;
            }

            QLabel#status {
                color: #96a9c4;
            }

            QLabel#savedText {
                color: #43da88;
                font-weight: 700;
            }

            QProgressBar {
                min-height: 6px;
                max-height: 6px;
                background: #13223a;
                border: none;
                border-radius: 3px;
            }

            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a7cff,
                    stop:1 #6a55ff
                );
                border-radius: 3px;
            }

            QMessageBox {
                background: #0c1728;
            }
            """
        )

    def update_quality_text(self, value: int):
        self.quality_value.setText(f"{value}%")

        if value <= 35:
            message = "Maximum compression • best when file size matters more than fine detail."
        elif value <= 55:
            message = "Strong compression • very small files with visible quality trade-offs."
        elif value <= 75:
            message = "Efficient compression • good for everyday sharing and storage."
        elif value <= 90:
            message = "High quality • recommended balance between detail and file size."
        else:
            message = "Near-original quality • larger HEIC files with minimal visual loss."

        self.quality_hint.setText(message)

    def output_mode_changed(self):
        self.output_btn.setEnabled(self.custom_folder_radio.isChecked() and not self.processing)

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select photos",
            "",
            "Photos (*.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp)",
        )
        if files:
            self.add_files([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add a folder of photos")
        if not folder:
            return

        base = Path(folder)
        files = [
            file
            for file in base.rglob("*")
            if file.is_file() and file.suffix.lower() in SUPPORTED
        ]
        self.add_files(files)

    def add_files(self, paths):
        existing = {str(path.resolve()).lower() for path in self.files}
        added = 0

        for path in paths:
            path = Path(path)
            if not path.exists() or not path.is_file() or path.suffix.lower() not in SUPPORTED:
                continue

            key = str(path.resolve()).lower()
            if key in existing:
                continue

            self.files.append(path)
            existing.add(key)
            added += 1

            item = QTreeWidgetItem(
                [
                    path.name,
                    format_bytes(path.stat().st_size),
                    "Waiting",
                    "—",
                ]
            )
            item.setToolTip(0, str(path))
            self.queue.addTopLevelItem(item)
            self.items[key] = item

        if added:
            self.update_queue_summary()
            self.progress.setValue(0)
            self.status.setText(f"Ready — {len(self.files):,} photo(s) in the queue.")

    def update_queue_summary(self):
        count = len(self.files)
        self.header_count.setText(f"{count:,} photo" + ("" if count == 1 else "s"))
        self.queue_count.setText(str(count))

        total = sum(path.stat().st_size for path in self.files if path.exists())
        self.original_stat.value_label.setText(format_bytes(total))

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if folder:
            self.output_dir = Path(folder)
            self.output_btn.setText(f"Output: {self.output_dir.name}")

    def clear_files(self):
        if self.processing:
            return

        self.files.clear()
        self.items.clear()
        self.queue.clear()
        self.total_output_bytes = 0

        self.header_count.setText("0 photos")
        self.queue_count.setText("0")
        self.original_stat.value_label.setText("0 B")
        self.output_stat.value_label.setText("—")
        self.saved_stat.value_label.setText("—")
        self.footer_saved.setText("")
        self.progress.setValue(0)
        self.status.setText("Ready — add photos to begin.")

    def set_controls_enabled(self, enabled: bool):
        self.drop.add_files_btn.setEnabled(enabled)
        self.drop.add_folder_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.quality_slider.setEnabled(enabled)
        self.same_folder_radio.setEnabled(enabled)
        self.custom_folder_radio.setEnabled(enabled)
        self.output_btn.setEnabled(
            enabled and self.custom_folder_radio.isChecked()
        )

    def start_conversion(self):
        if self.processing:
            return

        if not self.files:
            QMessageBox.information(self, APP_TITLE, "Add or drop some photos first.")
            return

        same_folder = self.same_folder_radio.isChecked()

        if not same_folder:
            if self.output_dir is None:
                self.choose_output()
            if self.output_dir is None:
                return
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.processing = True
        self.total_output_bytes = 0

        for path in self.files:
            key = str(path.resolve()).lower()
            item = self.items.get(key)
            if item:
                item.setText(2, "Waiting")
                item.setText(3, "—")

        self.progress.setValue(0)
        self.output_stat.value_label.setText("0 B")
        self.saved_stat.value_label.setText("—")
        self.footer_saved.setText("")
        self.status.setText(f"Converting {len(self.files):,} photo(s)…")

        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Converting…")
        self.set_controls_enabled(False)

        self.signals = WorkerSignals()
        self.signals.file_done.connect(self.file_finished)
        self.signals.progress.connect(self.update_progress)
        self.signals.finished.connect(self.finished)

        quality = self.quality_slider.value()
        files = list(self.files)

        threading.Thread(
            target=process_files,
            args=(files, self.output_dir, same_folder, quality, self.signals),
            daemon=True,
        ).start()

    def file_finished(self, src_text, old_size, new_size, success, error):
        key = str(Path(src_text).resolve()).lower()
        item = self.items.get(key)

        if item:
            if success:
                item.setText(2, "Completed")
                item.setText(3, format_bytes(new_size))
                ratio = (1 - new_size / old_size) * 100 if old_size else 0
                item.setToolTip(2, f"Saved {ratio:.1f}%")
            else:
                item.setText(2, "Failed")
                item.setText(3, "—")
                item.setToolTip(2, error)

        if success:
            self.total_output_bytes += new_size
            self.output_stat.value_label.setText(format_bytes(self.total_output_bytes))

            original_total = sum(path.stat().st_size for path in self.files if path.exists())
            if original_total:
                saved = (1 - self.total_output_bytes / original_total) * 100
                # While conversion is running this is provisional, but still useful.
                self.saved_stat.value_label.setText(f"{saved:.1f}%")

    def update_progress(self, current, total, name):
        percent = round(current * 100 / total) if total else 0
        self.progress.setValue(percent)
        self.status.setText(f"Converting {current:,}/{total:,} — {name}")

    def finished(self, ok, failed):
        self.processing = False

        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Start Conversion")
        self.set_controls_enabled(True)

        total_old = sum(row[2] for row in ok)
        total_new = sum(row[3] for row in ok)
        saved = (1 - total_new / total_old) * 100 if total_old else 0

        self.progress.setValue(100 if ok else 0)

        if ok:
            self.output_stat.value_label.setText(format_bytes(total_new))
            self.saved_stat.value_label.setText(f"{saved:.1f}%")
            self.footer_saved.setText(f"Saved {saved:.1f}%")
        else:
            self.output_stat.value_label.setText("—")
            self.saved_stat.value_label.setText("—")
            self.footer_saved.setText("")

        if failed:
            self.status.setText(
                f"Finished — {len(ok):,} converted, {len(failed):,} failed."
            )
        else:
            self.status.setText(f"Finished — {len(ok):,} photo(s) converted successfully.")

        output_text = (
            "Beside each source photo"
            if self.same_folder_radio.isChecked()
            else str(self.output_dir)
        )

        message = (
            f"Converted: {len(ok):,}\n"
            f"Failed: {len(failed):,}\n\n"
            f"Original: {format_bytes(total_old)}\n"
            f"HEIC: {format_bytes(total_new)}\n"
            f"Space saved: {saved:.1f}%\n\n"
            f"Output: {output_text}"
        )

        QMessageBox.information(self, APP_TITLE, message)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyle("Fusion")

    icon_path = resource_path(ICON_NAME)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = Window()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
