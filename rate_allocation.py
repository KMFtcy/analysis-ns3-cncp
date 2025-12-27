import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse

# 设置全局字体样式
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 14,  # 增加基础字体大小
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titleweight': 'bold',
    'axes.labelsize': 24,  # 增加坐标轴标签字体大小
    'axes.titlesize': 22,  # 增加标题字体大小
    'xtick.labelsize': 22,  # 增加x轴刻度标签字体大小
    'ytick.labelsize': 22,  # 增加y轴刻度标签字体大小
    'legend.fontsize': 22,  # 增加图例字体大小
    'legend.title_fontsize': 24  # 增加图例标题字体大小
})

# 读取日志文件
def read_log_file(file_path):
    # 定义列名 - 更新以匹配新的日志格式
    columns = ['node_id', 'ip', 'sport', 'dport', 'old_rate', 'new_rate', 'timestamp']
    # 只读取以 [CNCP Update] 开头的行，并去掉前缀
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line[len('[CNCP Update] '):] for line in f if line.startswith('[CNCP Update]')]
    print("len(lines):", len(lines))
    # 用pd.read_csv解析这些行
    from io import StringIO
    df = pd.read_csv(StringIO(''.join(lines)), sep=' ', names=columns)
    print("df.head():", df.head())
    # print length of df
    print("len(df):", len(df))
    
    # 添加调试信息
    print(f"node_id column dtype: {df['node_id'].dtype}")
    print(f"node_id unique values: {df['node_id'].unique()}")
    print(f"Sample node_id values: {df['node_id'].head()}")
    
    # 确保时间戳为数值类型，并将日志中的纳秒转换为秒，便于与CLI的秒级参数比较
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['timestamp'] = df['timestamp'] / 1e9
    
    return df

def plot_rates(df, node_id=4, ip=None, sport=None, dport=None, timestamp_start=None, timestamp_end=None):
    # 筛选指定条件的数据
    filtered_data = df[df['node_id'] == node_id]
    print(f"After filtering by node_id={node_id}: {len(filtered_data)} records")
    print(f"Sample of filtered data:")
    print(filtered_data.head())
    
    # 时间区间过滤（参数为秒，日志时间戳已转换为秒）
    if timestamp_start is not None:
        filtered_data = filtered_data[filtered_data['timestamp'] >= timestamp_start]
        print(f"After filtering by timestamp_start={timestamp_start}s: {len(filtered_data)} records")
    if timestamp_end is not None:
        filtered_data = filtered_data[filtered_data['timestamp'] <= timestamp_end]
        print(f"After filtering by timestamp_end={timestamp_end}s: {len(filtered_data)} records")
    
    if ip is not None:
        filtered_data = filtered_data[filtered_data['ip'] == ip]
        print(f"After filtering by ip={ip}: {len(filtered_data)} records")
    if sport is not None:
        filtered_data = filtered_data[filtered_data['sport'] == sport]
        print(f"After filtering by sport={sport}: {len(filtered_data)} records")
    if dport is not None:
        filtered_data = filtered_data[filtered_data['dport'] == dport]
        print(f"After filtering by dport={dport}: {len(filtered_data)} records")
    
    if filtered_data.empty:
        print(f"No data found for the specified criteria: node_id={node_id}, ip={ip}, sport={sport}, dport={dport}")
        return
    
    # 分离有效数据和跳过的数据
    valid_data = filtered_data[(filtered_data['old_rate'] != -1) | (filtered_data['new_rate'] != 0)]
    skipped_data = filtered_data[(filtered_data['old_rate'] == -1) & (filtered_data['new_rate'] == 0)]
    
    print(f"Valid data count: {len(valid_data)}")
    print(f"Skipped data count: {len(skipped_data)}")
    print(f"Sample of valid data:")
    print(valid_data.head())
    
    if valid_data.empty:
        print(f"No valid data found for the specified criteria: node_id={node_id}, ip={ip}, sport={sport}, dport={dport}")
        return
    
    # 设置绘图风格
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6), dpi=300)  # 增加DPI以提高图片质量
    
    # 创建自定义颜色映射
    color_dict = {100: 'red', 101: 'blue'}
    label_dict = {100: '1', 101: '2'}  # 新的标签映射
    
    # 绘制折线图（只使用有效数据）
    for dport in valid_data['dport'].unique():
        flow_data = valid_data[valid_data['dport'] == dport]
        color = color_dict.get(dport, 'green')  # 默认绿色
        label = label_dict.get(dport, str(dport))  # 默认使用flow_id作为标签
        plt.plot(flow_data['timestamp'], flow_data['new_rate'] / 1e9, 
                color=color, 
                linewidth=2.5,  # 增加线条粗细
                label=f'Flow {label}')  # 使用新的标签
    
    # 在x轴上标记跳过的更新点
    if not skipped_data.empty:
        # 获取y轴的最小值，用于放置红点
        y_min = plt.gca().get_ylim()[0] if plt.gca().get_ylim()[0] != 0 else -0.1
        
        # 为每个dport绘制跳过的点
        for dport in skipped_data['dport'].unique():
            skipped_timestamps = skipped_data[skipped_data['dport'] == dport]['timestamp']
            plt.scatter(skipped_timestamps, [y_min] * len(skipped_timestamps), 
                       color='red', s=50, marker='o', alpha=0.7, 
                       label=f'Skipped updates (Flow {label_dict.get(dport, str(dport))})' if dport == skipped_data['dport'].iloc[0] else "")
    
    # 设置图表标题和标签
    title_parts = [f'Node {node_id}']
    # if ip:
    #     title_parts.append(f'IP: {ip}')
    # if sport:
    #     title_parts.append(f'SPort: {sport}')
    # if dport:
    #     title_parts.append(f'DPort: {dport}')
    # if timestamp_start is not None or timestamp_end is not None:
    #     title_parts.append(f'Time: {timestamp_start if timestamp_start is not None else "-"} ~ {timestamp_end if timestamp_end is not None else "-"} (s)')
    
    plt.title(' - '.join(title_parts), pad=20)
    plt.xlabel('Timestamp (s)')
    plt.ylabel('Rate (Gbps)')
    
    # 设置网格线样式
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 显示图例
    plt.legend(title='Flow ID', frameon=True, framealpha=1)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表（使用高DPI）
    filename_parts = [f'node_{node_id}']
    if ip:
        filename_parts.append(f'ip_{ip.replace(".", "_")}')
    if sport:
        filename_parts.append(f'sport_{sport}')
    if dport:
        filename_parts.append(f'dport_{dport}')
    if timestamp_start is not None or timestamp_end is not None:
        filename_parts.append(f'ts_{timestamp_start if timestamp_start is not None else "-"}_{timestamp_end if timestamp_end is not None else "-"}s')
    
    filename = '_'.join(filename_parts) + '_rates.png'
    plt.savefig(filename, 
                dpi=300, 
                bbox_inches='tight',
                pad_inches=0.1)
    plt.close()
    print(f"Chart saved as: {filename}")
    
    # 打印统计信息
    print(f"Valid updates: {len(valid_data)}")
    print(f"Skipped updates: {len(skipped_data)}")

