# Codex Agent Loop 消费指南：Hooks、App Server 与程序集成

> 调研日期：2026-07-16  
> 资料来源：[Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)、[Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)、[Hooks](https://developers.openai.com/codex/hooks)、[App Server](https://developers.openai.com/codex/app-server)、[SDK](https://developers.openai.com/codex/sdk)、[Non-interactive](https://developers.openai.com/codex/noninteractive)、[Advanced Configuration](https://developers.openai.com/codex/config-advanced)

本文回答三件事：

1. Codex 桌面端与 CLI 是否共享同一套 hooks
2. App Server 是什么、处在架构哪一层
3. 用程序开发可以消费哪些 agent loop 生命周期点（开始前、结束后等）

---



## 1. 一句话结论


| 问题                   | 结论                                                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------- |
| 桌面端与 CLI 是否共享 hooks？ | **是。** Hooks 挂在共享的 Codex core（harness）上，由 `~/.codex` / 项目 `.codex` 等配置层发现并执行；桌面端、CLI、IDE 扩展走同一套 agent 逻辑时都会命中。 |
| App Server 是什么？      | **把 Codex harness 暴露给富客户端的双向 JSON-RPC 进程/协议。** 桌面应用、VS Code 扩展等通过它启动线程、开 turn、收流式事件、处理审批。                      |
| 程序怎么消费 agent loop？   | 按深度分四档：**hooks（注入循环内）**、**notify（回合结束侧信道）**、**app-server / SDK（完整事件流）**、`codex exec --json`**（无 UI 自动化流）**。    |


---



## 2. 架构：同一套 harness，多种外壳

OpenAI 把「模型推理 + 工具调用 + 会话持久化 + 沙箱策略」统称为 **Codex harness（agent loop）**，实现落在开源 Codex CLI 的 **Codex core** 里。

表面上的产品形态：

- Web / ChatGPT 中的 Codex
- Codex CLI（TUI）
- IDE 扩展（VS Code 等）
- Codex / ChatGPT **桌面端**

底层都由同一套 core 驱动。差异主要在 **客户端如何连上 core**：

```text
  Desktop / VS Code / JetBrains / 自研 UI / CLI TUI
                      |
                      |  JSON-RPC (stdio / ws / unix)
                      v
              Codex App Server
         (消息处理 + Thread Manager)
                      |
                      v
           Codex Core (harness)
    thread / turn / item / 工具 / 沙箱
         MCP / Skills / Hooks
```

要点：

- **Hooks、MCP、Skills、**`AGENTS.md`**、subagents** 属于「文件系统侧特性」：配置/脚本放在 `~/.codex/`、项目 `.codex/` 等位置，core 启动会话时加载。只要客户端走同一 harness，这些特性就会生效，**不需要每个客户端各自再实现一套 hooks**。
- 桌面端官方说明：制品里会捆绑并固定某个版本的 Codex 二进制，以子进程方式拉起 App Server，经 stdio 说 JSON-RPC。
- CLI TUI 历史上可直接链 core；官方方向是让 TUI 也变成 App Server 的普通客户端（并可 `codex --remote` 连远程 app-server）。

因此：**共享的是 harness + 配置层上的 hooks；桌面端没有另一套独立 hook 协议。** 桌面设置里的「回合完成通知」属于应用层 UI，不要和 `hooks.json` / `notify` 混为一谈。

---



## 3. App Server 详解



### 3.1 定位

`codex app-server` 既是：

1. **长驻进程**：托管多个 Codex core thread
2. **协议**：客户端友好的双向 JSON-RPC（线上常省略 `"jsonrpc":"2.0"`，stdio 用 JSONL）

适用场景：要在自有产品里做 **认证、会话历史、审批、流式 agent 事件** 的深度集成。  
若只是 CI/脚本跑完任务，官方更推荐 **SDK** 或 `codex exec`。

### 3.2 传输


| 传输          | 启动示例                                            | 说明                  |
| ----------- | ----------------------------------------------- | ------------------- |
| stdio（默认）   | `codex app-server`                              | 子进程管道，本地集成最常见       |
| WebSocket   | `codex app-server --listen ws://127.0.0.1:4500` | 实验性；远程需配 auth / TLS |
| Unix socket | `codex app-server --listen unix://`             | 本地控制 socket         |


远程 TUI 示例：

```bash
# 机器 A
codex app-server --listen ws://127.0.0.1:4500

# 机器 B（或本机另一终端）
codex --remote ws://127.0.0.1:4500
```



### 3.3 三个会话原语


| 原语         | 含义                                | 典型 API / 事件                                                                |
| ---------- | --------------------------------- | -------------------------------------------------------------------------- |
| **Thread** | 一次持久对话（可 resume / fork / archive） | `thread/start`、`thread/resume`、`thread/started`                            |
| **Turn**   | 一次用户输入触发的 agent 工作单元              | `turn/start`、`turn/steer`、`turn/interrupt`、`turn/started`、`turn/completed` |
| **Item**   | 输入/输出原子单元（消息、命令、diff、MCP 调用等）     | `item/started` → 可选 `item/*/delta` → `item/completed`                      |


一次典型交互：

1. `initialize` → `initialized`
2. `thread/start`（或 `resume` / `fork`）
3. `turn/start` 带上用户输入
4. 持续读通知：`turn/started`、`item/*`、审批请求、`turn/completed`
5. 需要时响应对方发起的 server request（例如审批）



### 3.4 程序侧可订阅的关键事件（节选）

**Turn 级**

- `turn/started` / `turn/completed`（`completed` | `interrupted` | `failed`）
- `turn/diff/updated`、`turn/plan/updated`
- `hook/started`、`hook/completed`（hooks 执行本身也可被客户端观察到）
- `thread/tokenUsage/updated`

**Item 级（**`item/started` **/** `item/completed` **+ delta）**

常见 `item.type`：`userMessage`、`agentMessage`、`reasoning`、`commandExecution`、`fileChange`、`mcpToolCall`、`webSearch`、`contextCompaction`、`plan` 等。

**线程生命周期**

- `thread/started`、`thread/archived`、`thread/unarchived`、`thread/closed`、`thread/status/changed`

可用 `initialize.params.capabilities.optOutNotificationMethods` 按方法名精确关闭噪声通知（如 `item/agentMessage/delta`）。

生成绑定：

```bash
codex app-server generate-ts --out ./schemas
codex app-server generate-json-schema --out ./schemas
```

---



## 4. Hooks：共享的「循环内」注入点



### 4.1 是什么

Hooks 让你在 agentic loop 的固定节点上 **spawn 外部命令**：stdin 收 JSON，stdout 回 JSON（或退出码），从而做审计、策略门禁、记忆摘要、额外上下文注入等。

行为要点：

- 多文件、多 handler 会 **全部匹配并并发启动**（一个 hook 不能阻止另一个已匹配 hook 启动）
- 非托管 command hook 需在 CLI 用 `/hooks` **审查并 trust**（按定义哈希）后才执行
- 可用 `[features] hooks = false` 关闭；企业侧可用 `requirements.toml` 强制托管 hooks



### 4.2 配置落点（桌面 / CLI 共用）


| 位置                             | 形式                                                            |
| ------------------------------ | ------------------------------------------------------------- |
| `~/.codex/hooks.json`          | JSON                                                          |
| `~/.codex/config.toml`         | 内联 `[hooks]` / `[[hooks.PreToolUse]]`                         |
| `<project>/.codex/hooks.json`  | 项目层（项目需 trusted）                                              |
| `<project>/.codex/config.toml` | 同上                                                            |
| 插件                             | `hooks/hooks.json` 或 `.codex-plugin/plugin.json` 的 `hooks` 字段 |


多层 **叠加加载**，高优先级层不会整表覆盖低优先级 hooks。

### 4.3 生命周期事件一览


| 事件                               | 作用域      | 常见用途                           | 能否介入行为（摘要）                                           |
| -------------------------------- | -------- | ------------------------------ | ---------------------------------------------------- |
| `SessionStart`                   | thread   | 会话启动/恢复时加载笔记                   | 注入 `additionalContext`；`continue: false` 可标记停止       |
| `UserPromptSubmit`               | turn     | 用户提示即将发送                       | 可 `decision: "block"`；可加上下文                          |
| `PreToolUse`                     | turn     | Bash / `apply_patch` / MCP 调用前 | `deny` / 改写 `updatedInput` / 加上下文（非完整强制边界）           |
| `PermissionRequest`              | turn     | 即将弹出审批时                        | `allow` / `deny`，否则走正常审批 UI                          |
| `PostToolUse`                    | turn     | 工具产出后                          | 可替换反馈、`continue: false`；**不能撤销已发生副作用**               |
| `PreCompact` / `PostCompact`     | turn     | 压缩前后                           | `continue: false` 可在压缩前/后停下                          |
| `SubagentStart` / `SubagentStop` | subagent | 子代理起停                          | 起：上下文；停：可要求再跑一轮                                      |
| `Stop`                           | turn     | 本轮 agent 将停下                   | `decision: "block"` **表示继续跑**（用 reason 当续写提示），不是拒绝本轮 |


范围说明：`PreToolUse` / `PostToolUse` 目前主要覆盖简易 shell、`apply_patch`、MCP；`unified_exec`、`WebSearch` 等路径拦截仍不完整。

### 4.4 与桌面端的关系

- 桌面端驱动的本地 agent 若使用同一 Codex home / 同一受信任项目配置，**会执行同一 hooks**。
- 管理信任、浏览 hook 源目前以 CLI `/hooks` 为主；桌面设置页主要管主题、通知权限等应用偏好。
- App Server 客户端还可调用 `hooks/list`，并收到 `hook/started` / `hook/completed`，便于在自研 UI 里展示「策略脚本正在跑」。

---



## 5. 程序消费 agent loop 的四条路径

按「介入深度」与「集成成本」选择。

### 路径 A：Hooks（循环内策略 / 侧写）

**适合：** 不写完整客户端，只要在「开始前 / 工具前 / 结束后」跑自家脚本。


| 你想做的事               | 推荐事件                             |
| ------------------- | -------------------------------- |
| 会话一开始注入规范 / 加载记忆    | `SessionStart`                   |
| 用户提交前扫密钥、拦危险 prompt | `UserPromptSubmit`               |
| 命令/改文件前策略引擎         | `PreToolUse`、`PermissionRequest` |
| 命令后审计、失败复盘          | `PostToolUse`                    |
| 回合结束强制再检查一轮         | `Stop`（`decision: "block"` = 继续） |
| 压缩前落盘摘要             | `PreCompact` / `PostCompact`     |


Handler 形态：`type: "command"`，工作目录为 session `cwd`；默认超时 600s。

最小示例（用户级 `~/.codex/hooks.json` 片段）：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/session_start.py",
            "statusMessage": "Loading session notes"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.codex/hooks/on_stop.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```



### 路径 B：`notify`（回合结束侧信道）

**适合：** 只要「agent 跑完提醒我」，例如桌面 toast、企业微信/Slack webhook、CI 状态。

在 **用户级** `~/.codex/config.toml`（项目级会忽略 `notify`，安全策略）：

```toml
notify = ["python3", "/path/to/notify.py"]
```

脚本从 **命令行参数** 收到一段 JSON；当前支持的类型主要是 `agent-turn-complete`，字段含 `thread-id`、`turn-id`、`cwd`、`input-messages`、`last-assistant-message` 等。

对比：


| 机制       | 粒度       | 能否拦截 agent |
| -------- | -------- | ---------- |
| hooks    | 多生命周期点   | 可以（按事件能力）  |
| `notify` | 基本只有回合完成 | 否，纯副作用     |


CLI 另有 `tui.notifications`（终端内建提醒），与外部 `notify` 程序不同。

### 路径 C：App Server / SDK（完整事件流 + 驱动循环）

**适合：** 自研编排台、外设状态灯（如 Codex Micro 类产品）、IDE、多 agent 并行监控——需要 **开始前 / 进行中 / 结束后的全量流**。


| 方式                             | 语言 / 形态         | 说明                                    |
| ------------------------------ | --------------- | ------------------------------------- |
| 直连 `codex app-server`          | 任意（自写 JSON-RPC） | 能力最全；可用 schema 生成绑定                   |
| Python SDK `openai-codex`      | Python ≥ 3.10   | 底层就是连本地 app-server                    |
| TypeScript `@openai/codex-sdk` | Node ≥ 18       | 应用内控制 thread；表面比 app-server 小，适合服务端编排 |


最小驱动骨架（概念）：

```ts
// 1) spawn: codex app-server
// 2) initialize + initialized
// 3) thread/start
// 4) turn/start { threadId, input: [...] }
// 5) 循环读 stdout：turn/started → item/* → turn/completed
```

可消费的「开始 / 结束」对照：


| 语义        | App Server 事件                     |
| --------- | --------------------------------- |
| 线程开始      | `thread/started`                  |
| 一轮工作开始    | `turn/started`                    |
| 某条消息/工具开始 | `item/started`                    |
| 流式正文      | `item/agentMessage/delta` 等       |
| 某条工作结束    | `item/completed`                  |
| 一轮结束      | `turn/completed`                  |
| Hook 脚本起止 | `hook/started` / `hook/completed` |
| 需要人批准     | server request（如权限审批）→ 客户端应答后循环继续 |




### 路径 D：`codex exec`（无 UI / CI）

**适合：** 流水线、一次性任务、把输出管道给下游。

```bash
codex exec --json "summarize the repo structure" | jq
```

`--json` 时 stdout 为 JSONL，事件类型包括 `thread.started`、`turn.started`、`turn.completed`、`turn.failed`、`item.*`、`error` 等——语义上贴近 app-server 的 thread/turn/item，但是 **单次进程、面向脚本**，不是长连 UI 协议。

还可用 `--output-schema` 约束最终结构化结果；`codex exec resume` 续跑。

### 其他相关入口（能力子集）


| 入口                         | 何时用                                        |
| -------------------------- | ------------------------------------------ |
| `codex mcp-server`         | 已有 MCP 编排，把 Codex 当可调用工具；会话语义弱于 App Server |
| Agents SDK 编排 MCP 中的 Codex | Codex 只是多智能体里的一员                           |


---



## 6. 选型速查

```text
只想在「开始前/工具前/结束后」跑脚本、改策略？
  → Hooks（必要时加 PermissionRequest）

只要回合完成弹通知 / webhook？
  → notify（用户级 config.toml）

要完整实时流、多线程、审批 UI、自研客户端？
  → App Server（或 Python/TS SDK）

CI / 脚本跑完拿结果？
  → codex exec（需要过程事件就加 --json）
```

若目标是「外设或旁路程序跟着 agent 状态变色/震动」：

1. **首选 App Server 事件流**（`thread/status`、`turn/`*、`item/*`）做实时态
2. 用 **hooks** 做策略与审计，不必用 hooks 驱动灯效
3. 用 `notify` 做「整轮结束」的粗粒度提醒即可

---



## 7. 与本仓库其他文档的关系

- [codex-micro-capabilities.md](./codex-micro-capabilities.md)：硬件键如何映射 agent 状态——状态源最终可来自 App Server 事件流。  
- [shortkey.md](./shortkey.md)：桌面端快捷键，属于应用外壳，不替代 hooks / app-server。

---



## 8. 参考链接

- [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/)
- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [Hooks – developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks)
- [App Server – developers.openai.com/codex/app-server](https://developers.openai.com/codex/app-server)
- [SDK – developers.openai.com/codex/sdk](https://developers.openai.com/codex/sdk)
- [Non-interactive – developers.openai.com/codex/noninteractive](https://developers.openai.com/codex/noninteractive)
- [Advanced Configuration（notify）](https://developers.openai.com/codex/config-advanced)
- 开源实现：`openai/codex` → `codex-rs/app-server`、Codex core

