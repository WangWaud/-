# 细菌生长曲线数据处理器
一个强大而灵活的 Python 脚本，用于处理和转换从酶标仪导出的原始 OD600 数据，生成一个干净、整洁的 CSV 文件。该文件格式非常适合在 R、Python 或 Prism 等软件中进行后续分析和可视化。

该工具的核心特性是支持自定义条件映射文件，让您无需修改脚本代码即可定义任何实验布局。

## 主要功能
- 自动解析: 智能地从原始 CSV 导出文件中提取时间点和对应的 OD 值。
- 数据整理: 将数据从“宽”格式转换为“长”格式（Tidy Data），便于分析。
- 自定义条件映射: 使用一个独立的、由用户提供的 CSV 文件，将每个孔 (Well) 映射到其具体的实验条件。
- 时间单位转换: 自动创建一个以小时为单位的时间列 (Time_h)，方便绘图。
- 命令行接口: 可通过终端轻松运行，实现可重复的工作流程。
- 错误检查: 提供有用的警告和错误提示（例如，当映射文件缺少孔位或必需的列时）。

## 环境准备
- Python 3.6 或更高版本
- Pandas 库

您可以使用 pip 安装所需的库：

```Bash
pip install pandas
```

## 使用方法
### 步骤 1: 创建一个条件映射文件
在运行脚本之前，您需要创建一个 CSV 文件，用来告诉脚本每个孔对应什么实验条件。这个文件必须包含两列：Well 和 Condition。

**示例 (my_conditions.csv):**

```
Well	Condition
A1	1/2 TSB without bacteria
A2	1/2 TSB without bacteria
A3	1/2 TSB without bacteria
A4	1/2 TSB without bacteria
A5	1/2 TSB
A6	1/2 TSB
...	...
D12	MM + 1%DMSO
```

### 步骤 2: 运行脚本
打开您的终端（或命令提示符），进入脚本所在的目录，然后使用以下结构运行命令：

```Bash
python process_growth_data.py <您的原始数据文件路径> --map <您的映射文件路径> -o <您想输出的文件路径>
```

命令行参数说明:
- input_file (必需): 从酶标仪导出的原始数据 CSV 文件的路径。
- --map (必需): 您在步骤 1 中创建的条件映射文件的路径。
- -o, --output_file (可选): 指定处理后输出的文件名。如果省略，将默认保存为 processed_growth_data.csv。

命令示例:
假设您的原始数据文件是 raw_data.csv，条件映射文件是 my_conditions.csv。您可以运行：

```Bash
python process_growth_data.py "raw_data.csv" --map "my_conditions.csv" -o "final_data_for_R.csv"
```

## 输出文件格式
脚本会输出一个干净的 CSV 文件，包含以下列，可以直接用于后续分析：

```
Well	Time_s	Time_h	OD	Condition
A1	0.0	0.0	0.101	1/2 TSB without bacteria
A2	0.0	0.0	0.102	1/2 TSB without bacteria
...	...	...	...	...
D12	86400.0	24.0	1.55	MM + 1%DMSO
```
