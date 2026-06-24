#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校正 /Library/Preferences/com.apple.windowserver.plist：
把外接显示器 (DisplayProductID=17226, DisplayVendorID=19587) 的所有布局条目
统一为 1600x900，使登录界面命中任意布局组都落到 1600x900。

做法：在所有 DisplayAnyUserSets 布局组里找到该显示器的 1600x900 模板条目，
然后把同一显示器的其它分辨率条目（如 1280x720）整条替换为模板内容
（保留各自的 OriginX/OriginY/Unit/IODisplayLocation 等位置信息）。

用法：
  sudo python3 force-login-1600x900.py            # 实际修改（自动先备份）
  sudo python3 force-login-1600x900.py --dry-run   # 只打印将要做的改动
"""
import plistlib, shutil, sys, time, copy

PLIST = "/Library/Preferences/com.apple.windowserver.plist"
TARGET_VENDOR = 19587      # 0x4c83
TARGET_PRODUCT = 17226     # 0x434a
WANT_W, WANT_H = 1600, 900
# 位置/拓扑相关键不从模板覆盖，保留条目自身的值
KEEP_KEYS = {
    "OriginX", "OriginY", "Unit", "IODisplayLocation", "DisplayID",
    "MirrorID", "Mirrored", "UnmirroredOriginX", "UnmirroredOriginY",
    "LimitsOriginX", "LimitsOriginY", "UnmirroredLimitsOriginX",
    "UnmirroredLimitsOriginY",
}

def is_target(entry):
    return (isinstance(entry, dict)
            and entry.get("DisplayProductID") == TARGET_PRODUCT
            and entry.get("DisplayVendorID") == TARGET_VENDOR)

def main():
    dry = "--dry-run" in sys.argv
    with open(PLIST, "rb") as f:
        data = plistlib.load(f)

    sets = data.get("DisplayAnyUserSets")
    if not isinstance(sets, list):
        print("ERROR: DisplayAnyUserSets 不存在或格式异常")
        sys.exit(1)

    # 1) 找到 1600x900 模板条目
    template = None
    for grp in sets:
        for entry in (grp if isinstance(grp, list) else []):
            if is_target(entry) and entry.get("Width") == WANT_W and entry.get("Height") == WANT_H:
                template = entry
                break
        if template:
            break
    if template is None:
        print("ERROR: 未找到该显示器的 1600x900 模板条目，请先在桌面选过一次 1600x900")
        sys.exit(1)

    # 2) 替换其它分辨率条目
    changed = 0
    for grp in sets:
        if not isinstance(grp, list):
            continue
        for i, entry in enumerate(grp):
            if is_target(entry) and not (entry.get("Width") == WANT_W and entry.get("Height") == WANT_H):
                old = f'{entry.get("Width")}x{entry.get("Height")}'
                new_entry = copy.deepcopy(template)
                for k in KEEP_KEYS:
                    if k in entry:
                        new_entry[k] = entry[k]
                grp[i] = new_entry
                changed += 1
                print(f"  布局组条目: {old} -> {WANT_W}x{WANT_H}")

    if changed == 0:
        print("无需改动：该显示器所有条目已是 1600x900")
        return

    if dry:
        print(f"[dry-run] 将修改 {changed} 个条目，未写入文件")
        return

    bak = f"{PLIST}.bak.{int(time.time())}"
    shutil.copy2(PLIST, bak)
    print(f"已备份: {bak}")
    with open(PLIST, "wb") as f:
        plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)
    print(f"已修改 {changed} 个条目并写回 {PLIST}")
    print("请重启验证登录界面分辨率。回滚: sudo cp <上述.bak> " + PLIST + " 后重启")

if __name__ == "__main__":
    main()
