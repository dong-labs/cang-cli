# TOOLS.md - 仓咚咚的工具箱

> 基于 Cang CLI 的 Agent 工具定义
> 所有数据操作通过 CLI 命令完成

---

## 🛠️ 工具调用方式

```bash
cang <module> <command> [options]
```

所有命令返回 JSON 格式：
```json
{"success": true|false, "data": {...}|{"error": {...}}
```

---

## 🚀 初始化

```bash
# 初始化数据库
cang init
```

---

## 📊 财务流动工具 (fin)

### 账户管理

```bash
# 列出所有账户
cang fin account ls

# 添加账户
cang fin account add --name "招商银行" --type bank --currency CNY

# 查询账户详情
cang fin account get --account-id 1

# 查询账户余额
cang fin account balance --account-id 1
```

### 交易记录

```bash
# 列出交易
cang fin tx ls --limit 10
cang fin tx ls --account-id 1 --category 餐饮

# 添加交易
cang fin tx add --amount 2500 --account 1 --category 餐饮 --note "午饭"

# 查询交易详情
cang fin tx get --tx-id 1

# 更新交易
cang fin tx update --tx-id 1 --amount 3000 --note "加个蛋"

# 删除交易
cang fin tx delete --tx-id 1

# 交易汇总
cang fin tx summary --start-date 2026-03-01 --end-date 2026-03-31 --group-by category
cang fin tx summary --group-by account
cang fin tx summary --group-by date
```

### 分类管理

```bash
# 列出分类
cang fin category ls

# 添加分类
cang fin category add --name "宠物"
```

### 转账

```bash
# 创建转账
cang fin transfer --from-account 1 --to-account 2 --amount 10000 --fee 50

# 列出转账记录
cang fin transfer ls
```

---

## 🏠 资产工具 (asset)

```bash
# 初始化
cang asset init

# 列出资产
cang asset ls

# 添加资产
cang asset add --name "腾讯控股" --type stock --value 500000 --code 00700

# 查询资产详情
cang asset get --asset-id 1

# 更新资产价值
cang asset update --asset-id 1 --value 520000

# 删除资产
cang asset delete --asset-id 1

# 查看净资产
cang asset networth

# 查看表结构
cang asset schema
```

---

## 📈 投资工具 (invest)

### 交易记录

```bash
# 初始化
cang invest init

# 列出交易
cang invest ls --symbol 510300
cang invest ls --type buy
cang invest ls --invest-tx-id 1

# 买入
cang invest buy --symbol 510300 --price 4.0 --quantity 100 --date 2026-03-15

# 卖出
cang invest sell --symbol 510300 --price 4.2 --quantity 50 --date 2026-03-20

# 分红
cang invest dividend --symbol 510300 --amount 500 --date 2026-03-25
```

### 持仓与收益

```bash
# 查看持仓
cang invest holdings
cang invest holdings --symbol 510300

# 查看收益
cang invest profit
cang invest profit --symbol 510300
cang invest profit --period all
cang invest profit --period month

# 查看表结构
cang invest schema
```

---

## 📊 预算工具 (budget)

```bash
# 初始化
cang budget init

# 列出预算
cang budget budget ls --period monthly
cang budget budget ls --category 餐饮

# 设置预算
cang budget budget set --category 餐饮 --amount 1200 --period monthly

# 查询预算详情
cang budget budget get --budget-id 1

# 更新预算
cang budget budget update --budget-id 1 --amount 1500

# 删除预算
cang budget budget delete --budget-id 1

# 查看预算状态
cang budget status

# 查看历史
cang budget history

# 查看表结构
cang budget schema
```

---

## 🎯 常用场景映射

| 用户说 | AI 调用的命令 |
|-----------------------|
| **记账** |
| "午饭 25" | `cang fin tx add --amount 2500 --account 1 --category 餐饮 --note "午饭"` |
| "工资到账 5000" | `cang fin tx add --amount 500000 --account 1 --category 工资 --note "月薪"` |
| **查询** |
| "我有钱吗" | `cang fin account balance --account-id 1` |
| "这月花了多少" | `cang fin tx summary --start-date <本月1号> --end-date <今天> --group-by category` |
| "净资产多少" | `cang asset networth` |
| "基金赚了多少" | `cang invest profit --symbol <基金代码>` |
| "预算用了多少" | `cang budget status` |
| **管理** |
| "设置餐饮预算 1200" | `cang budget budget set --category 餐饮 --amount 120000 --period monthly` |
| "买了台电脑 8000" | `cang asset add --name "电脑" --type electronic --value 800000` |

---

## 📋 分类标准

| 分类 | 说明 | Emoji | 自动关键词 |
|------|------|-------|-----------|
| 餐饮 | 早中晚饭、零食、饮料 | 🍜 | 饭、餐、吃、喝、零食 |
| 交通 | 地铁、公交、打车、加油 | 🚗 | 地铁、打车、加油、停车 |
| 购物 | 日用品、衣服、电子设备 | 🛍️ | 买、购、淘宝、京东 |
| 娱乐 | 电影、游戏、聚会 | 🎮 | 电影、游戏、KTV |
| 居住 | 房租、房贷、水电、物业 | 🏠 | 房租、房贷、物业、水电 |
| 通讯 | 手机、网络 | 📱 | 手机、话费、宽带 |
| 医疗 | 看病、买药 | 💊 | 医院、药店、买药 |
| 学习 | 书籍、课程 | 📚 | 书、课程、培训 |
| 投资 | 股票、基金、理财 | 📈 | 基金、股票、理财、定投 |
| 其他 | 无法分类的支出 | 📦 | - |
| 工资 | 收入 | 💵 | 工资、奖金、副业 |

---

## 🔧 金额转换规则

- 用户输入：`25` (元)
- CLI 需要：`2500` (分)
- 转换：`amount_cents = int(amount * 100)`

---

## 📌 默认配置

```yaml
# 默认账户 ID（根据实际情况调整）
default_account_id: 1

# 默认货币
default_currency: CNY
```

---

*所有工具基于 Cang CLI，数据存储在 ~/.cang/cang.db* 🐹
