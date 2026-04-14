# A股数据源速查手册

> 基于akshare 1.18.49实测，持续更新

## 核心结论

- **最稳定：** 同花顺财务数据（stock_financial_abstract_ths）→ 无需代理
- **最关键：** BDI指数（macro_shipping_bdi）→ 无需代理
- **需代理：** 实时行情/历史K线 → 通过mihomo访问

---

## Layer 1：每日自动采集（稳定）

### 财务数据
```python
import akshare as ak

# 年报数据
annual = ak.stock_financial_abstract_ths("600150", "按年度")
# → 30行×25列：营收/净利/ROE/毛利率/负债率等

# 季报数据
quarterly = ak.stock_financial_abstract_ths("600150", "按报告期")
```

### BDI指数
```python
bdi = ak.macro_shipping_bdi().tail(1)
# → 最新BDI/BCI/BSI/BHMI
```

### 北向资金
```python
north = ak.stock_hsgt_hold_stock_em(symbol='北向资金')
ship = north[north['名称'].str.contains('船舶|动力')]
```

### 行业板块
```python
industries = ak.stock_board_industry_name_ths()
# → 90个行业分类
```

---

## Layer 2：定期采集（偶发失败）

### 资金流向
```python
flow = ak.stock_fund_flow_individual("600150")
# → 主力/散户/大单净流入
```

### 个股信息
```python
info = ak.stock_individual_info_em("600150")
# → 总市值/流通市值/市盈率/换手率等
```

---

## Layer 3：需代理（当前云服务器受限）

### 历史K线
```python
# 需要通过mihomo代理
hist = ak.stock_zh_a_hist(symbol="600150", period="daily",
                          start_date="20260101", end_date="20260415")
```

### 实时行情
```python
# 需要通过mihomo代理
spot = ak.stock_zh_a_spot_em()
# → 全市场实时行情（5000+股票）
```

---

## tushare（需Token）

```python
import tushare as ts
pro = ts.pro_api('YOUR_TOKEN')

# 财务数据（需要积分）
df = pro.fina_indicator(ts_code='600150.SH')
```

**Token配置位置：** memory/stock-portfolio.md 或 TOOLS.md

---

## 数据源可靠性排行

| 排名 | 数据源 | 稳定性 | 免费 | 代理需求 |
|------|--------|--------|------|---------|
| 1 | 同花顺财务 | ⭐⭐⭐⭐⭐ | ✅ | 无 |
| 2 | 波罗的海BDI | ⭐⭐⭐⭐⭐ | ✅ | 无 |
| 3 | 北向资金 | ⭐⭐⭐⭐ | ✅ | 无 |
| 4 | 东方财富资金流 | ⭐⭐⭐ | ✅ | 无 |
| 5 | 历史K线 | ⭐⭐⭐ | ✅ | **需代理** |
| 6 | 实时行情 | ⭐⭐ | ✅ | **需代理** |

---

*最后更新：2026-04-15（Day 26）*
