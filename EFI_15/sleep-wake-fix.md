# 睡眠唤醒问题排查与经验沉淀（Fujitsu CELSIUS J5012 黑苹果）

> 适用机型：Fujitsu CELSIUS J5012 ｜ 引导：OpenCore（EFI_15）｜ 系统：macOS 15.7.8 (24G809) ｜ SMBIOS：MacPro7,1
> 最后更新：2026-06-24

## 一、问题现象

进入睡眠后无法唤醒，唤醒时直接内核 panic 强制重启。

pmset 日志：
```
Sleep    Entering Sleep state due to '': Using AC
Failure  Failure during wake: PEG1(),GFX0(),I2C1(),HECI(),SAT0(AppleAHCI),RP21(),RP05()
         : Some drivers failed to handle setPowerState panic
```

内核 panic（`/Library/Logs/DiagnosticReports/Kernel-*.panic`）：
```
panic: "[6:0:0] GPU Not Found! PCI Config Access Fails!!!" @AmdRadeonController.cpp:2022
AMDRadeonX6000Framebuffer:
  AmdRadeonControllerNavi11::isPoweredUp()
  → AmdRadeonFramebuffer::doWake()
  → setSystemPowerState()
  → IOFramebuffer::checkPowerWork()
```

## 二、根因（关键结论）

**睡眠 panic 的根因是 AMD RX 5700 XT (Navi) 通过 Oculink 外接显卡坞接入，Oculink 链路在系统睡眠 (S3) 时掉电/断链。**

- Oculink ≠ Thunderbolt：它是 PCIe 信号直出，**没有热插拔控制器、没有标准 PCIe 电源域协商**。
- 睡眠时外接 PCIe 链路掉电 → 唤醒时 macOS 对该 GPU 执行 `doWake`，但此时 5700 XT 的 **PCI 配置空间已不可访问**（设备等于"消失"）→ AMD 驱动 `doGPUPanic` → 内核崩溃。
- **这与 macOS 睡眠本身、AMD 驱动版本、kext、boot-args 均无关**，是 Oculink eGPU 与 macOS 睡眠电源管理的架构性不兼容。

### 验证证据
移除 5700 XT、改用内置 **RX 550（Device ID 0x67ff，直连主板 PCIe）** 后，实测睡眠/唤醒日志完全干净：
```
Wake  DarkWake to FullWake ... due to HID Activity        （多次成功唤醒）
零 Failure during wake / 零 GPU Not Found / 零 panic
```
→ 证实 panic 由 Oculink 外接链路掉电引起，直连 PCIe 显卡无此问题。

## 三、硬件与配置上下文

| 项目 | 值 |
|------|-----|
| 外接显卡 | AMD RX 5700 XT (Navi, 0x731f)，**Oculink 显卡坞接入** |
| 内置显卡 | AMD RX 550 (0x67ff)，直连主板 PCIe |
| boot-args | `keepsyms=1 debug=0x100 brcmfx-country=HK ... -wegnoigpu agdpmod=pikera hibernatemode=0 -v -nvmefoff brcmfx-driver=2 brcmfx-delay=15000 brcmfx-aspm=0 -brcmfxdbg` |
| 关键 boot-arg | `-wegnoigpu`（禁用 Intel 核显，显示走独显）、`agdpmod=pikera` |

> 注意：`-wegnoigpu` 禁用了核显，导致 **vPro/AMT KVM 无法显示 macOS 桌面画面**（KVM 依赖核显帧缓冲），远程排查需改用 SSH + 日志。

## 四、解决方案

### 方案 A：禁用系统睡眠（接 Oculink eGPU 时的可靠规避）
适用：**必须使用 Oculink 外接 5700 XT** 时。唯一 100% 可靠的方案——从源头杜绝外接 GPU 经历睡眠掉电。

两层落地：
1. 运行时策略：
   ```bash
   sudo pmset -a disablesleep 1 sleep 0 standby 0 autopoweroff 0 powernap 0 hibernatemode 0
   ```
