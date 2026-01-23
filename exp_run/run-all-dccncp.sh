# 根据时间戳设置session name
SESSION_NAME=$(date +%Y%m%d%H%M%S)
# 项目根目录（可通过第一个参数传递，默认/home/chaoyang）
PROJECT_ROOT="${1:-/home/chaoyang}"
# 实验根目录
EXP_ROOT="${2:-$PROJECT_ROOT/runtime_config}"

# 定义窗口名
WINDOW_NAMES=(
    cc_11
)

# 定义每个窗口要运行的命令（顺序要和窗口名一一对应）
WINDOW_CMDS=(
    "./ns3 run scratch/third -- $EXP_ROOT/config_cc_11_100G.txt $EXP_ROOT 2>&1 | tee $EXP_ROOT/cc_11_output.log"
)

# 创建tmux session，初始窗口名为init
tmux new-session -d -s $SESSION_NAME -n init

# 创建所有自定义窗口
for WIN in "${WINDOW_NAMES[@]}"; do
    tmux new-window -t $SESSION_NAME -n "$WIN"
done

# 删除初始窗口
tmux kill-window -t $SESSION_NAME:0

# 每个窗口进入项目根目录并执行各自命令
for i in "${!WINDOW_NAMES[@]}"; do
    WIN="${WINDOW_NAMES[$i]}"
    CMD="${WINDOW_CMDS[$i]}"
    tmux send-keys -t $SESSION_NAME:"$WIN" "cd $PROJECT_ROOT; $CMD" C-m
done

# 创建监视窗口
MONITOR_PANE_COUNT=${#WINDOW_NAMES[@]}
tmux new-window -t $SESSION_NAME -n monitor

tmux select-window -t $SESSION_NAME:monitor

tmux select-pane -t $SESSION_NAME:monitor.0
# 依次分割出剩余的pane
for ((i=1; i<MONITOR_PANE_COUNT; i++)); do
    tmux split-window -t $SESSION_NAME:monitor
    tmux select-layout -t $SESSION_NAME:monitor tiled
    tmux select-pane -t $SESSION_NAME:monitor.$i
    sleep 0.1  # 避免分割太快导致顺序错乱
done

tmux select-layout -t $SESSION_NAME:monitor tiled

# 让monitor窗口的每个pane都进入项目根目录并监控各自的fct文件
for i in "${!WINDOW_NAMES[@]}"; do
    tmux send-keys -t $SESSION_NAME:monitor.$i "cd $PROJECT_ROOT; watch -n 1 wc -l $EXP_ROOT/fct/${WINDOW_NAMES[$i]}_fct.txt" C-m
done
