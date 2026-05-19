"""PyQt5 GUI for Music Video Compiler."""

import os
import sys
import json
import random
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from .ffmpeg_engine import (
    EncodingSettings,
    Resolution,
    GPUAccel,
    detect_gpu,          
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QLabel, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QTextEdit, QProgressBar, QSlider,
    QColorDialog, QMessageBox, QScrollArea,
    QGridLayout, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from .ffmpeg_engine import (
    EncodingSettings, Resolution, GPUAccel, RateControl,
    detect_gpu, find_ffmpeg, get_media_duration,
    concat_audio_files, loop_video_to_duration, merge_video_audio,
    create_slideshow, add_intro_outro,
    build_encoding_args,
)
from .effects_engine import (
    ALL_EFFECTS,
    build_effect_filter_chain, get_random_effect,
    get_categories,
)
from .overlay_engine import (
    OverlayPosition, SongTitleOverlaySettings,
    apply_song_titles_to_video,
    MultiOverlayItem, OverlayType,
)
from .timestamp_generator import (
    generate_youtube_timestamps, generate_playlist_png,
    generate_playlist_description, PlaylistPNGSettings,
    save_timestamps_to_file,
)
from .audio_mixer import EQ_PRESETS
from .batch_processor import (
    BatchProcessor, BatchSettings,
    get_supported_audio_extensions,
    get_supported_video_extensions,
    get_supported_image_extensions,
)
settings = EncodingSettings(
    gpu_accel=GPUAccel.NONE,   # Paksa CPU
    preset="medium",
    crf=18
)

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2d2d5e;
    background-color: #16213e;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #1a1a2e;
    color: #8888aa;
    padding: 10px 20px;
    border: 1px solid #2d2d5e;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #16213e;
    color: #ff6b35;
    border-bottom: 2px solid #ff6b35;
}
QTabBar::tab:hover {
    color: #ff8c5a;
    background-color: #1e2a4a;
}
QGroupBox {
    border: 1px solid #2d2d5e;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #ff6b35;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #ff6b35;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #ff8c5a;
}
QPushButton:pressed {
    background-color: #e05a2a;
}
QPushButton:disabled {
    background-color: #555;
    color: #999;
}
QPushButton#secondaryBtn {
    background-color: #2d2d5e;
    color: #ccc;
}
QPushButton#secondaryBtn:hover {
    background-color: #3d3d7e;
}
QPushButton#dangerBtn {
    background-color: #c0392b;
}
QPushButton#dangerBtn:hover {
    background-color: #e74c3c;
}
QListWidget {
    background-color: #0f1629;
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}
QListWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1a1a3e;
}
QListWidget::item:selected {
    background-color: #2d2d5e;
    color: #ff6b35;
}
QComboBox {
    background-color: #0f1629;
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
    min-height: 24px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #0f1629;
    color: #e0e0e0;
    border: 1px solid #2d2d5e;
    selection-background-color: #2d2d5e;
}
QSpinBox, QDoubleSpinBox {
    background-color: #0f1629;
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    min-height: 24px;
}
QLineEdit {
    background-color: #0f1629;
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
    min-height: 24px;
}
QTextEdit {
    background-color: #0f1629;
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    padding: 6px;
    color: #e0e0e0;
}
QProgressBar {
    border: 1px solid #2d2d5e;
    border-radius: 4px;
    background-color: #0f1629;
    text-align: center;
    color: white;
    min-height: 24px;
}
QProgressBar::chunk {
    background-color: #ff6b35;
    border-radius: 3px;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #2d2d5e;
    background-color: #0f1629;
}
QCheckBox::indicator:checked {
    background-color: #ff6b35;
    border-color: #ff6b35;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #2d2d5e;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ff6b35;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #ff6b35;
    border-radius: 3px;
}
QStatusBar {
    background-color: #0f1629;
    color: #8888aa;
    border-top: 1px solid #2d2d5e;
}
QMenuBar {
    background-color: #0f1629;
    color: #e0e0e0;
    border-bottom: 1px solid #2d2d5e;
}
QMenuBar::item:selected {
    background-color: #2d2d5e;
}
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2d2d5e;
}
QMenu::item:selected {
    background-color: #2d2d5e;
}
QScrollBar:vertical {
    background: #0f1629;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #2d2d5e;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #3d3d7e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: bold;
    color: #ff6b35;
    padding: 4px 0;
}
QFrame#separator {
    background-color: #2d2d5e;
    max-height: 1px;
}
"""


class RenderThread(QThread):
    """Background thread for rendering video."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, render_func, parent=None):
        super().__init__(parent)
        self.render_func = render_func

    def run(self):
        try:
            self.render_func(
                progress_callback=self.progress.emit,
                status_callback=self.status.emit,
            )
            self.finished_signal.emit(True, "Render complete!")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Video Compiler v1.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self.audio_files: list[str] = []
        self.video_file: str = ""
        self.intro_file: str = ""
        self.outro_file: str = ""
        self.overlay_items: list[MultiOverlayItem] = []
        self.slideshow_images: list[str] = []
        self.timestamps: list[tuple[float, str]] = []
        self.render_thread: Optional[RenderThread] = None
        self.detected_gpu = GPUAccel.NONE

        self._init_ui()
        self._detect_system()

    def _detect_system(self):
        """Detect system capabilities."""
        try:
            find_ffmpeg()
            self.statusBar().showMessage("FFmpeg detected")
        except FileNotFoundError:
            QMessageBox.warning(
                self, "FFmpeg Not Found",
                "FFmpeg is required. Please install FFmpeg and add it to PATH."
            )

        try:
            self.detected_gpu = detect_gpu()
            if self.detected_gpu != GPUAccel.NONE:
                self.gpu_combo.setCurrentText(self.detected_gpu.value)
                self.statusBar().showMessage(
                    f"GPU Detected: {self.detected_gpu.name}"
                )
        except Exception:
            pass

    def _init_ui(self):
        """Initialize the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        self._create_menu_bar()

        header = QLabel("MUSIC VIDEO COMPILER")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setStyleSheet("color: #ff6b35; padding: 8px;")
        main_layout.addWidget(header)

        subtitle = QLabel("Professional Music Compilation Video Creator")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8888aa; font-size: 12px; padding-bottom: 8px;")
        main_layout.addWidget(subtitle)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        tabs.addTab(self._create_main_tab(), "Main")
        tabs.addTab(self._create_effects_tab(), "Effects")
        tabs.addTab(self._create_overlay_tab(), "Overlays")
        tabs.addTab(self._create_timestamps_tab(), "Timestamps")
        tabs.addTab(self._create_audio_tab(), "Audio")
        tabs.addTab(self._create_encoding_tab(), "Encoding")
        tabs.addTab(self._create_batch_tab(), "Batch")

        progress_group = QGroupBox("Render Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #8888aa;")
        progress_layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()

        self.render_btn = QPushButton("START RENDER")
        self.render_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.render_btn.setMinimumHeight(44)
        self.render_btn.clicked.connect(self._start_render)
        btn_layout.addWidget(self.render_btn)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.setMinimumHeight(44)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_render)
        btn_layout.addWidget(self.cancel_btn)

        progress_layout.addLayout(btn_layout)
        main_layout.addWidget(progress_group)

        self.statusBar().showMessage("Ready")

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Project", self._new_project)
        file_menu.addAction("Open Project", self._open_project)
        file_menu.addAction("Save Project", self._save_project)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self._show_about)

    def _create_main_tab(self) -> QWidget:
        """Create the main input tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Audio files section
        audio_group = QGroupBox("Audio Files (Songs)")
        audio_layout = QVBoxLayout(audio_group)

        self.audio_list = QListWidget()
        self.audio_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.audio_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.audio_list.setMinimumHeight(150)
        audio_layout.addWidget(self.audio_list)

        audio_btn_layout = QHBoxLayout()
        add_audio_btn = QPushButton("Add Audio Files")
        add_audio_btn.clicked.connect(self._add_audio_files)
        audio_btn_layout.addWidget(add_audio_btn)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setObjectName("secondaryBtn")
        add_folder_btn.clicked.connect(self._add_audio_folder)
        audio_btn_layout.addWidget(add_folder_btn)

        remove_audio_btn = QPushButton("Remove Selected")
        remove_audio_btn.setObjectName("dangerBtn")
        remove_audio_btn.clicked.connect(self._remove_audio_files)
        audio_btn_layout.addWidget(remove_audio_btn)

        clear_audio_btn = QPushButton("Clear All")
        clear_audio_btn.setObjectName("dangerBtn")
        clear_audio_btn.clicked.connect(self._clear_audio_files)
        audio_btn_layout.addWidget(clear_audio_btn)

        shuffle_btn = QPushButton("Shuffle")
        shuffle_btn.setObjectName("secondaryBtn")
        shuffle_btn.clicked.connect(self._shuffle_audio)
        audio_btn_layout.addWidget(shuffle_btn)

        audio_layout.addLayout(audio_btn_layout)

        self.audio_count_label = QLabel("0 files loaded")
        self.audio_count_label.setStyleSheet("color: #8888aa;")
        audio_layout.addWidget(self.audio_count_label)
        scroll_layout.addWidget(audio_group)

        # Video file section
        video_group = QGroupBox("Background Video")
        video_layout = QHBoxLayout(video_group)

        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select background video file...")
        self.video_path_edit.setReadOnly(True)
        video_layout.addWidget(self.video_path_edit)

        video_btn = QPushButton("Browse")
        video_btn.clicked.connect(self._select_video)
        video_layout.addWidget(video_btn)
        scroll_layout.addWidget(video_group)

        # Slideshow mode
        slide_group = QGroupBox("Slideshow Mode (Alternative to Video)")
        slide_layout = QVBoxLayout(slide_group)

        self.slideshow_check = QCheckBox("Enable Slideshow Mode")
        slide_layout.addWidget(self.slideshow_check)

        self.slide_list = QListWidget()
        self.slide_list.setMaximumHeight(100)
        slide_layout.addWidget(self.slide_list)

        slide_btn_layout = QHBoxLayout()
        add_slide_btn = QPushButton("Add Images")
        add_slide_btn.clicked.connect(self._add_slideshow_images)
        slide_btn_layout.addWidget(add_slide_btn)

        clear_slide_btn = QPushButton("Clear")
        clear_slide_btn.setObjectName("dangerBtn")
        clear_slide_btn.clicked.connect(lambda: (self.slide_list.clear(), self.slideshow_images.clear()))
        slide_btn_layout.addWidget(clear_slide_btn)
        slide_layout.addLayout(slide_btn_layout)

        dur_layout = QHBoxLayout()
        dur_layout.addWidget(QLabel("Duration per image:"))
        self.slide_duration = QDoubleSpinBox()
        self.slide_duration.setRange(1.0, 60.0)
        self.slide_duration.setValue(10.0)
        self.slide_duration.setSuffix(" sec")
        dur_layout.addWidget(self.slide_duration)

        dur_layout.addWidget(QLabel("Transition:"))
        self.slide_transition = QComboBox()
        self.slide_transition.addItems(["fade", "dissolve", "slideright", "slideleft", "wiperight", "wipeleft"])
        dur_layout.addWidget(self.slide_transition)
        slide_layout.addLayout(dur_layout)
        scroll_layout.addWidget(slide_group)

        # Intro/Outro
        io_group = QGroupBox("Intro & Outro Video")
        io_layout = QGridLayout(io_group)

        io_layout.addWidget(QLabel("Intro Video:"), 0, 0)
        self.intro_path_edit = QLineEdit()
        self.intro_path_edit.setPlaceholderText("Optional intro video...")
        self.intro_path_edit.setReadOnly(True)
        io_layout.addWidget(self.intro_path_edit, 0, 1)
        intro_btn = QPushButton("Browse")
        intro_btn.clicked.connect(self._select_intro)
        io_layout.addWidget(intro_btn, 0, 2)

        io_layout.addWidget(QLabel("Outro Video:"), 1, 0)
        self.outro_path_edit = QLineEdit()
        self.outro_path_edit.setPlaceholderText("Optional outro video...")
        self.outro_path_edit.setReadOnly(True)
        io_layout.addWidget(self.outro_path_edit, 1, 1)
        outro_btn = QPushButton("Browse")
        outro_btn.clicked.connect(self._select_outro)
        io_layout.addWidget(outro_btn, 1, 2)

        io_layout.addWidget(QLabel("Audio Mode:"), 2, 0)
        self.audio_mode_combo = QComboBox()
        self.audio_mode_combo.addItems(["Normal", "Seamless", "Mixed"])
        io_layout.addWidget(self.audio_mode_combo, 2, 1)
        scroll_layout.addWidget(io_group)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout(output_group)

        output_layout.addWidget(QLabel("Output File:"), 0, 0)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output file path...")
        output_layout.addWidget(self.output_path_edit, 0, 1)
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(self._select_output)
        output_layout.addWidget(output_btn, 0, 2)
        scroll_layout.addWidget(output_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget

    def _create_effects_tab(self) -> QWidget:
        """Create the visual effects tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Effect list panel
        list_panel = QVBoxLayout()
        list_panel.addWidget(QLabel("Available Effects (30+)"))

        self.effect_filter_combo = QComboBox()
        self.effect_filter_combo.addItem("All Categories")
        for cat in get_categories():
            self.effect_filter_combo.addItem(cat.value)
        self.effect_filter_combo.currentTextChanged.connect(self._filter_effects)
        list_panel.addWidget(self.effect_filter_combo)

        self.effect_list = QListWidget()
        self.effect_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.effect_list.currentItemChanged.connect(self._on_effect_selected)
        list_panel.addWidget(self.effect_list)

        random_btn = QPushButton("Random Effect (Anti-Template)")
        random_btn.clicked.connect(self._apply_random_effect)
        list_panel.addWidget(random_btn)

        layout.addLayout(list_panel, 2)

        # Effect settings panel
        settings_panel = QVBoxLayout()
        settings_panel.addWidget(QLabel("Effect Settings"))

        self.effect_enabled_check = QCheckBox("Enable Selected Effect")
        self.effect_enabled_check.stateChanged.connect(self._toggle_effect)
        settings_panel.addWidget(self.effect_enabled_check)

        self.effect_desc_label = QLabel("")
        self.effect_desc_label.setWordWrap(True)
        self.effect_desc_label.setStyleSheet("color: #8888aa; padding: 8px;")
        settings_panel.addWidget(self.effect_desc_label)

        controls_group = QGroupBox("Controls")
        controls_layout = QGridLayout(controls_group)

        controls_layout.addWidget(QLabel("Intensity:"), 0, 0)
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)
        controls_layout.addWidget(self.intensity_slider, 0, 1)
        self.intensity_label = QLabel("50%")
        controls_layout.addWidget(self.intensity_label, 0, 2)
        self.intensity_slider.valueChanged.connect(
            lambda v: self.intensity_label.setText(f"{v}%")
        )

        controls_layout.addWidget(QLabel("Speed:"), 1, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 300)
        self.speed_slider.setValue(100)
        controls_layout.addWidget(self.speed_slider, 1, 1)
        self.speed_label = QLabel("1.0x")
        controls_layout.addWidget(self.speed_label, 1, 2)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v / 100:.1f}x")
        )

        controls_layout.addWidget(QLabel("Opacity:"), 2, 0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(70)
        controls_layout.addWidget(self.opacity_slider, 2, 1)
        self.opacity_label = QLabel("70%")
        controls_layout.addWidget(self.opacity_label, 2, 2)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )

        controls_layout.addWidget(QLabel("Size:"), 3, 0)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(10, 300)
        self.size_slider.setValue(100)
        controls_layout.addWidget(self.size_slider, 3, 1)
        self.size_label = QLabel("1.0x")
        controls_layout.addWidget(self.size_label, 3, 2)
        self.size_slider.valueChanged.connect(
            lambda v: self.size_label.setText(f"{v / 100:.1f}x")
        )

        settings_panel.addWidget(controls_group)

        # Active effects list
        active_group = QGroupBox("Active Effects")
        active_layout = QVBoxLayout(active_group)
        self.active_effects_list = QListWidget()
        self.active_effects_list.setMaximumHeight(120)
        active_layout.addWidget(self.active_effects_list)

        active_btn_layout = QHBoxLayout()
        remove_effect_btn = QPushButton("Remove")
        remove_effect_btn.setObjectName("dangerBtn")
        remove_effect_btn.clicked.connect(self._remove_active_effect)
        active_btn_layout.addWidget(remove_effect_btn)

        clear_effects_btn = QPushButton("Clear All")
        clear_effects_btn.setObjectName("dangerBtn")
        clear_effects_btn.clicked.connect(self._clear_active_effects)
        active_btn_layout.addWidget(clear_effects_btn)
        active_layout.addLayout(active_btn_layout)

        settings_panel.addWidget(active_group)
        layout.addLayout(settings_panel, 1)

        self._populate_effects()
        return widget

    def _create_overlay_tab(self) -> QWidget:
        """Create the overlay settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Song title overlay
        title_group = QGroupBox("Song Title Overlay")
        title_layout = QGridLayout(title_group)

        self.title_overlay_check = QCheckBox("Enable Song Title Overlay")
        self.title_overlay_check.setChecked(True)
        title_layout.addWidget(self.title_overlay_check, 0, 0, 1, 2)

        title_layout.addWidget(QLabel("Position:"), 1, 0)
        self.title_position_combo = QComboBox()
        for pos in OverlayPosition:
            self.title_position_combo.addItem(pos.label, pos)
        self.title_position_combo.setCurrentIndex(7)  # Bottom Center
        title_layout.addWidget(self.title_position_combo, 1, 1)

        title_layout.addWidget(QLabel("Font Size:"), 2, 0)
        self.title_font_size = QSpinBox()
        self.title_font_size.setRange(12, 120)
        self.title_font_size.setValue(36)
        title_layout.addWidget(self.title_font_size, 2, 1)

        title_layout.addWidget(QLabel("Font Color:"), 3, 0)
        self.title_color_btn = QPushButton("White")
        self.title_color_btn.setStyleSheet("background-color: white; color: black;")
        self.title_color_btn.clicked.connect(lambda: self._pick_color(self.title_color_btn))
        title_layout.addWidget(self.title_color_btn, 3, 1)

        title_layout.addWidget(QLabel("BG Color:"), 4, 0)
        self.title_bg_color_btn = QPushButton("Black (60%)")
        self.title_bg_color_btn.setStyleSheet("background-color: rgba(0,0,0,0.6); color: white;")
        title_layout.addWidget(self.title_bg_color_btn, 4, 1)

        title_layout.addWidget(QLabel("Display Duration:"), 5, 0)
        self.title_duration = QDoubleSpinBox()
        self.title_duration.setRange(1.0, 30.0)
        self.title_duration.setValue(5.0)
        self.title_duration.setSuffix(" sec")
        title_layout.addWidget(self.title_duration, 5, 1)

        title_layout.addWidget(QLabel("Fade In/Out:"), 6, 0)
        fade_layout = QHBoxLayout()
        self.title_fade_in = QDoubleSpinBox()
        self.title_fade_in.setRange(0.0, 5.0)
        self.title_fade_in.setValue(0.5)
        self.title_fade_in.setSuffix(" s")
        fade_layout.addWidget(self.title_fade_in)
        self.title_fade_out = QDoubleSpinBox()
        self.title_fade_out.setRange(0.0, 5.0)
        self.title_fade_out.setValue(0.5)
        self.title_fade_out.setSuffix(" s")
        fade_layout.addWidget(self.title_fade_out)
        title_layout.addLayout(fade_layout, 6, 1)

        title_layout.addWidget(QLabel("Custom Font:"), 7, 0)
        font_layout = QHBoxLayout()
        self.font_path_edit = QLineEdit()
        self.font_path_edit.setPlaceholderText("Optional .ttf font file")
        font_layout.addWidget(self.font_path_edit)
        font_browse_btn = QPushButton("Browse")
        font_browse_btn.clicked.connect(self._select_font)
        font_layout.addWidget(font_browse_btn)
        title_layout.addLayout(font_layout, 7, 1)

        scroll_layout.addWidget(title_group)

        # Multi-overlay support
        multi_group = QGroupBox("Multi-Overlay Support")
        multi_layout = QVBoxLayout(multi_group)

        self.overlay_list = QListWidget()
        self.overlay_list.setMaximumHeight(100)
        multi_layout.addWidget(self.overlay_list)

        ovl_btn_layout = QHBoxLayout()
        add_ovl_btn = QPushButton("Add Overlay")
        add_ovl_btn.clicked.connect(self._add_overlay)
        ovl_btn_layout.addWidget(add_ovl_btn)

        remove_ovl_btn = QPushButton("Remove")
        remove_ovl_btn.setObjectName("dangerBtn")
        remove_ovl_btn.clicked.connect(self._remove_overlay)
        ovl_btn_layout.addWidget(remove_ovl_btn)
        multi_layout.addLayout(ovl_btn_layout)

        ovl_settings = QGridLayout()
        ovl_settings.addWidget(QLabel("Type:"), 0, 0)
        self.overlay_type_combo = QComboBox()
        for ot in OverlayType:
            self.overlay_type_combo.addItem(ot.value)
        ovl_settings.addWidget(self.overlay_type_combo, 0, 1)

        ovl_settings.addWidget(QLabel("Opacity:"), 1, 0)
        self.overlay_opacity = QDoubleSpinBox()
        self.overlay_opacity.setRange(0.0, 1.0)
        self.overlay_opacity.setValue(1.0)
        self.overlay_opacity.setSingleStep(0.1)
        ovl_settings.addWidget(self.overlay_opacity, 1, 1)

        ovl_settings.addWidget(QLabel("Similarity:"), 2, 0)
        self.overlay_similarity = QDoubleSpinBox()
        self.overlay_similarity.setRange(0.0, 1.0)
        self.overlay_similarity.setValue(0.3)
        self.overlay_similarity.setSingleStep(0.05)
        ovl_settings.addWidget(self.overlay_similarity, 2, 1)

        ovl_settings.addWidget(QLabel("Blend:"), 3, 0)
        self.overlay_blend = QDoubleSpinBox()
        self.overlay_blend.setRange(0.0, 1.0)
        self.overlay_blend.setValue(0.5)
        self.overlay_blend.setSingleStep(0.1)
        ovl_settings.addWidget(self.overlay_blend, 3, 1)

        multi_layout.addLayout(ovl_settings)
        scroll_layout.addWidget(multi_group)

        # Spectrum overlay
        spectrum_group = QGroupBox("Audio Spectrum Overlay")
        spectrum_layout = QGridLayout(spectrum_group)

        self.spectrum_check = QCheckBox("Enable Spectrum Overlay")
        spectrum_layout.addWidget(self.spectrum_check, 0, 0, 1, 2)

        spectrum_layout.addWidget(QLabel("Mode:"), 1, 0)
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["combined", "separate", "line"])
        spectrum_layout.addWidget(self.spectrum_mode, 1, 1)

        spectrum_layout.addWidget(QLabel("Color:"), 2, 0)
        self.spectrum_color = QComboBox()
        self.spectrum_color.addItems(["intensity", "rainbow", "moreland", "nebulae", "fire", "fiery", "fruit", "cool"])
        spectrum_layout.addWidget(self.spectrum_color, 2, 1)

        spectrum_layout.addWidget(QLabel("Opacity:"), 3, 0)
        self.spectrum_opacity = QDoubleSpinBox()
        self.spectrum_opacity.setRange(0.1, 1.0)
        self.spectrum_opacity.setValue(0.8)
        self.spectrum_opacity.setSingleStep(0.1)
        spectrum_layout.addWidget(self.spectrum_opacity, 3, 1)

        spectrum_layout.addWidget(QLabel("Position:"), 4, 0)
        self.spectrum_position = QComboBox()
        for pos in OverlayPosition:
            self.spectrum_position.addItem(pos.label, pos)
        self.spectrum_position.setCurrentIndex(7)  # Bottom Center
        spectrum_layout.addWidget(self.spectrum_position, 4, 1)

        scroll_layout.addWidget(spectrum_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget

    def _create_timestamps_tab(self) -> QWidget:
        """Create the timestamps and playlist tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Timestamps preview
        ts_group = QGroupBox("YouTube Timestamps")
        ts_layout = QVBoxLayout(ts_group)

        self.timestamps_text = QTextEdit()
        self.timestamps_text.setReadOnly(True)
        self.timestamps_text.setPlaceholderText(
            "Timestamps will appear here after adding audio files..."
        )
        ts_layout.addWidget(self.timestamps_text)

        ts_btn_layout = QHBoxLayout()
        gen_ts_btn = QPushButton("Generate Timestamps")
        gen_ts_btn.clicked.connect(self._generate_timestamps)
        ts_btn_layout.addWidget(gen_ts_btn)

        copy_ts_btn = QPushButton("Copy to Clipboard")
        copy_ts_btn.setObjectName("secondaryBtn")
        copy_ts_btn.clicked.connect(self._copy_timestamps)
        ts_btn_layout.addWidget(copy_ts_btn)

        save_ts_btn = QPushButton("Save to File")
        save_ts_btn.setObjectName("secondaryBtn")
        save_ts_btn.clicked.connect(self._save_timestamps)
        ts_btn_layout.addWidget(save_ts_btn)

        ts_layout.addLayout(ts_btn_layout)
        layout.addWidget(ts_group)

        # Playlist PNG
        png_group = QGroupBox("Playlist PNG Image")
        png_layout = QVBoxLayout(png_group)

        png_settings = QGridLayout()
        png_settings.addWidget(QLabel("Title:"), 0, 0)
        self.playlist_title = QLineEdit("PLAYLIST")
        png_settings.addWidget(self.playlist_title, 0, 1)

        png_settings.addWidget(QLabel("Size:"), 1, 0)
        size_layout = QHBoxLayout()
        self.png_width = QSpinBox()
        self.png_width.setRange(640, 3840)
        self.png_width.setValue(1280)
        size_layout.addWidget(self.png_width)
        size_layout.addWidget(QLabel("x"))
        self.png_height = QSpinBox()
        self.png_height.setRange(480, 2160)
        self.png_height.setValue(720)
        size_layout.addWidget(self.png_height)
        png_settings.addLayout(size_layout, 1, 1)

        png_settings.addWidget(QLabel("Font Size:"), 2, 0)
        self.png_font_size = QSpinBox()
        self.png_font_size.setRange(10, 60)
        self.png_font_size.setValue(24)
        png_settings.addWidget(self.png_font_size, 2, 1)

        png_settings.addWidget(QLabel("Columns:"), 3, 0)
        self.png_columns = QSpinBox()
        self.png_columns.setRange(1, 4)
        self.png_columns.setValue(1)
        png_settings.addWidget(self.png_columns, 3, 1)

        self.png_show_numbers = QCheckBox("Show Numbers")
        self.png_show_numbers.setChecked(True)
        png_settings.addWidget(self.png_show_numbers, 4, 0)

        self.png_show_timestamps = QCheckBox("Show Timestamps")
        self.png_show_timestamps.setChecked(True)
        png_settings.addWidget(self.png_show_timestamps, 4, 1)

        png_layout.addLayout(png_settings)

        png_btn_layout = QHBoxLayout()
        gen_png_btn = QPushButton("Generate Playlist PNG")
        gen_png_btn.clicked.connect(self._generate_playlist_png)
        png_btn_layout.addWidget(gen_png_btn)

        preview_png_btn = QPushButton("Preview PNG")
        preview_png_btn.setObjectName("secondaryBtn")
        preview_png_btn.clicked.connect(self._preview_playlist_png)
        png_btn_layout.addWidget(preview_png_btn)

        png_layout.addLayout(png_btn_layout)
        layout.addWidget(png_group)

        # Description generator
        desc_group = QGroupBox("YouTube Description Generator")
        desc_layout = QVBoxLayout(desc_group)

        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(120)
        desc_layout.addWidget(self.desc_text)

        desc_btn_layout = QHBoxLayout()
        gen_desc_btn = QPushButton("Generate Description")
        gen_desc_btn.clicked.connect(self._generate_description)
        desc_btn_layout.addWidget(gen_desc_btn)

        copy_desc_btn = QPushButton("Copy")
        copy_desc_btn.setObjectName("secondaryBtn")
        copy_desc_btn.clicked.connect(self._copy_description)
        desc_btn_layout.addWidget(copy_desc_btn)
        desc_layout.addLayout(desc_btn_layout)

        layout.addWidget(desc_group)
        return widget

    def _create_audio_tab(self) -> QWidget:
        """Create the audio mixing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Crossfade
        crossfade_group = QGroupBox("Crossfade Audio")
        crossfade_layout = QGridLayout(crossfade_group)

        self.crossfade_check = QCheckBox("Enable Crossfade")
        crossfade_layout.addWidget(self.crossfade_check, 0, 0, 1, 2)

        crossfade_layout.addWidget(QLabel("Duration:"), 1, 0)
        self.crossfade_duration = QDoubleSpinBox()
        self.crossfade_duration.setRange(0.5, 5.0)
        self.crossfade_duration.setValue(2.0)
        self.crossfade_duration.setSingleStep(0.5)
        self.crossfade_duration.setSuffix(" sec")
        crossfade_layout.addWidget(self.crossfade_duration, 1, 1)

        crossfade_layout.addWidget(QLabel("Curve:"), 2, 0)
        self.crossfade_curve = QComboBox()
        self.crossfade_curve.addItems(["tri", "exp", "log", "par", "qsin", "hsin", "esin"])
        crossfade_layout.addWidget(self.crossfade_curve, 2, 1)

        layout.addWidget(crossfade_group)

        # Audio mixing
        mix_group = QGroupBox("Audio Mixing")
        mix_layout = QGridLayout(mix_group)

        mix_layout.addWidget(QLabel("Master Volume:"), 0, 0)
        self.master_volume = QSlider(Qt.Horizontal)
        self.master_volume.setRange(0, 200)
        self.master_volume.setValue(100)
        mix_layout.addWidget(self.master_volume, 0, 1)
        self.master_vol_label = QLabel("100%")
        mix_layout.addWidget(self.master_vol_label, 0, 2)
        self.master_volume.valueChanged.connect(
            lambda v: self.master_vol_label.setText(f"{v}%")
        )

        mix_layout.addWidget(QLabel("Effect Audio:"), 1, 0)
        self.effect_volume = QSlider(Qt.Horizontal)
        self.effect_volume.setRange(0, 200)
        self.effect_volume.setValue(30)
        mix_layout.addWidget(self.effect_volume, 1, 1)
        self.effect_vol_label = QLabel("30%")
        mix_layout.addWidget(self.effect_vol_label, 1, 2)
        self.effect_volume.valueChanged.connect(
            lambda v: self.effect_vol_label.setText(f"{v}%")
        )

        mix_layout.addWidget(QLabel("Video Audio:"), 2, 0)
        self.video_volume = QSlider(Qt.Horizontal)
        self.video_volume.setRange(0, 200)
        self.video_volume.setValue(0)
        mix_layout.addWidget(self.video_volume, 2, 1)
        self.video_vol_label = QLabel("0%")
        mix_layout.addWidget(self.video_vol_label, 2, 2)
        self.video_volume.valueChanged.connect(
            lambda v: self.video_vol_label.setText(f"{v}%")
        )

        self.normalize_check = QCheckBox("Normalize Audio (Loudnorm)")
        self.normalize_check.setChecked(True)
        mix_layout.addWidget(self.normalize_check, 3, 0, 1, 2)

        self.compressor_check = QCheckBox("Audio Compressor")
        mix_layout.addWidget(self.compressor_check, 4, 0, 1, 2)

        mix_layout.addWidget(QLabel("EQ Preset:"), 5, 0)
        self.eq_combo = QComboBox()
        for preset in EQ_PRESETS:
            self.eq_combo.addItem(preset.replace("_", " ").title(), preset)
        mix_layout.addWidget(self.eq_combo, 5, 1)

        layout.addWidget(mix_group)

        # Fade in/out
        fade_group = QGroupBox("Audio Fade")
        fade_layout = QGridLayout(fade_group)

        fade_layout.addWidget(QLabel("Fade In:"), 0, 0)
        self.audio_fade_in = QDoubleSpinBox()
        self.audio_fade_in.setRange(0.0, 10.0)
        self.audio_fade_in.setValue(0.0)
        self.audio_fade_in.setSuffix(" sec")
        fade_layout.addWidget(self.audio_fade_in, 0, 1)

        fade_layout.addWidget(QLabel("Fade Out:"), 1, 0)
        self.audio_fade_out = QDoubleSpinBox()
        self.audio_fade_out.setRange(0.0, 10.0)
        self.audio_fade_out.setValue(0.0)
        self.audio_fade_out.setSuffix(" sec")
        fade_layout.addWidget(self.audio_fade_out, 1, 1)

        layout.addWidget(fade_group)
        layout.addStretch()
        return widget

    def _create_encoding_tab(self) -> QWidget:
        """Create the encoding settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Resolution & FPS
        res_group = QGroupBox("Resolution & FPS")
        res_layout = QGridLayout(res_group)

        res_layout.addWidget(QLabel("Resolution:"), 0, 0)
        self.resolution_combo = QComboBox()
        for r in Resolution:
            self.resolution_combo.addItem(r.label, r)
        self.resolution_combo.setCurrentIndex(1)  # 1080p
        res_layout.addWidget(self.resolution_combo, 0, 1)

        res_layout.addWidget(QLabel("FPS:"), 1, 0)
        self.fps_combo = QComboBox()
        for fps in [24, 25, 30, 50, 60]:
            self.fps_combo.addItem(f"{fps} fps", fps)
        self.fps_combo.setCurrentIndex(2)  # 30 fps
        res_layout.addWidget(self.fps_combo, 1, 1)

        layout.addWidget(res_group)

        # Encoder
        enc_group = QGroupBox("Encoder & GPU Acceleration")
        enc_layout = QGridLayout(enc_group)

        enc_layout.addWidget(QLabel("GPU:"), 0, 0)
        self.gpu_combo = QComboBox()
        for gpu in GPUAccel:
            self.gpu_combo.addItem(gpu.name.replace("_", " "), gpu)
        enc_layout.addWidget(self.gpu_combo, 0, 1)

        detect_btn = QPushButton("Auto-Detect GPU")
        detect_btn.setObjectName("secondaryBtn")
        detect_btn.clicked.connect(self._detect_gpu)
        enc_layout.addWidget(detect_btn, 0, 2)

        enc_layout.addWidget(QLabel("Rate Control:"), 1, 0)
        self.rate_combo = QComboBox()
        self.rate_combo.addItem("VBR (Variable Bitrate)", RateControl.VBR)
        self.rate_combo.addItem("CBR (Live Stream Ready)", RateControl.CBR)
        enc_layout.addWidget(self.rate_combo, 1, 1)

        enc_layout.addWidget(QLabel("Video Bitrate:"), 2, 0)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["4M", "6M", "8M", "10M", "12M", "15M", "20M", "30M", "50M"])
        self.bitrate_combo.setCurrentIndex(2)  # 8M
        enc_layout.addWidget(self.bitrate_combo, 2, 1)

        enc_layout.addWidget(QLabel("CRF (Quality):"), 3, 0)
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(18)
        enc_layout.addWidget(self.crf_spin, 3, 1)

        enc_layout.addWidget(QLabel("Preset:"), 4, 0)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow"
        ])
        self.preset_combo.setCurrentIndex(5)  # medium
        enc_layout.addWidget(self.preset_combo, 4, 1)

        enc_layout.addWidget(QLabel("Audio Bitrate:"), 5, 0)
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.audio_bitrate_combo.setCurrentIndex(1)  # 192k
        enc_layout.addWidget(self.audio_bitrate_combo, 5, 1)

        enc_layout.addWidget(QLabel("Keyframe Interval:"), 6, 0)
        self.keyframe_spin = QSpinBox()
        self.keyframe_spin.setRange(1, 10)
        self.keyframe_spin.setValue(2)
        self.keyframe_spin.setSuffix(" sec")
        enc_layout.addWidget(self.keyframe_spin, 6, 1)

        layout.addWidget(enc_group)

        # CBR Live Stream
        cbr_group = QGroupBox("Live Stream Settings (CBR)")
        cbr_layout = QVBoxLayout(cbr_group)
        cbr_info = QLabel(
            "For 24/7 live streaming, use CBR mode with keyframe interval of 2 seconds.\n"
            "YouTube recommends: 1080p = 8M, 720p = 5M, 4K = 30M"
        )
        cbr_info.setWordWrap(True)
        cbr_info.setStyleSheet("color: #8888aa;")
        cbr_layout.addWidget(cbr_info)
        layout.addWidget(cbr_group)

        layout.addStretch()
        return widget

    def _create_batch_tab(self) -> QWidget:
        """Create the batch processing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Batch mode
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QVBoxLayout(batch_group)

        batch_info = QLabel(
            "Process multiple videos at once. Each batch item uses the same settings "
            "but can have different audio orders and effects."
        )
        batch_info.setWordWrap(True)
        batch_info.setStyleSheet("color: #8888aa;")
        batch_layout.addWidget(batch_info)

        self.batch_random_order = QCheckBox("Random Audio Order per Batch")
        batch_layout.addWidget(self.batch_random_order)

        self.batch_random_effects = QCheckBox("Random Effects per Batch (Anti-Template)")
        batch_layout.addWidget(self.batch_random_effects)

        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("Number of Variations:"))
        self.batch_variations = QSpinBox()
        self.batch_variations.setRange(1, 100)
        self.batch_variations.setValue(1)
        var_layout.addWidget(self.batch_variations)
        batch_layout.addLayout(var_layout)

        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output Directory:"))
        self.batch_output_edit = QLineEdit()
        self.batch_output_edit.setPlaceholderText("Select output directory...")
        out_layout.addWidget(self.batch_output_edit)
        batch_out_btn = QPushButton("Browse")
        batch_out_btn.clicked.connect(self._select_batch_output)
        out_layout.addWidget(batch_out_btn)
        batch_layout.addLayout(out_layout)

        batch_btn_layout = QHBoxLayout()
        start_batch_btn = QPushButton("Start Mass Batch")
        start_batch_btn.clicked.connect(self._start_mass_batch)
        batch_btn_layout.addWidget(start_batch_btn)
        batch_layout.addLayout(batch_btn_layout)

        layout.addWidget(batch_group)

        # Master+Copy strategy
        master_group = QGroupBox("Master + Copy Strategy")
        master_layout = QVBoxLayout(master_group)
        master_info = QLabel(
            "Render effects once on a master video, then copy/loop for each batch.\n"
            "This saves time by avoiding re-encoding effects for each variation."
        )
        master_info.setWordWrap(True)
        master_info.setStyleSheet("color: #8888aa;")
        master_layout.addWidget(master_info)

        self.master_copy_check = QCheckBox("Use Master+Copy Strategy")
        master_layout.addWidget(self.master_copy_check)

        layout.addWidget(master_group)
        layout.addStretch()
        return widget

    # ─── Event Handlers ───────────────────────────────────────────────────────

    def _add_audio_files(self):
        ext_str = " ".join(f"*{e}" for e in get_supported_audio_extensions())
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            f"Audio Files ({ext_str});;All Files (*)"
        )
        if files:
            self.audio_files.extend(files)
            for f in files:
                self.audio_list.addItem(Path(f).name)
            self.audio_count_label.setText(f"{len(self.audio_files)} files loaded")

    def _add_audio_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Audio Folder")
        if folder:
            from .batch_processor import scan_audio_files
            files = scan_audio_files(folder)
            if files:
                self.audio_files.extend(files)
                for f in files:
                    self.audio_list.addItem(Path(f).name)
                self.audio_count_label.setText(f"{len(self.audio_files)} files loaded")
            else:
                QMessageBox.information(self, "No Audio", "No audio files found in folder.")

    def _remove_audio_files(self):
        for item in reversed(self.audio_list.selectedItems()):
            idx = self.audio_list.row(item)
            self.audio_list.takeItem(idx)
            if idx < len(self.audio_files):
                self.audio_files.pop(idx)
        self.audio_count_label.setText(f"{len(self.audio_files)} files loaded")

    def _clear_audio_files(self):
        self.audio_list.clear()
        self.audio_files.clear()
        self.audio_count_label.setText("0 files loaded")

    def _shuffle_audio(self):
        if self.audio_files:
            combined = list(zip(self.audio_files, range(len(self.audio_files))))
            random.shuffle(combined)
            self.audio_files = [f for f, _ in combined]
            self.audio_list.clear()
            for f in self.audio_files:
                self.audio_list.addItem(Path(f).name)

    def _select_video(self):
        ext_str = " ".join(f"*{e}" for e in get_supported_video_extensions())
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            f"Video Files ({ext_str});;All Files (*)"
        )
        if file:
            self.video_file = file
            self.video_path_edit.setText(file)

    def _add_slideshow_images(self):
        ext_str = " ".join(f"*{e}" for e in get_supported_image_extensions())
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            f"Image Files ({ext_str});;All Files (*)"
        )
        if files:
            self.slideshow_images.extend(files)
            for f in files:
                self.slide_list.addItem(Path(f).name)

    def _select_intro(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Intro Video", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        if file:
            self.intro_file = file
            self.intro_path_edit.setText(file)

    def _select_outro(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Outro Video", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        if file:
            self.outro_file = file
            self.outro_path_edit.setText(file)

    def _select_output(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Select Output", "",
            "MP4 Video (*.mp4);;All Files (*)"
        )
        if file:
            if not file.endswith(".mp4"):
                file += ".mp4"
            self.output_path_edit.setText(file)

    def _select_batch_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.batch_output_edit.setText(folder)

    def _select_font(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Font", "",
            "Font Files (*.ttf *.otf);;All Files (*)"
        )
        if file:
            self.font_path_edit.setText(file)

    def _pick_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet(
                f"background-color: {color.name()}; "
                f"color: {'black' if color.lightness() > 128 else 'white'};"
            )

    def _detect_gpu(self):
        self.detected_gpu = detect_gpu()
        if self.detected_gpu != GPUAccel.NONE:
            for i in range(self.gpu_combo.count()):
                if self.gpu_combo.itemData(i) == self.detected_gpu:
                    self.gpu_combo.setCurrentIndex(i)
                    break
            QMessageBox.information(
                self, "GPU Detected",
                f"Detected: {self.detected_gpu.name}\nGPU acceleration enabled!"
            )
        else:
            QMessageBox.information(
                self, "No GPU",
                "No compatible GPU detected. Using CPU encoding."
            )

    # ─── Effects Handlers ─────────────────────────────────────────────────────

    def _populate_effects(self):
        self.effect_list.clear()
        for effect in ALL_EFFECTS:
            item = QListWidgetItem(f"[{effect.category.value}] {effect.name}")
            item.setData(Qt.UserRole, effect.name)
            self.effect_list.addItem(item)

    def _filter_effects(self, category_text: str):
        self.effect_list.clear()
        for effect in ALL_EFFECTS:
            if category_text == "All Categories" or effect.category.value == category_text:
                item = QListWidgetItem(f"[{effect.category.value}] {effect.name}")
                item.setData(Qt.UserRole, effect.name)
                self.effect_list.addItem(item)

    def _on_effect_selected(self, current, _previous):
        if current:
            name = current.data(Qt.UserRole)
            from .effects_engine import get_effect_by_name
            effect = get_effect_by_name(name)
            if effect:
                self.effect_desc_label.setText(
                    f"{effect.name}\n{effect.description}\n"
                    f"Category: {effect.category.value}"
                )
                self.effect_enabled_check.setChecked(effect.enabled)

    def _toggle_effect(self, state):
        current = self.effect_list.currentItem()
        if current:
            name = current.data(Qt.UserRole)
            from .effects_engine import get_effect_by_name
            effect = get_effect_by_name(name)
            if effect:
                effect.enabled = bool(state)
                if state:
                    effect.settings.intensity = self.intensity_slider.value() / 100
                    effect.settings.speed = self.speed_slider.value() / 100
                    effect.settings.opacity = self.opacity_slider.value() / 100
                    found = False
                    for i in range(self.active_effects_list.count()):
                        if self.active_effects_list.item(i).data(Qt.UserRole) == name:
                            found = True
                            break
                    if not found:
                        item = QListWidgetItem(effect.name)
                        item.setData(Qt.UserRole, name)
                        self.active_effects_list.addItem(item)
                else:
                    for i in range(self.active_effects_list.count()):
                        if self.active_effects_list.item(i).data(Qt.UserRole) == name:
                            self.active_effects_list.takeItem(i)
                            break

    def _apply_random_effect(self):
        effect = get_random_effect()
        effect.enabled = True
        item = QListWidgetItem(f"{effect.name} (Random)")
        item.setData(Qt.UserRole, effect.name)
        self.active_effects_list.addItem(item)
        QMessageBox.information(
            self, "Random Effect",
            f"Applied: {effect.name}\n{effect.description}"
        )

    def _remove_active_effect(self):
        current = self.active_effects_list.currentItem()
        if current:
            name = current.data(Qt.UserRole)
            from .effects_engine import get_effect_by_name
            effect = get_effect_by_name(name)
            if effect:
                effect.enabled = False
            self.active_effects_list.takeItem(self.active_effects_list.row(current))

    def _clear_active_effects(self):
        for effect in ALL_EFFECTS:
            effect.enabled = False
        self.active_effects_list.clear()

    # ─── Overlay Handlers ─────────────────────────────────────────────────────

    def _add_overlay(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Overlay File", "",
            "Media Files (*.png *.gif *.mp4 *.avi *.mov *.webm);;All Files (*)"
        )
        if file:
            overlay = MultiOverlayItem(
                file_path=file,
                overlay_type=OverlayType(self.overlay_type_combo.currentText()),
                opacity=self.overlay_opacity.value(),
                similarity=self.overlay_similarity.value(),
                blend=self.overlay_blend.value(),
            )
            self.overlay_items.append(overlay)
            self.overlay_list.addItem(f"{overlay.overlay_type.value}: {Path(file).name}")

    def _remove_overlay(self):
        current = self.overlay_list.currentRow()
        if current >= 0:
            self.overlay_list.takeItem(current)
            if current < len(self.overlay_items):
                self.overlay_items.pop(current)

    # ─── Timestamp Handlers ───────────────────────────────────────────────────

    def _generate_timestamps(self):
        if not self.audio_files:
            QMessageBox.warning(self, "No Audio", "Please add audio files first.")
            return

        self.status_label.setText("Generating timestamps...")
        self.timestamps = []
        current_time = 0.0

        for af in self.audio_files:
            name = Path(af).stem
            self.timestamps.append((current_time, name))
            duration = get_media_duration(af)
            current_time += duration

        ts_text = generate_youtube_timestamps(self.timestamps)
        self.timestamps_text.setPlainText(ts_text)
        self.status_label.setText(f"Generated {len(self.timestamps)} timestamps")

    def _copy_timestamps(self):
        text = self.timestamps_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("Timestamps copied to clipboard!", 3000)

    def _save_timestamps(self):
        if not self.timestamps:
            QMessageBox.warning(self, "No Timestamps", "Generate timestamps first.")
            return
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Timestamps", "timestamps.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if file:
            save_timestamps_to_file(self.timestamps, file)
            self.statusBar().showMessage(f"Timestamps saved to {file}", 3000)

    def _generate_playlist_png(self):
        if not self.timestamps:
            self._generate_timestamps()
        if not self.timestamps:
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "Save Playlist PNG", "playlist.png",
            "PNG Image (*.png);;All Files (*)"
        )
        if file:
            settings = PlaylistPNGSettings(
                width=self.png_width.value(),
                height=self.png_height.value(),
                font_size=self.png_font_size.value(),
                title_text=self.playlist_title.text(),
                columns=self.png_columns.value(),
                show_numbers=self.png_show_numbers.isChecked(),
                show_timestamps=self.png_show_timestamps.isChecked(),
            )
            generate_playlist_png(self.timestamps, file, settings)
            self.statusBar().showMessage(f"Playlist PNG saved to {file}", 3000)

    def _preview_playlist_png(self):
        if not self.timestamps:
            self._generate_timestamps()
        if not self.timestamps:
            return

        temp_path = os.path.join(tempfile.gettempdir(), "playlist_preview.png")
        settings = PlaylistPNGSettings(
            width=self.png_width.value(),
            height=self.png_height.value(),
            font_size=self.png_font_size.value(),
            title_text=self.playlist_title.text(),
            columns=self.png_columns.value(),
            show_numbers=self.png_show_numbers.isChecked(),
            show_timestamps=self.png_show_timestamps.isChecked(),
        )
        generate_playlist_png(self.timestamps, temp_path, settings)

        try:
            import subprocess
            import sys
            if sys.platform == "win32":
                os.startfile(temp_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", temp_path])
            else:
                subprocess.run(["xdg-open", temp_path])
        except Exception:
            QMessageBox.information(
                self, "Preview", f"PNG saved at:\n{temp_path}"
            )

    def _generate_description(self):
        if not self.timestamps:
            self._generate_timestamps()
        if not self.timestamps:
            return

        desc = generate_playlist_description(self.timestamps)
        self.desc_text.setPlainText(desc)

    def _copy_description(self):
        text = self.desc_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("Description copied to clipboard!", 3000)

    # ─── Render Logic ─────────────────────────────────────────────────────────

    def _get_encoding_settings(self) -> EncodingSettings:
        return EncodingSettings(
            resolution=self.resolution_combo.currentData(),
            fps=self.fps_combo.currentData(),
            gpu_accel=self.gpu_combo.currentData(),
            rate_control=self.rate_combo.currentData(),
            video_bitrate=self.bitrate_combo.currentText(),
            audio_bitrate=self.audio_bitrate_combo.currentText(),
            crf=self.crf_spin.value(),
            preset=self.preset_combo.currentText(),
            keyframe_interval=self.keyframe_spin.value(),
        )

    def _get_title_overlay_settings(self) -> SongTitleOverlaySettings:
        return SongTitleOverlaySettings(
            enabled=self.title_overlay_check.isChecked(),
            position=self.title_position_combo.currentData(),
            font_file=self.font_path_edit.text(),
            font_size=self.title_font_size.value(),
            font_color=self.title_color_btn.text() if self.title_color_btn.text() != "White" else "white",
            display_duration=self.title_duration.value(),
            fade_in=self.title_fade_in.value(),
            fade_out=self.title_fade_out.value(),
        )

    def _validate_inputs(self) -> Optional[str]:
        if not self.audio_files:
            return "Please add audio files."
        if not self.video_file and not (self.slideshow_check.isChecked() and self.slideshow_images):
            return "Please select a background video or enable slideshow mode with images."
        if not self.output_path_edit.text():
            return "Please select an output file path."
        return None

    def _start_render(self):
        error = self._validate_inputs()
        if error:
            QMessageBox.warning(self, "Missing Input", error)
            return

        self.render_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        settings = self._get_encoding_settings()
        output_path = self.output_path_edit.text()

        def render_task(progress_callback=None, status_callback=None):
            try:
                if status_callback:
                    status_callback("Concatenating audio files...")

                crossfade = self.crossfade_duration.value() if self.crossfade_check.isChecked() else 0.0
                
                temp_audio = tempfile.mktemp(suffix=".m4a")
                timestamps = concat_audio_files(
                    self.audio_files, temp_audio,
                    crossfade_duration=crossfade,
                    progress_callback=progress_callback,
                )
                self.timestamps = timestamps

                total_duration = get_media_duration(temp_audio)

                if status_callback:
                    status_callback("Processing video...")

                temp_video = tempfile.mktemp(suffix=".mp4")

                if self.slideshow_check.isChecked() and self.slideshow_images:
                    dur_per_img = total_duration / len(self.slideshow_images)
                    create_slideshow(
                        self.slideshow_images, dur_per_img, temp_video,
                        settings, self.slide_transition.currentText(),
                    )
                else:
                    loop_video_to_duration(
                        self.video_file, total_duration, temp_video,
                        settings, progress_callback,
                    )

                if progress_callback:
                    progress_callback(60)

                # Effects
                active_effects = [e for e in ALL_EFFECTS if e.enabled]
                if active_effects:
                    if status_callback:
                        status_callback("Applying visual effects...")
                    effect_filter = build_effect_filter_chain(active_effects)
                    if effect_filter:
                        temp_fx = tempfile.mktemp(suffix=".mp4")
                        ffmpeg = find_ffmpeg()
                        cmd = [ffmpeg, "-y", "-i", temp_video, "-vf", effect_filter]
                        cmd.extend(build_encoding_args(settings))
                        cmd.extend(["-an", temp_fx])
                        subprocess.run(cmd, capture_output=True, check=True)
                        os.unlink(temp_video)
                        temp_video = temp_fx

                if progress_callback:
                    progress_callback(75)

                if status_callback:
                    status_callback("Merging video and audio...")

                temp_merged = tempfile.mktemp(suffix=".mp4")
                merge_video_audio(temp_video, temp_audio, temp_merged, settings)

                if progress_callback:
                    progress_callback(85)

                # TITLE OVERLAY DINONAKTIFKAN
                current_video = temp_merged
                print("⏭️ Song Title Overlay dinonaktifkan sementara")

                if progress_callback:
                    progress_callback(90)

                # Intro & Outro
                if self.intro_file or self.outro_file:
                    if status_callback:
                        status_callback("Adding intro/outro...")
                    temp_io = tempfile.mktemp(suffix=".mp4")
                    add_intro_outro(
                        current_video,
                        self.intro_file if self.intro_file else None,
                        self.outro_file if self.outro_file else None,
                        temp_io,
                        settings
                    )
                    os.unlink(current_video)
                    current_video = temp_io

                if progress_callback:
                    progress_callback(95)

                shutil.move(current_video, output_path)

                # Cleanup
                for f in [temp_audio, temp_video]:
                    if os.path.exists(f):
                        try:
                            os.unlink(f)
                        except:
                            pass

                ts_file = output_path.rsplit(".", 1)[0] + "_timestamps.txt"
                save_timestamps_to_file(timestamps, ts_file)

                if progress_callback:
                    progress_callback(100)
                if status_callback:
                    status_callback("Render complete!")

            except Exception as e:
                if status_callback:
                    status_callback(f"Error: {str(e)}")
                raise

        self.render_thread = RenderThread(render_task)
        self.render_thread.progress.connect(self.progress_bar.setValue)
        self.render_thread.status.connect(self.status_label.setText)
        self.render_thread.finished_signal.connect(self._on_render_finished)
        self.render_thread.start()
        
    def _cancel_render(self):
        if self.render_thread and self.render_thread.isRunning():
            self.render_thread.terminate()
            self.render_thread.wait()
            self.status_label.setText("Render cancelled")
            self.render_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    def _on_render_finished(self, success: bool, message: str):
        self.render_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Render failed:\n{message}")
        self.status_label.setText(message)

    def _start_mass_batch(self):
        error = self._validate_inputs()
        if error and "output" not in error.lower():
            QMessageBox.warning(self, "Missing Input", error)
            return

        output_dir = self.batch_output_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "No Output Dir", "Select output directory.")
            return

        settings = BatchSettings(
            output_dir=output_dir,
            encoding=self._get_encoding_settings(),
            random_effects=self.batch_random_effects.isChecked(),
            random_audio_order=self.batch_random_order.isChecked(),
            crossfade_duration=(
                self.crossfade_duration.value()
                if self.crossfade_check.isChecked()
                else 0.0
            ),
            num_variations=self.batch_variations.value(),
        )

        self.render_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        def batch_task(progress_callback=None, status_callback=None):
            processor = BatchProcessor()

            def on_progress(bp):
                if progress_callback:
                    total_pct = int(bp.completed_items / bp.total_items * 100)
                    progress_callback(total_pct)
                if status_callback:
                    status_callback(
                        f"Processing {bp.current_item} "
                        f"({bp.completed_items}/{bp.total_items})"
                    )

            processor.process_mass_batch(
                self.audio_files, self.video_file,
                settings, on_progress,
            )

        self.render_thread = RenderThread(batch_task)
        self.render_thread.progress.connect(self.progress_bar.setValue)
        self.render_thread.status.connect(self.status_label.setText)
        self.render_thread.finished_signal.connect(self._on_render_finished)
        self.render_thread.start()

    # ─── Project Management ───────────────────────────────────────────────────

    def _new_project(self):
        self._clear_audio_files()
        self.video_file = ""
        self.video_path_edit.clear()
        self.intro_file = ""
        self.intro_path_edit.clear()
        self.outro_file = ""
        self.outro_path_edit.clear()
        self.output_path_edit.clear()
        self.slideshow_images.clear()
        self.slide_list.clear()
        self.overlay_items.clear()
        self.overlay_list.clear()
        self.timestamps.clear()
        self.timestamps_text.clear()
        self.desc_text.clear()
        self._clear_active_effects()
        self.progress_bar.setValue(0)
        self.status_label.setText("New project created")

    def _save_project(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "project.mvcproj",
            "MVC Project (*.mvcproj);;All Files (*)"
        )
        if file:
            project = {
                "audio_files": self.audio_files,
                "video_file": self.video_file,
                "intro_file": self.intro_file,
                "outro_file": self.outro_file,
                "output_path": self.output_path_edit.text(),
                "slideshow_images": self.slideshow_images,
                "slideshow_enabled": self.slideshow_check.isChecked(),
                "resolution": self.resolution_combo.currentIndex(),
                "fps": self.fps_combo.currentIndex(),
                "gpu": self.gpu_combo.currentIndex(),
                "crossfade_enabled": self.crossfade_check.isChecked(),
                "crossfade_duration": self.crossfade_duration.value(),
            }
            with open(file, "w") as f:
                json.dump(project, f, indent=2)
            self.statusBar().showMessage(f"Project saved: {file}", 3000)

    def _open_project(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "MVC Project (*.mvcproj);;All Files (*)"
        )
        if file:
            with open(file) as f:
                project = json.load(f)

            self._new_project()
            self.audio_files = project.get("audio_files", [])
            for af in self.audio_files:
                self.audio_list.addItem(Path(af).name)
            self.audio_count_label.setText(f"{len(self.audio_files)} files loaded")

            self.video_file = project.get("video_file", "")
            self.video_path_edit.setText(self.video_file)
            self.intro_file = project.get("intro_file", "")
            self.intro_path_edit.setText(self.intro_file)
            self.outro_file = project.get("outro_file", "")
            self.outro_path_edit.setText(self.outro_file)
            self.output_path_edit.setText(project.get("output_path", ""))

            self.slideshow_images = project.get("slideshow_images", [])
            for img in self.slideshow_images:
                self.slide_list.addItem(Path(img).name)
            self.slideshow_check.setChecked(project.get("slideshow_enabled", False))

            idx = project.get("resolution", 1)
            if idx < self.resolution_combo.count():
                self.resolution_combo.setCurrentIndex(idx)
            idx = project.get("fps", 2)
            if idx < self.fps_combo.count():
                self.fps_combo.setCurrentIndex(idx)

            self.crossfade_check.setChecked(project.get("crossfade_enabled", False))
            self.crossfade_duration.setValue(project.get("crossfade_duration", 2.0))

            self.statusBar().showMessage(f"Project loaded: {file}", 3000)

    def _show_about(self):
        QMessageBox.about(
            self, "About Music Video Compiler",
            "Music Video Compiler v1.0\n\n"
            "Professional Music Compilation Video Creator\n\n"
            "Features:\n"
            "• 30+ Visual Effects\n"
            "• GPU Acceleration (NVENC, AMF, QSV)\n"
            "• YouTube Timestamps & Playlist PNG\n"
            "• Song Title Overlays\n"
            "• Batch Processing\n"
            "• Crossfade Audio\n"
            "• Intro/Outro Support\n"
            "• Multi-Overlay\n"
            "• Slideshow Mode\n"
            "• Live Stream Ready (CBR)\n"
        )


def run_app():
    """Launch the application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setApplicationName("Music Video Compiler")
    app.setOrganizationName("MVC")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
