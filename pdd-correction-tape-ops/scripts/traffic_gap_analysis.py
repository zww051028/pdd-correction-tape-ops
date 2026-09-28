#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""traffic_gap_analysis.py — 拼多多修正带店铺流量缺口拆解计算器

用途：输入昨日（或任意一天）各渠道浏览量，输出距离目标浏览量的缺口、
各渠道应承担的目标量与差距、优先级排序，以及达成路径参考。

用法示例：
  python traffic_gap_analysis.py --search 1800 --recommend 900 --activity 200 --paid 300 --private 300
  python traffic_gap_analysis.py --total 6500 --target 20000 --days 60
  python traffic_gap_analysis.py --search 3000 --recommend 1600 --activity 400 --paid 800 --other 700 --depth 1.6

参数：
  --search      免费搜索渠道浏览量（不含付费）
  --recommend   推荐渠道浏览量
  --activity    活动渠道浏览量
  --paid        付费推广渠道浏览量
  --private     私域/老客回访浏览量
  --other       其他渠道浏览量（可选）
  --total       不知道渠道明细时，直接给总浏览量
  --target      目标日浏览量，默认 20000
  --depth       当前人均浏览深度，默认 1.8（用于反推访客数）
  --days        计划用多少天达成目标（输出所需日均复合增速）
"""

import argparse
import sys

# 成长期修正带店铺的目标渠道结构（占比）
BENCHMARK = [
    ("免费搜索", "search", 0.45,
     "关键词扩容、多链接矩阵卡位、坑产冲刺（限时折扣顶日销售额）"),
    ("推荐流量", "recommend", 0.25,
     "多多视频每周 2-3 条种草、高颜值款拉新、转化率优化"),
    ("活动流量", "activity", 0.15,
     "9.9 特卖/限时秒杀常驻，节点专题第一时间报名"),
    ("付费流量", "paid", 0.15,
     "多多搜索小额测词（日限 30-50 元起），节点加码到 100-200 元"),
    ("私域/老客", "private", 0.10,
     "包裹卡导关注、粉丝群专属券、45-60 天复购提醒"),
    ("其他", "other", 0.0,
     "占比异常时排查（分享裂变/站外等）"),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="拼多多修正带店铺流量缺口拆解")
    p.add_argument("--search", type=float)
    p.add_argument("--recommend", type=float)
    p.add_argument("--activity", type=float)
    p.add_argument("--paid", type=float)
    p.add_argument("--private", type=float)
    p.add_argument("--other", type=float)
    p.add_argument("--total", type=float, help="渠道明细未知时的总浏览量")
    p.add_argument("--target", type=float, default=20000)
    p.add_argument("--depth", type=float, default=1.8)
    p.add_argument("--days", type=float, help="计划达成天数")
    args = p.parse_args()

    channels = {k: v for k, v in {
        "search": args.search, "recommend": args.recommend,
        "activity": args.activity, "paid": args.paid,
        "private": args.private, "other": args.other,
    }.items() if v is not None}

    if not channels:
        if args.total is None:
            p.error("至少提供各渠道浏览量或 --total 总浏览量")
        channels = {"search": args.total * 0.45, "recommend": args.total * 0.25,
                    "activity": args.total * 0.15, "paid": args.paid or args.total * 0.15,
                    "private": args.total * 0.10, "other": args.other or 0.0}
        print("⚠️  未提供渠道明细，已按成长期基准结构估算（建议补录后台渠道数据）\n")

    total = sum(channels.values())
    gap = args.target - total

    print("=" * 62)
    print(f"当前日浏览量合计: {total:,.0f}    目标: {args.target:,.0f}    缺口: {gap:+,.0f}")
    print(f"按人均浏览深度 {args.depth:.1f} 估算: 当前访客约 {total/args.depth:,.0f}，"
          f"目标访客约 {args.target/args.depth:,.0f}")
    if args.days:
        if args.days > 1 and total > 0:
            rate = (args.target / total) ** (1 / args.days) - 1
            print(f"{args.days:.0f} 天达成目标所需日均复合增速: {rate*100:.1f}%/天")
        elif total <= 0:
            print("当前浏览量为 0，无法计算增速，请先完成链接冷启动（基础销量 50-100 单）")
    print("=" * 62)

    rows = []
    for label, key, share, action in BENCHMARK:
        cur = channels.get(key, 0.0)
        tgt = args.target * share
        rows.append((label, cur, cur / total * 100 if total else 0,
                     tgt, tgt - cur, action))

    # 优先级：缺口绝对值大且当前占比低于基准占比的渠道优先
    def priority(row):
        label, cur, cur_pct, tgt, gap_c, _ = row
        bench_share = dict((k, s) for _, k, s, _ in BENCHMARK)[
            [k for l, k, _, _ in BENCHMARK if l == label][0]]
        return gap_c if cur_pct / 100 < bench_share + 0.05 else gap_c * 0.5

    rows.sort(key=priority, reverse=True)

    print(f"\n{'渠道':<8}{'当前':>8}{'占比':>7}{'目标':>9}{'缺口':>9}  优先动作")
    print("-" * 62)
    for label, cur, pct, tgt, gap_c, action in rows:
        flag = "🔴" if gap_c > 3000 else ("🟡" if gap_c > 1000 else "🟢")
        print(f"{label:<7}{cur:>8,.0f}{pct:>6.1f}%{tgt:>9,.0f}{gap_c:>+9,.0f}  {flag} {action}")

    print("-" * 62)
    print("建议：每天优先补缺口最大的 1-2 个渠道（🔴），动作清单见晨报；"
          "节点期（开学季/618）活动流量目标可上浮至 30%+。")
    if gap > 0:
        print(f"提示：缺口 {gap:,.0f} 相当于每天多出 {gap/args.depth:,.0f} 个访客，"
              f"或靠活动/爆款单链接日增 {gap:,.0f} 次浏览。")


if __name__ == "__main__":
    main()
