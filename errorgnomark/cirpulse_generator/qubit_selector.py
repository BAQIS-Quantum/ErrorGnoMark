import networkx as nx
from matplotlib import rcParams
import pandas as pd
import matplotlib.pyplot as plt


def build_chessboard_graph(chip_row, chip_col, file_path=r"", run_all=False):
    """
    构建棋盘格量子芯片的图结构，并筛选可用节点

    功能：
    1. 从CSV文件读取量子芯片参数和连接关系
    2. 构建二维棋盘格图结构（节点按行列编号）
    3. 根据T1/T2/Fidelity参数（全非零）筛选可用节点
    4. 建立节点间的连接关系（CZ门实现）

    参数：
        chip_row (int): 芯片的行数
        chip_col (int): 芯片的列数
        file_path (str): 参数文件路径（CSV格式）

    返回：
        tuple: (networkx.Graph对象, 可用节点列表)
               - 图对象包含节点位置信息和连接关系
               - 可用节点列表是满足参数要求的节点ID

    文件格式要求：
        CSV文件应包含以下列（按顺序）：
        - 第0列: 节点ID（如 '0','1',...）
        - 第1列: T1时间（μs）
        - 第2列: T2时间（μs）
        - 第3列: 单比特门保真度（0-1）
        - 第4列: 频率（GHz）
        - 第5列: 连接关系（格式如 '0_1:0.5'，表示节点0和1间的CZ门实现值）
    """

    # 设置中文字体（用于图形显示）
    rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']
    rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    try:
        # 读取量子芯片参数文件
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return None, None
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None, None

    # 创建棋盘格图
    G = nx.Graph()

    # 添加所有节点（按行列编号）
    for row in range(1, chip_row + 1):
        for col in range(1, chip_col + 1):
            # 计算一维节点编号（从上到下、从左到右）
            node_num = (row-1)*chip_col + (col-1)
            node_name = str(node_num)
            # 添加节点并记录位置（使用负y坐标使绘图方向符合常规）
            G.add_node(node_name, pos=(col, -row))

    # 处理连接关系（读取第6列）
    connections = df.iloc[:, 5].dropna()

    for connection_str in connections:
        # 分割多连接字符串（换行符分隔多个连接）
        connection_list = connection_str.splitlines()

        for connection in connection_list:
            if '_' in connection and ':' in connection:
                # 解析连接关系（格式：源节点_目标节点:CZ值）
                nodes_part, cz_value = connection.split(':')
                nodes_part = nodes_part.strip()
                cz_value = cz_value.strip()

                if not run_all:
                    # 仅当CZ值非零时建立连接
                    if cz_value != '0':
                        node1, node2 = nodes_part.split('_')
                        # 验证节点存在性后添加边
                        if node1 in G.nodes and node2 in G.nodes:
                            G.add_edge(node1, node2)
                        else:
                            print(f"警告：连接关系 {connection} 包含不存在的节点")
                    # else:
                    #     print(f"信息：跳过cz值为0的连接 {connection}")
                else:
                    node1, node2 = nodes_part.split('_')
                    # 验证节点存在性后添加边
                    if node1 in G.nodes and node2 in G.nodes:
                        G.add_edge(node1, node2)

    if not run_all:
        # 筛选可用节点（T1/T2/Fidelity均非零）
        available_nodes = []
        for index, row in df.iterrows():
            node_id = str(row.iloc[0])  # 第一列是节点ID
            t1 = row.iloc[1]  # 第二列是T1
            t2 = row.iloc[2]  # 第三列是T2
            fidelity = row.iloc[3]  # 第四列是Single qubit fidelity

            # 检查三个参数是否都不为零
            if t1 != 0 and t2 != 0 and fidelity != 0:
                if node_id in G.nodes:  # 确保节点存在于图中
                    available_nodes.append(node_id)
                else:
                    print(f"警告：节点 {node_id} 参数有效但不在图中")
    else:
        available_nodes = []
        for index, row in df.iterrows():
            node_id = str(row.iloc[0])  # 第一列是节点ID

            if node_id in G.nodes:  # 确保节点存在于图中
                available_nodes.append(node_id)

    return G, available_nodes


