# PlanckBoy Color RMK 固件

这是 nRF52840 PlanckBoy Color 分体键盘的 RMK 0.9.0 固件。左半是 BLE central，也负责 USB；右半是 BLE peripheral 0。

## 已实现功能

- 44 个低电平有效的直连按键，以及左右两个编码器按压键
- BLE 分体、USB/BLE 双输出、三个主机配对槽位
- 左右两半均通过 VDDH 上报电池电量
- 两个 EC11 编码器
- 从 ZMK 迁移的四层键图和九组基础层组合键
- Vial 动态键图
- 60 分钟无操作后进入低功耗，矩阵使用中断唤醒
- 左右两半各自的三通道 PWM RGB 状态灯
- UF2、Intel HEX 和 ELF 构建产物

编码器按压在 RMK 中是独立输入。它们的动作复制了原先 ZMK composite 扫描所共享的键位。

## 硬件版本

r1 与 r2 共用矩阵、编码器、键图、电池输入和 flash 布局。仓库中的差异是 RGB PWM 通道顺序。

- `hw-r1`：对应 `config/boards/arm/planck/revisions/r1`
- `hw-r2`：对应 `config/boards/arm/planck/revisions/r2`，也是默认版本

显式构建时必须且只能选择其中一个 feature。两个都不选或同时选择都会导致编译失败。

蓝牙名称：

- RMK r1：`PBC R1`
- RMK r2：`PBC R2`
- ZMK r1：`PBC Z1`
- ZMK r2：`PBC Z2`

RMK 0.9 的主机广播包在必需字段之后最多容纳 16 字节名称。名称更长时，广播会在运行时失败，主机将完全搜索不到键盘。

## 连接与休眠

- 60 分钟无操作后进入低功耗休眠，但不会主动断开已连接的电脑。
- 左右手会持续保持 BLE 连接，也不会因为空闲而主动断开。
- 按任意键即可从休眠唤醒。
- 电脑通过 USB 发出挂起指令时，键盘会立即休眠。
- 未连接任何主机时，蓝牙广播持续 5 分钟；超时后停止广播并休眠，按键后重新广播。

信号真正丢失时的判定时间：

- 正常状态：约 6 秒。
- 休眠状态：约 15 秒。

左右手重连：

- 左半最多用 15 秒尝试连接已保存的右半。
- 右半先向已保存的左半定向广播 10 秒，失败后开放广播 5 分钟。
- 右半 5 分钟仍未连上左半时进入休眠，等待按键唤醒。

只有 `central` 固件会向电脑或手机广播。`peripheral` 固件只寻找左半，不会出现在主机的蓝牙设备列表中。

## 切换电脑

按住右半最下排最左边的两个键进入 BLE 层，再操作左半按键：

- 短按 `Q`：切换到第一台电脑，不删除配对。
- 短按 `A`：切换到第二台电脑，不删除配对。
- 短按 `Z`：切换到第三台电脑，不删除配对。
- 长按 `Q`、`A` 或 `Z` 约 5 秒：清除对应槽位的配对，并重新进入可配对状态。

连接第二台电脑时，进入 BLE 层后长按 `A` 约 5 秒，然后在第二台电脑上搜索并配对。之后切回第一台时，进入 BLE 层并短按 `Q`，不要长按。

清除配对后，电脑上原来保存的密钥也会失效。需要先在电脑上忽略该键盘，再重新搜索和配对。

## RGB 状态灯

RMK 使用状态灯表示当前层：

- 基础层：关闭
- CHAR 层：琥珀色
- ARROW 层：蓝色
- BLE 层：紫色
- 休眠：关闭

RMK 没有实现 ZMK 键图中的 `rgb_ug` 底灯和 `ext_power` 外设电源控制，因为原仓库没有对应的硬件节点。ZMK 用 RGBLED Widget 经 `gpio-leds` 驱动状态灯，对应的 PWM 节点保持关闭，避免和 GPIO 抢同一批脚。这些 ZMK 行为没有被 RMK 改造移除。

## 构建依赖

