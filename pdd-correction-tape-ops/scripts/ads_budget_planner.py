#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ads_budget_planner.py — 拼多多修正带店铺付费投放预算测算器

用途：在投放前算清盈亏平衡点，避免"投得越多亏得越多"。
输入客单价、毛利率、点击单价、转化率、日预算，输出：
  - 盈亏平衡点击单价（超过这个价就是亏）
  - ROI 预测
  - 100 元预算的渠道分配建议
  - 风险等级与行动建议

用法示例：
  python ads_budget_planner.py --price 5.9 --margin 0.35 --cpc 0.3 --cvr 0.03 --budget 100
  python ads_budget_planner.py --price 15 --margin 0.35 --cpc 0.3 --cvr 0.05 --budget 100
  python ads_budget_planner.py --price 5.9 --quick          # 快速跑常见组合
"""

import argparse
import sys


def plan(price, margin, cpc, cvr, budget, offline_rate=0.05):
    """返回测算结果字典。

    offline_rate: 退款/退货率，默认 5%，从毛利中扣除
    """
    gross_per_order = price * margin * (1 - offline_rate)   # 每单实际毛利
    clicks = budget / cpc
    orders = clicks * cvr
    revenue = orders * price
    organic_profit = orders * gross_per_order              # 成交带来的毛利
    net = organic_profit - budget                           # 扣除推广费后的净利
    roi = revenue / budget if budget else 0
    breakeven_cpc = gross_per_order * cvr if cvr else 0     # 盈亏平衡点击单价
    breakeven_cvr = cpc / gross_per_order if gross_per_order else 0  # 盈亏平衡转化率
    return {
        "gross_per_order": gross_per_order, "clicks": clicks, "orders": orders,
        "revenue": revenue, "organic_profit": organic_profit, "net": net,
        "roi": roi, "breakeven_cpc": breakeven_cpc, "breakeven_cvr": breakeven_cvr,
    }


def risk_level(r):
    if r["net"] > 0 and r["roi"] >= 1.5:
        return "🟢 健康", "可放心投放，逐步提预算"
    if r["net"] > 0 and r["roi"] >= 1.0:
        return "🟡 微利", "保持预算，重点优化转化率与客单价以提升 ROI"
    if r["net"] <= 0 and r["roi"] >= 0.7:
        return "🟠 亏损但可接受", "视为买权重成本；必须确认免费流量在涨，否则 7 天内停投"
    return "🔴 严重亏损", "立即停投！先修转化率与客单价（见下方建议），再谈投放"


def allocate(budget, mode):
    if mode == "node":
        return [("多多搜索（主推款抢排名）", budget * 0.50),
                ("全站推广（主推款放量）", budget * 0.25),
                ("场景推广（高颜值款拉新）", budget * 0.25)]
    return [("多多搜索（主推款·长尾词）", budget * 0.50),
            ("场景推广（高颜值款·吃竞品流量）", budget * 0.30),
            ("全站推广（主推款·按成交出价）", budget * 0.20)]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="拼多多修正带付费投放预算测算")
    p.add_argument("--price", type=float, required=True, help="主推款客单价（元）")
    p.add_argument("--margin", type=float, default=0.35, help="毛利率，默认 0.35")
    p.add_argument("--cpc", type=float, default=0.30, help="平均点击单价，默认 0.30")
    p.add_argument("--cvr", type=float, default=0.03, help="支付转化率，默认 0.03")
    p.add_argument("--budget", type=float, default=100, help="日推广预算，默认 100")
    p.add_argument("--mode", choices=["daily", "node"], default="daily",
                   help="daily=日常期，node=节点期（分配比例不同）")
    p.add_argument("--quick", action="store_true", help="快速跑常见客单价组合对比")
    args = p.parse_args()

    if args.quick:
        print("=" * 68)
        print("常见客单价 × 点击单价 的 ROI 对比（毛利率 35%，转化率 3%，退款率 5%）")
        print("=" * 68)
        print(f"{'客单价':>8}{'点击单价':>10}{'日订单':>9}{'日销售额':>10}{'ROI':>8}{'净利':>9}  风险")
        print("-" * 68)
        for price in [3.9, 5.9, 9.9, 15.0]:
            for cpc in [0.15, 0.25, 0.35]:
                r = plan(price, 0.35, cpc, 0.03, 100)
                lvl, _ = risk_level(r)
                print(f"{price:>8.1f}{cpc:>10.2f}{r['orders']:>9.1f}"
                      f"{r['revenue']:>10.0f}{r['roi']:>8.2f}{r['net']:>+9.1f}  {lvl}")
        print("-" * 68)
        print("结论：客单价 <10 元时，点击单价 0.25 元以上基本必亏。")
        print("      修正带投放正确定位 = 买权重，靠免费流量增长回本。")
        return

    r = plan(args.price, args.margin, args.cpc, args.cvr, args.budget)
    lvl, advice = risk_level(r)

    print("=" * 62)
    print("付费投放测算")
    print("=" * 62)
    print(f"输入：客单价 ¥{args.price} | 毛利率 {args.margin:.0%} | 点击单价 ¥{args.cpc}"
          f" | 转化率 {args.cvr:.1%} | 日预算 ¥{args.budget}")
    print("-" * 62)
    print(f"预计日点击：{r['clicks']:.0f} 次")
    print(f"预计日订单：{r['orders']:.1f} 单")
    print(f"预计日销售额：¥{r['revenue']:.0f}")
    print(f"预计 ROI：{r['roi']:.2f}")
    print(f"扣除推广费后净利：¥{r['net']:+.1f} / 天  （月 {r['net']*30:+.0f} 元）")
    print("-" * 62)
    print(f"盈亏平衡点击单价：¥{r['breakeven_cpc']:.3f}  "
          f"（当前 ¥{args.cpc}，{'✅ 在安全线内' if args.cpc <= r['breakeven_cpc'] else '❌ 已超出！'}）")
    print(f"盈亏平衡所需转化率：{r['breakeven_cvr']:.2%}  "
          f"（当前 {args.cvr:.1%}，{'✅ 达标' if args.cvr >= r['breakeven_cvr'] else '❌ 不足'}）")
    print("=" * 62)
    print(f"风险等级：{lvl}")
    print(f"行动建议：{advice}")

    print(f"\n【{args.budget:.0f} 元预算分配建议（{'节点期' if args.mode=='node' else '日常期'}）】")
    for name, amount in allocate(args.budget, args.mode):
        print(f"  · {name}：¥{amount:.0f}/天")

    print("\n【提效要点】")
    print("  1. 只投长尾词（修正带3个装/学生用），不投大词「修正带」")
    print("  2. 出价从市场均价 80% 起步，跑 3 天看数据再加")
    print("  3. 点击率<3% 先换主图；烧满 30 元零成交当天关词")
    print("  4. 判定投放成功的唯一标准：免费流量涨了没有")
    if r["net"] <= 0:
        print("\n【亏损补救】提高客单价的三个动作：")
        print("  · 推「3支装+错题本」组合装，把客单从 6 元提到 12-15 元")
        print("  · 详情页加关联套餐，凑单满减（满 15 减 3）")
        print("  · 转投场景推广（点击价通常比搜索低 30%）")


if __name__ == "__main__":
    main()
