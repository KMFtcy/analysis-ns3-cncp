import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse
import re
import numpy as np

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

def smooth_data(data, window_size=5):
    """
    对数据进行平滑处理
    使用移动平均方法
    """
    if len(data) < window_size:
        return data
    
    # 使用pandas的rolling方法进行移动平均
    smoothed = data.rolling(window=window_size, center=True, min_periods=1).mean()
    return smoothed

# 读取日志文件
def read_log_file(file_path, target_id=None, source_port=None, dest_port=None, smooth_window=5, timestamp_start=None, timestamp_end=None):
    """
    读取日志文件，只处理包含 [RdmaHw Receiving] 的行
    格式: [RdmaHw Receiving] id source_port dest_port data_size timestamp
    计算接收速率：data_size * 8 / time_interval (bits/s)
    可选：只保留 timestamp_start <= timestamp <= timestamp_end 的数据（单位：秒，float）
    """
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 只处理包含 [RdmaHw Receiving] 的行
            if '[RdmaHw Receiving]' in line:
                # 提取 [RdmaHw Receiving] 后面的数据
                parts = line.strip().split('[RdmaHw Receiving] ')[1].split()
                
                if len(parts) >= 5:
                    node_id = int(parts[0])
                    dst_port = int(parts[1])  # 接收日志中，第二个字段是目标端口
                    src_port = int(parts[2])  # 接收日志中，第三个字段是源端口
                    data_size = int(parts[3])
                    # timestamp原为ns，转为秒（float）
                    timestamp = float(parts[4]) / 1e9
                    
                    # 如果指定了过滤条件，则进行过滤
                    if target_id is not None and node_id != target_id:
                        continue
                    if source_port is not None and src_port != source_port:
                        continue
                    if dest_port is not None and dst_port != dest_port:
                        continue
                    if timestamp_start is not None and timestamp < timestamp_start:
                        continue
                    if timestamp_end is not None and timestamp > timestamp_end:
                        continue
                    
                    data.append({
                        'node_id': node_id,
                        'source_port': src_port,
                        'dest_port': dst_port,
                        'data_size': data_size,
                        'timestamp': timestamp
                    })
    
    df = pd.DataFrame(data)
    
    # 计算接收速率 (bits/s)
    if len(df) > 0:
        # 按节点ID分组计算速率
        rate_data = []
        for node_id in df['node_id'].unique():
            node_data = df[df['node_id'] == node_id].sort_values('timestamp')
            
            for i in range(1, len(node_data)):
                current_row = node_data.iloc[i]
                prev_row = node_data.iloc[i-1]
                
                time_interval = current_row['timestamp'] - prev_row['timestamp']
                if time_interval > 0:  # 避免除零错误
                    # 时间戳已为秒
                    time_interval_seconds = time_interval
                    # 将字节转换为比特，然后除以时间间隔得到 bits/s
                    rate = (current_row['data_size'] * 8) / time_interval_seconds
                    rate_data.append({
                        'node_id': node_id,
                        'source_port': current_row['source_port'],
                        'dest_port': current_row['dest_port'],
                        'data_size': current_row['data_size'],
                        'timestamp': current_row['timestamp'],
                        'rate': rate  # 速率 (bits/s)
                    })
        
        if rate_data:
            df = pd.DataFrame(rate_data)
            
            # 对每个节点的速率数据进行平滑处理
            if smooth_window > 1:
                smoothed_df = []
                for node_id in df['node_id'].unique():
                    node_data = df[df['node_id'] == node_id].sort_values('timestamp').copy()
                    node_data['rate_smoothed'] = smooth_data(node_data['rate'], smooth_window)
                    smoothed_df.append(node_data)
                df = pd.concat(smoothed_df, ignore_index=True)
    
    return df

def plot_receiving_rate(df, node_ids=None, show_raw=True):
    # 如果没有指定节点ID，则绘制所有节点
    if node_ids is None:
        node_ids = df['node_id'].unique()
    
    # 设置绘图风格
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6), dpi=300)  # 增加DPI以提高图片质量
    
    # 创建自定义颜色映射
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    # 绘制折线图
    for i, node_id in enumerate(node_ids):
        node_data = df[df['node_id'] == node_id]
        if len(node_data) > 0:  # 确保有数据
            color = colors[i % len(colors)]
            
            # 绘制原始数据（如果启用且存在）
            if show_raw and 'rate' in node_data.columns:
                plt.plot(node_data['timestamp'], node_data['rate'] / 1e9, 
                        color=color, 
                        linewidth=1.0,  # 原始数据线条较细
                        alpha=0.5,      # 透明度较低
                        label=f'Flow 1')
            
            # 绘制平滑数据（如果存在）
            if 'rate_smoothed' in node_data.columns:
                plt.plot(node_data['timestamp'], node_data['rate_smoothed'] / 1e9, 
                        color=color, 
                        linewidth=2.5,  # 平滑数据线条较粗
                        label=f'Flow 1')
            else:
                # 如果没有平滑数据，绘制原始数据
                plt.plot(node_data['timestamp'], node_data['rate'] / 1e9, 
                        color=color, 
                        linewidth=2.5,
                        label=f'Flow 1')
    
    # 设置图表标题和标签
    plt.title('Node 4', pad=20)
    plt.xlabel('Timestamp')
    plt.ylabel('Rate (Gbps)')
    
    # 设置网格线样式
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 显示图例
    plt.legend(title='Flow ID', frameon=True, framealpha=1)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表（使用高DPI）
    plt.savefig('receiving_rate.png', 
                dpi=300, 
                bbox_inches='tight',
                pad_inches=0.1)
    plt.close()