通过 rustup 安装 Rust。目标架构和 LLVM 工具由 `rust-toolchain.toml` 固定。打包 UF2 需要 `cargo-make`；其任务会在缺失时安装 `cargo-binutils`、`flip-link` 和 `cargo-hex-to-uf2`。RMK 的 nRF BLE 加密依赖还需要 `arm-none-eabi-gcc`。

```sh
# macOS
brew tap osx-cross/arm
brew trust --formula osx-cross/arm/arm-gcc-bin@14
brew install osx-cross/arm/arm-gcc-bin@14
export PATH="$(brew --prefix arm-gcc-bin@14)/bin:$PATH"
cargo install cargo-make
```

## 检查与构建

在本目录执行：

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

生成文件：

- `target/thumbv7em-none-eabihf/release/central`
- `target/thumbv7em-none-eabihf/release/peripheral`
- `planck-boy-color-rmk-r1-central.{hex,uf2}`
- `planck-boy-color-rmk-r1-peripheral.{hex,uf2}`
- `planck-boy-color-rmk-r2-central.{hex,uf2}`
- `planck-boy-color-rmk-r2-peripheral.{hex,uf2}`

GitHub Actions 会在一次运行中发布 `planck-boy-color-zmk-r1`、`planck-boy-color-zmk-r2`、`planck-boy-color-rmk-r1` 和 `planck-boy-color-rmk-r2`。

## 刷写

1. 首次刷写前保留一份可用的 ZMK UF2，并准备 SWD 调试器用于恢复。
2. 每次只让目标半区进入 UF2 bootloader。
3. 按 PCB 版本选择固件。将 `central` 刷到左半，将 `peripheral` 刷到右半。
4. 重启两半。固件更换后如果两半无法发现对方，清除已保存的 split peer。
5. 修改编译期默认键图后清除 RMK storage，否则 Vial 中保存的键图会继续覆盖新默认值。

两半都把本地矩阵 `(0,0)` 设为 bootmagic。复位时按住该键可请求进入兼容 Adafruit 的 bootloader。

链接脚本和 storage 边界刻意保持与 ZMK `nrf52840-nosd` 布局一致。如果板载 bootloader 与 `config/boards/arm/planck/planck.dtsi` 所表示的布局不同，先更新 `memory.x`，不要直接刷写。

## 蓝牙层按键

RMK 使用 `User` 动作管理无线连接：

- `User0` 至 `User2`：短按选择槽位；长按 5 秒清除该槽位并重新配对
- `User3`：下一个槽位
- `User4`：上一个槽位
- `User5`：清除当前槽位
- `User6`：切换 USB/BLE 首选输出
- `User7`：长按清除已保存的 split peer

原 ZMK 的“发现设备”键已映射到对应槽位，因为 RMK 通过长按完成清除和重新配对。RGB 与外设电源位置为 `No`，原因是原仓库没有定义这些硬件。

## 搜索不到蓝牙时

- 确认刷入的是对应版本的 `central` 固件；`peripheral` 不会出现在主机蓝牙列表中。
- 确认两半使用相同固件框架和硬件版本，刷写后分别重新上电。
- 刷写 UF2 不会清除 storage。先在主机上删除旧键盘，再进入 BLE 层，长按目标槽位约 5 秒以清除旧配对并重新广播。
- 检查产品名称是否超过 16 字节。超长名称会导致 RMK 无法构造主机广播包。
- r1 与 r2 当前使用相同的 BLE、DCDC、发射功率、PHY、矩阵和电池配置。如果同一块板刷 r2 可以广播而 r1 不行，先抓取 defmt 日志或清除 RMK storage，不要先改动无线参数。

## 与 ZMK 的行为差异

- ZMK Studio 由 Vial 替代。
- RMK 的组合键按动作匹配，而不是按原始物理位置匹配，因此迁移的九组桌面和层组合键都限制在第 0 层。
- 三个 tap-dance 已保留为 RMK Morse 定义，但没有绑定到键位，因为原 ZMK 键图也没有引用它们。
- 未实现 underglow 和动态外设电源控制。

引脚对照见 `HARDWARE.md`，实机验证步骤见 `VALIDATION.md`。
