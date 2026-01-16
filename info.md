[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

A Home Assistant custom component for **LightStack** - a priority-based alert management system for Inovelli LED switches.

## Features

- **Real-time updates** via WebSocket (no polling required)
- **Current alert sensor** with full LED effect attributes:
  - Color, effect, brightness, duration
  - Human-readable names for all values
- **21 LED effects** supported for Inovelli Blue series switches
- **Alert active binary sensor** for simple automations
- **Clear all alerts button** for quick management
- **Services** for triggering and clearing alerts from automations

**This component will set up the following platforms.**

| Platform        | Description                                       |
| --------------- | ------------------------------------------------- |
| `sensor`        | Shows the current (highest priority) active alert |
| `binary_sensor` | Indicates if any alert is active                  |
| `button`        | Clear all active alerts                           |

## Services

| Service                       | Description                                      |
| ----------------------------- | ------------------------------------------------ |
| `lightstack.trigger_alert`    | Trigger an alert with optional priority override |
| `lightstack.clear_alert`      | Clear a specific alert                           |
| `lightstack.clear_all_alerts` | Clear all active alerts                          |

{% if not installed %}

## Installation

1. Click install.
2. Restart Home Assistant.
3. Go to Settings -> Devices & Services -> Add Integration.
4. Search for "LightStack".
5. Enter your LightStack server host and port.

{% endif %}

## Configuration

Configuration is done through the Home Assistant UI. You'll need:

- **Host**: The hostname or IP address of your LightStack server
- **Port**: The WebSocket API port (default: 8080)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[commits]: https://github.com/sjafferali/lightstack-homeassistant/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/sjafferali/lightstack-homeassistant/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40sjafferali-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[releases]: https://github.com/sjafferali/lightstack-homeassistant/releases
[user_profile]: https://github.com/sjafferali
