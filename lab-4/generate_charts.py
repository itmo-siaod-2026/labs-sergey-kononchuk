"""
Generate benchmark charts from JMH JSON output.
Usage: python3 generate_charts.py results/results.json charts/
"""

import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import numpy as np

COLORS = {
    "concurrent": "#2196F3",
    "jdk":        "#4CAF50",
    "hashmap":    "#FF9800",
}


def load_results(path):
    with open(path) as f:
        raw = json.load(f)
    return {e["benchmark"].split(".")[-1]: (e["primaryMetric"]["score"],
                                             e["primaryMetric"]["scoreError"])
            for e in raw}


def bar_chart(ax, labels, values, errors, colors, ylabel="ops/ms", title=""):
    x = np.arange(len(labels))
    bars = ax.bar(x, values, yerr=errors, capsize=5, color=colors,
                  edgecolor="white", linewidth=0.5, width=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=14, ha="right", fontsize=8.5)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.015,
                f"{v/1000:.0f}k", ha="center", va="bottom", fontsize=7.5)


# ---------------------------------------------------------------------------
# 1. Single-thread comparison
# ---------------------------------------------------------------------------

def chart1_single_thread(ops, out):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fig.suptitle("Single-threaded throughput (1 thread)", fontsize=12, fontweight="bold")

    for ax, op in zip(axes, ["put", "get"]):
        specs = [
            (f"Custom\n({op})",  f"singleThread_{op}_concurrent", "concurrent"),
            (f"JDK CHM\n({op})",   f"singleThread_{op}_jdk",        "jdk"),
            (f"HashMap\n({op})",   f"singleThread_{op}_hashmap",    "hashmap"),
        ]
        lbls   = [s[0] for s in specs if s[1] in ops]
        vals   = [ops[s[1]][0] for s in specs if s[1] in ops]
        errs   = [ops[s[1]][1] for s in specs if s[1] in ops]
        colors = [COLORS[s[2]] for s in specs if s[1] in ops]
        bar_chart(ax, lbls, vals, errs, colors, title=f"{op}() single-threaded")

    plt.tight_layout()
    p = out / "chart1_single_thread.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {p}")


# ---------------------------------------------------------------------------
# 2. put() scalability
# ---------------------------------------------------------------------------

def chart2_scalability_put(ops, out):
    threads = [1, 2, 4, 8]
    km = {
        "concurrent": {1: "singleThread_put_concurrent", 2: "multiThread2_put",
                       4: "multiThread4_put",             8: "multiThread8_put"},
        "jdk":        {1: "singleThread_put_jdk",         2: "multiThread2_put_jdk",
                       4: "multiThread4_put_jdk",          8: "multiThread8_put_jdk"},
    }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, impl, color in [("Custom", "concurrent", COLORS["concurrent"]),
                                ("JDK CHM",  "jdk",        COLORS["jdk"])]:
        vals = [ops.get(km[impl][t], (0, 0))[0] for t in threads]
        errs = [ops.get(km[impl][t], (0, 0))[1] for t in threads]
        ax.errorbar(threads, vals, yerr=errs, marker="o", color=color,
                    label=label, linewidth=2, capsize=4)

    ax.set_xlabel("Thread count", fontsize=10)
    ax.set_ylabel("Throughput (ops/ms)", fontsize=10)
    ax.set_title("put() scalability vs thread count", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(threads)

    plt.tight_layout()
    p = out / "chart2_scalability_put.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {p}")


# ---------------------------------------------------------------------------
# 3. get() scalability (lock-free reads)
# ---------------------------------------------------------------------------

def chart3_scalability_get(ops, out):
    threads = [1, 2, 4, 8]
    km = {
        "concurrent": {1: "singleThread_get_concurrent", 2: "multiThread2_get",
                       4: "multiThread4_get",             8: "multiThread8_get"},
        "jdk":        {1: "singleThread_get_jdk",         2: "multiThread2_get_jdk",
                       4: "multiThread4_get_jdk",          8: "multiThread8_get_jdk"},
    }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, impl, color in [("Custom", "concurrent", COLORS["concurrent"]),
                                ("JDK CHM",  "jdk",        COLORS["jdk"])]:
        vals = [ops.get(km[impl][t], (0, 0))[0] for t in threads]
        errs = [ops.get(km[impl][t], (0, 0))[1] for t in threads]
        ax.errorbar(threads, vals, yerr=errs, marker="s", color=color,
                    label=label, linewidth=2, capsize=4)

    # ideal linear scale line
    base = ops.get("singleThread_get_concurrent", (100000, 0))[0]
    ax.plot(threads, [base * t for t in threads], linestyle=":", color="gray",
            linewidth=1.2, label="Ideal linear scale")

    ax.set_xlabel("Thread count", fontsize=10)
    ax.set_ylabel("Throughput (ops/ms)", fontsize=10)
    ax.set_title("get() scalability (lock-free reads)", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(threads)

    plt.tight_layout()
    p = out / "chart3_scalability_get.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {p}")


# ---------------------------------------------------------------------------
# 4. Mixed workloads
# ---------------------------------------------------------------------------

