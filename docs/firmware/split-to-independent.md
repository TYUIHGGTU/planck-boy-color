# 把 ZMK 分体键盘改造成两台独立键盘

本文记录把本仓库从「左主右从的分体键盘」改造成「两台各自独立、可单独连电脑的键盘」的完整过程与原理，供后续类似的分体键盘改造参考。

- 硬件：`planck_left` / `planck_right`（两块 nRF52840，各带旋钮编码器与 RGB 指示灯）。
- 改造前：`planck_left` 是中央机（central），`planck_right` 是外设（peripheral），右板把按键状态通过蓝牙发给左板，由左板统一发给电脑；右板离开左板无法单独使用。
- 改造后：两块板各自是一台完整的 HID 键盘，各自直连电脑，互不依赖。

---

## 一、先厘清一个关键认知：ZMK 里「一套键盘」不是「一个目录」

改造前很容易误以为「一套键盘要有一套独立目录」。其实 ZMK 的组织方式是三层，和目录结构无关：

1. **board 定义 = 键盘本体。** 一个目录（`config/boards/arm/planck/`）里可以用 `board.yml` 声明多块板。本仓库早就声明了 `planck_left` 和 `planck_right` 两块独立 board，各有自己的 `.dts`、`_defconfig`、`Kconfig.<board>`。它们共用一个目录只是因为是同系列硬件变体，完全合法。`west build -b planck_left` 和 `-b planck_right` 本来就是两次独立编译。

2. **user config（`config/` 目录）= 每块板的键位与配置。** ZMK 靠**文件名匹配 board 名**来区分，一个 `config/` 目录可以给任意多套键盘存配置。文件名规则见下一节。

3. **`build.yaml` = 要产出哪些固件。** 每一行对应一次独立编译、一个独立 UF2。

> 结论：改造前后产物**都是两个 UF2**。真正让两块板「主从依赖」的从来不是目录，而是 `CONFIG_ZMK_SPLIT` / `ZMK_SPLIT_ROLE_CENTRAL` 两个开关。

---

## 二、ZMK 配置文件的命名与查找规则（改造成败的关键）

依据 ZMK 官方文档（Config Overview）：

- ZMK 在 `config/` 里按 **`<board>.keymap` / `<board>.conf`** 查找用户配置。
- **分体特例：** 可以用一个不带 `_left` / `_right` 后缀的共享文件同时配置两边，例如 `planck.keymap`、`planck.conf` 会同时作用于 `planck_left` 和 `planck_right`。
- **重点：如果共享文件存在，带 `_left` / `_right` 后缀的文件会被忽略。**

所以要让两块板用**不同**的键位，必须：

- 删掉共享的 `planck.keymap`，改成 `planck_left.keymap` + `planck_right.keymap`。
- `.conf` 若左右需求相同，可继续共享 `planck.conf`（本次左右一致，保留共享）。

这条规则是 ZMK 原生机制，**不需要给 board 改名**。

---

## 三、具体改动清单

### 1. 关闭分体开关（`config/boards/arm/planck/Kconfig.defconfig`）

删除 `ZMK_SPLIT` 和 `ZMK_SPLIT_ROLE_CENTRAL`，并给左右设不同蓝牙名（电脑上显示为两个可区分设备）：

```
if BOARD_PLANCK_LEFT
config ZMK_KEYBOARD_NAME
        default "PlanckBoy L"
endif

if BOARD_PLANCK_RIGHT
config ZMK_KEYBOARD_NAME
        default "PlanckBoy R"
endif

if BOARD_PLANCK_LEFT || BOARD_PLANCK_RIGHT
config BT_CTLR
        default BT
if USB
config USB_NRFX
    default y
config USB_DEVICE_STACK
    default y
endif # USB
endif
```

关掉 `ZMK_SPLIT` 后，ZMK 会给**两块板都**编译 HID / keymap / BLE（分体时只有中央机才编译这些），于是两块板都成了完整键盘。

### 2. 拆分键位表

- 删除共享 `config/planck.keymap`。
- 新建 `config/planck_left.keymap`、`config/planck_right.keymap`，各自只放本侧的键位。
- 每份 keymap 的绑定数必须等于该板矩阵变换的位置数（本仓库改造后是 22）。

### 3. 拆分矩阵变换与物理布局

分体时用的是一个 44 键（左半 + 右半）的共享变换，右板还用 `col-offset = <22>` 把自己的键拼到右半。独立后每块板应各自是 22 键：

- `planck.dtsi`：把 `default_transform` 从 44 键改成 22 键（`RC(0,0)..RC(0,21)`，`columns = <22>`），删除原来 44 键的共享物理布局。
- `planck_left.dts`：定义 22 键的 `left_physical_layout`，`chosen { zmk,physical-layout }` 指向它。
- `planck_right.dts`：**删除 `&default_transform { col-offset = <22>; }`**，定义 22 键的 `right_physical_layout`。

> 位置映射一致性：去掉 `col-offset` 后，右板每个物理键落到的位置和以前一一对应（例如右板原始列 0 以前经 +22 偏移落在旧位置 6=Y，现在直接落在新位置 0=Y），只是位置索引从 0 重新编号，实际按键行为不变。旋钮旋转走的是 EC11 sensor，与此无关。

### 4. 每块板只保留自己的编码器

