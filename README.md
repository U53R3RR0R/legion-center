# Legion Center - Decky Plugin

[![](https://img.shields.io/github/downloads/U53R3RR0R/legion-center/total.svg)](https://github.com/U53R3RR0R/legion-center/releases)

A Decky Loader plugin from InnoVision Games for the original Lenovo Legion Go (Z1E). It provides controller remapping, touchpad and gyro settings, fan controls, power LED control, and charge-limit management on SteamOS and compatible Linux systems, including Bazzite. Custom fan curves require a matching kernel module and are experimental.

- [Functionality](#functionality)
- [Install Instructions](#install-instructions)
  - [Prerequisites](#prerequisites)
  - [Quick Install / Update](#quick-install--update)
  - [Manual Install](#manual-install)
- [Manual Build](#manual-build)
- [Experimental Features](#experimental-features)
  - [Custom Fan Curves](#custom-fan-curves)
    - [Setup Instructions](#fan-curve-setup-instructions)
- [Troubleshooting/FAQ](#troubleshooting--frequently-asked-questions)
  - [LED management seems to work temporarily](#led-management-seems-to-work-temporarily)
  - [Can I turn off the power LED light while the device is asleep?](#can-i-turn-off-the-power-led-while-the-device-is-asleep)
- [Attribution](#attribution)
  - [AI assistance and disclaimer](#ai-assistance-and-disclaimer)

![fan-control image](./images/fan-control.png)

![remap buttons image](./images/remap-buttons.png)

# Functionality

### This plugin uses the Lenovo-built remapping + bios functionality that's used for Legion Space, which means that this plugin can only do what Legion Space is capable of

This remapping plugin also only covers remapping for the X-input mode of the controller, it does NOT support FPS mode or D-input modes.

Included Functionality in this plugin:

- Power LED on/off control
- Back Button Remapping for Y1, Y2, Y3, M2, M3 (M1 is not supported)
- Enabling/Disabling the touchpad
- Gyro remapping to Left or Right Control Stick
- allow any of these settings on a per-game basis
- 80% charge limit through the native Lenovo battery interface when available
- Custom fan curves through `acpi_call`

# Install Instructions

### Prerequisites

Decky Loader must already be installed.

### Quick Install / Update

Run the following in a terminal as your regular user. It works for a fresh
install or an update. Decky Loader must already be installed.

```bash
curl --fail --location \
  https://raw.githubusercontent.com/U53R3RR0R/legion-center/v0.2.0-alpha.1/install.sh \
  --output /tmp/install-legion-center.sh &&
bash /tmp/install-legion-center.sh &&
rm /tmp/install-legion-center.sh
```

The installer installs the latest release into Decky's `~/homebrew/plugins`
directory, adds the Legion Go USB udev rule if it is missing, and restarts the
Decky plugin loader. On Bazzite, no read-only toggle or `rpm-ostree` command is
needed. The udev rule is written to the mutable `/etc/udev/rules.d`; the plugin
itself stays in your home directory. This alpha release is distributed from
the `U53R3RR0R/legion-center` repository.

### Manual Install

Download `LegionCenter-0.2.0-alpha.1.tar.gz` from the
[alpha release](https://github.com/U53R3RR0R/legion-center/releases/tag/v0.2.0-alpha.1)
to `~/Downloads`, then extract it into
Decky's plugin directory:

```bash
mkdir -p "$HOME/homebrew/plugins"
archive="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'LegionCenter-*.tar.gz' -print -quit)"
tar -xzf "$archive" -C "$HOME/homebrew/plugins"
```

If controller access does not work, add the udev rule below. The automatic
installer creates it if it is missing.

If that file is not already present, create
`/etc/udev/rules.d/90-legion-center.rules` with `sudoedit` and add:

```udev
# allow r/w access by all local/physical sessions (seats)
# https://github.com/systemd/systemd/issues/4288
SUBSYSTEMS=="usb", ATTRS{idVendor}=="17ef", TAG+="uaccess"

# allow r/w access by all users
SUBSYSTEMS=="usb", ATTRS{idVendor}=="17ef", MODE="0666"
```

Reload udev rules and restart Decky Loader:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb
sudo systemctl restart plugin_loader.service
```

If Decky Loader is configured as a user service instead, use
`systemctl --user restart plugin_loader.service`.

# Manual Build

- Node.js v16.14+ and pnpm installed

```bash
git clone --branch v0.2.0-alpha.1 https://github.com/U53R3RR0R/legion-center.git

cd legion-center

# if pnpm not already installed
npm install -g pnpm

pnpm install
pnpm run build
```

To create the same release archive used by the installer:

```bash
pnpm run package
```

Extract the generated `artifacts/LegionCenter-<version>.tar.gz` into
`$HOME/homebrew/plugins`, then restart Decky Loader as described above.

# Custom Fan Curves

## WARNING: If you don't properly cool your device, it can go into thermal shutdown! Make sure you set proper fan curves to keep your device cool!

Note that this is using the fan curve implementation in the Legion Go's bios. This may require additional bios update from Lenovo to become fully functional.

Fan support can be installed entirely from the plugin in Gaming Mode:

1. Open Legion Center.
2. Scroll to **System**.
3. Select **Install Fan Support** and confirm.
4. Keep the device awake while the plugin obtains matching kernel headers,
   builds `acpi_call`, and verifies `/proc/acpi/call`.
5. Enable custom fan curves after the status changes to **Ready**.

No Desktop Mode, Konsole commands, or manual header installation is required.
The initial setup needs an internet connection and can take several minutes.

On SteamOS, the plugin downloads matching kernel packages and uses DKMS.
SteamOS updates can replace the kernel. If fan support shows **Repair needed**
after an update, select **Repair Fan Support** from the same panel.

## Bazzite / other immutable Fedora installations

Fan support builds `acpi_call` in a temporary Fedora container using the
running kernel's matching `kernel-devel` tree. It requires Podman, Git, and
those matching headers to be available. The resulting module is kept under
Decky's persistent plugin settings and loaded directly; this path does not use
`rpm-ostree`, layer packages, or write to the host's `/usr` or `/etc`. The
module is specific to the running kernel, so run **Repair Fan Support** after
a kernel update. Controller remapping, the power LED, touchpad/gyro, and
supported charge-limit controls do not require this fan-support backend.

# Troubleshooting / Frequently Asked Questions

## The Plugin isn't working

First try reinstalling or updating the plugin to the latest version, there's an update button at the bottom of the plugin. You can also re-run the installer to update:

```bash
curl --fail --location \
  https://raw.githubusercontent.com/U53R3RR0R/legion-center/v0.2.0-alpha.1/install.sh \
  --output /tmp/install-legion-center.sh &&
bash /tmp/install-legion-center.sh &&
rm /tmp/install-legion-center.sh
```

If this doesn't fix your issue, next try deleting your `$HOME/homebrew/settings/Legion Center/settings.json` file, and rebooting.

If neither works, please create a github issue.

# Attribution

Legion Center builds on the hardware protocol research and prior plugin work of others in the SteamOS/handheld Linux community. See `THIRD_PARTY_NOTICES.md` for full license details on everything referenced below.

Special thanks to [antheas](https://github.com/antheas) for [reverse engineering and documenting the HID protocols](https://github.com/antheas/hwinfo/tree/master/devices/legion_go) for the Legion Go Controllers, etc.

Also special thanks to [corando98](https://github.com/corando98) for writing + testing the backend functions for talking to the HID devices, investigating fan curves, as well as contributing to the RGB light management code on the frontend.

The `\_SB.GZFD` ACPI/WMI calls used for fan curve, TDP mode, charge limit, and power LED control are documented by the [hhd-dev/adjustor](https://github.com/hhd-dev/adjustor) project (GPLv3).

This plugin originated as a fork of Aarron Lee's `LegionGoRemapper` (BSD 3-Clause); its HID and ACPI backend modules have since been reimplemented by InnoVision Games. See `LICENSE` and `THIRD_PARTY_NOTICES.md` for the full license chain.

Icon and controller button SVG files generated from PromptFont using FontForge.

> PromptFont by Yukari "Shinmera" Hafner, available at https://shinmera.com/promptfont

## AI assistance and disclaimer

GitHub Copilot has assisted with portions of the code and documentation. The
hardware protocol research and original contributions remain attributable to
the people and projects credited above and in `THIRD_PARTY_NOTICES.md`; AI
assistance is not a source of that research.

AI-assisted code and documentation may be incomplete or inaccurate. Review and
test changes before relying on them. This plugin interacts with device
firmware, including cooling and power controls; verify behavior and
temperatures on your own hardware. Use the software at your own risk.
