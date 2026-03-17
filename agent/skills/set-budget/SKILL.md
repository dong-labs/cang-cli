---
name: set-budget
description: 设置预算。当用户说"设置预算"、"预算设为XX"、"餐饮预算1000"时使用。
---

# 设置预算

## 功能

为某个分类设置月度预算。

## CLI 命令

```bash
cang budget budget set --category <分类> --amount <金额分> --period month
```

## 示例

用户："餐饮预算设为1000"
执行：设置餐饮分类月度预算 100000 分

## 输出格式

```
预算设置成功！✅

分类：餐饮
周期：月度
金额：1,000 元
```