def main():
    parser = argparse.ArgumentParser(description='Plot bandwidth allocation for a node from log file.')
    parser.add_argument('-i', '--file', type=str, required=True, help='Path to the log file')
    parser.add_argument('-n', '--node', type=int, default=4, help='Node ID to plot (default: 4)')
    parser.add_argument('--ip', type=str, help='Filter by IP address')
    parser.add_argument('--sport', type=int, help='Filter by source port')
    parser.add_argument('--dport', type=int, help='Filter by destination port')
    # 新增时间区间过滤参数（单位：秒）
    parser.add_argument('--timestamp-start', type=float, default=None, help='Only include records with timestamp >= this value (seconds, float)')
    parser.add_argument('--timestamp-end', type=float, default=None, help='Only include records with timestamp <= this value (seconds, float)')
    args = parser.parse_args()

    # 读取日志文件
    df = read_log_file(args.file)
    
    # 绘制图表
    plot_rates(df, node_id=args.node, ip=args.ip, sport=args.sport, dport=args.dport,
               timestamp_start=args.timestamp_start, timestamp_end=args.timestamp_end)

if __name__ == "__main__":
    main() 

# # 只显示节点4的数据
# python plot_rates.py -i log.txt -n 4

# # 显示节点4，IP为11.0.1.1的数据
# python plot_rates.py -i log.txt -n 4 --ip 11.0.1.1

# # 显示节点4，IP为11.0.1.1，源端口为10000的数据
# python plot_rates.py -i log.txt -n 4 --ip 11.0.1.1 --sport 10000

# # 显示节点4，目标端口为101的数据
# python plot_rates.py -i log.txt -n 4 --dport 101

# # 显示所有条件都匹配的数据
# python plot_rates.py -i log.txt -n 4 --ip 11.0.1.1 --sport 10000 --dport 101
# # 加入时间区间过滤示例（时间单位：秒）
# python plot_rates.py -i log.txt -n 4 --timestamp-start 2.0 --timestamp-end 5.0