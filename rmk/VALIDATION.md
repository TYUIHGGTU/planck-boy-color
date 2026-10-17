# 验证

## 自动化检查

运行：

```sh
python3 tests/validate_config.py
python3 tests/validate_hardware_revisions.py
cargo fmt --check

cargo build --release --bin central --bin peripheral \
  --no-default-features --features hw-r1
RMK_REVISION=r1 cargo make uf2
python3 tests/validate_artifacts.py --revision r1

cargo build --release --bin central --bin peripheral \
  --no-default-features --features hw-r2
RMK_REVISION=r2 cargo make uf2
python3 tests/validate_artifacts.py --revision r2
```

静态校验器会把 RMK 的直连引脚顺序与 ZMK 设备树对照，核对分体几何与偏移，检查两个编码器及 RGB 引脚归属，并拒绝意外的 `rgb_ug` 或 `ext_power` 声明。产物校验器检查 UF2 帧结构、nRF52840 系列 ID、块编号以及应用程序地址范围。

版本校验器从 ZMK DTSI 推导每种颜色的 PWM 通道，并与对应的 RMK 配置对照。它还会确认两个版本中全部 46 路开关输入仍为低电平有效且带上拉。

## 首次硬件点亮

这些检查需要实体键盘，无法仅从源码推断：

- 确认 UF2 bootloader 接受从 `0x1000` 开始的应用程序。
- 在测试休眠之前，确认左右两半都能通过 UF2 或 SWD 恢复。
- 对匹配的 PCB，分别用 r1 和 r2 固件重复矩阵测试。
- 在 Vial 矩阵测试中，按下全部 44 个可见按键以及两个编码器按压开关。
- 确认编码器按压产生的动作与原先 ZMK 组合键位相同。
- 将两个编码器各向转动一格，并核对音量方向。
- 配对全部三个主机配置；测试配置选择、长按重新配对、下一个/上一个配置，以及清除当前配置。
- 确认只有中央半边向主机广播，且名称分别为 r1 的 `PBC R1` 和 r2 的 `PBC R2`。
- 拔掉 USB，验证左右两半都能通过中央半边向主机发送 BLE 输入。
- 分别给左右半边断电再上电，验证分体自动重连。
- 核对左右 Battery Service 数值是否合理。
- 让键盘进入空闲休眠，然后从每一半唤醒，并记录延迟与电流。
- 对两套版本专用固件包，分别验证每一半的 RGB 通道顺序、层颜色以及休眠熄灭行为。
- 清除持久化存储后，走一遍全部四层和九个组合键。

## 预期现象

- 基础层：状态灯熄灭
- CHAR 层：琥珀色状态
- ARROW 层：蓝色状态
- BLE 层：品红色状态
- 休眠中：状态灯熄灭
- 在 BLE subrating 生效时，从外设半边唤醒可能明显慢于从中央半边唤醒；RMK 文档给出的最坏情况约为 232 ms（主机已连接时）。

进行实物验证时，请在本文件中记录板卡版本、bootloader 版本、测得的空闲电流，以及任何反接的编码器或 RGB 通道。
