#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_dir="${DECKY_HOME:-${HOME}/homebrew}/plugins/LegionCenter"

cd "${repo_dir}"
pnpm run build
sudo rm -rf "${plugin_dir}"
sudo mkdir -p "${plugin_dir}"
sudo cp -R "${repo_dir}/." "${plugin_dir}/"

if sudo systemctl restart plugin_loader.service; then
  echo "Legion Center reloaded."
elif systemctl --user restart plugin_loader.service; then
  echo "Legion Center reloaded."
else
  echo "Plugin files were copied, but plugin_loader.service could not be restarted." >&2
  echo "Restart Decky Loader from Steam or reboot to load the plugin." >&2
  exit 1
fi
