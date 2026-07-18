# 网页控制 LED（planck_left）

通过网页（WebHID）经 USB 直接控制左板 3 颗板载 LED 的开灭。

## 效果

- 打开 `tools/led-web/index.html`，点“连接键盘”，即可分别点亮/熄灭 LED0(蓝)/LED1(红)/LED2(绿)，或一键全亮/全灭。
- 电量与 BLE/USB 连接状态变化时，LED 会短暂闪一下对应颜色，然后回到网页设定的状态（两者不冲突）。

## 原理

```
网页(WebHID) --32字节 report--> USB(HID 0xFF60) --> zmk-raw-hid 模块
    --> raw_hid_received_event --> src/led_control.c --> GPIO 点/灭 3 颗 LED
```

- 传输层用社区模块 [`zzeneg/zmk-raw-hid`](https://github.com/zzeneg/zmk-raw-hid)，新增一个 usage page `0xFF60` 的 HID 接口，主机可经控制端点 `SET_REPORT` 向键盘下发数据。
- 本仓库根目录是一个 ZMK 模块（`zephyr/module.yml` + `CMakeLists.txt` + `Kconfig` + `src/led_control.c`），CI 会自动作为 `ZMK_EXTRA_MODULES` 编入构建。
- LED 用 GPIO 直接驱动（复用 `leds_left.dtsi` 里的 `led0/led1/led2`，`GPIO_ACTIVE_HIGH`），不走 PWM，语义明确。

### 下行协议（主机 → 键盘）

32 字节 report：

| 字节 | 含义 |
| --- | --- |
| 0 | 固定 `0xAB`（命令：设置 LED） |
| 1 | bitmask：bit0=LED0(蓝) bit1=LED1(红) bit2=LED2(绿)，1=亮 |
| 2..31 | 忽略 |

report 无 report ID，故 WebHID 用 `sendReport(0, data)`。

## 只改了左板

- 全部开关放在 `config/planck_left.conf`（ZMK 按 board 名加载 `<board>.conf`）。右板 `planck_right` 不含这些配置，行为不变。
- 注意：仓库原有的 `config/planck.conf` 文件名与 board 名（`planck_left`/`planck_right`）不匹配，**从未生效**；本功能不依赖它。

## 使用步骤

### 1. 构建固件

推送到 GitHub 后，Actions 会自动构建，产物里取 `planck_left` 的 `.uf2`。也可手动触发 workflow。

### 2. 刷写（仅左板）

进入 bootloader（一般双击复位）后，把 `planck_left*.uf2` 拷到出现的 U 盘盘符。

> 刷写有风险，务必备好可恢复的固件。

### 3. 打开网页控制

1. 用 **USB 线**连接左板到电脑（WebHID + Raw HID 只在 USB 下可靠；蓝牙不支持）。
2. 用 **Chrome 或 Edge** 打开 `tools/led-web/index.html`（本地双击打开即可，file:// 也支持 WebHID）。
3. 点“连接键盘”，在弹窗里选 `PlanckBoy L`。
4. 点各 LED 或“全亮/全灭”。

## 可调项（`config/planck_left.conf`）

- `CONFIG_PLANCK_LED_STATUS=n`：关掉状态闪烁，LED 纯由网页控制。
- `CONFIG_PLANCK_LED_STATUS_BLINK_MS`：状态闪烁时长（默认 1200ms）。

## 已知限制 / 风险

- 需 Chrome/Edge + USB；Firefox/Safari 无 WebHID。
- 本仓库 `zmk` 跟 `main` 分支，若上游改动破坏旧版 USB device stack 或事件 API，可能需要将 `config/west.yml` 里 `zmk` 与 `zmk-raw-hid` 固定到对应发布版本。
- `zmk-raw-hid` 曾有“键盘→主机发送”方向的问题（Zephyr 旧 USB stack）；本功能只用“主机→键盘”方向，不受影响，但仍建议真机验证。