def chart4_mixed(ops, out):
    specs = [
        ("Read-heavy\n4T Custom",    "readHeavy4_concurrent",  "concurrent"),
        ("Read-heavy\n4T JDK",    "readHeavy4_jdk",         "jdk"),
        ("Read-heavy\n8T Custom",    "readHeavy8_concurrent",  "concurrent"),
        ("Read-heavy\n8T JDK",    "readHeavy8_jdk",         "jdk"),
        ("Write-heavy\n4T Custom",   "writeHeavy4_concurrent", "concurrent"),
        ("Write-heavy\n4T JDK",   "writeHeavy4_jdk",        "jdk"),
        ("Write-heavy\n8T Custom",   "writeHeavy8_concurrent", "concurrent"),
        ("Write-heavy\n8T JDK",   "writeHeavy8_jdk",        "jdk"),
    ]
    lbls   = [s[0] for s in specs if s[1] in ops]
    vals   = [ops[s[1]][0] for s in specs if s[1] in ops]
    errs   = [ops[s[1]][1] for s in specs if s[1] in ops]
    colors = [COLORS[s[2]] for s in specs if s[1] in ops]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    bar_chart(ax, lbls, vals, errs, colors,
              title="Mixed workloads: read-heavy (90% get / 10% put) vs write-heavy (80% put / 20% get)")

    legend = [mpatches.Patch(color=COLORS["concurrent"], label="Custom"),
              mpatches.Patch(color=COLORS["jdk"],        label="JDK CHM")]
    ax.legend(handles=legend, loc="upper right", fontsize=9)

    plt.tight_layout()
    p = out / "chart4_mixed_workloads.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {p}")


# ---------------------------------------------------------------------------
# 5. merge() contention
# ---------------------------------------------------------------------------

def chart5_merge(ops, out):
    specs = [
        ("Custom\n4 threads", "merge4_concurrent", "concurrent"),
        ("JDK CHM\n4 threads",  "merge4_jdk",        "jdk"),
    ]
    lbls   = [s[0] for s in specs if s[1] in ops]
    vals   = [ops[s[1]][0] for s in specs if s[1] in ops]
    errs   = [ops[s[1]][1] for s in specs if s[1] in ops]
    colors = [COLORS[s[2]] for s in specs if s[1] in ops]

    fig, ax = plt.subplots(figsize=(5, 4))
    bar_chart(ax, lbls, vals, errs, colors,
              title="merge() throughput\n(100-key range, high contention, 4 threads)")
    plt.tight_layout()
    p = out / "chart5_merge.png"
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {p}")


# ---------------------------------------------------------------------------
# 6. Стресс-сценарии, где выигрывает CHM (коллизии и resize-heavy)
# ---------------------------------------------------------------------------

def chart6_stress(out, stress_file="results/results_stress.json"):
    p_in = Path(stress_file)
    if not p_in.exists():
        print(f"  (no {stress_file}, skipping chart6)")
        return
    s = load_results(stress_file)  # {name: (score, error)}

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    fig.suptitle("Сценарии, на которые рассчитан CHM",
                 fontsize=12, fontweight="bold")

    # --- коллизии: throughput, log-шкала (разница в десятки раз) ---
    ax = axes[0]
    specs = [("get\nCustom", "collisionGet_concurrent", "concurrent"),
             ("get\nCHM",  "collisionGet_jdk",        "jdk"),
             ("put\nCustom", "collisionPut_concurrent", "concurrent"),
             ("put\nCHM",  "collisionPut_jdk",        "jdk")]
    vals = [s[k][0] for _, k, _ in specs]
    errs = [s[k][1] for _, k, _ in specs]
    cols = [COLORS[c] for _, _, c in specs]
    x = np.arange(len(specs))
    ax.bar(x, vals, yerr=errs, capsize=4, color=cols, edgecolor="white", width=0.6)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([l for l, _, _ in specs], fontsize=8.5)
    ax.set_ylabel("ops/ms (log)", fontsize=9)
    ax.set_title("5000 ключей в одну ячейку\n(выше = лучше)",
                 fontsize=9.5)
    ax.grid(axis="y", linestyle="--", alpha=0.35, which="both")
    for xi, v in zip(x, vals):
        ax.text(xi, v * 1.1, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)

    # --- resize-heavy: время, меньше=лучше ---
    ax = axes[1]
    specs = [("Custom", "bulkLoad8_concurrent", "concurrent"),
             ("CHM",  "bulkLoad8_jdk",        "jdk")]
    vals = [s[k][0] for _, k, _ in specs]
    errs = [s[k][1] for _, k, _ in specs]
    cols = [COLORS[c] for _, _, c in specs]
    x = np.arange(len(specs))
    ax.bar(x, vals, yerr=errs, capsize=5, color=cols, edgecolor="white", width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([l for l, _, _ in specs], fontsize=9)
    ax.set_ylabel("ms / bulk load (8 потоков)", fontsize=9)
    ax.set_title("Конкурентная заливка 500k ключей с ёмкости 16\n(ниже = лучше)",
                 fontsize=9.5)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    for xi, v in zip(x, vals):
        ax.text(xi, v + max(vals) * 0.02, f"{v:.1f} ms", ha="center", va="bottom", fontsize=8.5)

    for a in axes:
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)

    plt.tight_layout()
    pth = Path(out) / "chart6_stress.png"
    plt.savefig(pth, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {pth}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results_file = sys.argv[1] if len(sys.argv) > 1 else "results/results.json"
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "charts")
    out_dir.mkdir(parents=True, exist_ok=True)

    ops = load_results(results_file)
    print(f"Loaded {len(ops)} benchmark entries, generating charts...")

    chart1_single_thread(ops, out_dir)
    chart2_scalability_put(ops, out_dir)
    chart3_scalability_get(ops, out_dir)
    chart4_mixed(ops, out_dir)
    chart5_merge(ops, out_dir)
    chart6_stress(out_dir)

    print("Done.")
