# PlanckBoy Color 固件

本仓库为 PlanckBoy Color 硬件版本 r1 与 r2 构建 ZMK 和 RMK 固件。

## 构建产物

一次 GitHub Actions 运行会发布四个产物：

- `planck-boy-color-zmk-r1`
- `planck-boy-color-zmk-r2`
- `planck-boy-color-rmk-r1`
- `planck-boy-color-rmk-r2`

每个产物都包含独立的左/右镜像。ZMK 称之为 `left` 和 `right`；RMK 称之为 `central` 和 `peripheral`。

不要在左右两半之间混用不同版本或不同固件框架。

蓝牙设备名称：

- RMK r1：`PBC R1`
- RMK r2：`PBC R2`
- ZMK r1：`PBC Z1`
- ZMK r2：`PBC Z2`

## 源码布局

- `config/`：共享的 ZMK 键位与板级配置
- `config/boards/arm/planck/revisions/r1`：r1 RGB PWM 映射
- `config/boards/arm/planck/revisions/r2`：r2 RGB PWM 映射
- `build/zmk/r1.yaml`、`build/zmk/r2.yaml`：ZMK 构建矩阵
- `rmk/`：共享的 RMK 固件
- `rmk/src/revisions/r1.rs`、`rmk/src/revisions/r2.rs`：RMK RGB 配置

两个版本共用同一套按键矩阵、低电平有效的开关接线、编码器、电池测量、键位以及 Flash 布局。仓库中唯一可见的差异是 RGB PWM 通道顺序。r2 的 ZMK 还会在左半边额外启用 USB ZMK Studio 传输。

RMK 的构建与烧录说明见 `rmk/README.md`。
