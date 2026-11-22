import Cocoa
import IOKit

final class AMDModeController {
    private func openClient() -> io_connect_t? {
        let svc = IOServiceGetMatchingService(kIOMasterPortDefault, IOServiceMatching("AMDRyzenCPUPowerManagement"))
        guard svc != 0 else { return nil }
        defer { IOObjectRelease(svc) }
        var conn: io_connect_t = 0
        let kr = IOServiceOpen(svc, mach_task_self_, 0, &conn)
        return kr == KERN_SUCCESS ? conn : nil
    }

    func setMode(pstate: UInt64, cpb: UInt64, ppm: UInt64) -> Bool {
        guard let conn = openClient() else { return false }
        defer { IOServiceClose(conn) }
        var vPpm = ppm, vCpb = cpb, vPs = pstate
        if ppm == 0 {
            IOConnectCallScalarMethod(conn, 14, &vPpm, 1, nil, nil)
            IOConnectCallScalarMethod(conn, 12, &vCpb, 1, nil, nil)
            IOConnectCallScalarMethod(conn, 10, &vPs, 1, nil, nil)
        } else {
            IOConnectCallScalarMethod(conn, 10, &vPs, 1, nil, nil)
            IOConnectCallScalarMethod(conn, 12, &vCpb, 1, nil, nil)
            IOConnectCallScalarMethod(conn, 14, &vPpm, 1, nil, nil)
        }
        return true
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private let ctl = AMDModeController()
    private var items: [NSMenuItem] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "ECO"
        let menu = NSMenu()
        let modes: [(String, Selector)] = [
            ("Power Saver (1600 MHz)", #selector(setSave)),
            ("Balanced (2560 MHz)", #selector(setBalanced)),
            ("Performance (3200 MHz + Boost)", #selector(setPerf)),
        ]
        for (title, action) in modes {
            let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
            item.target = self
            menu.addItem(item)
            items.append(item)
        }
        menu.addItem(.separator())
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        statusItem.menu = menu
        items[0].state = .on
    }

    private func select(_ idx: Int, label: String, pstate: UInt64, cpb: UInt64, ppm: UInt64) {
        if ctl.setMode(pstate: pstate, cpb: cpb, ppm: ppm) {
            statusItem.button?.title = label
            for (i, item) in items.enumerated() { item.state = (i == idx ? .on : .off) }
        }
    }

    @objc func setSave()     { select(0, label: "ECO",  pstate: 2, cpb: 0, ppm: 0) }
    @objc func setBalanced() { select(1, label: "BAL",  pstate: 1, cpb: 0, ppm: 0) }
    @objc func setPerf()     { select(2, label: "PERF", pstate: 0, cpb: 1, ppm: 1) }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
