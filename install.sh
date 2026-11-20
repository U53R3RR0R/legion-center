#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Please run this installer as your regular user, not as root." >&2
  exit 1
fi

decky_home="${DECKY_HOME:-${HOME}/homebrew}"
plugin_dir="${decky_home}/plugins"
if [[ ! -d "${decky_home}" ]]; then
  echo "Decky Loader directory not found: ${decky_home}" >&2
  echo "Install Decky Loader first, then rerun this installer." >&2
  exit 1
fi
mkdir -p "${plugin_dir}"

temporary_dir="$(mktemp -d)"
cleanup() {
  rm -rf "${temporary_dir}"
}
trap cleanup EXIT

rules_file="/etc/udev/rules.d/90-legion-center.rules"
if [[ ! -f "${rules_file}" ]]; then
  cat > "${temporary_dir}/90-legion-center.rules" <<'EOF'
# allow r/w access by all local/physical sessions (seats)
# https://github.com/systemd/systemd/issues/4288
SUBSYSTEMS=="usb", ATTRS{idVendor}=="17ef", TAG+="uaccess"

# allow r/w access by all users
SUBSYSTEMS=="usb", ATTRS{idVendor}=="17ef", MODE="0666"
EOF
  sudo install -D -m 0644 "${temporary_dir}/90-legion-center.rules" "${rules_file}"
  sudo udevadm control --reload-rules
  sudo udevadm trigger --subsystem-match=usb
fi

download_url="$(
  curl --fail --silent --show-error --location \
    "https://api.github.com/repos/U53R3RR0R/legion-center/releases?per_page=100" |
    python3 -c '
import json
import sys

releases = json.load(sys.stdin)
if not isinstance(releases, list):
    raise SystemExit("GitHub did not return a release list")

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
        available.append((release.get("published_at") or "", asset))

if not available:
    raise SystemExit("No published LegionCenter release archive was found")
print(max(available, key=lambda item: item[0])[1]["browser_download_url"])
'
)"

archive="${temporary_dir}/LegionCenter.tar.gz"
extract_dir="${temporary_dir}/extract"
mkdir -p "${extract_dir}"
curl --fail --silent --show-error --location --retry 3 \
  "${download_url}" --output "${archive}"
tar -xzf "${archive}" -C "${extract_dir}"
if [[ ! -d "${extract_dir}/LegionCenter" ]]; then
  echo "Downloaded archive does not contain a LegionCenter plugin folder." >&2
  exit 1
fi

echo "Installing Legion Center to ${plugin_dir}"
sudo rm -rf "${plugin_dir}/LegionCenter"
sudo mv "${extract_dir}/LegionCenter" "${plugin_dir}/LegionCenter"

if sudo systemctl restart plugin_loader.service; then
  echo "Legion Center installed and Decky Loader restarted."
elif systemctl --user restart plugin_loader.service; then
  echo "Legion Center installed and the user Decky Loader service restarted."
else
  echo "Legion Center files were installed, but plugin_loader.service could not be restarted." >&2
  echo "Restart Decky Loader from Steam or reboot to load the plugin." >&2
  exit 1
fi
