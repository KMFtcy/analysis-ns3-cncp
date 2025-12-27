import matplotlib.pyplot as plt
import sys
from matplotlib.ticker import FuncFormatter
import math
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 设置全局字体样式
plt.rcParams.update({
    # 'font.family': 'Times New Roman',
    'font.size': 14,  # 增加基础字体大小
    # 'font.weight': 'bold',
    # 'axes.labelweight': 'bold',
    # 'axes.titleweight': 'bold',
    'axes.labelsize': 24,  # 增加坐标轴标签字体大小
    'axes.titlesize': 22,  # 增加标题字体大小
    'xtick.labelsize': 22,  # 增加x轴刻度标签字体大小
    'ytick.labelsize': 22,  # 增加y轴刻度标签字体大小
    'legend.fontsize': 22,  # 增加图例字体大小
    'legend.title_fontsize': 24  # 增加图例标题字体大小
})

def format_size(x, pos):
    if x >= 1_000_000:
        return f'{x/1_000_000:.0f}M'
    elif x >= 1_000:
        return f'{x/1_000:.0f}K'
    else:
        return f'{int(x)}'

def draw_fct_analysis(result_file, cc_names):
    """
    画出分析结果的三幅图：中位数、95分位、99分位 slow down
    :param result_file: 分析结果文件名
    :param cc_names: CC名字列表，顺序与分析时一致
    """
    logging.info(f"开始处理: 结果文件={result_file}, CC算法数量={len(cc_names)}")
    logging.info(f"CC算法列表: {', '.join(cc_names)}")
    
    # 读取数据
    x = []  # 文件大小
    y_median = [[] for _ in cc_names]
    y_95 = [[] for _ in cc_names]
    y_99 = [[] for _ in cc_names]

    total_lines = 0
    skipped_lines = 0
    with open(result_file, 'r') as fin:
        for line in fin:
            total_lines += 1
            parts = line.strip().split()
            if len(parts) < 2 + 3 * len(cc_names):
                skipped_lines += 1
                continue
            x.append(int(parts[1]))
            for idx in range(len(cc_names)):
                base = 2 + idx * 3
                y_median[idx].append(float(parts[base]))
                y_95[idx].append(float(parts[base+1]))
                y_99[idx].append(float(parts[base+2]))
    
    logging.info(f"数据读取完成: 总行数={total_lines}, 有效数据行数={len(x)}, 跳过行数={skipped_lines}")
    if len(x) == 0:
        logging.warning("警告: 没有读取到有效数据!")
        return

    # 画图
    logging.info(f"开始绘图: 数据点数量={len(x)}")
    percentiles = ['Median', '95th', '99th']
    y_all = [y_median, y_95, y_99]

    x_labels = x
    x_pos = list(range(len(x_labels)))

    # 新增：合并为一幅宽图
    max_per_row = 5  # 每行最多4个图例，可根据实际宽度调整
    legend_rows = math.ceil(len(cc_names) / max_per_row)
    base_height = 7
    fig_height = base_height + 1.0  # 额外为legend留空间
    fig, axes = plt.subplots(1, 3, figsize=(24, fig_height), dpi=300)  # 横向三图，宽度可根据需要调整
    handles, labels = [], []
    subtitle_labels = ['Avg.', '95pct', '99pct']
    for i, ax in enumerate(axes):
        y = y_all[i]
        for idx, cc in enumerate(cc_names):
            line, = ax.plot(x_pos, y[idx], label=cc, linewidth=5)
            if i == 0:  # 只收集一次图例
                handles.append(line)
                labels.append(cc)
        # ax.set_xlabel('Flow size (Byte)')
        # ax.set_ylabel('FCT Slow down')
        # ax.set_title(f'FCT Slow Down - {percentiles[i]}', pad=20)
        # 设置稀疏的x轴标签
        step = max(1, len(x_labels) // 10)  # 让每个子图大约6个x轴标签
        xtick_pos = x_pos[::step]
        xtick_labels = [format_size(val, None) for val in x_labels][::step]
        ax.set_xticks(xtick_pos)
        ax.set_xticklabels(xtick_labels, rotation=45)
        # 在每个子图左上角添加标签
        ax.text(0.1, 0.8, subtitle_labels[i], transform=ax.transAxes, fontsize=34, va='top', ha='left')
    # 添加统一图例
    ncol = min(len(cc_names), max_per_row)
    leg = fig.legend(handles, labels, loc='upper center', ncol=ncol, fontsize=24, bbox_to_anchor=(0.5, 1.13))
    leg.get_frame().set_linewidth(0)  # 去除边框
    fig.supxlabel('Flow size (Byte)', fontsize=34, x=0.5)
    fig.supylabel('FCT Slow down', fontsize=34)
    fig.tight_layout(rect=[0, 0, 1, 0.98])

    # 将图片保存到结果文件所在目录
    out_dir = os.path.dirname(os.path.abspath(result_file))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_filename = f'fct_slowdown_all_{timestamp}.png'
    out_path = os.path.join(out_dir, out_filename)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    logging.info(f"图片已保存: {out_path}")

if __name__ == "__main__":
    # 用法示例：
    # python draw_fct_analysis.py result_file cc1 cc2 ...
    if len(sys.argv) < 3:
        print("Usage: python draw_fct_analysis.py <result_file> <cc1> <cc2> ...")
        sys.exit(1)
    result_file = sys.argv[1]
    cc_names = sys.argv[2:]
    draw_fct_analysis(result_file, cc_names)
