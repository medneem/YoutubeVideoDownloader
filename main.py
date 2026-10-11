"""Russian-language desktop UI for YoutubeVideoDownloader."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QThread, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from downloader import DownloadWorker
from version import APP_VERSION
from settings import (
    default_settings,
    load_settings,
    save_settings,
    settings_file,
    validate_http_proxy,
)

APP_NAME = "YoutubeVideoDownloader"

def application_icon() -> QIcon:
    """Generate a sharp Qt window/taskbar icon from the bundled SVG."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    svg = QSvgRenderer(str(base / "assets" / "app.svg"))
    if not svg.isValid():
        return QIcon()
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    svg.render(painter)
    painter.end()
    return QIcon(pixmap)

def open_download_folder(folder: str) -> bool:
    """Open the selected destination using Windows File Explorer."""
    path = Path(folder).expanduser()
    if not path.is_dir():
        return False
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))



class ProxySettingsDialog(QDialog):
    def __init__(self, settings: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки HTTP-прокси")
        self.setMinimumWidth(440)
        self.proxy_enabled = QCheckBox("Использовать HTTP-прокси")
        self.proxy_enabled.setChecked(settings["proxy_enabled"])
        self.proxy_url = QLineEdit(settings["proxy_url"])
        self.proxy_url.setPlaceholderText("http://127.0.0.1:8118")
        self.proxy_enabled.toggled.connect(self.proxy_url.setEnabled)
        self.proxy_url.setEnabled(self.proxy_enabled.isChecked())

        form = QFormLayout()
        form.addRow(self.proxy_enabled)
        form.addRow("Адрес прокси:", self.proxy_url)

        hint = QLabel(
            "Поддерживаются HTTP и HTTPS-прокси. Если адрес содержит "
            "логин и пароль, они сохраняются открытым текстом в config.json."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    def accept(self) -> None:
        address = self.proxy_url.text().strip()
        if self.proxy_enabled.isChecked():
            try:
                address = validate_http_proxy(address)
            except ValueError as exc:
                QMessageBox.warning(self, "Неверный прокси", str(exc))
                return
        self.result_proxy_enabled = self.proxy_enabled.isChecked()
        self.result_proxy_url = address
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(680, 375)
        self.setMinimumWidth(570)
        try:
            self.settings = load_settings()
        except (ValueError, OSError) as exc:
            self.settings = default_settings()
            QMessageBox.warning(
                self,
                "Ошибка config.json",
                f"{exc}\n\nЗагружены настройки по умолчанию. "
                "Проверьте config.json рядом с программой.",
            )

        self.thread: QThread | None = None
        self.worker: DownloadWorker | None = None
        self.active_download_directory: str | None = None

        root = QWidget()
        outer = QVBoxLayout(root)
        self.setCentralWidget(root)

        top = QHBoxLayout()
        title = QLabel("Скачивание видео и аудио с YouTube")
        title.setStyleSheet("font-weight: 600; font-size: 17px;")
        self.settings_button = QPushButton("⚙ Настройки")
        self.settings_button.clicked.connect(self.open_settings)
        top.addWidget(title, 1)
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setToolTip("Версия соответствует номеру GitHub Actions pipeline")
        top.addWidget(version_label)
        top.addWidget(self.settings_button)
        outer.addLayout(top)

        self.url = QLineEdit()
        self.url.setPlaceholderText("https://www.youtube.com/watch?v=...")
        outer.addWidget(QLabel("Ссылка на видео:"))
        outer.addWidget(self.url)

        group = QGroupBox("Параметры загрузки")
        form = QFormLayout(group)
        self.mode = QComboBox()
        self.mode.addItem("Видео MP4", "video")
        self.mode.addItem("Аудио MP3 (192 кбит/с)", "audio")
        self.quality = QComboBox()
        for label, code in (
            ("Максимальное", "best"),
            ("4K / 2160p", "2160"),
            ("2K / 1440p", "1440"),
            ("Full HD / 1080p", "1080"),
            ("HD / 720p", "720"),
            ("480p", "480"),
            ("360p", "360"),
        ):
            self.quality.addItem(label, code)
        mode_index = self.mode.findData(self.settings["mode"])
        quality_index = self.quality.findData(self.settings["quality"])
        self.mode.setCurrentIndex(max(0, mode_index))
        self.quality.setCurrentIndex(max(0, quality_index))
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        self.quality.currentIndexChanged.connect(self._save_preferences)

        self.folder = QLineEdit(self.settings["download_dir"])
        self.folder.setReadOnly(True)
        browse = QPushButton("Обзор…")
        browse.clicked.connect(self.choose_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(browse)
        form.addRow("Формат:", self.mode)
        form.addRow("Качество:", self.quality)
        form.addRow("Сохранить в:", folder_row)
        outer.addWidget(group)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.status = QLabel("Готово к загрузке.")
        self.status.setWordWrap(True)
        outer.addWidget(self.progress)
        outer.addWidget(self.status)

        controls = QHBoxLayout()
        self.download_button = QPushButton("Скачать")
        self.download_button.setDefault(True)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        controls.addStretch()
        controls.addWidget(self.cancel_button)
        controls.addWidget(self.download_button)
        outer.addLayout(controls)

        # Do not overwrite an unreadable config.json automatically at startup.
        self.quality.setEnabled(self.mode.currentData() == "video")
        self.statusBar().showMessage(f"Настройки: {settings_file()}")

    def _on_mode_changed(self) -> None:
        self.quality.setEnabled(self.mode.currentData() == "video")
        self._save_preferences()

    def _save_preferences(self) -> bool:
        latest = self.settings.copy()
        latest["mode"] = self.mode.currentData()
        latest["quality"] = self.quality.currentData()
        latest["download_dir"] = self.folder.text()
        try:
            save_settings(latest)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Не удалось сохранить настройки", str(exc))
            return False
        self.settings = latest
        return True

    def choose_folder(self) -> None:
        target = QFileDialog.getExistingDirectory(
            self, "Выберите папку для загрузок", self.folder.text()
        )
        if target:
            self.folder.setText(target)
            self._save_preferences()

    def open_settings(self) -> None:
        dialog = ProxySettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = self.settings.copy()
            new_settings["proxy_enabled"] = dialog.result_proxy_enabled
            new_settings["proxy_url"] = dialog.result_proxy_url
            try:
                save_settings(new_settings)
            except (ValueError, OSError) as exc:
                QMessageBox.critical(self, "Не удалось сохранить настройки", str(exc))
                return
            self.settings = new_settings
            self.status.setText(
                "Прокси включён." if self.settings["proxy_enabled"]
                else "Прямое подключение (без прокси)."
            )

    def start_download(self) -> None:
        if self.thread is not None:
            return
        value = self.url.text().strip()
        try:
            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Укажите корректную ссылку http(s) на видео.")
        except ValueError as exc:
            QMessageBox.warning(self, "Неверная ссылка", str(exc))
            return
        if not self._save_preferences():
            return
        self.active_download_directory = self.settings["download_dir"]

        self.progress.setValue(0)
        self.status.setText("Подключение к YouTube…")
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.settings_button.setEnabled(False)
        self.mode.setEnabled(False)
        self.quality.setEnabled(False)

        self.thread = QThread(self)
        self.worker = DownloadWorker(value, self.settings)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread_stopped)
        self.thread.start()

    def update_progress(self, value: int, description: str) -> None:
        self.progress.setValue(value)
        self.status.setText(description)

    def download_finished(self, success: bool, description: str) -> None:
        self.status.setText(description)
        if success:
            self.progress.setValue(100)
            if self.active_download_directory and not open_download_folder(self.active_download_directory):
                self.status.setText(description + " Не удалось открыть папку автоматически.")

    def thread_stopped(self) -> None:
        self.thread = None
        self.worker = None
        self.active_download_directory = None
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.settings_button.setEnabled(True)
        self.mode.setEnabled(True)
        self.quality.setEnabled(self.mode.currentData() == "video")

    def cancel_download(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.status.setText("Отмена загрузки…")
            self.cancel_button.setEnabled(False)

    def closeEvent(self, event) -> None:
        if self.thread is not None:
            self.cancel_download()
            QMessageBox.information(
                self,
                "Загрузка выполняется",
                "Загрузка отменяется. Закройте окно после её завершения.",
            )
            event.ignore()
            return
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(application_icon())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
