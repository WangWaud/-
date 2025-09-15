# OD600 Transformer

一个用于处理和转换微生物生长数据（OD600读数）的Python工具。该工具可以从多种格式的微孔板读板机导出文件中提取数据，并将其转换为结构化的、易于分析的格式。

## 功能特点

- 支持从CSV和Excel（.xlsx和.xls）格式的板读机导出文件中提取数据
- 完整支持96孔板格式（A1-H12）
- 通过用户提供的映射文件将实验条件映射到每个孔位
- 自动计算小时为单位的时间值（从秒转换）
- 生成标准化的CSV输出，方便后续数据分析和可视化
- 提供详细的错误处理和用户反馈

## 安装要求

确保您的系统安装了Python 3.6或更高版本，以及以下Python库：

```bash
pip install pandas numpy argparse
```
如果需要处理Excel文件，还需要安装：

```
pip install openpyxl
```
## 使用方法
### 基本用法
```
python process_growth_data.py 输入文件.csv --map 条件映射文件.csv
```

或者对于Excel格式：
```
python process_growth_data.py 输入文件.xlsx --map 条件映射文件.xlsx
```
### 命令行参数

```
usage: process_growth_data.py [-h] --map MAP [-o OUTPUT_FILE] input_file

Process bacterial growth data from a plate reader CSV or Excel export.

positional arguments:
  input_file            Path to the input file from the plate reader (CSV, XLSX, or XLS format).

optional arguments:
  -h, --help            show this help message and exit
  --map MAP             [REQUIRED] Path to the CSV or Excel file that maps wells to conditions.
                        The file must contain 'Well' and 'Condition' columns.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Path for the output processed CSV file. (default: processed_growth_data.csv)
```

## 输入文件格式

### 板读机数据文件 (CSV 或 Excel)

该工具支持多种常见板读机导出的文件格式。数据文件中应包含以下格式的数据：

1. 时间信息行以"Time [s]"开头，后面跟着秒为单位的时间值
2. 数据行以孔板行标识符(A-H)开头，后面跟着12列光密度数据
示例CSV格式：

```
Time [s],0,,,,,,,,,,,
Temp. [°C],28.9,,,,,,,,,,,
<>,1,2,3,4,5,6,7,8,9,10,11,12
A,0.104,0.1001,0.1058,0.103,0.1519,0.1507,0.1489,0.1476,0.1015,0.1054,0.1022,0.1457
B,0.1032,0.1047,0.1048,0.1039,0.1036,0.1033,0.1042,0.1037,0.1047,0.1054,0.1034,0.0985
```

Excel文件也应包含类似的数据结构。


### 条件映射文件 (CSV 或 Excel)

条件映射文件需要包含以下列：

- Well: 孔位标识符（例如：A1, B5, H12）
- Condition: 对应孔位的实验条件描述
示例:

```csv
Well,Condition
A1,MM
A2,MM
A3,MM
A4,MM
A5,MM + 0.2% dextrose
A6,MM + 0.2% dextrose
```
## 输出文件
程序输出一个CSV文件（默认名称为processed_growth_data.csv），包含以下列：

- Well: 孔位标识符
- Time_s: 以秒为单位的时间点
- Time_h: 以小时为单位的时间点
- OD: 光密度读数值
- Condition: 从映射文件匹配的实验条件

示例输出：
```csv
Well,Time_s,Time_h,OD,Condition
A1,0.0,0.0,0.104,MM
A2,0.0,0.0,0.1001,MM
A3,0.0,0.0,0.1058,MM
...
A1,7198.928,1.9997022222222223,0.0943,MM
...
```

## 贡献与问题报告

如果您发现任何问题或有改进建议，请在GitHub仓库中提交Issue或Pull Request。

