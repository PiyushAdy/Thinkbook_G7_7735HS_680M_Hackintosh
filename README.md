# Lenovo ThinkBook 16 Gen 7 (Ryzen 7 7735HS / Radeon 680M) — OpenCore EFI

OpenCore EFI collection, power-mode switcher, and complete debugging notes for running **macOS Sequoia 15.8** on the **Lenovo ThinkBook 16 Gen 7 (AMD Ryzen 7 7735HS + Radeon 680M)** (tested in a triple-boot setup alongside Windows 11 and Fedora 44).

> **Disclaimer (Hobby Project)**
> This is a personal hobby project shared as-is for reference and for my own future reinstalls. It will **not** be updated frequently, and GitHub issues or pull requests may not be fixed or entertained. Always back up your EFI and data before making changes, and read the [Troubleshooting & Bugs Solved](#troubleshooting--bugs-solved) section below if you hit a snag.

---

## Tested Hardware & Environment

Match your hardware against this list before using these EFIs as-is:

| Component | Model / Details | Status | Driver / Kext |
| :--- | :--- | :--- | :--- |
| **Laptop** | Lenovo ThinkBook 16 Gen 7 (AMD) | Working | OpenCore (`MacBookPro16,3` daily / `iMacPro1,1` install) |
| **macOS Version** | **macOS Sequoia 15.8** | Working | — |
| **CPU** | AMD Ryzen 7 7735HS (Rembrandt-R, 8C/16T) | Working | AMD Vanilla patches + `ForgedInvariant.kext` + `AMDRyzenCPUPowerManagement.kext` |
| **iGPU** | AMD Radeon 680M (Rembrandt) | Working (Hardware Accel) | `RembrandtGfx.kext` + `ATY,bin_image` VBIOS injection |
| **Display** | `LEN9156` 1920×1200 @ 60 Hz | Working (Backlight + Keys) | `SSDT-PNLF.aml` + `BrightnessKeys.kext` |
| **NVMe SSD** | Samsung PM9C1a NVMe | Working (TRIM enabled) | `NVMeFix.kext` + `SetApfsTrimTimeout = -1` |
| **Wi-Fi** | Realtek RTL89xx | Working on Sequoia | `AirPort_RTW89.kext` + `IOSkywalkFamily` + `IO80211FamilyLegacy` + `AMFIPass` |
| **Bluetooth** | Realtek Bluetooth | Working | `RealtekBluetoothFirmware.kext` + `BlueToolFixup.kext` |
| **Ethernet** | Realtek RTL8111 | Working | `RealtekRTL8111.kext` |
| **Audio** | Realtek HDA | Working | `AppleALC.kext` (`alcid=11` / `layout-id = 0x0b`) |
| **Touchpad** | `ELAN06FA:00` (`04F3:327E`, I2C HID, 119×73 mm) | Working (`libinput`-style tap & drag) | `VoodooI2C` + `VoodooI2CHID` + custom [`VoodooInput.kext`](https://github.com/PiyushAdy/MacVodooWithBetterDragSupport) |
| **Keyboard** | Internal PS/2 Keyboard | Working | `VoodooPS2Controller.kext` + `VoodooPS2Keyboard.kext` |
| **Battery / EC** | Embedded Controller | Working | `ECEnabler.kext` + `SMCBatteryManager.kext` |
| **USB Ports** | Mapped for ThinkBook G7 | Working | `USBToolBox.kext` + `UTBMap.kext` |

---

## Repository Structure (Which EFI to Use)

Three EFIs are included so you have a clean path from Recovery → Debugging → Daily Use:

| Folder | SMBIOS | Purpose | Key Differences |
| :--- | :--- | :--- | :--- |
| **`1_EFI_Install_Recovery/`** | `iMacPro1,1` | **macOS Recovery & Installation** | Clean GOP/VESA (no `RembrandtGfx`), `ForgedInvariant.kext` enabled, Wi-Fi + Ethernet enabled for online Recovery, `-v debug=0x144`, `ShowPicker = True` (5s). |
| **`2_EFI_Debug_Verbose/`** | `MacBookPro16,3` | **Post-Install Testing & Debugging** | Full daily kext stack (`RembrandtGfx`, Audio, BT, Power Mgmt, custom v7 `VoodooInput`), with `-v`, `ShowPicker = True` (5s), `Debug Target = 67`, `AppleDebug = True`, `ApplePanic = True`. |
| **`3_EFI_Daily_Use/`** | `MacBookPro16,3` | **Silent Daily Driver** | Identical to `2_EFI_Debug_Verbose` but silent: no `-v`, `ShowPicker = False`, `Timeout = 0`, `Debug Target = 0`. Move to this once `2_EFI_Debug_Verbose` boots cleanly. |
| **`Tools/AMDModeSwitcher/`** | — | **CPU Power-Mode Switcher** | Zero-CPU CLI (`amdmode.py`) + optional menu-bar app (`AMDModeBar.swift`) to switch between Power Saver, Balanced, and Performance modes. |

> **Why are there separate Install/Recovery and Daily-Use EFIs?**
> `RembrandtGfx.kext` works on the full macOS desktop, but can black-screen or panic inside the minimal macOS Recovery/Installer environment. Always use **`1_EFI_Install_Recovery`** to boot Recovery or reinstall macOS, test your installed system with **`2_EFI_Debug_Verbose`**, and then switch to **`3_EFI_Daily_Use`**.

---

## Before You Boot (Mandatory Setup)

### 1. Generate Your Own SMBIOS Identifiers
All personal identifiers have been stripped from every `config.plist` in this repo (`SystemSerialNumber`, `MLB`, `SystemUUID` are set to `CHANGE_ME_WITH_GENSMBIOS`, and `ROM` is set to `112233445566`).

Before booting, use [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) to generate fresh identifiers and paste them into `PlatformInfo → Generic` in `EFI/OC/config.plist`:
- For `1_EFI_Install_Recovery`: generate **`iMacPro1,1`**
- For `2_EFI_Debug_Verbose` and `3_EFI_Daily_Use`: generate **`MacBookPro16,3`** (use the same generated serials across both)
- Set `ROM` to your Ethernet/Wi-Fi MAC address (6 bytes, no colons) or a random 6-byte hex value.

### 2. Required BIOS Settings
- **AMD Pluton Security Processor**: **Disabled** *(critical — see [Troubleshooting](#1-backlight-turns-off--boot-hang-right-after-opencore-picker-amd-pluton-on))*
- **Secure Boot**: **Disabled**
- **Fast Boot**: **Disabled**

### 3. Hardware-Specific Checks
- **USB Ports (`UTBMap.kext`):** Mapped for this exact ThinkBook 16 Gen 7. If any USB ports or internal Bluetooth/webcam don't work on your revision, remap them using [USBToolBox](https://github.com/USBToolBox/tool).
- **Audio (`alcid=11`):** Configured for `layout-id = 11` (`0x0b`). Adjust `alcid=` in `boot-args` and `DeviceProperties` if your variant uses a different codec layout.

---

## CPU Power Management & `AMDModeSwitcher`

By default, **`AMDRyzenCPUPowerManagement.kext`** in `2_EFI_Debug_Verbose` and `3_EFI_Daily_Use` is configured to **boot in Power Saver mode** (`CPBStatus = 0`, `SpeedID = 2` → **1600 MHz, Core Performance Boost OFF**) for significantly lower idle/load temperatures, quieter fans, and better battery life.

Whenever you need more speed (compiling, gaming, heavy multitasking), use **`Tools/AMDModeSwitcher/`** (0% background CPU) to switch power states live without rebooting:

```zsh
cd Tools/AMDModeSwitcher
chmod +x amdmode.py
sudo cp amdmode.py /usr/local/bin/amdmode
amdmode status
amdmode save
amdmode balanced
amdmode perf
```

- `save` — 1600 MHz (P2), CPB Off (default at boot)
- `balanced` — 2560 MHz (P1), CPB Off
- `perf` — 3200 MHz (P0), CPB On (up to 4.83 GHz boost), Auto scaling

See [`Tools/AMDModeSwitcher/README.md`](Tools/AMDModeSwitcher/README.md) if you also want to compile the lightweight ~150 KB native macOS menu-bar switcher (`AMDModeBar.swift`).

---

## Touchpad Setup (`MacVodooWithBetterDragSupport`)

`2_EFI_Debug_Verbose` and `3_EFI_Daily_Use` ship with a custom `VoodooInput.kext` (nested inside `EFI/OC/Kexts/VoodooPS2Controller.kext/Contents/PlugIns/VoodooInput.kext`) from [**MacVodooWithBetterDragSupport**](https://github.com/PiyushAdy/MacVodooWithBetterDragSupport).

It implements a kernel-level `libinput`-style state machine so macOS behaves like Linux/Windows Precision Touchpads (single-tap click, double-tap double-click, 1-finger double-tap & slide to drag with 0 ms center drop and 300 ms edge continuation, and 2-finger tap right-click) while keeping native 3-finger Mission Control/Spaces gestures intact.

**Required macOS Settings for the custom touchpad kext:**
1. **System Settings → Trackpad → Point & Click**
   - **Tap to click**: **OFF** *(handled directly in `VoodooInput.kext` to avoid double-click conflicts on window title bars)*
   - **Secondary click**: **Click with two fingers** (**ON**)
2. **System Settings → Accessibility → Pointer Control → Trackpad Options**
   - **Use trackpad for dragging**: **OFF**

---

## Post-Install Tweaks

### Prevent Sleep-Loop SSD Wear (Recommended for Samsung PM9C1a)
OpenCore already sets `HibernateMode = None`, `DisableRtcChecksum = True`, and `SetApfsTrimTimeout = -1`. Run this once in macOS Terminal to disable hibernation/standby/wake-loop writes:

```zsh
sudo pmset -a hibernatemode 0 standby 0 autopoweroff 0 tcpkeepalive 0 proximitywake 0
sudo rm -f /private/var/vm/sleepimage
```

### Dual / Triple-Booting with Linux (`rEFInd` vs GRUB2)
- **Do NOT chainload OpenCore from GRUB2** — it triggers the macOS 🚫 prohibited sign even when pointing at `BOOTx64.efi`.
- Instead, register `\EFI\OC\OpenCore.efi` directly as a UEFI boot entry (`efibootmgr`) or use **[rEFInd](https://www.rodsbooks.com/refind/)** as your primary boot manager.

---

## Troubleshooting & Bugs Solved

A complete log of every issue encountered while bringing up macOS Sequoia 15.8 on this laptop (and how each was fixed), so both future installs and users on similar AMD Ryzen 6000/7000 laptops can debug themselves out:

### 1. Backlight turns off / boot hang right after OpenCore picker (AMD Pluton ON)
- **Symptom:** Right after selecting macOS in OpenCore, the screen backlight shuts off or the kernel hangs early (Stop-16).
- **Cause:** **AMD Pluton Security Processor** enabled in BIOS interferes with early macOS boot on Lenovo Ryzen 7000 laptops.
- **Fix:** Disable **AMD Pluton Security Processor** in BIOS. *(Note: Turning Pluton OFF did not break Windows 11 or standard proctored apps on this machine.)*

### 2. Stuck at "Examining Drives..." in macOS Recovery
- **Symptom:** macOS Recovery boots, but Disk Utility / the installer hangs indefinitely at *"Examining Drives..."* or fails to enumerate the NVMe drive.
- **Cause:** Conflicting legacy NVMe kexts (such as `HackrNVMeFamily`) or aggressive APFS TRIM timeouts on the Samsung PM9C1a NVMe SSD.
- **Fix:** Keep **only** `NVMeFix.kext` enabled (never enable `HackrNVMeFamily`), and set `Kernel → Quirks → SetApfsTrimTimeout = -1`.

### 3. Laggy touchpad, stuttering UI, and repeated/multiple keystrokes in Recovery & macOS
- **Symptom:** Moving the cursor in Recovery lags badly, and pressing a key once types multiple repeated characters (`aaaa`, `eeee`).
- **Cause:** **TSC (Time Stamp Counter) / TSync desync** across CPU cores on Ryzen 6000/7000 mobile CPUs.
- **Fix:** Add and enable **`ForgedInvariant.kext`** in **both** the Install/Recovery EFI and the Daily-Use EFI. This immediately eliminated cursor lag and key-repeat glitches.

### 4. Cannot connect to Apple servers to download macOS in Recovery
- **Symptom:** Online Recovery boots, but macOS installer reports *"Cannot connect to Apple servers"* or *"An internet connection is required"*.
- **Cause:** Missing/broken network stack in Recovery, or `SecureBootModel` / `DmgLoading` / `csr-active-config` mismatch.
- **Fix:** Include working network kexts in `1_EFI_Install_Recovery` (`AirPort_RTW89.kext` + `IOSkywalkFamily.kext` + `IO80211FamilyLegacy.kext` + `AMFIPass.kext` for Wi-Fi, plus `RealtekRTL8111.kext` for Ethernet), block native `com.apple.iokit.IOSkywalkFamily`, and set `SecureBootModel = Disabled`, `DmgLoading = Signed`, `csr-active-config = 030A0000`.

### 5. Daily-use EFI (`RembrandtGfx.kext`) black-screens or panics in Recovery
- **Symptom:** Trying to boot macOS Recovery with the daily-use EFI stalls or black-screens.
- **Cause:** `RembrandtGfx.kext` expects a full macOS desktop environment.
- **Fix:** Use **`1_EFI_Install_Recovery`** (clean VESA/GOP without `RembrandtGfx`) whenever you need Recovery or a fresh install.

### 6. GRUB2 chainloading OpenCore fails with 🚫 prohibited sign
- **Symptom:** Booting OpenCore from a Linux GRUB2 menu immediately hits the 🚫 symbol.
- **Fix:** Boot `\EFI\OC\OpenCore.efi` directly via UEFI NVRAM or via **rEFInd**.

### 7. Native macOS "Use trackpad for dragging" doesn't grab windows on `ELAN06FA`
- **Symptom:** Enabling macOS *Use trackpad for dragging* (*Without Drag Lock* / *With Drag Lock*) fails on `ELAN06FA` + `VoodooI2CHID`, leaving only Three-Finger Drag (which breaks 3-finger Mission Control/Spaces).
- **Fix:** Replaced `VoodooInput.kext` (inside `VoodooPS2Controller.kext/Contents/PlugIns/`) with our custom `libinput`-style build from [MacVodooWithBetterDragSupport](https://github.com/PiyushAdy/MacVodooWithBetterDragSupport) and turned macOS's built-in *Tap to click* and *Use trackpad for dragging* OFF.

### 8. Stats app shows `0 KB/s` download speed on Wi-Fi
- **Symptom:** Menu-bar monitors like Stats report `0` download throughput on `en1` while internet works fine.
- **Cause:** `AirPort_RTW89.kext` does not increment `if_ibytes` on the interface.
- **Fix:** In Stats → Network settings, switch **Reader type** from *Interface based* to **Process based**.

### 9. Avoid LinearMouse for trackpad speed on macOS Sequoia
- **Note:** Using LinearMouse on macOS Sequoia can break the native macOS Trackpad speed slider ([linearmouse/linearmouse#851](https://github.com/linearmouse/linearmouse/issues/851)). Keep trackpad tuning inside macOS System Settings.

---

## Credits

Huge thanks to the open-source Hackintosh community whose work made this build possible:

- **[Acidanthera](https://github.com/acidanthera):** OpenCore, `Lilu`, `VirtualSMC`, `SMCBatteryManager`, `AppleALC`, `NVMeFix`, `RestrictEvents`, `BrightnessKeys`, `VoodooPS2`, `BlueToolFixup`, `VoodooInput` (upstream)
- **[AMD-OSX](https://github.com/AMD-OSX/AMD_Vanilla):** AMD Vanilla OpenCore kernel patches
- **[ChefKissInc / Noot](https://github.com/ChefKissInc):** `ForgedInvariant.kext` and AMD mobile GPU research (`RembrandtGfx`)
- **[trulyspinach](https://github.com/trulyspinach/SMCAMDProcessor):** `AMDRyzenCPUPowerManagement.kext` & `SMCAMDProcessor.kext`
- **[AirPort_RTW89](https://github.com/OpenIntelWireless) / Realtek Wi-Fi & BT contributors:** `AirPort_RTW89.kext`, `RealtekBluetoothFirmware.kext`, `AMFIPass.kext` (OpenCore Legacy Patcher / Dortania)
- **[Mieze](https://github.com/Mieze/RTL8111_driver_for_OS_X):** `RealtekRTL8111.kext`
- **[VoodooI2C Team](https://github.com/VoodooI2C/VoodooI2C):** `VoodooI2C.kext`, `VoodooI2CHID.kext`, `VoodooGPIO`, `VoodooI2CServices`
- **[MacVodooWithBetterDragSupport](https://github.com/PiyushAdy/MacVodooWithBetterDragSupport):** Custom `libinput`-style tap-to-click & 1-finger tap-drag `VoodooInput.kext`
- **[USBToolBox](https://github.com/USBToolBox/kext):** `USBToolBox.kext` & `UTBMap.kext`
- **[1Revenger1](https://github.com/1Revenger1/ECEnabler):** `ECEnabler.kext`
- **[CorpNewt](https://github.com/corpnewt/GenSMBIOS):** `GenSMBIOS`
- **[Roderick W. Smith](https://www.rodsbooks.com/refind/):** `rEFInd` boot manager
