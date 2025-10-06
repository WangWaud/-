# OD600 Transformer V2

一个用于处理和转换微生物生长数据（OD600读数）的Python工具。该工具可以从多种格式的微孔板读板机导出文件中提取数据，并将其转换为结构化的、易于分析的格式。

**V2更新（2025/10/06）**: 适配最新版本软件的数据格式，特别是改进了Excel文件的处理逻辑以支持新的表格结构。

## 功能特点

- 支持从CSV和Excel（.xlsx和.xls）格式的板读机导出文件中提取数据
- 完整支持96孔板格式（A1-H12）
- **V2新增**: 适配最新版本软件的Excel输出格式，自动识别新的表格结构
- **V2改进**: 优化Excel文件解析逻辑，支持包含Cycle Nr.、Time [s]、Temp. [°C]等列的新格式
- 可选地通过用户提供的映射文件将实验条件映射到每个孔位
- 自动计算小时为单位的时间值（从秒转换）
- 生成标准化的CSV输出，方便后续数据分析和可视化（如在R或Python中）
- 提供详细的错误处理和用户反馈

## 安装要求

确保您的系统安装了Python 3.6或更高版本，以及以下Python库：

```bash
pip install pandas numpy argparse
```

如果需要处理Excel文件，还需要安装：

```bash
pip install openpyxl
```

## 使用方法

### 基本用法

**只转换基本数据（不添加条件）:**

```bash
python process_growth_data.py 输入文件.csv -o 输出文件.csv
```

**包含条件映射（可选）:**

```bash
python process_growth_data.py 输入文件.csv --map 条件映射文件.csv
```

或者对于Excel格式：

```bash
python process_growth_data.py 输入文件.xlsx --map 条件映射文件.xlsx
```

### 命令行参数

```
usage: process_growth_data.py [-h] [--map MAP] [-o OUTPUT_FILE] input_file

Process bacterial growth data from a plate reader CSV or Excel export (V2 for updated format).

positional arguments:
  input_file            Path to the input file from the plate reader (CSV, XLSX, or XLS format).

optional arguments:
  -h, --help            show this help message and exit
  --map MAP             Path to the CSV or Excel file that maps wells to conditions.
                        The file must contain 'Well' and 'Condition' columns.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path for the output processed CSV file. (default: processed_growth_data.csv)
```

## 最佳实践

### 数据处理流程

1. **转换基础数据**: 使用此工具从板读机导出文件中提取基本数据（孔位、时间、OD值）
2. **后续分析**: 在R或其他统计软件中导入转换后的CSV文件
3. **条件映射**: 根据需要，在分析环境中手动创建条件映射并与数据合并

这种方法的优势:
- 保持原始数据转换过程简单明了
- 提供更大的灵活性，可以在不同分析场景中应用不同的条件映射
- 避免在每次数据提取时都需要提供条件映射文件

### R中合并条件示例

```R
# 读取转换后的数据
growth_data <- read.csv("processed_growth_data.csv")

# 创建条件映射
conditions <- data.frame(
  Well = c("A1", "A2", "A3", "A4", "A5", "A6"),
  Condition = c("Control", "Control", "Treatment", "Treatment", "Control+Dextrose", "Control+Dextrose"),
  Replicate = c(1, 2, 1, 2, 1, 2)
)

# 合并数据
merged_data <- merge(growth_data, conditions, by="Well")

# 进行后续分析
library(ggplot2)
ggplot(merged_data, aes(x=Time_h, y=OD, color=Condition, group=interaction(Condition, Replicate))) +
  geom_line() +
  theme_minimal() +
  labs(title="Growth Curves", x="Time (hours)", y="OD600")
```

## 输入文件格式

### 板读机数据文件 (CSV 或 Excel)

该工具支持多种常见板读机导出的文件格式。

#### CSV格式
CSV数据文件中应包含以下格式的数据：

1. 时间信息行以"Time [s]"开头，后面跟着秒为单位的时间值
2. 数据行以孔板行标识符(A-H)开头，后面跟着12列光密度数据

示例CSV格式：
```
Time [s],0,,,,,,,,,,,
Temp. [°C],28.9,,,,,,,,,,,
<>,1,2,3,4,5,6,7,8,9,10,11,12
A,0.104,0.1001,0.1058,0.103,0.1519,0.1507,0.1489,0.1476,0.1015,0.1054,0.1022,0.1457
B,0.1032,0.1047,0.1048,0.1039,0.1036,0.1033,0.1042,0.1037,0.1047,0.1054,0.1034,0.0985
...
```

#### Excel格式 (V2更新)
**V2版本**专门优化了Excel文件的处理，支持最新软件版本的输出格式：

- 自动跳过文件头部信息，定位到数据表格
- 支持包含以下列的新表格结构：
  - `Cycle Nr.`: 循环编号
  - `Time [s]`: 时间（秒）
  - `Temp. [°C]`: 温度
  - `A1` 到 `H12`: 各孔位的OD600读数

Excel文件的数据应该是一个规整的表格，每行代表一个时间点的测量结果，包含所有96个孔位的数据。

### 条件映射文件 (CSV 或 Excel) - 可选

如果您**选择在数据转换阶段添加条件**，映射文件需要包含以下列：

- `Well`: 孔位标识符（例如：A1, B5, H12）
- `Condition`: 对应孔位的实验条件描述

示例:
```csv
Well,Condition
A1,MM
A2,MM
A3,MM
A4,MM
A5,MM + 0.2% dextrose
A6,MM + 0.2% dextrose
...
```

## 输出文件

程序输出一个CSV文件（默认名称为`processed_growth_data.csv`），包含以下列：

- `Well`: 孔位标识符
- `Time_s`: 以秒为单位的时间点
- `Time_h`: 以小时为单位的时间点
- `OD`: 光密度读数值
- `Condition`: 从映射文件匹配的实验条件（如果提供了映射文件）

示例输出（无条件映射）：
```csv
Well,Time_s,Time_h,OD
A1,0.0,0.0,0.104
A2,0.0,0.0,0.1001
A3,0.0,0.0,0.1058
...
A1,7198.928,1.9997022222222223,0.0943
...
```

示例输出（含条件映射）：
```csv
Well,Time_s,Time_h,OD,Condition
A1,0.0,0.0,0.104,MM
A2,0.0,0.0,0.1001,MM
A3,0.0,0.0,0.1058,MM
...
A1,7198.928,1.9997022222222223,0.0943,MM
...
```

## 版本历史

### V2 (2025/10/06)
- **重大更新**: 适配最新版本软件的数据格式
- **Excel处理优化**: 重写Excel文件解析逻辑，支持新的表格结构
- **自动格式识别**: 能够自动识别并处理包含Cycle Nr.、Time [s]、Temp. [°C]等列的新格式
- **改进的错误处理**: 更好的错误提示和数据验证

### V1
- 初始版本，支持基本的CSV和Excel文件处理
- 96孔板数据提取和时间转换功能
- 可选条件映射功能

## 贡献与问题报告

如果您发现任何问题或有改进建议，请在GitHub仓库中提交Issue或Pull Request。

**注意**: 如果您使用的是旧版本软件输出的数据文件，请使用V1版本的脚本。V2版本专门针对最新软件版本进行了优化。
