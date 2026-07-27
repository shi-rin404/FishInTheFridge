import os
import subprocess

from PySide6.QtCore import QObject, QTimer

from core.options_memory import launch_preset, load_mods_on_launch

SENTINEL_ASSET = "chr/player/dm65_survivor_w/dm65_survivor_w_yiyaoshi/dm65_survivor_w_yiyaoshi_lv1.gim"


class AutoLoadModsController(QObject):
    def __init__(self, main_page):
        super().__init__(main_page)
        self._main_page = main_page
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self._remaining = 0
        self._countdown_text = None
        self._countdown_error = False
        self._countdown_done = None

    def start_if_enabled(self):
        if not load_mods_on_launch():
            return
        preset_name = launch_preset()
        if not preset_name:
            return

        if self._is_game_running():
            self._apply_launch_preset()
            return

        if self._launch_game():
            self._start_countdown(
                15,
                lambda seconds: f"Waiting for the game open ({seconds})",
                error=False,
                done=self._apply_launch_preset,
            )

    def _is_game_running(self) -> bool:
        try:
            from modding.modder import _pid_by_name
            _pid_by_name("dwrg.exe")
            return True
        except RuntimeError:
            return False

    def _launch_game(self) -> bool:
        from database.user.user_variables import user_variables

        game_executable = user_variables.game_executable
        if not game_executable or not os.path.exists(game_executable):
            self._main_page.bottom_row._set_preset_feedback(
                "Game executable was not found", error=True
            )
            return False

        subprocess.Popen([game_executable], cwd=user_variables.game_dir)
        return True

    def _apply_launch_preset(self):
        from modding.apply_mod import AssetsNotLoadedError
        from modding.preset_manager import apply_preset

        preset_name = launch_preset()
        if not preset_name:
            return

        try:
            apply_preset(
                preset_name,
                force=True,
                sentinel_targets=[SENTINEL_ASSET],
            )
            self._main_page.bottom_row._set_preset_feedback(
                "Preset applied successfully", success=True
            )
        except AssetsNotLoadedError:
            self._start_countdown(
                10,
                lambda seconds: f"Assets has not loaded yet, trying again in {seconds} seconds..",
                error=True,
                done=self._apply_launch_preset,
            )
        except RuntimeError:
            if self._launch_game():
                self._start_countdown(
                    15,
                    lambda seconds: f"Waiting for the game open ({seconds})",
                    error=False,
                    done=self._apply_launch_preset,
                )
        except Exception:
            self._main_page.bottom_row._set_preset_feedback(
                "An error occured upon modding", error=True
            )
            raise

    def _start_countdown(self, seconds: int, text_factory, *, error: bool, done):
        self._countdown_timer.stop()
        self._remaining = seconds
        self._countdown_text = text_factory
        self._countdown_error = error
        self._countdown_done = done
        self._show_countdown_feedback()
        self._countdown_timer.start()

    def _on_countdown_tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._countdown_timer.stop()
            done = self._countdown_done
            self._countdown_done = None
            if done is not None:
                done()
            return
        self._show_countdown_feedback()

    def _show_countdown_feedback(self):
        self._main_page.bottom_row._set_preset_feedback(
            self._countdown_text(self._remaining),
            error=self._countdown_error,
        )
