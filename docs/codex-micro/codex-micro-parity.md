# planck_left × Codex Micro：能力还原度评估

> 更新日期：2026-07-18
> 背景：本文替代/更新 [07-micro-shortcut-feasibility.json](./layout/07-micro-shortcut-feasibility.json) 的「纯快捷键」视角。
> 当时只有键盘发快捷键这一条通道，很多 Codex Micro 能力被标红（做不到）。
> 现在仓库已落地 [led-web-control.md](../firmware/led-web-control.md)（WebHID → Raw HID → 3 颗板载 LED），
> 再叠加可消费的 Codex 事件流（[codex-agent-loop-hooks-app-server.md](./codex-agent-loop-hooks-app-server.md)），
> 部分「状态灯」类能力从「完全做不到」变成「粗粒度可做」。

本文把 planck_left 对 Codex Micro 的还原度分成三档：

- 🟢 **A 档 — 100% 还原**：只靠键盘（ZMK 快捷键 / 宏 / 图层），无需任何外部程序即可等价。
- 🟡 **B 档 — 桥接部分实现**：靠 `LED 网页控制通道 + 一个本机桥接程序`（消费 codex hooks / app-server / notify，再下发 HID report），只能做到**粗粒度**近似。
- 🔴 **C 档 — 完全无法做到**：受 Micro 专有硬件或 Codex 原生协议独占，键盘侧没有等价物。

---

## 0. 先理解新增的这条通道能干什么

在评估 B 档之前，必须先明确 LED 通道的**物理上限**，否则容易高估。

```text
Codex 事件源                         本机桥接程序                planck_left
──────────────                    ───────────────           ─────────────
app-server 事件流  ┐
hooks (Stop/Pre..) ┼─►  解析 turn/item/审批/thread status ─►  WebHID / HID API
notify (回合完成)   ┘        映射成 0xAB + bitmask report        0xAB report
                                                              ├ LED0 蓝 开/关
                                                              ├ LED1 红 开/关
                                                              └ LED2 绿 开/关
```

硬约束（来自 `led-web-control.md`）：

| 维度 | 现状 | 影响 |
| --- | --- | --- |
| LED 数量 | **3 颗**（LED0 蓝 / LED1 红 / LED2 绿） | 无法一键对一线程地映射 6 个 Agent Key |
| 颜色 | **3 颗独立单色灯**，非 RGB 灯珠 | 无法呈现「白 / 蓝 / 绿 / 琥珀 / 桃 / 红」六色连续谱 |
| 亮度 | **纯开关**（GPIO，不走 PWM） | 无呼吸 / 渐变，只能用「亮 / 灭 / 闪烁模式」编码状态 |
| 方向 | 仅「主机 → 键盘」可靠 | 灯能被点亮，但键盘无法把自身状态回报给主机 |
| 链路 | WebHID **仅 USB**（蓝牙不可靠） | 蓝牙模式下整条状态灯通道失效 |
| 订阅 | 网页 / 键盘**都不订阅** codex | 必须有一个**常驻本机桥接程序**去消费事件再下发 |

结论：LED 通道能做的是「把 Codex 的**聚合 / 少量线程的粗粒度状态**用 3 颗单色灯表达出来」，
**不是**复刻 Micro 那种「6 键 × 六色 × 每键绑定一个线程」的监控墙。

---

## 1. 🟢 A 档 — 键盘 100% 还原（无需外部程序）

这些能力本质是「发一个桌面端快捷键」，ZMK 直接映射按键 / 宏 / 图层即可等价，与 Micro 无差别。

### 1.1 已有默认快捷键，直接映射

