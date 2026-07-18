# Codex Micro 能力清单调研

> 调研日期：2026-07-16
> 资料来源：OpenAI 官方 learn.chatgpt.com、Work Louder 官网（worklouder.cc），以及 Ars Technica、CNET、TestingCatalog、fonearena 等公开报道。

## 产品定位

- 型号 `kbd-1.0-codex-micro`，OpenAI 与外设厂商 Work Louder 联名的限量宏键盘（macropad），基于 Work Louder 的 Creator Micro 2 机身改造。
- 售价 230 美元，2026 年 7 月 15 日开售，通过 OpenAI 的 Supply Co. 商店销售。
- 定位为 Codex 编程智能体的“物理遥控 / 监控台”，而非全尺寸键盘，也不是与 Jony Ive 合作的消费级 AI 设备。

## 核心能力

### 1. Agent Keys（6 个磨砂状态键）——实时监控多个 Codex 线程

- 每个键用 RGB 灯实时反映一个 Codex 任务 / 线程的状态，即使该任务不在屏幕前台也能一眼看到：
  - 白色：空闲（idle）
  - 蓝色：思考 / 运行中（thinking）
  - 绿色：已完成 / 有未读（complete / unread）
  - 琥珀 / 桃色：需要人工输入或审批（needs input / question）
  - 红色：出错（error）
  - 熄灭：无任务运行
- 交互：单击将该任务切到前台会话（不弹出 ChatGPT 窗口）；350 毫秒内双击则切换任务并把 ChatGPT 窗口调到最前。
- 可绑定到固定任务、最近任务、特定工作流或特定 agent。

### 2. Command Keys（命令键）——常用 Codex 动作快捷键

- 默认映射：接受更改、拒绝输出、按住说话（push-to-talk）、新建对话、分支线程等。
- 可在 Codex 设置中直接改键（Settings > Codex Micro），并搭配 32 颗图标键帽物理换帽。
- 可绑定动作包括：打开浏览器 / 终端、审查更改、Git 提交、创建 PR、附加文件或图片、管理定时任务、调整推理强度、打开 Skills 等。

### 3. Joystick（平面摇杆）——触发工作流

- 向四个方向拨动可触发预设或自定义技能，例如：审查 PR、调试错误、重构代码。
- 可放置最多 4 个预设 / 自定义 skill，映射可重定义。

### 4. Rotary Dial（旋钮）——调节推理强度

- 转动旋钮实时调整 Codex 的 reasoning level（推理强度）：简单任务调低跑得快，复杂任务拧高深入推理。
- 两种模式：Composer 导航（在编辑器控件 / 选项间移动，按下打开或选择）或仅 Reasoning（转动即打开并调整推理强度）。
- 旋钮右侧的 Agent Key 在有控件打开时会亮红，作为取消键。

### 5. Touch Sensor（触摸传感器）——图层切换

- 左下角触摸传感器配 3 个图层 LED，用于在 6 个可编程图层间循环。
- Layer 1 保留给 Codex；Layer 2–6 通过 Work Louder Input 软件映射任意应用的通用快捷键。
- 支持 AppSense：根据前台应用（聚焦 5 秒后）自动切换图层。

### 6. 语音与灯效

- push-to-talk 语音输入；亚克力边框在麦克风开启 / Codex 监听时亮起。

## 软件与集成

- 深度集成进 Codex / ChatGPT 桌面版应用：改键、调布局无需额外下载软件即可完成（Agent Key 实时状态需配合 ChatGPT 桌面应用运行）。
- 通用快捷键映射由 Work Louder Input 软件负责（6 个可编程图层）。

## 硬件规格

| 项目 | 规格 |
| --- | --- |
| 输入方式 | 13 个机械轴 + 1 个触摸传感器 + 1 个旋转编码器 + 1 个平面摇杆 |
| 轴体 | 低矮 POM/POK 轴；段落轴（clicky，橙色轴心）/ 线性静音轴（silent，蓝色轴心）两版 |
| 轴体参数 | 触发力 40±10gf、总行程 2.8±0.25mm、寿命 5000 万次 |
| 机身 | CNC 加工 PC + 铝合金，喷砂阳极氧化底座，防滑圈 |
| 键帽 | PBT + PC 键帽，橡胶摇杆帽 |
| 键帽套装 | 32 颗 Codex 定制图标键帽 + 11 颗纯色键帽 |
| 连接 | 蓝牙 / USB-C 双模 |
| 兼容 | Mac / Windows |
| 软件 | ChatGPT Codex、Work Louder Input |
| 附件 | USB-C to USB-C 线缆、Codex Icon Keyset |

## 一句话总结

Codex Micro 把编程从“打字”转向“监工”：摇杆派活、命令键批准或打回、旋钮分配推理资源、6 个状态灯一眼掌握多个 agent 的进度，是目前唯一原生集成进 Codex 的物理控制器。

## 参考链接

- [Codex Micro | ChatGPT Learn](https://learn.chatgpt.com/docs/features/codex-micro)
- [WORK LOUDER — Codex Micro](https://worklouder.cc/codex-micro)
- [OpenAI's first branded hardware is... a light-up keyboard? — Ars Technica](https://arstechnica.com/ai/2026/07/openais-first-branded-hardware-is-a-light-up-keyboard/)
- [OpenAI's First Hardware Release Turns Out to Be Keypad for Codex — CNET](https://www.cnet.com/tech/services-and-software/openais-first-hardware-release-turns-out-to-be-keypad-for-codex/)
- [OpenAI prepares Codex Micro keypad to control AI Agents — TestingCatalog](https://www.testingcatalog.com/openai-prepares-codex-micro-keypad-to-control-ai-agents/)
