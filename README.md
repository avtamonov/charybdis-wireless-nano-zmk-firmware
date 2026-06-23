# Charybdis Wireless Nano ZMK Firmware

Firmware configuration for a wireless Charybdis Nano 3x5 build with a PMW3610
trackball and SuperMini nRF52840 controllers.

The repo builds ZMK firmware for two operating modes:

- Bluetooth/USB split: right half is the central half, left half is the peripheral.
- Dongle split: left and right halves connect to a dedicated dongle.

The default keymap is QWERTY. Additional keymaps live in `config/keymap/`.

## Hardware

- Keyboard: Charybdis Nano 3x5
- Controllers: SuperMini nRF52840
- Sensor: PMW3610 trackball on the right half
- Matrix: 4 rows x 6 scanned columns per half, with a 3x5 physical layout
- Main layout transform: `five_column_transform`

This build uses direct `gpio0`/`gpio1` references for the SuperMini matrix rows
where the Pro Micro/nice!nano aliases do not match the actual board labels.

### SuperMini Matrix Pinout

Rows are the same on both halves:

| Matrix row | SuperMini label | ZMK GPIO |
| ---------- | --------------- | -------- |
| R1 | `031` | `&gpio0 31` |
| R2 | `115` | `&gpio1 15` |
| R3 | `024` | `&gpio0 24` |
| R4 | `022` | `&gpio0 22` |

Left columns:

| Matrix column | SuperMini label | ZMK GPIO |
| ------------- | --------------- | -------- |
| C1 | `002` | `&gpio0 2` |
| C2 | `029` | `&gpio0 29` |
| C3 | `009` | `&gpio0 9` |
| C4 | `100` | `&gpio1 0` |
| C5 | `011` | `&gpio0 11` |
| C6 | not populated | unused |

The left overlay keeps one unused scanned column at index 0 because
`five_column_transform` maps the left main keys to columns `1..5`.

Right columns currently keep the existing Pro Micro aliases because that side is
working with the current wiring and transform.

## Firmware Outputs

GitHub Actions builds the configured firmware artifacts from `build.yaml`.

Main shields:

- `charybdis_left`
- `charybdis_right`
- `charybdis_dongle`
- `settings_reset`

Main keymap:

- `qwerty`

## Flashing

1. Download the firmware artifact from GitHub Actions.
2. Unzip the artifact.
3. Connect the target controller by USB.
4. Double-click reset to mount the UF2 bootloader drive.
5. Copy the matching UF2 file to the drive.
6. Wait for the controller to reboot.
7. Repeat for each required half or dongle.

For Bluetooth split mode, flash:

- `charybdis_left` to the left half
- `charybdis_right` to the right half

The right half is the central half. The computer connects to the right half; the
left half sends key events to it over split BLE.

Use `settings_reset` when flashing for the first time, changing between dongle
and Bluetooth modes, clearing BLE profiles, or recovering from split pairing
issues. Routine keymap or matrix changes usually do not require a reset flash.

## Pairing Notes

After `settings_reset`, flash normal firmware to both halves again, then:

1. Power off both halves.
2. Power on the right half.
3. Power on the left half.
4. Pair/connect the host to the right half.

The left half will not type directly into the host when plugged in by USB with
the normal split firmware, because it is built as a peripheral.

## Keymap Overview

The base keymap is in `config/keymap/qwerty.keymap`.

Rendered diagrams:

- Base layer: `keymap-drawer/base/qwerty.svg`
- Full layout: `keymap-drawer/qwerty.svg`

Configured layers:

| # | Layer | Purpose |
| - | ----- | ------- |
| 0 | BASE | Main typing layer with home-row mods |
| 1 | NUM | Numbers and function keys |
| 2 | NAV | Navigation, arrows, tmux helpers, mouse movement |
| 3 | SYM | Symbols and editing helpers |
| 4 | GAME | Simple gaming layer |
| 5 | EXTRAS | Bluetooth, output, media, and utility keys |
| 6 | SLOW | Slow pointer mode |
| 7 | SCROLL | Trackball scroll mode |

Common ZMK layer bindings:

```dts
&mo 1          // hold to activate layer 1
&tog 1         // toggle layer 1
&to 1          // switch to layer 1
&lt 1 SPACE    // tap Space, hold layer 1
```

Common number bindings:

```dts
&kp N1
&kp N2
&kp N3
```

## Trackball

Trackball configuration is split across:

- `config/charybdis_pmw3610.dtsi`
- `config/charybdis_pointer.dtsi`

The right half owns the PMW3610 sensor. In Bluetooth mode, the right half is also
the split central, so pointer events are sent directly from the central half.

## Editing

Useful files:

- `config/keymap/qwerty.keymap` - main keymap
- `config/keymap/behaviors.dtsi` - local behaviors
- `config/keymap/combos.dtsi` - combos
- `config/keymap/macros.dtsi` - macros
- `config/charybdis_pointer.dtsi` - pointer processing
- `boards/shields/charybdis_bt/` - Bluetooth split shield files
- `boards/shields/charybdis_dongle/` - dongle split shield files

ZMK Studio is enabled for Bluetooth builds on the right half.

## Building

The normal build path is GitHub Actions. Push changes and download the generated
artifacts from the workflow run.

Local container builds are available under `local-build/`:

```sh
cd local-build
docker-compose run --rm builder
```

## Troubleshooting

- If one half stops typing after `settings_reset`, reflash both halves and let
  them pair again.
- If an entire row is dead, verify the row line with a multimeter and compare it
  to the `row-gpios` entries.
- If an entire column is dead, verify the corresponding `C*` line and compare it
  to `col-gpios`.
- On SuperMini controllers, prefer the printed GPIO label such as `031`, `115`,
  or `024` and map it directly to `&gpio0`/`&gpio1` when the Pro Micro alias is
  not correct.

## Credits

- badjeff for the PMW3610 driver
- eigatech
- nickcoutsos for the keymap editor
- caksoylar for keymap-drawer and physical layout tooling
- urob for timeless home-row mod ideas