2. 开机固化（防 OTA 更新 / NVRAM 重置失效）——LaunchDaemon `/Library/LaunchDaemons/com.local.disablesleep.plist`：
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key><string>com.local.disablesleep</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/pmset</string><string>-a</string>
           <string>disablesleep</string><string>1</string>
           <string>sleep</string><string>0</string>
           <string>standby</string><string>0</string>
           <string>autopoweroff</string><string>0</string>
           <string>powernap</string><string>0</string>
           <string>hibernatemode</string><string>0</string>
       </array>
       <key>RunAtLoad</key><true/>
       <key>StandardErrorPath</key><string>/var/log/disablesleep.log</string>
   </dict>
   </plist>
   ```
   安装：
   ```bash
   sudo cp <plist> /Library/LaunchDaemons/com.local.disablesleep.plist
   sudo chown root:wheel /Library/LaunchDaemons/com.local.disablesleep.plist
   sudo chmod 644 /Library/LaunchDaemons/com.local.disablesleep.plist
   sudo launchctl load -w /Library/LaunchDaemons/com.local.disablesleep.plist
   ```

验证（关键标志）：
```bash
pmset -g | grep -i SleepDisabled    # 期望: SleepDisabled  1
```
- `SleepDisabled 1` = 方案生效；菜单栏点睡眠/合盖/空闲超时均不再进 S3。
- 显示器息屏（displaysleep）仍正常，GPU 持续供电，安全。
- LaunchDaemon 是 `RunAtLoad` 一次性任务，`launchctl list` 不显示它属正常。

回滚：
```bash
sudo launchctl unload -w /Library/LaunchDaemons/com.local.disablesleep.plist
sudo rm /Library/LaunchDaemons/com.local.disablesleep.plist
sudo pmset -a disablesleep 0 sleep 1
```

### 方案 B：改用直连 PCIe 显卡（根治）
拔掉 Oculink 外接 5700 XT，使用内置 RX 550（或任何直插主板 PCIe 的显卡）→ 睡眠唤醒恢复正常，无需禁睡眠。**已实测验证有效。**

### 方案 C：BIOS 层（治本补充，未实测）
关闭对应 PCIe 槽 / Oculink 通道的 ASPM、L1 Substates、PEG Power Saving。可降低概率，但 Navi eGPU 唤醒历来不稳，不能单独依赖。

## 五、当前状态（2026-06-24）
- 已断开 5700 XT，使用内置 RX 550，睡眠正常。
- 方案 A 已**完全回滚**：`SleepDisabled 0`、`sleep 1`、LaunchDaemon 已删除。
- 系统恢复正常睡眠节能。

## 六、经验速查

| 场景 | 处置 |
|------|------|
| 重新接回 Oculink 5700 XT，睡眠又崩 | 重新启用方案 A（禁睡眠 + LaunchDaemon） |
| 想保留睡眠节能 | 用直连 PCIe 显卡（方案 B），勿用 Oculink eGPU |
| 排查唤醒 panic | 看 `pmset -g log \| grep "Failure during wake"` + `/Library/Logs/DiagnosticReports/Kernel-*.panic` |
| 远程排查但 KVM 黑屏 | 因 `-wegnoigpu` 禁核显，改用 SSH + 日志，勿依赖 AMT KVM 画面 |
| 判定睡眠是否真生效 | 认准 `pmset -g` 里的 `SleepDisabled` 标志（1=禁睡眠 / 0=可睡眠） |

## 七、诊断命令备忘
```bash
# 唤醒失败 / GPU panic 记录
pmset -g log | grep -iE "Failure during wake|GPU Not Found|setPowerState"
# 睡眠/唤醒事件
pmset -g log | grep -iE "Entering Sleep|DarkWake to FullWake|Wake from"
# 当前电源策略
pmset -g
# 阻止睡眠的进程断言（caffeinate / screensharingd 等）
pmset -g assertions | grep -iE "PreventSystemSleep|PreventUserIdleSystemSleep"
# 当前显卡
system_profiler SPDisplaysDataType | grep -iE "Chipset|Device ID"
# 内核 panic 报告
ls -lt /Library/Logs/DiagnosticReports/*.panic
```
