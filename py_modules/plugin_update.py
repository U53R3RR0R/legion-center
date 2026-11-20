import decky
import subprocess
import urllib.request
import json
import os
from pathlib import Path
from common.lib.package_downloader import PackageDownloader, default_ssl_context

def download_latest_build():
    url = "https://api.github.com/repos/U53R3RR0R/legion-center/releases?per_page=100"

    with urllib.request.urlopen(url, context=default_ssl_context()) as response:
        releases = json.load(response)

    if not isinstance(releases, list):
        raise RuntimeError("GitHub did not return a release list")

    available = []
    for release in releases:
        if release.get("draft"):
            continue
        asset = next(
            (
                item for item in release.get("assets", [])
                if item.get("name", "").startswith("LegionCenter-")
                and item.get("name", "").endswith(".tar.gz")
            ),
            None,
        )
        if asset:
            available.append((release.get("published_at") or "", release, asset))

    if not available:
        raise RuntimeError("No published LegionCenter release archive was found")

    _, release, asset = max(available, key=lambda item: item[0])

    download_url = asset["browser_download_url"]
    decky.logger.info(
        "Downloading Legion Center %s from %s" % (release.get("tag_name"), download_url)
    )

    file_path = Path('/tmp/LegionCenter.tar.gz')
    file_path.unlink(missing_ok=True)
    downloader = PackageDownloader(file_path.parent)
    return str(downloader.download(download_url, filename=file_path.name))

def ota_update():
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ""
    download_latest_build()

    plugin_dir = Path(__file__).resolve().parent.parent
    update_script = plugin_dir / "ota_update.sh"
    if not update_script.is_file():
        raise FileNotFoundError("Bundled update script is missing: %s" % update_script)

    env["HOME"] = decky.DECKY_USER_HOME
    result = subprocess.run(
        ["bash", str(update_script)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(plugin_dir),
    )

    if result.stdout:
        decky.logger.info(result.stdout)
    if result.stderr:
        decky.logger.error(result.stderr)
    if result.returncode != 0:
        raise RuntimeError("Legion Center update failed with exit code %s" % result.returncode)
    return result
