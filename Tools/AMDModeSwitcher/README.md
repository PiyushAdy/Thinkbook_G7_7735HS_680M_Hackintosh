# AMDModeSwitcher

Lightweight, **0% background CPU** power-mode switcher for `AMDRyzenCPUPowerManagement.kext` on AMD Hackintosh laptops.

By default, this EFI boots into **Power Saver** (`SpeedID = 2`, `CPBStatus = 0` → 1600 MHz, CPB Off) for cool temperatures and quiet fans. Use `AMDModeSwitcher` whenever you want to switch to Balanced or full Performance (4.83 GHz boost) without rebooting.

## Modes

| Mode | Clock / P-State | Core Performance Boost (CPB) | Scaling |
| :--- | :--- | :--- | :--- |
| `save` (default at boot) | 1600 MHz (P2) | Off | Manual |
| `balanced` | 2560 MHz (P1) | Off | Manual |
| `perf` | 3200 MHz (P0) | On (up to 4.83 GHz boost) | Auto |

## 1. Instant CLI (No Compiling Required)

Uses macOS's built-in `python3`:

```zsh
chmod +x amdmode.py
sudo cp amdmode.py /usr/local/bin/amdmode
amdmode status
amdmode save
amdmode balanced
amdmode perf
```

## 2. Optional Menu-Bar App (~150 KB Native Binary, 0% Idle CPU)

Uses macOS's built-in `swiftc` (Xcode Command Line Tools):

```zsh
swiftc -O AMDModeBar.swift -o AMDModeBar -framework Cocoa -framework IOKit
./AMDModeBar &
```
