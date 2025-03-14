# BD2 Auto Stress Test

这是一个用于 BD2 系统的自动化压力测试和客户端模拟工具。该工具包含两个主要脚本：`bd2_load_test.py` 用于负载测试，`bd2_client_sim.py` 用于客户端模拟。

## 目录结构

```
.
├── bd2_client_sim/          # 客户端模拟器相关代码
├── bd2_load_test/          # 负载测试相关代码
├── config/                 # 配置文件目录
├── logs/                  # 日志输出目录
├── scripts/               # 辅助脚本
├── utils/                # 工具类
│   └── cli/             # 命令行工具
│       ├── bd2_client_sim/  # 客户端模拟器命令行解析
│       └── bd2_load_test/   # 负载测试命令行解析
├── var/                  # 运行时变量存储
├── bd2_client_sim.py     # 客户端模拟器主程序
├── bd2_load_test.py      # 负载测试主程序
├── clean.py              # 清理脚本
└── requirements.txt      # Python 依赖包
```

## 环境要求

- Python 3.x
- 依赖包：
  - requests >= 2.31.0
  - pyyaml >= 6.0.1
  - cryptography >= 41.0.7
  - sseclient-py >= 1.8.0

## 使用说明

### 1. BD2 负载测试工具 (bd2_load_test.py)

用于执行 BD2 系统的负载测试。

#### 基本用法
```bash
bd2_load_test.py <测试用例文件> [选项]
```

#### 参数说明
- `测试用例文件`：YAML 格式的测试用例文件（必需）

#### 可选参数
- `-t, --time <分钟>`：测试持续时间（分钟）
- `--uds-log on|off`：启用/禁用 UDS 日志
- `--ccs-log on|off`：启用/禁用 CCS 日志
- `--log-level LEVEL`：设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-h, --help`：显示帮助信息

#### 示例
```bash
# 基本用法
bd2_load_test.py load_test_cases_001.yaml

# 设置测试时间（60分钟）
bd2_load_test.py load_test_cases_001.yaml -t 60

# 启用 UDS 日志和 CCS 日志
bd2_load_test.py load_test_cases_001.yaml --uds-log on --ccs-log on

# 设置日志级别
bd2_load_test.py load_test_cases_001.yaml --log-level DEBUG

# 组合使用
bd2_load_test.py load_test_cases_001.yaml -t 60 --uds-log on --ccs-log on --log-level DEBUG
```

### 2. BD2 客户端模拟器 (bd2_client_sim.py)

用于模拟 BD2 客户端的各种操作，包括认证、证书管理和诊断功能。

#### 基本用法
```bash
bd2_client_sim.py <task_type> <action> [<args>] [--uds-log] [--ccs-log] [--log-level]
```

#### 任务类型和操作

1. 认证任务 (auth)
   - `login`：用户登录
   - `get_login_st`：检查登录状态
   - `get_vehicle_st`：获取车辆状态

2. 证书管理 (cert)
   - `init`：初始化证书功能
   - `deploy`：部署证书（需要 -ecu 参数）
   - `revoke`：撤销证书（需要 -ecu 参数）
   - `get_cert_st`：获取证书状态

3. 诊断任务 (diag)
   - `run`：运行诊断任务

#### 可选参数
- `--uds-log on|off`：UDS 日志开关
- `--ccs-log on|off`：CCS 日志开关
- `--log-level LEVEL`：设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-h, --help`：显示帮助信息

#### ECU 类型
- 部署证书支持的 ECU：
  - `ccc`：CCC
  - `zone_front`：前区域
  - `zone_rear`：后区域
  - `all`：所有 ECU

- 获取证书状态支持的 ECU：
  - `adf`：ADF
  - `cdf`：CDF
  - `saf`：SAF
  - `vdf_mcore`：VDF MCORE
  - `vdf`：VDF
  - `zone_ftm`：ZONE FTM
  - `zone_fte`：ZONE FTE
  - `zone_rem`：ZONE REM
  - `zone_ree`：ZONE REE

#### 示例
```bash
# 认证操作
bd2_client_sim.py auth login --uds-log on
bd2_client_sim.py auth get_login_st
bd2_client_sim.py auth get_vehicle_st

# 证书操作
bd2_client_sim.py cert init
bd2_client_sim.py cert deploy -ecu ccc --ccs-log on
bd2_client_sim.py cert revoke -ecu zone_front
bd2_client_sim.py cert get_cert_st -ecu saf

# 诊断操作
bd2_client_sim.py diag run --uds-log on
```
