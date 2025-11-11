# 富士通 CELSIUS J5012 黑苹果引导

![macOS](https://img.shields.io/badge/macOS-Sequoia%2015.7.2-blue)
![macOS](https://img.shields.io/badge/macOS-Ventura%2013.7.8-blue)
![OpenCore](https://img.shields.io/badge/OpenCore-1.0.6-green)
![Celsius](https://img.shields.io/badge/Fujitsu-Celsius%20J5012-orange)

## 项目简介

本项目提供富士通 CELSIUS J5012 工作站运行macOS的完整OpenCore引导配置。支持最新的macOS 15.7.2 (Sequoia)和macOS 13.7.8 (Ventura)系统，使用OpenCore 1.0.6引导器和最新版的Kexts驱动，引导配置已经过优化，系统运行稳定。

## 硬件配置

### 基本信息
- **处理器**: 13th Gen Intel(R) Core(TM) i5-13500
- **处理器速度**: 2.5 GHz
- **核心数量**: 14核（6P+8E）
- **内存**: 64 GB DDR4 3200 MHz (4x16GB Micron)
- **显示**: Intel UHD Graphics 770 (不可用)
- **网络**: 
  - 内置有线网卡: Intel I219-V
  - 额外加装有线网卡: Intel 82576 NS
  - 无线网卡: DW1820A
  - 蓝牙: DW1820A集成
- **USB**: USB 3.2控制器
- **存储**: 系统盘已命名为"Sequoia"

## 功能兼容性

### 工作正常
- ✅ 处理器全部核心识别与Turbo Boost功能
- ✅ 内存正确识别和运行
- ✅ 有线网络（Intel I219-V和Intel 82576 NS）
- ✅ 无线网络（DW1820A）
- ✅ 蓝牙功能（DW1820A）
- ✅ USB端口（2.0/3.0/3.1）
- ✅ 系统更新
- ✅ iCloud服务
- ✅ App Store
- ✅ 音频输出
- ✅ NVMe SSD加速
- ✅ CPU温度监控
- ✅ 电池状态（如适用）

### 部分工作
- ⚠️ 睡眠/唤醒功能（时间久会睡死）
- ⚠️ iMessage/FaceTime（可能需要进一步配置序列号）
- ⚠️ 硬件加速（部分功能可用）

### 不工作
- ❌ Intel UHD Graphics 770核显

## 屏幕截图

### 系统概览
![系统概览](images/截屏2025-11-11%2022.52.17.png)

### 关于本机
![关于本机](images/截屏2025-11-11%2022.52.57.png)

### 系统信息
![系统信息](images/截屏2025-11-11%2022.56.38.png)

### 硬件详情
![硬件详情](images/截屏2025-11-11%2022.58.13.png)

### 网络配置
![网络配置](images/截屏2025-11-11%2022.58.45.png)

### 系统信息1
![系统信息1](images/截屏2025-11-11%2022.59.31.png)

### 系统信息2
![系统信息2](images/截屏2025-11-11%2022.59.37.png)

## EFI目录说明

本项目包含两个EFI文件夹，分别用于不同版本的macOS：

### EFI_13
适用于macOS Ventura 13.7.8的引导配置
- OpenCore 1.0.6
- 针对Ventura优化的config.plist
- 完整的ACPI、Drivers和Kexts文件

### EFI_15
适用于macOS Sequoia 15.7.2的引导配置
- OpenCore 1.0.6
- 针对Sequoia优化的config.plist
- 完整的ACPI、Drivers和Kexts文件
- 包含富士通专用EVTE目录

## Kexts驱动说明

### 核心驱动
- **Lilu.kext** - 核心补丁框架，其他许多驱动的基础
- **VirtualSMC.kext** - SMC模拟器，黑苹果必备
- **WhateverGreen.kext** - 显卡补丁，解决显示问题
- **AppleALC.kext** - 音频驱动，提供原生音频支持

### 网络驱动
- **IntelMausi.kext** - Intel网卡驱动（I219-V和82576 NS）
- **AirportBrcmFixup.kext** - 无线网卡补丁
- **BrcmBluetoothInjector.kext** - 蓝牙注入
- **BrcmFirmwareData.kext** - 蓝牙固件数据
- **BrcmFirmwareRepo.kext** - 蓝牙固件仓库
- **BrcmPatchRAM3.kext** - 蓝牙驱动
- **BlueToolFixup.kext** - 蓝牙工具修复

### 电源管理
- **CPUFriend.kext** - CPU电源管理优化
- **CpuTopologyRebuild.kext** - CPU拓扑结构重建
- **HibernationFixup.kext** - 修复睡眠唤醒问题

### 存储驱动
- **NVMeFix.kext** - NVMe SSD优化
- **CtlnaAHCIPort.kext** - AHCI存储端口修复

### USB驱动
- **USBInjectAll.kext** - 注入所有USB端口
- **USBToolBox.kext** - USB端口管理工具
- **UTBMap.kext** - USB端口映射
- **XHCI-unsupported.kext** - 解决XHCI控制器问题

### 其他重要驱动
- **AMFIPass.kext** - 绕过AMFI安全验证
- **AppleMCEReporterDisabler.kext** - 禁用MCE报告器
- **IntelMausi.kext** - Intel有线网络驱动
- **RestrictEvents.kext** - 限制特定事件和功能
- **SMCProcessor.kext** - CPU信息监控
- **SMCSuperIO.kext** - 超级IO设备监控

## 富士通CELSIUS J5012 BIOS设置指南

### 必要设置
1. **开机按F2进入BIOS**
2. **Security** 选项卡:
   - 禁用 **Secure Boot**
   - 禁用 **Intel SGX**
3. **Boot** 选项卡:
   - 将启动模式设置为 **UEFI**
   - 禁用 **Legacy Boot**
4. **Advanced** 选项卡:
   - **CPU Configuration**:
     - 启用 **Intel Virtualization Technology**
     - 禁用 **Intel SGX Control**
   - **System Agent (SA) Configuration**:
     - 禁用 **VT-d** (如遇到启动问题)
   - **Devices**:
     - 启用 **USB Configuration** 中的所有USB端口
     - 设置 **XHCI Hand-off** 为 **Enabled**
5. **保存设置并退出** (按F10)

## 安装指南

### 准备工作
1. 准备一个至少16GB的U盘
2. 从Apple官网下载macOS安装程序 (Ventura或Sequoia)
3. 使用[BalenaEtcher](https://www.balena.io/etcher/)或其他工具制作安装U盘
4. 使用[OpenCore Configurator](https://mackie100projects.altervista.org/opencore-configurator/)挂载EFI分区
5. 将对应版本的EFI文件夹内容复制到U盘的EFI分区

### 安装步骤
1. 开机按F12选择启动设备
2. 选择U盘启动
3. 在OpenCore引导界面选择macOS安装程序
4. 进入macOS恢复模式后，使用磁盘工具格式化目标磁盘为APFS格式
5. 安装macOS系统
6. 安装完成后，使用OpenCore Configurator挂载系统EFI分区
7. 复制对应版本的EFI文件夹内容到系统EFI分区
8. 重启电脑，享受黑苹果系统

### 配置调整
- 可以使用OpenCore Configurator根据个人需求调整config.plist
- 建议保留原始EFI备份以便恢复
- 首次启动后建议使用[GenSMBIOS](https://github.com/corpnewt/GenSMBIOS)生成唯一的序列号和平台信息，以获得更好的iCloud服务兼容性

## 更新日志

### v1.0.6 (2024年11月)
- 更新OpenCore至1.0.6版本
- 更新所有Kexts至最新版本
- 优化macOS 15.7.2的兼容性
- 添加更多富士通CELSIUS J5012工作站特有的优化
- 修复已知问题，提升系统稳定性

### v1.0.5 (2024年10月)
- 添加对macOS 13.7.8的支持
- 初始版本发布

## 安装后优化

### 系统优化
1. **启用TRIM** (针对SSD):
   ```bash
   sudo trimforce enable
   ```
2. **优化电源管理**:
   - 确保Energy Saver设置正确
   - 调整屏幕亮度和睡眠设置以获得最佳电池寿命
3. **清理系统缓存**:
   - 定期使用系统维护工具清理缓存和日志

### 驱动管理
1. **定期更新Kexts**:
   - 关注[Acidanthera](https://github.com/acidanthera)的最新驱动更新
   - 每次大版本更新macOS前，请确保所有Kexts都已更新到兼容版本

### 性能优化
1. **禁用不必要的登录项**:
   - 在系统设置 > 用户与群组 > 登录项中移除不需要的应用
2. **优化启动项**:
   - 检查并禁用不必要的系统扩展
3. **调整虚拟内存**:
   - 根据需要调整交换文件大小

## 注意事项

1. **系统安全性**：当前系统完整性保护(SIP)处于禁用状态，如需启用请修改config.plist
2. **更新谨慎**：在更新macOS之前，请先备份EFI分区和重要数据
3. **硬件修改**：如果更换或升级硬件，可能需要重新配置EFI
4. **使用风险**：本EFI配置仅供参考和学习使用，作者不承担任何使用风险

## 故障排除

### 常见问题
- **无法启动**：
  - 检查BIOS设置，确保UEFI模式和安全启动已禁用
  - 尝试重置NVRAM (启动时按Cmd+Opt+P+R)
  - 检查config.plist是否正确配置
- **显卡问题**：
  - 如遇到显示异常，尝试添加agdpmod=pikera引导参数
  - 检查WhateverGreen.kext是否正确加载
- **网络问题**：
  - 确认IntelMausi.kext和AirportBrcmFixup.kext是否正确加载
  - 尝试重置网络设置
- **睡眠唤醒问题**：
  - 检查HibernationFixup.kext是否正确配置
  - 尝试禁用Power Nap功能
- **USB端口不工作**：
  - 检查USB驱动是否正确加载
  - 尝试调整USBToolBox和UTBMap配置
- **iMessage/FaceTime问题**：
  - 使用GenSMBIOS生成新的序列号和平台信息
  - 确保config.plist中的PlatformInfo配置正确

## 致谢

- OpenCore团队提供优秀的引导器
- 黑苹果社区提供的技术支持和驱动开发
- Dortania的[OpenCore安装指南](https://dortania.github.io/OpenCore-Install-Guide/)

---

**免责声明**：本项目仅用于技术研究和学习目的，请确保您的macOS使用符合Apple的许可协议。