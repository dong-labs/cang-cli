# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Cang CLI

**仓咚咚 (Cang)** - 个人金融命令行工具，AI 原生设计。

### 核心设计原则

1. **Agent First, Human Second** - 所有命令设计优先考虑 AI 调用，而非人类体验
2. **极简主义** - 只做增删改查，不做报表、分析、建议
3. **确定性输出** - 所有命令返回 JSON，错误也要结构化
4. **边界清晰** - 明确定位每个模块的职责和不做什么

### 四个模块

| 模块 | 职责 | 核心问题 |
|------|------|----------|
| `cang fin` | 财务流动 | 钱怎么花的？ |
| `cang asset` | 资产存量 | 我拥有什么？ |
| `cang invest` | 投资记录 | 买卖了什么？ |
| `cang budget` | 预算管理 | 计划花多少？ |

### 技术栈

- **语言**: Python 3.11+
- **CLI 框架**: Typer
- **数据库**: SQLite (单文件 `~/.cang/cang.db`)
- **输出**: 所有命令返回 JSON

### 命令结构

```
cang
├── fin
│   ├── init           # 初始化数据库
│   ├── account ls/add/balance
│   ├── tx ls/add/get/summary
│   └── schema
├── asset (待开发)
├── invest (待开发)
└── budget (待开发)
```

### 输出格式规范

所有命令必须返回 JSON：

```json
{
  "success": true|false,
  "data": {...},           // 成功时
  "error": {...}           // 失败时
}
```

### 项目边界（严禁范围蔓延）

**做的：** 记收支、存数据、返回 JSON、CLI、AI 原生
**不做的：** 不记资产、不做图表、不做预算提醒、不同步银行、不做 GUI

> 原则："有疑问时，不加。想加新功能？先划掉一个旧的。"

### 开发顺序

1. **fin** - 最基础，每天都有
2. **budget** - 依赖 fin 的数据
3. **invest** - 独立，记录买卖
4. **asset** - 汇总所有，计算净值

### 安装与运行

```bash
# 开发模式安装
pip install -e .

# 运行
cang fin init
cang fin account ls
cang fin tx add --amount 29.9 --category 餐饮
```

### 模块独立性

每个模块在代码上互不依赖，共享同一个数据库。AI 负责调用、组合、分析。
