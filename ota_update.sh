#!/usr/bin/env bash

set -euo pipefail

archive="/tmp/LegionCenter.tar.gz"
if [[ ! -s "${archive}" ]]; then
  echo "Downloaded Legion Center archive is missing or empty: ${archive}" >&2
  exit 1
fi

plugin_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugins_dir="$(dirname "${plugin_dir}")"
temporary_dir="$(mktemp -d "${plugins_dir}/.LegionCenter-update.XXXXXX")"
backup_dir="${plugins_dir}/.LegionCenter-old.$$"
cleanup() {
  rm -rf "${temporary_dir}"
}
trap cleanup EXIT

tar -xzf "${archive}" -C "${temporary_dir}"
if [[ ! -d "${temporary_dir}/LegionCenter" ]]; then
  echo "Downloaded archive does not contain a LegionCenter plugin folder." >&2
  exit 1
fi

if [[ -e "${plugin_dir}" ]]; then
  mv "${plugin_dir}" "${backup_dir}"
fi
if ! mv "${temporary_dir}/LegionCenter" "${plugin_dir}"; then
  if [[ -e "${backup_dir}" ]]; then
    mv "${backup_dir}" "${plugin_dir}"
  fi
  echo "Could not install the new Legion Center plugin files." >&2
  exit 1
fi

rm -rf "${backup_dir}"
rm -f "${archive}"

if systemctl restart plugin_loader.service; then
  echo "Legion Center updated and Decky Loader restarted."
elif systemctl --user restart plugin_loader.service; then
  echo "Legion Center updated and the user Decky Loader service restarted."
else
  echo "Legion Center was updated, but plugin_loader.service could not be restarted." >&2
  echo "Restart Decky Loader from Steam or reboot to load the update." >&2
  exit 1
fi
