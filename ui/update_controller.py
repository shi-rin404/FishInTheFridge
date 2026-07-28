from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QMessageBox


class UpdateWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, action: str, asset=None):
        super().__init__()
        self.action = action
        self.asset = asset

    def run(self):
        try:
            if self.action == "check":
                from core.auto_updater import check_for_updates

                self.finished.emit(check_for_updates())
            elif self.action == "install":
                from core.auto_updater import install_update

                install_update(self.asset)
                self.finished.emit(self.asset)
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateController(QObject):
    state_changed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        parent=None,
        *,
        show_no_updates: bool = True,
        show_errors: bool = True,
    ):
        super().__init__(parent)
        self.show_no_updates = show_no_updates
        self.show_errors = show_errors
        self._threads = []

    def check_for_updates(self):
        self.state_changed.emit("Checking...")
        self._start_worker("check")

    def _start_worker(self, action: str, asset=None):
        thread = QThread(self)
        worker = UpdateWorker(action, asset)
        worker.moveToThread(thread)
        self._threads.append(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_worker_finished)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._forget_thread(thread))
        thread.start()

    def _forget_thread(self, thread: QThread):
        if thread in self._threads:
            self._threads.remove(thread)

    def _on_worker_finished(self, result):
        from core.auto_updater import ReleaseAsset

        self.state_changed.emit("Check for Updates")
        if isinstance(result, ReleaseAsset):
            QMessageBox.information(
                self.parent(),
                "Update Completed",
                _completed_update_message(result),
            )
            QApplication.quit()
            self.finished.emit()
            return

        if not result.update_available:
            if self.show_no_updates:
                QMessageBox.information(
                    self.parent(),
                    "No Updates Found",
                    f"You are already on the latest version ({result.current_version}).",
                )
            self.finished.emit()
            return

        reply = QMessageBox.question(
            self.parent(),
            "Update Available",
            (
                f"Version {result.latest_version} is available.\n"
                f"Current version: {result.current_version}\n\n"
                "Install it now?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.state_changed.emit("Installing...")
            self._start_worker("install", result.asset)
            return
        self.finished.emit()

    def _on_worker_failed(self, message: str):
        self.state_changed.emit("Check for Updates")
        if self.show_errors:
            QMessageBox.critical(self.parent(), "Update Failed", message)
        self.finished.emit()


def _completed_update_message(asset) -> str:
    notes = asset.release_notes.strip()
    if not notes:
        return asset.release_title
    return f"{asset.release_title}\n\n{notes}"
