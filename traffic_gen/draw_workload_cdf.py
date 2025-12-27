import matplotlib.pyplot as plt

# 设置全局字体样式
plt.rcParams.update({
    # 'font.family': 'Times New Roman',
    'font.size': 14,  # 增加基础字体大小
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titleweight': 'bold',
    'axes.labelsize': 20,  # 增加坐标轴标签字体大小
    'axes.titlesize': 20,  # 增加标题字体大小
    'xtick.labelsize': 20,  # 增加x轴刻度标签字体大小
    'ytick.labelsize': 16,  # 增加y轴刻度标签字体大小
    'legend.fontsize': 18,  # 增加图例字体大小
    'legend.title_fontsize': 24  # 增加图例标题字体大小
})

workloads = [
    # {
    #     'name': 'AliStorage2019',
    #     'file': 'AliStorage2019.txt'
    # },
    {
        'name': 'Facebook Hadoop',
        'file': 'FbHdp_distribution.txt'
    },
    {
        'name': 'Google RPC',
        'file': 'GoogleRPC2008.txt'
    },
    {
        'name': 'Web Search',
        'file': 'WebSearch_distribution.txt'
    },
]

def read_distribution(file_path):
    sizes = []
    percentiles = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                size = float(parts[0])
                if size == 0:
                    size = 0.1
                sizes.append(size)
                percentiles.append(float(parts[1]))
    return sizes, percentiles

plt.figure(figsize=(10, 4))

for workload in workloads:
    file_path = workload['file']
    name = workload['name']
    try:
        sizes, percentiles = read_distribution(file_path)
        plt.plot(sizes, percentiles, label=name)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

plt.xlabel('Flow Size (Bytes)')
plt.ylabel('CDF (%)')
# plt.title('Workload Flow Size CDF')
plt.legend(
    loc='lower center',           # 图例在下方中央
    bbox_to_anchor=(0.5, 1.02),   # 0.5表示x轴居中，1.02表示在图的上方
    ncol=3,                       # 图例分为3列（根据你的曲线数量调整）
    frameon=False                 # 去掉图例边框（可选）
)
plt.xscale('log')
plt.xlim(left=1)
plt.ylim(bottom=0)
plt.tight_layout()
# plt.minorticks_on()
# plt.tick_params(axis='y', which='minor', length=4)
plt.yticks(range(0, 110, 25))
plt.savefig('workload_cdf_comparison.png')
plt.show()