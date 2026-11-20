import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class PackageDownloader:
    def __init__(self, *_args, **_kwargs):
        pass


stub_versions = types.SimpleNamespace(
    get_kernel_headers_filename=lambda _version: "headers",
    get_kernel_modules_filename=lambda _version: "modules",
    get_os_version=lambda: {},
)
stub_downloader = types.SimpleNamespace(PackageDownloader=PackageDownloader)
sys.modules.setdefault("common.lib.dkms_supported_versions", stub_versions)
sys.modules.setdefault("common.lib.package_downloader", stub_downloader)

from py_modules.acpi_enabler.acpi_enabler import AcpiEnabler


class RecordingEnabler(AcpiEnabler):
    def __init__(self, installed=False, fail_install=False):
        self.verbose = False
        self.installed = installed
        self.fail_install = fail_install
        self.calls = []
        self._build_work = None
        self._build_merged = None

    def _log(self, _message):
        pass

    def prep_steamos(self):
        self.calls.append("prep")

    def finalize_steamos(self):
        self.calls.append("finalize")

    def distro_family(self):
        return "steamos"

    def _acpi_call_installed(self, _kernel_release):
        return self.installed

    def download_kernel_packages(self):
        self.calls.append("download")
        return Path("modules"), Path("headers")

    def install_kernel_packages(self, _modules, _headers):
        self.calls.append("install-kernel")

    def install_acpi_call_module(self):
        self.calls.append("install-acpi")
        if self.fail_install:
            raise RuntimeError("build failed")
        self.installed = True

    def _teardown_build_overlay(self):
        self.calls.append("teardown")

    def cleanup(self, _modules, _headers):
        self.calls.append("cleanup")


class AcpiEnablerTests(unittest.TestCase):
    def test_distro_family_detects_bazzite_os_release(self):
        enabler = AcpiEnabler.__new__(AcpiEnabler)
        os_release = "\n".join([
            'NAME="Bazzite"',
            'ID=bazzite',
            'VARIANT="Bazzite"',
            'VARIANT_ID=bazzite',
        ])
        with patch("pathlib.Path.read_text", return_value=os_release):
            self.assertEqual(enabler.distro_family(), "bazzite")

    def test_immutable_build_repairs_container_selinux_labels(self):
        enabler = RecordingEnabler()
        module_dir = Path("/home/user/settings/acpi-call/test-kernel")
        enabler._run = lambda command: enabler.calls.append(command)

        with patch(
            "py_modules.acpi_enabler.acpi_enabler.os.getxattr",
            return_value=b"system_u:object_r:container_file_t:s0",
        ), patch(
            "py_modules.acpi_enabler.acpi_enabler.shutil.which",
            return_value="/usr/bin/restorecon",
        ):
            enabler._restore_immutable_module_context(module_dir / "acpi_call.ko")

        self.assertEqual(
            enabler.calls,
            [["sudo", "-n", "/usr/bin/restorecon", "-RF", str(module_dir)]],
        )

    def test_immutable_loader_installs_policy_before_starting_service(self):
        enabler = AcpiEnabler.__new__(AcpiEnabler)
        enabler._log = lambda _message: None
        helper_binary = Path("/tmp/acpi-call-loader")
        policy_package = Path("/tmp/legion_center_acpi_loader.pp")
        module_path = Path("/tmp/acpi_call.ko")
        calls = []
        enabler._build_immutable_loader_artifacts = lambda _version: (
            helper_binary,
            policy_package,
        )
        enabler._run = lambda command: calls.append(command)

        with patch(
            "py_modules.acpi_enabler.acpi_enabler.Path.is_file",
            return_value=True,
        ):
            enabler._install_immutable_module_loader(module_path, "42")

        semodule_index = next(
            index for index, command in enumerate(calls) if command[2] == "semodule"
        )
        restart_index = next(
            index for index, command in enumerate(calls)
            if command[2:4] == ["systemctl", "restart"]
        )
        self.assertLess(semodule_index, restart_index)
        self.assertEqual(
            calls[semodule_index],
            ["sudo", "-n", "semodule", "-i", str(policy_package)],
        )
        self.assertEqual(
            calls[restart_index],
            [
                "sudo",
                "-n",
                "systemctl",
                "restart",
                AcpiEnabler.IMMUTABLE_LOADER_UNIT_NAME,
            ],
        )

    def test_loader_policy_does_not_grant_decky_module_loading(self):
        policy_path = (
            Path(__file__).parents[1]
            / "py_modules"
            / "acpi_enabler"
            / "selinux_loader"
            / "legion_center_acpi_loader.te"
        )
        policy = policy_path.read_text()

        self.assertIn(
            "allow legion_center_acpi_loader_t self:system module_load;",
            policy,
        )
        self.assertIn(
            "allow legion_center_acpi_loader_t legion_center_acpi_module_t:file",
            policy,
        )
        self.assertNotIn("unconfined_service_t", policy)
        self.assertNotIn("module_unload", policy)

    def test_run_raises_on_required_command_failure(self):
        enabler = RecordingEnabler()
        failed = SimpleNamespace(returncode=9, stdout="", stderr="bad command")
        with patch("subprocess.run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "bad command"):
                enabler._run(["false"])

    def test_run_quiet_returns_expected_failure(self):
        enabler = RecordingEnabler()
        failed = SimpleNamespace(returncode=1, stdout="", stderr="expected")
        with patch("subprocess.run", return_value=failed):
            self.assertIs(enabler._run_quiet(["false"]), failed)

    def test_enable_skips_download_when_current_module_is_installed(self):
        enabler = RecordingEnabler(installed=True)
        with patch("pathlib.Path.is_file", return_value=True):
            enabler.enable()
        self.assertEqual(
            enabler.calls,
            ["prep", "install-acpi", "teardown", "cleanup", "finalize"],
        )

    def test_enable_always_cleans_up_and_restores_readonly_on_failure(self):
        enabler = RecordingEnabler(fail_install=True)
        with self.assertRaisesRegex(RuntimeError, "build failed"):
            enabler.enable()
        self.assertEqual(
            enabler.calls,
            [
                "prep",
                "download",
                "install-kernel",
                "install-acpi",
                "teardown",
                "cleanup",
                "finalize",
            ],
        )


if __name__ == "__main__":
    unittest.main()
