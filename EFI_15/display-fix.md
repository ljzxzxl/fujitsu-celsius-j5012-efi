# 显示器问题修复记录（RX 550 外接显示器）

> 机型：Fujitsu CELSIUS J5012 黑苹果，使用 `EFI_15` 引导，显卡 RX 550。
> 外接小尺寸显示器原生分辨率 3200×1800。
> 本文档沉淀两个显示相关问题的根因与完整解决方案，便于重装/升级后快速恢复。
> 注意：所有改动均在 **macOS 系统层**，OpenCore 引导配置（`EFI_15/OC/config.plist`）**零改动**。

## 显示器标识（ioreg 读取）

| 项 | 十进制 | 十六进制 | Override 用值 |
|----|--------|----------|----------------|
| DisplayVendorID | 19587 | 0x4C83 | `4c83` |
| DisplayProductID | 17226 | 0x434A | `434a` |

读取命令：
```bash
ioreg -lw0 | grep -i "DisplayVendorID\|DisplayProductID"
```

---

## 问题一：开机默认最高分辨率 3200×1800，文字过小

### 现象
显示器默认以最高分辨率 3200×1800 点亮，尺寸又小，登录界面与桌面文字极小难以阅读。期望登录界面与桌面固定为 **1600×900 HiDPI** 并重启持久保持。

### 根因 / 思路
macOS 按 `DisplayVendorID-xxxx/DisplayProductID-xxxx` 在 `/Library/Displays/Contents/Resources/Overrides/` 查找显示器覆盖配置。通过注入 `scale-resolutions`，可新增一个 **1600×900 HiDPI** 模式（像素缓冲 3200×1800，正好 2 倍，文字大且清晰）。Intel 平台支持 sub‑4K HiDPI（Apple Silicon 才有 4K 以下限制）。选中一次后写入 `com.apple.windowserver.plist`，登录界面读同一份偏好，从而持久。

### scale-resolutions 字节格式
每个 HiDPI 项 16 字节：`[width 4B BE][height 4B BE][00 00 00 01][00 20 00 00]`，width/height 为像素缓冲尺寸（逻辑分辨率 ×2）。

- 1600×900 HiDPI → 像素 3200×1800：`00000c80 00000708 00000001 00200000` → Base64 `AAAMgAAABwgAAAABACAAAA==`
- 1600×900 普通（8B）：`00000640 00000384` → Base64 `AAAGQAAAA4Q=`

计算脚本：
```python
import base64, struct
def hidpi(w,h):
    return base64.b64encode(struct.pack('>II',w*2,h*2)+bytes([0,0,0,1,0,0x20,0,0])).decode()
def normal(w,h):
    return base64.b64encode(struct.pack('>II',w,h)).decode()
print(hidpi(1600,900), normal(1600,900))
```

### 解决方案：写入显示器 Override 文件

目标文件：`/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-4c83/DisplayProductID-434a`

文件内容：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>DisplayProductName</key>
	<string>Display 1600x900 HiDPI</string>
	<key>DisplayVendorID</key>
	<integer>19587</integer>
	<key>DisplayProductID</key>
	<integer>17226</integer>
	<key>scale-resolutions</key>
	<array>
		<data>AAAMgAAABwgAAAABACAAAA==</data> <!-- 1600x900 HiDPI (px 3200x1800) -->
		<data>AAAGQAAAA4Q=</data>            <!-- 1600x900 normal (fallback) -->
	</array>