`planck.dtsi` 的 `sensors` 节点原本同时列了左右两个编码器。独立后在各板 `.dts` 覆盖，只留本侧：

```
// planck_left.dts
&sensors { sensors = <&left_encoder>; };
// planck_right.dts
&sensors { sensors = <&right_encoder>; };
```

对应地，每份 keymap 的 `sensor-bindings` 只留 1 条。

### 5. 每块板各自的 BLE 管理层

独立后每块板要能自己管理蓝牙配对。两份 keymap 各带一个 `BLE` 层，放 `&bt BT_SEL 0..3`、`&bt BT_CLR`、`&bt BT_CLR_ALL`（以及本仓库的 `&tog_io` LED 开关）。

进入 BLE 层的入口不能跨板（combo / 组合键只能用同一块板上的键位）：

- 左板：保留原来那个三键 combo（`&mo 1`）。
- 右板：用底排一个空位键设为 `&mo 1`（按住进入 BLE 层）。

> 注意：combo 的 `key-positions` 是**位置索引**。矩阵变换重新编号后，索引会变——本次左板 combo 从 `<25 13 1>` 改成 `<1 7 13>`（仍是同样那三个物理键）。

### 6. keymap-editor 的布局 json

nickcoutsos 的 keymap-editor 按 **keymap 文件名**找同名 `.json`（`config/<keyboard>.json`），并**按数组顺序**把布局格子映射到 keymap 绑定。所以：

- keymap 改名后，json 也要改成 `planck_left.json` / `planck_right.json`，否则报 "No Layout Available"。
- json 的格子数必须和 keymap 绑定数一致（22），否则错位。
- json 里的 `sensors` 也各自只留本侧编码器。

---

## 四、可选：物理旋转（左逆时针 90°、右顺时针 90°）

竖向手把常希望把每半旋转 90°。做法是直接**重算坐标**（键帽不倾斜，排成 4 列 × 6 行），比用 `rot` 角度参数更直观可控：

- 逆时针 90°（左）：`new_x = row`，`new_y = (列数-1) - col`。
- 顺时针 90°（右）：`new_x = (行数-1) - row`，`new_y = col`。

两处要同步改：

- 固件侧（ZMK Studio 用）：各板 `.dts` 的 `key_physical_attrs`（单位 1/100 键，`100` = 1u），`rot` 保持 0，只改 `x` / `y`。
- 编辑器侧（keymap-editor 用）：各板 `.json` 的 `x` / `y`（单位为键）。

---

## 五、改造后文件对照

| 文件 | 改造前 | 改造后 |
|------|--------|--------|
| `Kconfig.defconfig` | 开 `ZMK_SPLIT` + 左为 central | 关分体，左右各设蓝牙名 |
| `config/planck.keymap` | 共享 44 键 | 删除 |
| `config/planck_left.keymap` | 无 | 左板 22 键 + combo + BLE 层 |
| `config/planck_right.keymap` | 无 | 右板 22 键 + `&mo 1` 入口 + BLE 层 |
| `config/planck.json` | 共享 | 删除 |
| `config/planck_left.json` / `planck_right.json` | 无 | 各 22 键、旋转、单编码器 |
| `planck.dtsi` | 44 键变换 + 共享物理布局 | 22 键变换，物理布局下放到各板 |
| `planck_left.dts` / `planck_right.dts` | 引用共享布局；右板 `col-offset=22` | 各自 22 键旋转布局；右板去偏移；各留本侧编码器 |
| `planck.conf` | 共享 | 不变（左右一致，继续共享） |
| `build.yaml` | 两块板 | 不变 |

---

## 六、通用改造检查清单

把任意「左主右从」ZMK 分体改成两台独立键盘，按此逐项过一遍：

1. `Kconfig.defconfig` / `.conf`：去掉 `ZMK_SPLIT`、`ZMK_SPLIT_ROLE_CENTRAL`；确认两块板都有 `ZMK_USB` / `ZMK_BLE`；可给不同 `ZMK_KEYBOARD_NAME`（≤16 字符）。
2. 键位表：删共享 `<base>.keymap`，建 `<board>_left.keymap` / `<board>_right.keymap`（否则被忽略）。
3. 矩阵变换：从「左+右」的合并变换拆成每块板独立、位置从 0 开始；去掉外设那侧的 `col-offset`。
4. 物理布局：每块板的 `keys` 数量 = 该板变换位置数；`chosen zmk,physical-layout` 指向本板布局。
5. 编码器/其他外设：`sensors` 等节点各板只留本侧；keymap 的 `sensor-bindings` 数量对齐。
6. 层切换入口：确认每块板都有**同板**的方式进入功能层（combo 只能用同板键位；combo 的位置索引随变换重新编号会变）。
7. keymap-editor 的 `.json`：与 keymap 同名、格子数一致、顺序一致。
8. 三处键数必须相等：`transform 位置数 == 物理布局 keys 数 == 每层 keymap 绑定数`。

---

## 七、验证

本仓库通过 GitHub Actions（`.github/workflows/build.yml` 调用 ZMK 的 `build-user-config.yml`）按 `build.yaml` 分别编译两块板，产出：

- `planck_left-zmk.uf2`
- `planck_right-zmk.uf2`

各自刷入对应板子即可。两块板需**分别与电脑配对**（各自管理蓝牙与电量）。
