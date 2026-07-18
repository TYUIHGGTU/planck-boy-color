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

| 字节  | 含义                                                     |
| ----- | -------------------------------------------------------- |
| 0     | 固定 `0xAB`（命令：设置 LED）                            |
| 1     | bitmask：bit0=LED0(蓝) bit1=LED1(红) bit2=LED2(绿)，1=亮 |
| 2..31 | 忽略                                                     |

report 无 report ID，故 WebHID 用 `sendReport(0, data)`。

## 涉及文件

| 文件                                   | 作用                                                            |
| -------------------------------------- | --------------------------------------------------------------- |
| `config/west.yml`                      | 新增 `zzeneg/zmk-raw-hid` 依赖                                  |
| `zephyr/module.yml`                    | 让仓库根成为 ZMK 模块（CI 自动作为 `ZMK_EXTRA_MODULES`）        |
| `CMakeLists.txt` / `Kconfig`（仓库根） | 模块构建入口与配置项 `PLANCK_LED_CONTROL` / `PLANCK_LED_STATUS` |
| `src/led_control.c`                    | 核心：收 Raw HID 驱动 LED + 电量/连接状态闪烁 + 优先级仲裁      |
| `config/planck_left.conf`              | 只对左板开启 `RAW_HID` / 第二 HID 接口 / 本模块 / 电量上报      |
| `.github/workflows/build.yml`          | 把根模块文件纳入 CI 触发路径                                    |
| `tools/led-web/index.html`             | WebHID 控制网页                                                 |

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

## 实现中的关键发现

这些是排查过程中确认的仓库现状，对后续维护很重要：

1. **`config/planck.conf` 从未生效（死配置）。** ZMK 按 board 名加载 `<board>.conf`，而 board 名是 `planck_left` / `planck_right`，与文件名 `planck.conf` 都不匹配（keymap 用的是正确的 `planck_left.keymap`）。因此其中的 `CONFIG_PWM`、`CONFIG_RGBLED_WIDGET`、`CONFIG_ZMK_BATTERY_REPORTING` 等**一直没被编进固件**。
2. **状态灯 widget 其实从未启用。** 由上一条，`rgbled-widget` 从未真正占用这 3 颗 LED——之前“被 widget 占用”的判断不成立。
3. **`&tog_io` 当前点不亮灯。** `zmk-tog-io` 走 PWM（`pwm_set_dt`），需要 `CONFIG_PWM=y`，而该配置只在失效的 `planck.conf` 里，所以 BLE 层的 `&tog_io` 实际是空操作。
4. **同一组引脚被同时声明为 PWM 与 GPIO LED。** `leds_left.dtsi` 里 `pwmleds`(pwm_led0..2) 与 `gpio-leds`(led0..2) 用的是同一批引脚（P0.09 / P1.06 / P1.04）。本方案不开 PWM、直接用 GPIO，避开了引脚归属冲突。
5. **仓库根即 ZMK 模块的构建机制。** ZMK 的 `build-user-config.yml` 检测到仓库根有 `zephyr/module.yml` 时，会自动 `-DZMK_EXTRA_MODULES=<repo root>`，因此自研 C 代码可以直接放仓库根被编译，无需另开仓库。
6. **Raw HID 方向可靠性不对称。** “主机→键盘”（本功能用到）经控制端点 `SET_REPORT` 稳定可用；“键盘→主机”在旧 USB stack 上有已知发送失败（-11）问题。
7. **WebHID 仅 USB 可靠。** 见“已知限制”。

## 后续可优化项（backlog）

按价值/成本粗排，供后续迭代参考：

- **清理死配置。** 把 `planck.conf` 里仍需要的项迁到 `planck_left.conf` / `planck_right.conf`，然后删除 `planck.conf`，消除“看着生效实则无效”的坑（另见 [CLEANUP.md](./CLEANUP.md)）。
- **亮度控制。** 现为纯开关。若接受用 PWM，可扩展协议加入每灯亮度（0–255），做呼吸/渐变。
- **fail-safe / 心跳。** 可选：主机断开或一段时间无 report 后自动回到某个默认状态，避免“忘了关”。
- **更丰富的下行协议。** 当前只有 `0xAB=设置`。可加入闪烁模式、单灯操作、查询等命令字。
- **蓝牙控灯。** WebHID 下发到 BLE 键盘不可靠；若要蓝牙可控，需改为本地程序用系统 HID API 或走 BLE GATT，成本与不确定性较高。
- **固定 ZMK 版本。** 目前 `zmk` / `zmk-raw-hid` 跟随 `main`，上游破坏性变更可能导致构建失败或行为变化。稳定后建议在 `config/west.yml` 固定到发布版本。
- **对称支持右板。** 如需右板也能网页控灯，为 `planck_right` 建对应 `planck_right.conf` 并复用同一模块（模块已按 `CONFIG_PLANCK_LED_CONTROL` 守卫，右板默认不启用）。
- **与 tog_io 收敛。** 既然 `&tog_io` 当前无效，可考虑移除 keymap 中的 `&tog_io`，统一由本模块管理 LED，避免概念重复。

## 可借鉴的协议 / 健壮性模式（参考 arkey）

同类开源项目 [shuhari04/arkey](https://github.com/shuhari04/arkey) 用 QMK Raw HID 做了成熟的「主机 → 键盘」灯效通道，其设计对本方案演进有直接参考价值（arkey 为 PolyForm Noncommercial，仅借鉴设计，不可照抄代码商用）：

- **能力协商（Hello / capabilities 握手）。** arkey 主机先发 Hello，校验固件 `layoutHash`、LED 数、feature flag，匹配后才开启完整控制，不匹配退回普通键盘。本方案当前 `0xAB` 是「无脑设置」，可加一条查询命令返回固件版本 / LED 数 / 能力位，避免主机程序与固件错配。
- **心跳 + fail-open（对应本文 backlog 的「fail-safe / 心跳」）。** arkey 固件在「心跳丢失 / 传输切换 / daemon 退出」后自动恢复到之前的 RGB 状态。arkey 实证了这一项值得做——主机程序崩溃或忘关时，LED 能自动回到默认态。
- **staged commit（暂存 + 原子提交）。** 多帧灯效先暂存、最后一帧带 commit 位再整体切换，避免刷新途中闪烁。本方案若将来扩展到多灯 / 动画，可借此避免中间态。
- **更完整的帧结构。** arkey 32 字节帧为 `magic(0xB0 0x47) + 版本 + opcode + payload_len + sequence + payload`；比当前单字节 `0xAB` 命令更利于扩展（版本协商、多命令字、序列号防重放）。本文「更丰富的下行协议」一项可朝此演进。

> 状态源侧（消费 codex app-server 事件 → 决定点哪颗灯）的映射规则见 [codex-agent-loop-hooks-app-server.md](../codex/codex-agent-loop-hooks-app-server.md) 第 7 节；整体还原度评估见 [codex-micro-parity.md](../codex/codex-micro-parity.md)。