def visualize_chessboard(G, available_nodes):
    """
    可视化棋盘格量子芯片的连接关系图

    功能：
    1. 显示量子芯片的二维布局
    2. 用不同颜色标记可用/不可用节点
    3. 显示节点间的连接关系
    4. 仅显示可用节点的标签

    参数：
        G (networkx.Graph): 通过build_chessboard_graph构建的图对象
        available_nodes (list): 可用节点ID列表

    显示特性：
        - 可用节点：浅蓝色
        - 不可用节点：黑色
        - 连接线：灰色
        - 标签：仅显示可用节点
    """

    # 检查输入图是否有效
    if G is None:
        print("警告：输入图为空")
        return

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']
    plt.rcParams['axes.unicode_minus'] = False

    # 获取节点位置信息（来自节点的'pos'属性）
    pos = nx.get_node_attributes(G, 'pos')

    # 将节点分为可用和不可用两类
    available = [node for node in G.nodes if node in available_nodes]
    unavailable = [node for node in G.nodes if node not in available_nodes]

    # 创建图形窗口
    plt.figure(figsize=(10, 8))

    # 1. 绘制可用节点（浅蓝色圆形）
    nx.draw_networkx_nodes(G,
                           pos,
                           nodelist=available,
                           node_color='lightblue',  # 浅蓝色填充
                           node_size=300,           # 节点大小
                           edgecolors='black',      # 黑色边框
                           linewidths=0.5           # 边框粗细
                           )

    # 2. 绘制不可用节点（黑色圆形）
    nx.draw_networkx_nodes(G,
                           pos,
                           nodelist=unavailable,
                           node_color='black',      # 黑色填充
                           node_size=300,
                           alpha=0.7                # 半透明效果
                           )

    # 3. 绘制所有连接边（灰色直线）
    nx.draw_networkx_edges(G,
                           pos,
                           edge_color='gray',       # 灰色连接线
                           width=1.5,               # 线宽
                           alpha=0.5                # 半透明
                           )

    # 4. 添加标签（仅显示可用节点）
    labels = {node: node for node in available}     # 创建标签字典
    nx.draw_networkx_labels(G,
                            pos,
                            labels,
                            font_size=8,            # 字体大小
                            font_color='black'      # 黑色文字
                            )

    plt.title("量子芯片连接关系图\n（蓝色：可用节点，黑色：不可用节点）", pad=20)
    plt.axis('off')     # 关闭坐标轴
    plt.tight_layout()  # 自动调整元素间距
    plt.show()