| Codex Micro 动作 | 快捷键 | 说明 |
| --- | --- | --- |
| 拒绝请求 | `Escape` | Command Key 核心动作 |
| 批准请求 | `Enter` | Command Key 核心动作 |
| 新建任务 | `⌘N` | |
| 归档任务 | `⇧⌘A` | |
| 置顶 / 取消置顶 | `⌥⌘P` | |
| 命令菜单 | `⌘K` / `⇧⌘P` | |
| 关闭标签 / 窗口 | `⌘W` | |
| 打开终端 | `` ⌃` `` | |
| 打开审查选项卡 | `⌃⇧G` | |
| 开始听写 | `⌃⇧D` | |
| 切换语音模式 | `⌃⇧V` | |
| 切换边栏 | `⌘B` | |
| 切换侧边面板 | `⌥⌘B` | |
| 切换底部面板 | `⌘J` | |
| 显示 / 隐藏浏览器面板 | `⇧⌘B` | |
| 切换文件树 | `⇧⌘E` | |
| 打开设置 | `⌘,` | |
| 打开模型选择器 | `⌃⇧M` | 也可给旋钮「按下」用 |
| 转到任务 1–9 | `⌘1`…`⌘9` | 对应 Micro 6 个 Agent Key 的「切任务」动作 |
| 上一 / 下一任务 | `⇧⌘[` / `⇧⌘]` | |
| 新聊天 | `⌥⌘N` | |

### 1.2 Codex 里「未分配」但有槽位，先自设即可（仍属 A 档）

这些动作 Codex 桌面端留了快捷键槽位但默认空，**先在 Codex 里绑一个组合键**，键盘再发同样组合即可等价。

| Codex Micro 动作 | 备注 |
| --- | --- |
| 提高 / 降低 / 循环推理强度 | 旋钮转动可映射为「自设的推理±快捷键」的连发宏 |
| 发送消息 | |
| 附加文件和文件夹 / 添加照片 | |
| 提交或推送 / 创建 PR | |
| 前往技能 / 强制重载技能 | 摇杆「打开技能列表」的弱折中方案 |
| MCP 配置 / 安装工作空间 | |
| 切换快速模式 / 规划模式 | |
| 复制为 Markdown | |
| 在新任务中继续（分支续写） | |
| 管理已安排任务（定时任务） | |
| 环境操作 2–9（Env2–9） | Env1 默认 `⇧⌘D` |

### 1.3 图层切换（Touch Sensor 的核心用途）

| Codex Micro | planck_left 等价 |
| --- | --- |
| 触摸传感器在多图层间切换 | ZMK 图层键（`&mo` / `&to` / `&tog`）100% 等价，且更可控 |

> 注意：「触摸**循环** 6 层」这种交互方式本身，以及 AppSense（按前台应用自动切层）属于 C 档，见后文。这里说的是「有图层、能切」这个能力本身没问题。

---

## 2. 🟡 B 档 — LED 桥接部分实现（需本机桥接程序 + USB）

这一档是本次更新的重点：原来标红的「状态灯」类能力，现在能用 `3 颗 LED + 桥接程序` 做**粗粒度**近似。
前提是：**运行一个常驻本机程序**消费 Codex 事件流，并按下面的映射下发 `0xAB` report；且键盘处于 **USB** 连接。

### 2.1 Agent 状态灯：从「6 键六色」降级为「3 灯粗粒度」

Micro 用 6 个 RGB 键分别盯 6 个线程，每键六色。我们做不到一一对应，但能做**两种可选投影**：

方案甲 —— **聚合状态（推荐，最稳）**：不区分具体线程，只表达「当前是否有事需要我」。

| 语义 | 事件来源 | LED 表现（蓝/红/绿） |
| --- | --- | --- |
| 有任务在思考 / 运行 | `turn/started`；`item/*` 进行中 | 蓝 常亮 |
| 需要审批 / 需人工输入 | app-server 审批 server request；`PermissionRequest` hook | 红 常亮（可闪烁强调） |
| 有任务完成 / 有未读 | `turn/completed`；`Stop` / `notify` 回合完成 | 绿 常亮 |
| 出错 / 失败 | `turn/completed(failed)`、`error` | 红 快闪 |
| 全部空闲 | 无活跃 turn | 全灭 |

方案乙 —— **3 线程视图**：把 LED0/1/2 各绑 1 个线程，用「亮 = 该线程需要注意」表达，靠闪烁模式区分「运行 / 完成 / 出错」。
代价：单色灯无法同时表达一个线程的多种状态，最多盯 3 个线程，语义比 Micro 粗很多。

**能做到的**：一眼看到「有没有任务在跑 / 要不要我审批 / 是不是完成了」——这正是 Micro 状态灯最高频的价值点。
**做不到的**：6 键分线程、六色连续语义、白色 idle 与琥珀 needs-input 的精细区分、灯上单击切到对应线程（见 C 档）。

### 2.2 语音 / 监听指示灯（替代亚克力麦边框）

| Micro 能力 | B 档近似 |
| --- | --- |
| 麦克风开启 / Codex 监听时亚克力边框亮起 | 桥接程序监听「语音 / 听写开启」状态（若 app-server / hooks 能给到语音态事件），点亮某颗 LED 作监听指示 |

注意：这依赖能拿到「语音开始 / 结束」的事件；若事件源拿不到语音态，则此项退回 C 档。属于「能力路径存在但取决于事件可得性」。
参考同类项目 arkey（见第 6 节）：它的语音是**在本机 macOS 客户端里自己做的 speech-to-text**（`SpeechCoordinator`），并**不是**从 codex app-server 事件流拿到的；其实验固件里的 native PTT 音频也是由 ChatGPT Desktop 直接处理、不经过 app-server。这基本印证：**app-server 事件流大概率给不到「语音开 / 关」信号**，所以本项若要落地，指示灯多半得由「本机桥接程序自己监听系统麦克风 / 快捷键触发态」来点亮，而非订阅 codex。

### 2.3 图层 / 状态自定义指示灯

| 用途 | 说明 |
| --- | --- |
| 用 LED 指示当前图层 | 纯本地即可（不需 codex），属键盘自控，稳定可做 |
| 用 LED 兼作 Codex 状态灯 | 与 2.1 复用同 3 颗灯，需和图层指示做优先级仲裁（`led_control.c` 已有状态闪烁 vs 网页设定的仲裁基础） |

### 2.4 B 档的共同限制（务必写清，避免误期望）

- 必须常驻一个桥接程序（Node `node-hid` / Python `hidapi`，或长开着 `tools/led-web` 的 WebHID 页面 + 一段订阅逻辑）。
- 仅 USB；切蓝牙即失效。
- 3 颗单色灯是硬顶：颜色 / 数量 / 亮度都不足以复刻 Micro 的监控墙，只能做「聚合信号灯」。
- 事件覆盖取决于 codex 侧：`PreToolUse` / `PostToolUse` 目前主要覆盖 shell / `apply_patch` / MCP，`unified_exec`、`WebSearch` 等路径拦截不完整；app-server 事件流最全，建议优先用它做实时态，hooks 做策略 / 审批，notify 做粗粒度「整轮结束」。

---

## 3. 🔴 C 档 — 完全无法做到

这些依赖 Micro 专有硬件或 Codex 原生绑定，键盘 + LED 通道都补不上。

| Codex Micro 能力 | 为什么做不到 |
| --- | --- |
| Agent Key **单击切前台且不弹窗** | 「切到该线程且不弹 ChatGPT 窗口」是桌面端对该物理键的原生行为，快捷键 `⌘1–9` 是否弹窗由桌面端决定，键盘不可控 |
| Agent Key **350ms 双击前置 ChatGPT** | 可做双击宏，但「把 ChatGPT 窗口调最前并绑定到具体线程」是 Micro↔桌面端的原生联动，键盘无此语义 |
| Agent Key **绑定固定 agent / 工作流 / 最近任务** | 这是 Micro 在 Codex 里的原生按键绑定，键盘只能发通用快捷键，绑不到「某个具体 agent 对象」 |
| **6 键 × 六色 RGB** 状态墙 | 硬件不具备：只有 3 颗单色开关灯，见第 0 节。B 档只能做粗粒度投影 |
| Joystick **四向直触预设 / 自定义 Skill** | Codex 无「触发第 N 个 skill」的快捷键槽位，只有「打开技能列表」（A 档弱折中），四向直触做不到 |
| Rotary **Composer 导航模式**（转=移控件、按=选择） | 依赖 Micro 与 Composer 的原生控件焦点协议，无对应快捷键 |
| Rotary **旁键在有控件时亮红作取消** | 需要「控件是否打开」的原生态回读 + 该键 RGB，双重缺失；`Escape`≈取消可代替动作但没有灯态联动 |
| Touch **循环 6 层的原生交互** | 触摸循层是 Micro 硬件；planck 用图层键可达等价功能，但不是「触摸循环」这一交互 |
| **AppSense**（聚焦某 app 5 秒自动切层） | Micro / Work Louder Input 的原生特性，ZMK 无法感知主机前台应用 |
| **Settings › Codex Micro 原生改键 UI** | Micro 在 Codex 设置页内直接改键 / 换布局；planck 改键走 ZMK keymap + 重新刷固件 |
| **物理换帽**（32 颗 Codex 图标键帽） | 纯硬件配件，与固件无关 |
| 键盘 → 主机**状态回报** | Raw HID「键盘 → 主机」方向在旧 USB stack 有已知发送失败，本方案只用「主机 → 键盘」，故无法反向上报 |

---

## 4. 总览速查

| 分类 | 归档 | 代表能力 |
| --- | --- | --- |
| 命令键动作（拒批 / 新建 / 归档 / 面板 / 终端 / 审查 / 设置 / 模型 / 听写 / 语音） | 🟢 A | 直接快捷键 |
| 推理± / 发送 / 附文件 / 提交推送 / 建 PR / 前往技能 / 定时任务 / 复制 MD / Env2–9 | 🟢 A | 需先在 Codex 自设快捷键 |
| 任务切换 1–9 / 上下任务 / 新聊天 | 🟢 A | 快捷键 |
| 图层切换（有图层、能切） | 🟢 A | ZMK 图层键 |
| Agent 状态灯（有任务在跑 / 待审批 / 已完成 / 出错的聚合信号） | 🟡 B | 桥接程序 + 3 LED，粗粒度 |
| 语音 / 监听指示灯 | 🟡 B | 取决于能否拿到语音态事件 |
| LED 图层 / 状态自定义指示 | 🟡 B | 本地即可，与状态灯需仲裁 |
| 6 键六色 RGB 线程墙 | 🔴 C | 硬件只有 3 颗单色灯 |
| 单击不弹窗切前台 / 双击前置 / 绑固定 agent | 🔴 C | 桌面端原生按键行为 |
| Joystick 四向直触 Skill | 🔴 C | 无快捷键槽位 |
| Rotary Composer 导航 / 旁键取消灯 | 🔴 C | 原生控件协议 |
| AppSense / 触摸循层交互 / 原生改键 UI / 物理换帽 | 🔴 C | Micro 专有软硬件 |

---

## 5. 落地建议（把 B 档变成现实的最小路径）

1. **选事件源**：优先 `codex app-server` 事件流（`turn/started`、`turn/completed`、审批 server request、`thread/status/changed` 最全）；轻量场景用 `notify`（仅回合完成）或 `Stop` hook。
2. **写桥接程序**：一个常驻进程，把上述事件按第 2.1 节映射成 3 位 bitmask，用 `0xAB` report 经 HID 下发（Node `node-hid` / Python `hidapi`，或复用 `tools/led-web` 的 WebHID 逻辑）。
3. **先做方案甲（聚合状态）**：蓝=运行、红=待审批、绿=完成、红闪=出错、全灭=空闲。这是投入产出比最高的一步。
4. **状态优先级仲裁**：待审批 / 出错 > 运行 > 完成 > 空闲；与「电量 / 连接闪烁」「图层指示」共用 3 颗灯时，沿用 `led_control.c` 已有的仲裁思路。
5. **明确边界**：文档 / README 里写清「仅 USB、3 灯单色、粗粒度」，避免被当成 Micro 监控墙的等价物。

---

## 6. 参考实现：arkey 项目的可借鉴点

[shuhari04/arkey](https://github.com/shuhari04/arkey)（source-available，PolyForm Noncommercial，QMK + macOS 客户端）做的正是本文 B 档设想的东西：一个本机 daemon 拉起 `codex app-server`，订阅事件流，用 Raw HID 把任务状态投射成键盘 RGB（它叫 AgentGlow）。它给我们两类价值：**可直接借鉴的工程做法**，以及**唯一一处 Codex Micro 专有协议线索**。

### 6.1 架构层面：印证 B 档路线正确

arkey 有两条互相隔离的链路：

```text
默认 App Server 模式（用公开开发接口，就是我们的 B 档）
  macOS app ── RPC ──► Node daemon
                        ├─ stdio JSONL ──► codex app-server   （状态源）
                        └─ 32B Raw HID ──► QMK 固件 + RGB      （灯效）

可选 Codex Micro Lab 模式（仿冒设备身份的实验，非公开 API）
  ChatGPT Desktop ── report 0x06 ──► Q6 Pro 实验固件
```

要点印证了我们的判断：它**不用 hooks 驱动灯效**，状态全部取自 app-server；`notify` 也没用到——与我们「实时态优先 app-server」的选型一致。且「完整控制仅 USB，蓝牙退化为普通键盘」的约束和我们完全一样。

### 6.2 可直接照搬：app-server 事件 → 灯状态 的映射与仲裁

这是对我们**最有用**的部分，`src/runtime.ts` 里的映射可几乎原样搬进我们的桥接程序：

| app-server 通知 | 判定 | 灯状态 |
| --- | --- | --- |
| `turn/started` | — | working（运行） |
| `turn/completed` | `status=completed` | completeUnread（完成未读） |
| `turn/completed` | `status=failed` | error（出错） |
| `turn/completed` | 其他 | idle |
| `thread/status/changed` | `active` 且 flags 含 `waitingOnApproval` / `waitingOnUserInput` | requiresInput（待输入 / 审批） |
| `thread/status/changed` | `active`（无上述 flag） | working |
| `thread/status/changed` | `systemError` / `notLoaded` | error / offline |
| 审批 server request | — | requiresInput |
| `serverRequest/resolved` | — | 重算该任务输入态 |
| `error`（`willRetry≠true`） | — | error |

多任务并存时的**优先级仲裁**（数字越大越优先，直接可用）：

```text
requiresInput(6) > completeUnread(5) > working(4) > idle > offline > unassigned
```

语义配色（arkey 的 7 态，供我们决定 3 颗单色灯如何取舍）：

| 状态 | arkey 颜色 | 我们 3 灯（蓝/红/绿）能否还原 |
| --- | --- | --- |
| idle 空闲 | 白 `#FFFFFF` | 勉强（三色都不是白，可用「全灭」代替 idle） |
| working 运行 | 蓝 `#304FFE` | 能，蓝亮 |
| completeUnread 完成 | 绿 `#00FF4C` | 能，绿亮 |
| requiresInput 待审批 | 琥珀 `#FF6D00` | 不能真还原，用红亮 / 红慢闪近似 |
| error 出错 | 红 `#FF0033` | 能，红快闪 |
| offline / unassigned | 灭 | 能，全灭 |

结论：arkey 用「白/蓝/绿/琥珀/红 + 呼吸/双脉冲」表达 7 态，我们只有蓝/红/绿三颗单色开关灯，**working / completeUnread / error 可对上，idle 与 requiresInput 只能近似**——正好对应第 2.1 节的取舍。

### 6.3 值得借鉴的健壮性设计（充实我们的 backlog）

- **Hello / capabilities 握手**：host 先发 Hello，校验 `layoutHash`、矩阵尺寸、feature flag，匹配后才开启完整控制；不匹配就退回普通键盘。可给我们的 `0xAB` 协议加一个版本 / 能力协商，避免固件与主机程序错配。
- **心跳 + fail-open**：固件在「心跳丢失 / 传输切换 / daemon 退出」后自动恢复原 RGB 状态。这正是我们 `led-web-control.md` backlog 里「fail-safe / 心跳」一项，arkey 证明它值得做。
- **staged commit（暂存 + 原子提交）**：多帧灯效先暂存、最后一帧带 commit 位再整体切换，避免刷新途中闪烁。
- **binding mask**：只有被显式绑定的键才被接管，未绑定键保持普通输入。对应我们「LED 与按键功能解耦」的思路。

（arkey 的 32-byte 帧：magic `0xB0 0x47` + 版本 + opcode + len + seq + payload；比我们当前的单字节 `0xAB` 命令更完整，可作为演进参考。）

### 6.4 唯一的 Codex Micro 专有协议线索：native-facing report `0x06`

arkey 的「Codex Micro Lab」实验模式揭示了本次调研中**唯一一处 codex-micro 专有协议信息**：

- ChatGPT Desktop 与真机 Codex Micro 之间存在一条**独立于 app-server 的原生 HID 通道**：**Report ID `0x06`，64 字节**，承载版本 / 设备状态、**六个任务灯**、keys/ambient 灯光、按键、旋钮、方向事件。
- 即：只要设备以 **ChatGPT Desktop 期望的 USB 身份**枚举，Desktop 会**原生驱动 6 个任务灯**并原生接收按键 / 旋钮 / 摇杆方向事件——**无需任何桥接程序**。
- arkey 另有一条 Report ID `0x07` 是它**自定义**的配置协议（帧格式完整公开：`0x07 + magic 0xA7 + 版本 + opcode + seq + len + payload`），但那是 arkey 的，不是 Codex 的。
- 原生目标也被枚举清楚：**13 个** = 6 Agent（`AG00–AG05`）+ 6 Command（`ACT06/07/08/09/10/12`）+ 1 编码器（`ENC_PRESS`），外加 4 个 joystick 方向事件。

**这对 planck_left 意味着什么**——理论上诱人，实际不划算，仍归 C 档：

1. **法律 / 合规风险**：走这条路必须**仿冒不属于你的 USB 身份**，涉及商标、服务条款、USB 身份与当地法律。arkey 把它严格隔离为「Lab」，构建需显式 `--acknowledge-device-identity-test`，且**从不自动刷写**，并反复声明不得销售 / 分发 / 宣称为官方 Micro。
2. **协议不公开且不稳定**：`0x06` 帧的确切字节布局这些文档**并未公布**（arkey 是逆向观察所得），且随 Desktop 更新可能随时失效。
3. **ZMK 工作量大**：需要让 ZMK 以特定身份枚举、并实现一个 64 字节 `0x06` HID 接口来解析 Desktop 下发、回发其期望事件——远超当前 `zmk-raw-hid`「主机→键盘点灯」的范围。
4. **硬件仍是硬顶**：即便 Desktop 愿意驱动「6 个任务灯」，planck_left 也只有 3 颗单色灯，物理上放不下 6 键六色。

所以：`0x06` 是有价值的**情报**（它解释了 Micro 为什么能「不弹窗单击切前台 / 六色状态墙 / 摇杆方向」——都靠这条原生通道），但对 planck 而言，走 app-server 桥接（B 档）是唯一正当且可维护的路线；`0x06` 仿冒路线维持在 C 档、仅作背景知识。

### 6.5 反向印证的边界结论

- **Skill / Cancel 无原生 target**：arkey 明确 Skill、Cancel 在 Lab 原生映射里**没有对应目标**，只能走 app-server，且工具**拒绝**把它们猜测性塞到 joystick 方向上。这印证了本文 C 档「Joystick 四向直触 Skill 做不到」的判断——**连仿冒真机身份都做不到**。
- **摇杆方向事件效果由 Desktop 设置决定**：即便发了方向事件，实际行为也取决于当前 ChatGPT Desktop 的 Codex Micro 设置，不是键盘能自证的能力。

### 6.6 使用提醒

arkey 采用 **PolyForm Noncommercial 1.0.0**（自有客户端 / host / 脚本 / 协议 / 文档），固件按上游 GPL/MIT。**不能直接照抄其代码用于商用**；本文只借鉴其**设计与协议思路**（尤其 6.2 的事件映射与 6.3 的健壮性模式），具体实现需自行编写。

---

## 7. 相关文档

- [codex-micro-capabilities.md](./codex-micro-capabilities.md) — Micro 原生能力清单（本文的对照基准）
- [layout/07-micro-shortcut-feasibility.json](./layout/07-micro-shortcut-feasibility.json) — 旧的「纯快捷键」红/绿可行性图
- [led-web-control.md](../firmware/led-web-control.md) — LED 网页控制通道（B 档的物理基础与限制来源）
- [codex-agent-loop-hooks-app-server.md](./codex-agent-loop-hooks-app-server.md) — 可消费的 Codex 事件流（B 档的状态源）
- [codex-shortcut.md](./codex-shortcut.md) — Codex 桌面端全部快捷键（A 档映射依据）
- [shuhari04/arkey](https://github.com/shuhari04/arkey) — 同类 source-available 项目（QMK + macOS）：B 档桥接的参考实现与 `0x06` 专有协议线索来源；协议细节见其 `docs/ARCHITECTURE.md` 与 `docs/CODEX_MICRO_LAB.md`