</dict>
</plist>
```

安装命令（终端执行，需 sudo）：
```bash
DST_DIR="/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-4c83"
sudo mkdir -p "$DST_DIR"
# 用上面的内容写入 $DST_DIR/DisplayProductID-434a
sudo chown root:wheel "$DST_DIR/DisplayProductID-434a"
sudo chmod 0644 "$DST_DIR/DisplayProductID-434a"
plutil -lint "$DST_DIR/DisplayProductID-434a"   # 应输出 OK
```

### 生效与持久化
1. 重启，「系统设置 > 显示器」缩放列表中出现 1600×900（HiDPI）选项（看不到时按住 Option 点「缩放」看完整列表）。
2. 选中 1600×900 → 桌面立即变 HiDPI，并写入 `com.apple.windowserver.plist`。
3. 此后重启/注销，登录界面与桌面均持久保持 1600×900。

### 验证（已实测通过）
```bash
system_profiler SPDisplaysDataType | grep -iA2 "Resolution"
# Resolution: 1600 x 900 ; UI Looks like: 1600 x 900 @ 60Hz ; 30-Bit Color → HiDPI 生效
```

### 回滚
删除 `/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-4c83/DisplayProductID-434a` 后重启。

---

## 问题二：颜色描述文件出现重复的 “Display 1600x900 HiDPI”

### 现象
加入 Override（给显示器起名）后，「系统设置 > 显示器 > 颜色描述文件」出现**两个同名** `Display 1600x900 HiDPI`：

```
Display 1600x900 HiDPI-ACE37841-A6E8-DD39-4F02-D1F8ECCA1BAA.icc   ← 真实 UUID（保留）
Display 1600x900 HiDPI-FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF.icc    ← 全 F 兜底（多余）
```

> 加 Override 前，全 F 文件名为 `HDMI-FFFFFFFF-...`，在设置里显示为 “unknown display”。

### 根因 / 思路
显示器 EDID 缺少唯一序列号，macOS **每次开机**都会为它额外生成一个 **全 F UUID** 的兜底 ColorSync 配置。Override 提供了显示器名后，该兜底文件继承同名 → 表现为重复项。**单纯删除无法永久解决，重启即复现**（已验证）。

治本方案是给 EDID 注入序列号（WhateverGreen），但需改 `config.plist` 注入 EDID、有黑屏风险，且违背“引导不动 EFI”原则，故不采用。采用**开机自动清理（方案 A）**。

### 解决方案：LaunchDaemon 开机自动清理全 F 文件

脚本 `/usr/local/bin/clean-display-fallback-icc.sh`：
```bash
#!/bin/bash
# 删除显示器全 F 兜底 ColorSync 配置（仅清理 -FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF.icc）
DIR="/Library/ColorSync/Profiles/Displays"
LOG="/var/log/clean-display-icc.log"
shopt -s nullglob
for f in "$DIR"/*-FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF.icc; do
    rm -f "$f" && echo "$(date '+%F %T') removed: $f" >> "$LOG"
done
exit 0
```

LaunchDaemon `/Library/LaunchDaemons/com.local.clean-display-icc.plist`：

> 关键：必须用 `WatchPaths` 监听 `Displays` 目录。仅用 `RunAtLoad` 会失效——WindowServer 常在脚本执行之后才重新生成全 F 文件，存在时间竞争；且需正确 `bootstrap` 才能开机自启（`launchctl load` 是临时会话级，重启后不生效）。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>com.local.clean-display-icc</string>
	<key>ProgramArguments</key>
	<array>
		<string>/usr/local/bin/clean-display-fallback-icc.sh</string>
	</array>
	<key>RunAtLoad</key>
	<true/>
	<key>WatchPaths</key>
	<array>
		<string>/Library/ColorSync/Profiles/Displays</string>
	</array>
</dict>
</plist>
```

安装命令（终端执行，需 sudo）：
```bash
# 写入上面两个文件后：
sudo chown root:wheel /usr/local/bin/clean-display-fallback-icc.sh
sudo chmod 755 /usr/local/bin/clean-display-fallback-icc.sh
sudo chown root:wheel /Library/LaunchDaemons/com.local.clean-display-icc.plist
sudo chmod 644 /Library/LaunchDaemons/com.local.clean-display-icc.plist
sudo launchctl bootout system/com.local.clean-display-icc 2>/dev/null   # 卸载旧的（若有）
sudo launchctl bootstrap system /Library/LaunchDaemons/com.local.clean-display-icc.plist  # 正确开机自启
sudo launchctl enable system/com.local.clean-display-icc
sudo /usr/local/bin/clean-display-fallback-icc.sh                       # 立即清一次
```

### 验证（已实测通过）
- `/Library/ColorSync/Profiles/Displays/` 仅剩 `Display 1600x900 HiDPI-ACE37841-...icc`
- `/var/log/clean-display-icc.log` 有 `removed: ...-FFFFFFFF-....icc` 记录
- `sudo launchctl print system/com.local.clean-display-icc` 显示 `state = spawn scheduled` 且含 `WatchPaths` → 目录变化即触发清理

### 回滚
```bash
sudo launchctl bootout system/com.local.clean-display-icc
sudo rm /Library/LaunchDaemons/com.local.clean-display-icc.plist
sudo rm /usr/local/bin/clean-display-fallback-icc.sh
```

---

## 问题三：登录界面仍以 3200×1800 点亮（登录后才变 1600×900）

### 现象
桌面已稳定 1600×900，但**登录界面（用户登录前）仍以最高分辨率 3200×1800 显示**，登录后才切到 1600×900。经确认与 WiFi 修复无关（`windowserver.plist` 未被其改动）。

### 根因 / 思路
登录窗口读取全局 `/Library/Preferences/com.apple.windowserver.plist` 的 `DisplayAnyUserSets`。该文件里同一显示器（DisplayProductID=17226 / VendorID=19587）存在**多组布局记录**，其中单屏组是 1600×900，但多屏布局组里残留一条 **1280×720**。登录窗口早期点亮时未稳定命中 1600×900，回退到面板最高物理分辨率。

解决思路：把该显示器在所有布局组里的条目**统一为 1600×900**，使登录窗口命中任意布局都落到 1600×900。

### 解决方案：校正全局 windowserver.plist

用脚本以 1600×900 那条 mode 为模板，覆盖同一显示器的其它分辨率条目（保留各自 OriginX/OriginY/Unit/IODisplayLocation 等位置信息），写入前自动备份。

脚本 `force-login-1600x900.py`（关键逻辑）：
- 定位 `DisplayAnyUserSets` 中 `DisplayProductID==17226 && DisplayVendorID==19587 && Width==1600 && Height==900` 的条目作模板；
- 把同显示器其它分辨率条目整条替换为模板，仅保留位置/拓扑键；
- `shutil.copy2` 备份为 `windowserver.plist.bak.<时间戳>`，再以二进制 plist 写回。

执行（终端，需 sudo）：
```bash
sudo python3 force-login-1600x900.py --dry-run   # 预览将改动的条目
sudo python3 force-login-1600x900.py             # 实际修改（自动备份）
sudo plutil -lint /Library/Preferences/com.apple.windowserver.plist
sudo chown root:wheel /Library/Preferences/com.apple.windowserver.plist
sudo chmod 644 /Library/Preferences/com.apple.windowserver.plist
```

### 验证（已实测通过）
- 脚本将多屏布局组里的 1280×720 条目改为 1600×900（改动 1 条）。
- **重启后登录界面直接以 1600×900 显示**，与桌面一致 ✅
- 单纯校正偏好即已稳定，未需额外开机兜底脚本。

### 回滚
```bash
sudo cp /Library/Preferences/com.apple.windowserver.plist.bak.<时间戳> /Library/Preferences/com.apple.windowserver.plist
# 然后重启
```

> 备注：若未来重装/升级后登录界面又回退，且单纯校正偏好不稳定，可加开机兜底（`displayplacer` 在登录前强制设 1600×900 + LaunchDaemon）。本机当前无需此步。

---

## 重装 / 系统升级后的恢复清单
1. 用 `ioreg` 确认 Vendor/Product ID 是否仍为 0x4c83 / 0x434a（变了需按新 ID 重建）。
2. 重建 Override 文件（问题一）→ 重启 → 设置里选一次 1600×900。
3. 重建清理脚本 + LaunchDaemon（问题二）。
4. 桌面确认 1600×900 后，跑 `force-login-1600x900.py` 校正登录界面（问题三）。

## 注意事项
- 换显示器或换接口可能改变 Vendor/Product ID，导致 Override 失效，需重新读取并重建。
- 清理脚本严格只匹配全 F 文件名，绝不误删真实 UUID 的 ICC。
- 全程未修改 `EFI_15/OC/config.plist`，`UIScale` 等引导配置保持原状。
- `windowserver.plist` 可能在某些系统更新后被重写，登录界面回退时重跑校正脚本即可。