def plot_single_node_rate(df, node_id=0, show_raw=True):
    # 筛选指定node_id的数据
    node_data = df[df['node_id'] == node_id]
    
    if len(node_data) == 0:
        print(f"No data found for node {node_id}")
        return
    
    # 设置绘图风格
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6), dpi=300)  # 增加DPI以提高图片质量
    
    # 绘制原始数据（如果启用且存在）
    if show_raw and 'rate' in node_data.columns:
        plt.plot(node_data['timestamp'], node_data['rate'] / 1e9, 
                color='lightcoral', 
                linewidth=1.0,
                alpha=0.5,
                label=f'Flow 1')
    
    # 绘制平滑数据（如果存在）
    if 'rate_smoothed' in node_data.columns:
        plt.plot(node_data['timestamp'], node_data['rate_smoothed'] / 1e9, 
                color='red', 
                linewidth=2.5,
                label=f'Flow 1')
    else:
        # 如果没有平滑数据，绘制原始数据
        plt.plot(node_data['timestamp'], node_data['rate'] / 1e9, 
                color='red', 
                linewidth=2.5,
                label=f'Flow 1')
    
    # 设置图表标题和标签
    plt.title(f'Receiving Rate on Node {node_id}', pad=20)
    plt.xlabel('Timestamp')
    plt.ylabel('Rate (Gbits/s)')
    
    # 设置网格线样式
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 显示图例
    plt.legend(frameon=True, framealpha=1)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表（使用高DPI）
    plt.savefig(f'node_{node_id}_receiving_rate.png', 
                dpi=300, 
                bbox_inches='tight',
                pad_inches=0.1)
    plt.close()

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Plot receiving rate from log file')
    parser.add_argument('-i', '--log_file', help='Path to the log file')
    parser.add_argument('-u', '--id', type=int, help='Filter by specific node ID')
    parser.add_argument('-s', '--source-port', type=int, help='Filter by source port')
    parser.add_argument('-d', '--dest-port', type=int, help='Filter by destination port')
    parser.add_argument('-n', '--single-node', type=int, help='Plot only a specific node ID')
    parser.add_argument('-w', '--smooth-window', type=int, default=200, help='Smoothing window size for rate data')
    parser.add_argument('--show-raw', action='store_true', help='Show raw rate data in plots')
    parser.add_argument('--timestamp-start', type=float, default=None, help='Only include records with timestamp >= this value (seconds, float)')
    parser.add_argument('--timestamp-end', type=float, default=None, help='Only include records with timestamp <= this value (seconds, float)')
    
    args = parser.parse_args()
    
    # 读取日志文件
    print(f"Reading log file: {args.log_file}")
    print(f"Filters - ID: {args.id}, Source Port: {args.source_port}, Dest Port: {args.dest_port}")
    print(f"Smoothing window: {args.smooth_window}")
    print(f"Show raw data: {args.show_raw}")
    print(f"Timestamp range: {args.timestamp_start} ~ {args.timestamp_end} (seconds)")
    
    df = read_log_file(args.log_file, args.id, args.source_port, args.dest_port, args.smooth_window, args.timestamp_start, args.timestamp_end)
    
    if len(df) == 0:
        print("No data found matching the specified criteria")
        return
    
    print(f"Found {len(df)} records")
    print(f"Node IDs: {sorted(df['node_id'].unique())}")
    
    # 根据参数决定绘制方式
    if args.single_node is not None:
        plot_single_node_rate(df, args.single_node, args.show_raw)
        print(f"Saved plot for node {args.single_node}")
    else:
        plot_receiving_rate(df, show_raw=args.show_raw)
        print("Saved plot for all nodes")

if __name__ == "__main__":
    main()

# # 绘制所有节点的接收速率
# python plot_receiving_rate.py -i your_log_file.log

# # 绘制特定节点的接收速率
# python plot_receiving_rate.py -i your_log_file.log -u 3

# # 按端口过滤
# python plot_receiving_rate.py -i your_log_file.log -s 10000 -d 101