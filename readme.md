# Cang CLI

> 仓咚咚 - 个人金融命令行工具 (AI Native)

Cang CLI 是一个本地优先的个人财务管理工具，所有数据存储在本地 SQLite 数据库中。

## 特性

- 🏦 **账户管理** - 管理现金、银行卡、支付宝、微信等各类账户
- 💰 **收支记录** - 记录日常收入和支出，支持分类管理
- 🔄 **转账记录** - 记录账户间的转账
- 📊 **资产记录** - 记录固定资产（房产、车辆等）
- 💹 **投资记录** - 记录股票买卖、分红等投资交易
- 📋 **预算管理** - 设置和跟踪月度预算

## 安装

```bash
# 先安装依赖
pip install dong-core

# 安装 cang-cli
pipx install dong-cang
```

## 快速开始

### 初始化

```bash
cang init
```

### 添加账户

```bash
# 添加现金账户
cang fin account add "现金" cash

# 添加银行卡
cang fin account add "招商银行" bank --currency CNY
```

### 记录支出

```bash
# 记录一笔餐饮支出
cang fin tx add --account "现金" --amount 50 --category "餐饮" "午餐"

# 记录购物支出
cang fin tx add --account "招商银行" --amount 299 --category "购物" "买衣服"
```

### 记录收入

```bash
cang fin tx add --account "招商银行" --amount 10000 --category "工资" --type income "发工资"
```

### 查看账户

```bash
# 列出所有账户
cang fin account ls

# 查看账户余额
cang fin account get 1
```

### 记录资产

```bash
# 添加固定资产
cang asset add --name "自住房" --type real_estate --value 5000000

# 添加车辆
cang asset add --name "特斯拉 Model 3" --type vehicle --value 250000 --purchase-date "2024-01-01"
```

### 记录投资

```bash
# 买入股票
cang invest buy --symbol "600519" --price 1800 --quantity 100

# 卖出股票
cang invest sell --symbol "600519" --price 1850 --quantity 50

# 记录分红
cang invest dividend --symbol "600519" --amount 500
```

### 查看持仓

```bash
cang invest holdings
```

## 命令结构

```
cang
├── init              # 初始化数据库
├── fin               # 财务流动 (收支/转账)
│   ├── init
│   ├── account       # 账户管理
│   ├── tx            # 交易记录
│   ├── transfer      # 转账
│   └── category      # 分类管理
├── asset             # 资产存量
│   ├── init
│   ├── ls            # 列出资产
│   ├── add           # 添加资产
│   ├── get           # 获取资产
│   ├── update        # 更新资产
│   ├── delete        # 删除资产
│   └── networth      # 净资产统计
├── budget            # 预算管理
│   ├── init
│   ├── budget        # 设置预算
│   ├── status        # 预算状态
│   └── history       # 历史记录
└── invest            # 投资记录
    ├── init
    ├── ls            # 列出交易
    ├── buy           # 买入
    ├── sell          # 卖出
    ├── dividend      # 分红
    ├── holdings      # 持仓
    └── profit        # 收益
```

## 数据存储

所有数据存储在本地 `~/.dong/cang/cang.db` SQLite 数据库中。

## 设计原则

- **本地优先** - 数据在你电脑上，不上云
- **AI 原生** - 所有命令返回 JSON，方便 Agent 调用
- **一个工具一件事** - 只做记录，不做报表、分析、推荐

## 依赖

- Python >= 3.11
- dong-core >= 0.1.0
- typer >= 0.12.0

## 许可证

MIT License - see [LICENSE](LICENSE) for details.
