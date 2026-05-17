# Self-Improving Compound · 自进化记忆系统

一个面向 AI Agent 的记忆与自进化系统，用结构化 SQLite 学习引擎替代朴素的文本记忆，通过实时捕获、定时审计、自动沉淀三层架构，让 Agent 越用越聪明。

## 解决什么问题

普通 Agent 每次都从零开始——昨天的错误今天还会犯，用户纠正过后下次还会遗忘。Self-Improving Compound 给 Agent 装上三个能力：

1. **当场记录**：任务结束前强制检查——有错误？有纠正？有 workaround？→ 写进 SQLite 记忆库
2. **事后审计**：每 2 小时扫描最近的对话记录，找出「明明犯过错但没记录」的遗漏
3. **自动升级**：经过验证的规则从 SQLite → Skill 文档 → Agent 指令，逐层固化

## 架构

```
对话中的错误/纠正/workaround
         │
         ▼
   ┌─────────────────┐
   │  Capture Gate    │  ← AGENTS.md 强制规则：最终回复前检查+记录
   │  search → log    │
   └────────┬────────┘
            │
   ┌────────▼────────┐
   │  cron Light Check│  ← 每 2h，隔离 session，sessions_history 扫描
   │  cron Heavy Audit│  ← 每 12h，生命周期维护+系统故障审计
   │  Daily Export    │  ← 每日导出 Markdown 供人类审阅
   └────────┬────────┘
            │
   ┌────────▼────────────────────────────┐
   │  learning/ → skills/ → AGENTS.md    │
   │            → TOOLS.md               │
   │            → MEMORY.md              │
   └─────────────────────────────────────┘
```

这是一个**封闭循环**：错误→记录→审计→升级→更少错误。

## 关键特性

- **SQLite 记忆引擎**：所有教训存为结构化 Chunk，支持评分、生命周期、去重、Pattern-Key 索引
- **Cron 审计管线**：通过 OpenClaw 隔离 cron 任务实现，不污染主对话上下文
- **Capture Gate 输出路由**：不同类型的教训自动流向正确目标（事实→memory/，错误→learning/，规则→skills/）
- **7+3 共演化模型**：7 个 Markdown 文件 + 3 个目录作为一个系统的不同层，任一层的改进推动其他层同步升级
- **Python 3.8+ CLI + Bash hooks**：无需网络、无需 Node.js 运行时

## 快速开始

```bash
# 1. 初始化学习存储
python3 scripts/learnings.py --root /path/to/workspace init

# 2. 记录一条纠正
python3 scripts/learnings.py --root /path/to/workspace log-correction \
  --summary "Telegram 用了表格格式" \
  --correct "用列表，不用表格" \
  --pattern chat:telegram-format

# 3. 搜索已有教训
python3 scripts/learnings.py --root /path/to/workspace search "telegram"

# 4. 每日导出
./scripts/learning-export.sh
```

## 安装到 OpenClaw

```bash
clawhub install self-improving-compound
```

安装后按 [`SKILL.md`](./SKILL.md) 的「激活硬化机制」章节配置 capture gate 和 cron 审计。

## 目录结构

```
learning/
├── memory_tree/chunks.db    # SQLite 源码真
├── index.md                 # 自动生成的快照
├── memory.md                # HOT 层（始终加载）
├── corrections.md           # 纠正日志
├── heartbeat-state.md       # 审计状态
├── projects/                # WARM 层（项目特定）
├── domains/                 # WARM 层（领域特定）
└── archive/                 # COLD 层（已归档）
```

## Author

Rockway Chen · [rockwaychen@gmail.com](mailto:rockwaychen@gmail.com) · [GitHub: LingmaFuture](https://github.com/LingmaFuture)

## License

MIT-0 — 自由使用、修改、分发。
