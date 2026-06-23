from __future__ import annotations

import os
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Slot
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget

from ..core.updater import (
    ReleaseInfo,
    UpdateCheckResult,
    create_update_script,
    check_for_update,
    current_executable_path,
    default_update_download_path,
    download_update,
    launch_update_script,
    preflight_update_target,
    should_check_for_updates,
)
from .workers import BackgroundTask, WorkerSignals


class DownloadUpdateTask(QRunnable):
    def __init__(self, release_info: ReleaseInfo, destination: Path) -> None:
        super().__init__()
        self.release_info = release_info
        self.destination = destination
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            downloaded_path = download_update(
                self.release_info,
                self.destination,
                progress_callback=self.signals.progress.emit,
            )
        except Exception:
            self.signals.failed.emit(traceback.format_exc())
            return

        self.signals.finished.emit(downloaded_path)


class UpdateController(QObject):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.parent_window = parent
        self._check_task: BackgroundTask | None = None
        self._download_task: DownloadUpdateTask | None = None
        self._progress_dialog: QProgressDialog | None = None
        self._pending_release: ReleaseInfo | None = None

    def start(self) -> None:
        if self._check_task is not None or not should_check_for_updates():
            return

        task = BackgroundTask(check_for_update)
        task.signals.finished.connect(self._handle_check_finished)
        task.signals.failed.connect(lambda error: self._show_error("Update check failed.", error))
        self._check_task = task
        QThreadPool.globalInstance().start(task)

    def _handle_check_finished(self, result: object) -> None:
        self._check_task = None
        if not isinstance(result, UpdateCheckResult):
            self._show_error("Update check failed.", f"Unexpected update result: {result!r}")
            return
        if result.latest_release is None:
            return

        self._pending_release = result.latest_release
        self._prompt_for_update(result)

    def _prompt_for_update(self, result: UpdateCheckResult) -> None:
        release_info = result.latest_release
        if release_info is None:
            return

        message_box = QMessageBox(self.parent_window)
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle("Update Available")
        message_box.setText("A new version of RGB Splitter is available.")
        message_box.setInformativeText(
            "\n".join(
                [
                    f"Current version: {result.current_version}",
                    f"New version: {release_info.version}",
                    f"Asset: {release_info.asset_name}",
                ]
            )
        )
        install_button = message_box.addButton("Install", QMessageBox.ButtonRole.AcceptRole)
        message_box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        message_box.exec()

        if message_box.clickedButton() is install_button:
            self._start_download(release_info)

    def _start_download(self, release_info: ReleaseInfo) -> None:
        target_exe = current_executable_path()
        if target_exe is None:
            return

        try:
            preflight_update_target(target_exe)
        except Exception:
            self._show_error("Update cannot be installed.", traceback.format_exc())
            return

        destination = default_update_download_path(release_info)
        self._progress_dialog = QProgressDialog("Downloading update...", "", 0, release_info.size, self.parent_window)
        self._progress_dialog.setWindowTitle("Updating RGB Splitter")
        self._progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)
        self._progress_dialog.show()

        task = DownloadUpdateTask(release_info, destination)
        task.signals.progress.connect(self._handle_download_progress)
        task.signals.finished.connect(lambda path: self._handle_download_finished(path, target_exe))
        task.signals.failed.connect(self._handle_download_failed)
        self._download_task = task
        QThreadPool.globalInstance().start(task)

    def _handle_download_progress(self, bytes_received: int, total_bytes: int) -> None:
        if self._progress_dialog is None:
            return
        self._progress_dialog.setMaximum(max(1, total_bytes))
        self._progress_dialog.setValue(min(bytes_received, max(1, total_bytes)))

    def _handle_download_finished(self, downloaded_path: object, target_exe: Path) -> None:
        self._download_task = None
        self._close_progress_dialog()
        if not isinstance(downloaded_path, Path):
            self._show_error("Update download failed.", f"Unexpected downloaded path: {downloaded_path!r}")
            return

        try:
            script_path = create_update_script(downloaded_path, target_exe, os.getpid())
            launch_update_script(script_path)
        except Exception:
            self._show_error("Update installation failed.", traceback.format_exc())
            return

        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _handle_download_failed(self, error: str) -> None:
        self._download_task = None
        self._close_progress_dialog()
        self._show_error("Update download failed.", error)

    def _close_progress_dialog(self) -> None:
        if self._progress_dialog is None:
            return
        self._progress_dialog.close()
        self._progress_dialog.deleteLater()
        self._progress_dialog = None

    def _show_error(self, title: str, details: str) -> None:
        self._check_task = None
        message_box = QMessageBox(self.parent_window)
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("RGB Splitter Update")
        message_box.setText(title)
        message_box.setDetailedText(details)
        message_box.exec()
