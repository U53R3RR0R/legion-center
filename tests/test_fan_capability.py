import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from py_modules import fan_capability


class FanCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.proc_path = Path(self.temp_directory.name) / "acpi_call"

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_existing_proc_file_is_supported_without_modprobe(self):
        self.proc_path.touch()
        result = fan_capability.ensure_acpi_call_available(
            self.proc_path,
            runner=lambda *_args, **_kwargs: self.fail("runner should not be called"),
        )
        self.assertTrue(result)

    def test_successful_modprobe_requires_proc_file(self):
        def runner(*_args, **_kwargs):
            self.proc_path.touch()
            return SimpleNamespace(returncode=0)

        self.assertTrue(
            fan_capability.ensure_acpi_call_available(self.proc_path, runner=runner)
        )

    def test_zero_exit_without_proc_file_is_not_supported(self):
        result = fan_capability.ensure_acpi_call_available(
            self.proc_path,
            runner=lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
        )
        self.assertFalse(result)

    def test_failed_or_missing_modprobe_is_not_supported(self):
        failed = fan_capability.ensure_acpi_call_available(
            self.proc_path,
            runner=lambda *_args, **_kwargs: SimpleNamespace(returncode=1),
        )

        def missing(*_args, **_kwargs):
            raise FileNotFoundError("modprobe")

        self.assertFalse(failed)
        self.assertFalse(
            fan_capability.ensure_acpi_call_available(self.proc_path, runner=missing)
        )

    def test_dkms_status_requires_exact_kernel_and_installed_state(self):
        calls = []

        def runner(command, **_kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout="acpi_call/1.2.2: installed")

        self.assertTrue(
            fan_capability.dkms_installed_for_running_kernel(
                runner=runner, kernel_release="6.18-test"
            )
        )
        self.assertEqual(
            calls[0],
            ["dkms", "status", "-m", "acpi_call", "-k", "6.18-test"],
        )

    def test_managed_module_is_loaded_from_persistent_settings(self):
        settings_dir = Path(self.temp_directory.name) / "settings"
        module_path = settings_dir / "acpi-call" / "6.18-test" / "acpi_call.ko"
        module_path.parent.mkdir(parents=True)
        module_path.touch()
        calls = []

        def runner(command, **_kwargs):
            calls.append(command)
            if command[-2] == "insmod":
                self.proc_path.touch()
            return SimpleNamespace(returncode=1 if command[0] == "modprobe" else 0)

        with patch.dict("os.environ", {"DECKY_PLUGIN_SETTINGS_DIR": str(settings_dir)}), \
                patch("py_modules.fan_capability.platform.release", return_value="6.18-test"):
            result = fan_capability.ensure_acpi_call_available(
                self.proc_path,
                runner=runner,
            )

        self.assertTrue(result)
        self.assertEqual(calls[-1], ["sudo", "-n", "insmod", str(module_path)])

    def test_managed_module_counts_as_installed_without_dkms(self):
        settings_dir = Path(self.temp_directory.name) / "settings"
        module_path = settings_dir / "acpi-call" / "6.18-test" / "acpi_call.ko"
        module_path.parent.mkdir(parents=True)
        module_path.touch()

        with patch.dict("os.environ", {"DECKY_PLUGIN_SETTINGS_DIR": str(settings_dir)}):
            self.assertTrue(
                fan_capability.dkms_installed_for_running_kernel(
                    kernel_release="6.18-test",
                    runner=lambda *_args, **_kwargs: self.fail("DKMS should not be queried"),
                )
            )


if __name__ == "__main__":
    unittest.main()