def select_connected_nodes(chessboard_graph, available_nodes, X, df, initial_qubit,
                           weights=None):
    """
    选择一组相互连接且量子参数最优的X个节点

    功能：
    1. 基于量子参数（T1/T2/Fidelity/Frequency）评估节点质量
    2. 优先选择连接度高且参数优良的节点
    3. 确保所选节点在拓扑结构上相互连通
    4. 返回节点列表及其内部连接数

    参数：
        chessboard_graph (nx.Graph): 棋盘格拓扑图（包含节点位置信息）
        available_nodes (list): 可用节点ID列表（已通过基础参数筛选）
        X (int): 需要选择的节点数量
        df (pd.DataFrame): 量子参数数据框，必须包含：
                           - 第0列：节点ID
                           - 第1列：T1时间（μs）
                           - 第2列：T2时间（μs）
                           - 第3列：单比特门保真度（0-1）
                           - 第4列：频率（GHz）
        initial_qubit: 初始节点选择
        weights (dict): 可选，各参数的权重分配，例如：
                        {'T1':0.3, 'T2':0.2, 'Fidelity':0.4, 'Frequency':0.1}

    返回：
        tuple: (selected_nodes, edge_count)
               - selected_nodes: 选中的节点ID列表
               - edge_count: 这些节点间的连接边数

    算法流程：
        1. 计算每个节点的综合质量评分（参数加权）
        2. 找出所有连通分量（完全连接的子图）
        3. 在足够大的连通分量中：
           a. 计算节点优先级（连接度+参数评分）
           b. 从最高优先级节点开始扩展选择
           c. 确保新增节点与已选节点直接相连
        4. 若无足够大的连通分量，返回最大连通子图
    """

    # 设置默认权重（T1/T2/Fidelity/Frequency）（节点ID -> 综合评分）
    if weights is None:
        weights = {'T1': 0.25, 'T2': 0.25, 'Fidelity': 0.3, 'Frequency': 0.2}

    # === 参数评分计算 ===
    param_scores = {}
    for node in available_nodes:
        try:
            # 获取当前节点的参数行
            row = df[df.iloc[:, 0].astype(str) == str(node)].iloc[0]
            # 参数归一化处理（所有指标转化为0-1范围，越大越好）
            t1 = row.iloc[1] / df.iloc[:, 1].max()  # T1
            t2 = row.iloc[2] / df.iloc[:, 2].max()  # T2
            fidelity = row.iloc[3]  # Fidelity (通常已经是0-1的值)
            # 频率评分：越接近中值越好（1-标准化距离）
            freq = 1 - abs(row.iloc[4] - df.iloc[:, 4].median()) / df.iloc[:, 4].std()

            # 计算加权综合评分
            score = (t1 * weights['T1'] +
                     t2 * weights['T2'] +
                     fidelity * weights['Fidelity'] +
                     freq * weights['Frequency'])
            param_scores[node] = score
        except:
            # 参数缺失的节点得0分（不会被优先选择）
            param_scores[node] = 0

    # === 连通分量分析 ===
    # 创建可用节点的子图（提升后续计算效率）
    available_graph = chessboard_graph.subgraph(available_nodes).copy()

    # 找出所有连通分量（完全连接的子图），按大小降序排列
    connected_components = sorted(nx.connected_components(available_graph),
                                  key=len, reverse=True)

    # === 节点选择策略 ===
    for component in connected_components:
        # 只在足够大的连通分量中选择（节点数>=X）
        if len(component) >= X:
            subgraph = available_graph.subgraph(component)

            # 计算节点优先级 = 50%连接度 + 50%参数评分
            degrees = dict(subgraph.degree())    # 每个节点的连接数
            max_degree = max(degrees.values())   # 最大连接数（用于归一化）
            node_priority = {
                node: 0.8 * (degrees[node] / max_degree) +
                      0.2 * param_scores[node]
                for node in degrees
            }

            # 按优先级降序排序
            sorted_nodes = sorted(node_priority.keys(),
                                  key=lambda x: node_priority[x],
                                  reverse=True)

            # 从最高优先级节点开始扩展选择
            # TODO 起始节点选择
            selected = set([str(initial_qubit)])  # 初始种子节点 initial_qubit

            while len(selected) < X and len(selected) < len(sorted_nodes):
                # 找出与已选节点直接相连的候选节点
                candidates = set()
                for node in selected:
                    candidates.update(neighbor for neighbor in subgraph.neighbors(node)
                                      if neighbor not in selected)

                if not candidates:  # 无相连候选节点时终止
                    break

                # 选择优先级最高的候选节点
                next_node = max(candidates, key=lambda x: node_priority[x])
                selected.add(next_node)

            # 如果成功选够X个节点，返回结果
            if len(selected) == X:
                edge_count = subgraph.subgraph(selected).number_of_edges()
                return list(selected), edge_count

    # === 后备方案 ===
    # 如果没有足够大的连通分量，返回最大连通子图
    largest_component = connected_components[0]
    edge_count = available_graph.subgraph(largest_component).number_of_edges()
    return list(largest_component), edge_count


