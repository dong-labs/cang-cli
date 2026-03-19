# TOOLS.md - 工具箱

我的核心工具是 `dong-cang` CLI。

## 安装

```bash
pipx install cang-cli
```

## 命令列表

### 初始化

```bash
dong-cang init
```

### 记录交易

```bash
dong-cang add "午餐" 25 --category food
dong-cang add "工资" 10000 --type income --category salary
dong-cang add "地铁" 6 --category transport
```

### 列出交易

```bash
dong-cang list                  # 列出最近交易
dong-cang list --month          # 本月交易
dong-cang list --category food  # 按分类筛选
```

### 统计信息

```bash
dong-cang stats                 # 统计收支情况
dong-cang stats --month         # 本月统计
```

## JSON 输出

所有命令支持 JSON 输出，方便 AI 解析：

```bash
dong-cang add "xxx" 100
dong-cang list
dong-cang stats
```

## 数据库

数据存储在 `~/.dong/cang.db`

---

*🐹 帮你管钱的小仓鼠*
