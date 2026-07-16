# 代码清理记录

对本仓库（ZMK 分体键盘固件，board：`planck_left` / `planck_right`）做的死代码/冗余配置清理记录与后续待办。

## 已完成（本轮，纯删除死代码，不影响编译产物）

共删除 58 行，涉及 6 个文件：

| 文件 | 清理内容 |
|------|----------|
| `config/planck.keymap` | 注释掉的 `chosen { zmk,physical-layout ... }` 块（已在 `.dts` 中正式设置） |
| `config/boards/arm/planck/planck.keymap` | 同上的注释块 |
| `config/boards/arm/planck/Kconfig.defconfig` | 空的 `if ZMK_DISPLAY` 块、整段 `if LVGL` 块、`ZMK_WIDGET_WPM_STATUS` 注释、无对应设备的 `I2C` / `SPI` 强制开启 |
| `config/planck.conf` | 注释掉的 `CONFIG_ZMK_STUDIO_TRANSPORT_BLE_PREF_LATENCY` |
| `config/boards/arm/planck/planck_left_defconfig` | `CONFIG_SPI=y` 及灯带残留注释（灯带已移除，无 SPI 设备） |
| `config/boards/arm/planck/planck_right_defconfig` | `CONFIG_SPI=y` |

说明：`SPI` / `I2C` 是早期挂载屏幕、可寻址灯带时留下的配置，当前设备树里已无任何 SPI / I2C 设备节点，故属死配置。

## 待办 TODO

### 1. 修正 DCDC 高压配置（建议修正，非删除）

`config/boards/arm/planck/Kconfig` 中 `BOARD_ENABLE_DCDC_HV` 是从上面复制粘贴而来，错误地 `select SOC_DCDC_NRF52X`（与主稳压器开关重复），应改为：

```
config BOARD_ENABLE_DCDC_HV
    bool "Enable High Voltage DCDC mode"
    select SOC_DCDC_NRF52X_HV
    default y
```

依据：设备树使用 `zmk,battery-nrf-vddh`（`planck.dtsi`），说明电池经 **VDDH 高压引脚**供电，芯片高压稳压器（REG0）在工作。改对后高压那一路以 DCDC 模式运行（而非默认 LDO），更省电、发热更低。

### 2. 清理遗留的 board 级 keymap（需先确认）

存在两个同名 keymap：

- `config/planck.keymap`：持续维护中（近期多次提交）。
- `config/boards/arm/planck/planck.keymap`：自初始提交 `add all file` 后未再改动，疑似遗留默认文件（其中还引用了设备树里并不存在的 `&ext_power` 节点）。

⚠️ ZMK 按 **board 名**查找 keymap（`config/<board>.keymap`），而 board 名为 `planck_left` / `planck_right`，与两个文件名均不匹配。删除前请查看 GitHub Actions 构建日志中的 `-- Using keymap file: ...` 一行，确认实际生效的是哪个，再删除冗余的那一个。

### 3. 核实 `CONFIG_ZMK_EXT_POWER`（疑似死配置）

两个 defconfig 开启了 `CONFIG_ZMK_EXT_POWER=y`，但设备树中没有任何 `zmk,ext-power` 节点，该配置可能无实际作用，待确认后决定是否移除。

## 已确认无需处理

- `config/west.yml` 中的 `zmk-tog-io` 依赖：**确认已使用**，保留。
- 其余文件（`build.yaml`、各 `.dts` / `.dtsi`、`planck.json`、`board.yml`、`planck.yaml`、`board.cmake` 等）均为构建所必需。