def save_to_txt(node_indices, selected_connections, file_path='node_indices & selected_connections.txt'):
    """
    将节点索引和连接关系保存到文本文件

    功能：
    1. 以清晰格式保存量子芯片的节点信息
    2. 自动处理不同格式的连接关系（列表或字符串）
    3. 添加章节标题提升可读性
    4. 完善的错误处理机制

    参数：
        node_indices (list): 节点索引列表，如 [0, 1, 2] 或 ['0','1','2']
        selected_connections (list): 连接关系列表，支持格式：
                                   - 字符串格式: ['0_1', '1_2']
                                   - 嵌套列表格式: [[0,1], [1,2]]
        file_path (str): 输出文件路径（默认当前目录）

    文件格式示例：
        === Nodes ===
        0
        1
        2

        === Connections ===
        0_1
        1_2
    """

    try:
        with open(file_path, 'w') as f:
            # === 节点部分 ===
            f.write("=== Nodes ===\n")
            # 将节点索引转换为字符串并换行连接
            # 示例输入: [0,1,2] → "0\n1\n2"
            f.write('\n'.join(map(str, node_indices)) + '\n\n')

            # === 连接部分 ===
            f.write("=== Connections ===\n")
            for conn in selected_connections:
                # 处理嵌套列表格式（如[[0,1],[1,2]]）
                if isinstance(conn, list):
                    # 用下划线连接列表元素 → "0_1"
                    f.write(f"{'_'.join(map(str, conn))}\n")
                # 处理字符串格式（如['0_1','1_2']）
                else:
                    f.write(f"{conn}\n")

        print(f"节点与连接关系成功保存到 {file_path}")
    except PermissionError:
        print(f"错误：没有写入权限 {file_path}")
    except Exception as e:
        print(f"保存文件时发生意外错误: {str(e)}")


class chip:
    """
    Represents a quantum chip with a 2D grid of qubits.

    This class provides the basic structure of a quantum chip, 
    defined by the number of rows and columns. It serves as 
    the foundation for qubit selection and connectivity in a 
    quantum system.

    Attributes:
        rows (int): Number of rows in the chip grid.
        columns (int): Number of columns in the chip grid.
    """

    def __init__(self, rows=12, columns=13):
        self.rows = rows
        self.columns = columns


