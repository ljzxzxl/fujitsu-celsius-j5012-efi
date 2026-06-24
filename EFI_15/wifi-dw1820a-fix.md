# DW1820A 无线网卡修复记录（macOS Sequoia 15.7.x）

## 症状
- `ifconfig en1` → `interface en1 does not exist`，`awdl0` 也不存在
- `ioreg -c IO80211Interface | grep -c en1` → 0
- 系统设置中 Wi-Fi 显示 `Off (forced)`，"all AirPort network services are disabled"
- 连带后果：AirDrop / Handoff / 通用剪贴板等所有依赖 AWDL 的 Continuity 功能全部失效

## 根因
不是"WiFi 被关"，而是**驱动未绑定到设备**：
- 硬件在册：PCI 设备 `pci14e4,43a3`（DW1820A / BCM4350），位于 `RP05@1C/IOPP/ARPT@0`
- 三件套 kext 均已加载：`IOSkywalkFamily`、`IO80211FamilyLegacy`、`AirportBrcmFixup`、`AirPort.BrcmNIC`
- 但 WiFi 设备节点上只挂了 `AirportBrcmFixup` 的注入桩 `FakeBrcm`，**没有真正的 `AirPort_BrcmNIC` 控制器实例**
- 原因：`AirportBrcmFixup` 对新版 macOS（15.7.x）默认不介入，必须用 `-brcmfxbeta` 显式放行其在 beta/较新系统上的补丁逻辑

## 解决方案（生效）
在 `EFI_15/OC/config.plist` 的 `boot-args` 末尾追加：
```
-brcmfxbeta
```
完整 boot-args（WiFi 相关部分）：
```
... brcmfx-country=HK ... brcmfx-driver=2 brcmfx-delay=15000 brcmfx-aspm=0 -brcmfxdbg -brcmfxbeta
```
重启后 `AirPort_BrcmNIC` 正常绑定，`en1` 与 `awdl0` 接口生成。

## 验证结果（2026-06-24，重启后）
```
en1: status active, inet 192.168.31.240, ether 30:52:cb:e7:b2:ad   ✅
ioreg IO80211Interface count = 3                                    ✅
awdl0: status active                                                ✅  (AirDrop/Handoff 骨干已起)
Wi-Fi Power (en1): On                                               ✅
Card Type: Wi-Fi (0x14E4, 0x21)  Status: Connected                 ✅
```

## 验证命令（复用）
```bash
ifconfig en1
ioreg -c IO80211Interface | grep -c en1
ifconfig awdl0
networksetup -getairportpower en1
system_profiler SPAirPortDataType | grep -iE "Card Type|Interfaces|Status"
```

## 排查过的其他候选（本次未用到，留作备选）
- Step B：移除 `brcmfx-driver=2` 让自动匹配
- Step C：去除/调小 `brcmfx-delay=15000`
- Step D：升级 IOSkywalkFamily / IO80211FamilyLegacy / AirportBrcmFixup 到最新 release
- Step E：核查 VT-d / AppleVTD / DisableIoMapper 一致性

## 注意
- ESP 上已保留备份 `config.plist.before-brcmfxbeta-*`
- 修改未触碰睡眠相关参数（`-wegnoigpu` / `agdpmod=pikera` / `hibernatemode=0`），不影响已修复的睡眠