class qubit_selection:

    """
    Selects qubits and their connectivity from a quantum chip based on specified constraints.

    Parameters:
        chip (chip): An instance of the chip class, defining the chip layout.
        qubit_index_max (int): Maximum allowable qubit index (default: 50).
        qubit_number (int): Number of qubits to select (default: 9).
        option (dict, optional): Selection options, including:
            - "max_qubits_per_row" (int): Maximum number of qubits per row.
            - "min_qubit_index" (int): Minimum allowable qubit index.
            - "max_qubit_index" (int): Maximum allowable qubit index.

    Methods:
        quselected():
            Returns selected qubit indices and their connectivity as a dictionary.
            Visualizes the selected qubits and connections on the chip grid.

    Features:
        - Adapts qubit selection based on chip layout and constraints.
        - Ensures logical connectivity for selected qubits.
    """

    def __init__(self, rows=12, cols=13, qubit_index_max=50, qubit_to_be_used=9,
                 initial_qubit=0,
                 option=None, file_path='', weights=None, run_all=False):
        # self.chip = chip
        self.qubit_index_max = qubit_index_max
        self.qubit_to_be_used = int(qubit_to_be_used)  # Ensure this is an integer
        self.option = option if option is not None else {}
        self.rows = rows
        self.columns = cols
        self.file_path = file_path
        self.weights = weights
        self.initial_qubit = initial_qubit
        self.run_all = run_all

    def quselected(self):
        """
        Selects qubits and their connectivity based on the specified constraints.

        Returns:
            dict: 
                - "qubit_index_list" (list): Indices of selected qubits.
                - "qubit_connectivity" (list): Connectivity data as pairs of qubits.
        """
        if not self.run_all:

            chessboard_graph, available_nodes = build_chessboard_graph(self.rows, self.columns, file_path=self.file_path,
                                                                       run_all=self.run_all)
            if 1:
                # 可视化所有节点
                visualize_chessboard(chessboard_graph, available_nodes)

            if self.qubit_to_be_used > len(available_nodes):
                print(f"要使用的量子比特数量{qubit_to_be_used}大于可用量子比特数: {len(available_nodes)}"
                      f"，请重新选择。")

            df = pd.read_csv(self.file_path)
            selected_nodes, edge_count = select_connected_nodes(chessboard_graph, available_nodes, self.qubit_to_be_used,
                                                                df=df,
                                                                initial_qubit=self.initial_qubit,
                                                                weights=self.weights)

            if 1:
                # 可视化选中的节点
                pos = nx.get_node_attributes(chessboard_graph, 'pos')
                plt.figure(figsize=(10, 8))

                # 绘制所有节点
                nx.draw_networkx_nodes(chessboard_graph, pos, node_color='lightgray', node_size=100)
                nx.draw_networkx_edges(chessboard_graph, pos, edge_color='lightgray')

                # 高亮显示选中的节点和连接
                subgraph = chessboard_graph.subgraph(selected_nodes)
                nx.draw_networkx_nodes(subgraph, pos, node_color='red', node_size=300)
                nx.draw_networkx_edges(subgraph, pos, edge_color='red', width=2)

                # 绘制标签
                labels = {node: node for node in selected_nodes}
                nx.draw_networkx_labels(chessboard_graph, pos, labels, font_size=8)

                plt.title(f"选中的{self.qubit_to_be_used}个相邻节点（红色）")
                plt.show()

            # 转换为序号并排序
            node_indices = sorted(int(x) for x in selected_nodes)

            # 保存选中节点的连接关系
            selected_connections = []
            for edge in chessboard_graph.edges:
                node1, node2 = edge
                if node1 in selected_nodes and node2 in selected_nodes:
                    idx1 = int(node1)
                    idx2 = int(node2)
                    selected_connections.append([idx1, idx2])

            # 保存可用点和连接关系
            save_to_txt(node_indices, selected_connections)

            best_selection = {"qubit_index_list": node_indices, "qubit_connectivity": selected_connections}

        else:
            chessboard_graph, available_nodes = build_chessboard_graph(self.rows, self.columns, file_path=self.file_path,
                                                                       run_all=self.run_all)
            node_indices = sorted(int(x) for x in available_nodes)

            # 保存选中节点的连接关系
            selected_connections = []
            for edge in chessboard_graph.edges:
                node1, node2 = edge
                if node1 in available_nodes and node2 in available_nodes:
                    idx1 = int(node1)
                    idx2 = int(node2)
                    selected_connections.append([idx1, idx2])

            # 保存可用点和连接关系
            save_to_txt(node_indices, selected_connections)

            best_selection = {"qubit_index_list": node_indices, "qubit_connectivity": selected_connections}

        return best_selection


if __name__ == '__main__':
    rows = 12
    cols = 13
    qubit_to_be_used = 10
    file_path = (r"E:\Repositories\ErrorGnoMark\example\Baihua_calibration_2025"
                               r"-04-21 12_26_19.csv")

    selection_options = {
        'max_qubits_per_row': 13,
        'min_qubit_index': 0,
        'max_qubit_index': rows * cols - 1
    }

    selector = qubit_selection(
        rows=12,
        cols=13,
        qubit_index_max=155,
        qubit_to_be_used=qubit_to_be_used,
        option=selection_options,
        file_path=file_path,
        initial_qubit=10,
        run_all=True
    )

    selection = selector.quselected()