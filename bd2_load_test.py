#!/usr/bin/env python3
"""
BD2 负载测试工具
支持从 YAML 文件加载测试用例并执行
"""

import os
import sys
import yaml
import time
import logging
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger_manager import LoggerManager
from utils.cli.bd2_load_test.cli_parser import CLIParser
import subprocess

# 使用importlib导入BD2ClientSim
root_dir = os.path.dirname(os.path.abspath(__file__))
bd2_client_sim_path = os.path.join(root_dir, "bd2_client_sim.py")
spec = importlib.util.spec_from_file_location("bd2_client_sim_module", bd2_client_sim_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BD2ClientSim = module.BD2ClientSim

class LoadTest:
    """负载测试类"""
    
    def __init__(self, 
                 test_cases_file: str, 
                 duration: Optional[int] = None,
                 uds_log: bool = False, 
                 ccs_log: bool = False, 
                 log_level: str = None):
        """
        初始化负载测试
        :param test_cases_file: 测试用例集文件路径
        :param duration: 测试持续时间（秒）
        :param uds_log: 是否启用 UDS 日志
        :param ccs_log: 是否启用 CCS 日志
        :param log_level: 日志级别
        """
        # 设置日志级别
        if log_level:
            LoggerManager.set_log_level(log_level)
            
        # 获取logger实例
        self.logger = LoggerManager.get_logger(__file__)
        
        # 记录执行命令（如果是通过命令行调用）
        if len(sys.argv) > 1:
            cmd = subprocess.list2cmdline(sys.argv)
            self.logger.info(f"执行命令: {cmd}")

        # 保存参数
        self.test_cases_file = test_cases_file
        self.duration = duration
        self.start_time = None
        self.end_time = None
        self.log_dir = LoggerManager.get_session_dir()
        
        # 初始化客户端
        self.client = BD2ClientSim(uds_log=uds_log, ccs_log=ccs_log, log_level=log_level)
        
        # 加载测试用例
        self.test_cases = self._load_test_cases()
        
        # 统计信息
        self.stats = {
            'total_cases': len(self.test_cases),
            'case_stats': {},
            'start_time': None,
            'end_time': None,
            'total_duration': 0
        }
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """
        加载测试用例
        :return: 测试用例列表
        """
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                test_cases = yaml.safe_load(f)
            
            # 验证测试用例格式
            if not isinstance(test_cases, list):
                raise ValueError("测试用例文件格式错误：应为列表格式")
            
            for case in test_cases:
                if not isinstance(case, dict):
                    raise ValueError("测试用例格式错误：应为字典格式")
                
                # 验证必需字段
                if 'name' not in case or 'method' not in case or 'weight' not in case:
                    raise ValueError("测试用例格式错误：缺少必要字段 'name'、'method' 或 'weight'")
                
                # 验证任务名称格式
                if not isinstance(case['name'], str):
                    raise ValueError(f"无效的任务名称: {case['name']}，必须是字符串")
                
                # 验证方法名称格式（必须包含一个点号，分隔任务类型和动作）
                if '.' not in case['method']:
                    raise ValueError(f"无效的方法名称格式: {case['method']}，必须包含任务类型和动作，以点号分隔")
                
                # 验证权重值
                if not isinstance(case['weight'], (int, float)) or case['weight'] <= 0:
                    raise ValueError(f"无效的权重值: {case['weight']}")
                
                # 验证可选参数
                if 'params' in case and not isinstance(case['params'], dict):
                    raise ValueError(f"无效的参数格式: {case['params']}")
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"加载测试用例失败: {str(e)}")
            raise
    
    def _login_and_check_vehicle(self) -> bool:
        """
        登录并检查车辆状态
        :return: 是否成功
        """
        try:
            self.logger.info("############## 负载测试 tear up 开始 ##############")
            # 登录
            self.logger.info("开始登录流程")
            login_result = self.client.run_task('auth', 'login')
            if not login_result.get('success'):
                self.logger.error(f"登录失败: {login_result.get('error')}")
                return False
            
            # 检查车辆状态
            self.logger.info("检查车辆状态")
            vehicle_result = self.client.run_task('auth', 'get_vehicle_st')
            if not vehicle_result.get('success'):
                self.logger.error(f"车辆状态异常: {vehicle_result.get('error')}")
                return False
            
            self.logger.info("登录和车辆状态检查成功")
            self.logger.info("############## 负载测试 tear up 结束 ##############")
            return True
            
        except Exception as e:
            self.logger.error(f"登录或检查车辆状态失败: {str(e)}")
            self.logger.info("############## 负载测试 tear up 失败，退出 ##############")
            return False
    
    def _update_case_stats(self, case_name: str, success: bool):
        """
        更新测试用例统计信息
        :param case_name: 测试用例名称
        :param success: 是否成功
        """
        if case_name not in self.stats['case_stats']:
            self.stats['case_stats'][case_name] = {
                'total': 0,
                'success': 0,
                'failed': 0
            }
        
        stats = self.stats['case_stats'][case_name]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        else:
            stats['failed'] += 1
    
    def _print_stats(self):
        """打印统计信息"""
        print("\n当前测试统计:")
        print(f"总测试用例数: {self.stats['total_cases']}")
        print("\n各用例执行情况:")
        for case_name, stats in self.stats['case_stats'].items():
            print(f"\n{case_name}:")
            print(f"  总执行次数: {stats['total']}")
            print(f"  成功次数: {stats['success']}")
            print(f"  失败次数: {stats['failed']}")
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
                print(f"  成功率: {success_rate:.2f}%")

    def _generate_report(self):
        """Generate load test report"""
        # Ensure the log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        report_file = os.path.join(self.log_dir, 'load_test_report.html')

        # Test statistics
        start_time = self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        end_time = self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')
        duration = self.stats['total_duration']

        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>BD2 Load Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .failed {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>BD2 Load Test Report</h1>
            <p><strong>Test Start Time:</strong> {start_time}</p>
            <p><strong>Test End Time:</strong> {end_time}</p>
            <p><strong>Total Duration:</strong> {duration:.2f} seconds</p>

            <h2>Test Case Statistics</h2>
            <table>
                <tr>
                    <th>Test Case</th>
                    <th>Total Executions</th>
                    <th>Success Count</th>
                    <th>Failure Count</th>
                    <th>Success Rate</th>
                </tr>
        """

        # Check if there is any test data
        if self.stats.get('case_stats'):
            for case_name, stats in self.stats['case_stats'].items():
                total = stats['total']
                success = stats['success']
                failed = stats['failed']
                success_rate = (success / total) * 100 if total > 0 else 0

                html_content += f"""
                <tr>
                    <td>{case_name}</td>
                    <td>{total}</td>
                    <td class="success">{success}</td>
                    <td class="failed">{failed}</td>
                    <td>{success_rate:.2f}%</td>
                </tr>
                """
        else:
            html_content += """
            <tr>
                <td colspan="5" style="text-align:center;">No test data available</td>
            </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        # Write the report file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"Test report generated: {report_file}")


    # def _generate_report(self):
    #     """生成测试报告"""
    #     report_file = os.path.join(self.log_dir, 'load_test_report.html')
        
    #     with open(report_file, 'w', encoding='utf-8') as f:
    #         f.write("""
    #         <!DOCTYPE html>
    #         <html>
    #         <head>
    #             <title>BD2 负载测试报告</title>
    #             <style>
    #                 body { font-family: Arial, sans-serif; margin: 20px; }
    #                 table { border-collapse: collapse; width: 100%; }
    #                 th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    #                 th { background-color: #f2f2f2; }
    #                 .success { color: green; }
    #                 .failed { color: red; }
    #             </style>
    #         </head>
    #         <body>
    #             <h1>BD2 负载测试报告</h1>
    #             <p>测试开始时间: {start_time}</p>
    #             <p>测试结束时间: {end_time}</p>
    #             <p>总测试时长: {duration:.2f} 秒</p>
    #             <h2>测试用例统计</h2>
    #             <table>
    #                 <tr>
    #                     <th>测试用例</th>
    #                     <th>总执行次数</th>
    #                     <th>成功次数</th>
    #                     <th>失败次数</th>
    #                     <th>成功率</th>
    #                 </tr>
    #         """.format(
    #             start_time=self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
    #             end_time=self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
    #             duration=self.stats['total_duration']
    #         ))
            
    #         for case_name, stats in self.stats['case_stats'].items():
    #             success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
    #             f.write(f"""
    #                 <tr>
    #                     <td>{case_name}</td>
    #                     <td>{stats['total']}</td>
    #                     <td class="success">{stats['success']}</td>
    #                     <td class="failed">{stats['failed']}</td>
    #                     <td>{success_rate:.2f}%</td>
    #                 </tr>
    #             """)
            
    #         f.write("""
    #             </table>
    #         </body>
    #         </html>
    #         """)
        
    #     self.logger.info(f"测试报告已生成: {report_file}")
    
    def run(self):
        """运行负载测试"""
        try:
            # 登录并检查车辆状态
            if not self._login_and_check_vehicle():
                self.logger.error("登录或车辆状态检查失败，终止测试")
                return
            
            # 记录开始时间
            self.start_time = datetime.now()
            self.stats['start_time'] = self.start_time
            
            # 计算总权重
            total_weight = sum(case['weight'] for case in self.test_cases)
            
            # 开始测试循环
            self.logger.info("##########  开始负载测试 ##########")
            while True:
                # 检查是否达到测试时间
                if self.duration and (datetime.now() - self.start_time).total_seconds() >= self.duration:
                    break
                
                # 根据权重选择测试用例
                for case in self.test_cases:
                    # 检查是否达到测试时间
                    if self.duration and (datetime.now() - self.start_time).total_seconds() >= self.duration:
                        break
                    
                    # 根据权重决定是否执行
                    if case['weight'] / total_weight > time.time() % 1:
                        # 执行测试用例
                        self.logger.info(f"执行测试用例: {case['name']} ({case['method']})")
                        
                        # 解析方法名称（格式：task_type.action）
                        task_type, action = case['method'].split('.')
                        
                        # 执行任务，传入可选参数
                        params = case.get('params', {})
                        result = self.client.run_task(task_type, action, **params)
                        
                        # 更新统计信息
                        self._update_case_stats(case['name'], result.get('success', False))
                        
                        # 打印统计信息
                        self._print_stats()
                
                # 短暂休眠，避免过于频繁的执行
                time.sleep(0.1)
            
            # 记录结束时间
            self.end_time = datetime.now()
            self.stats['end_time'] = self.end_time
            self.stats['total_duration'] = (self.end_time - self.start_time).total_seconds()
            
            # 生成测试报告
            self._generate_report()
            
            self.logger.info("##########  负载测试完成 ##########")
            
        except KeyboardInterrupt:
            self.logger.info("##########  负载测试被用户中断 ##########")
        except Exception as e:
            self.logger.error(f"error: {str(e)}")
            self.logger.error(f"##########  负载测试执行失败 ##########")
        finally:
            # 生成最终报告
            self._generate_report()

def main():
    """主函数"""
    try:
        # 获取命令行参数
        parser = CLIParser()
        params = parser.parse_args()
        
        # 创建负载测试实例
        load_test = LoadTest(**params)
        
        # 运行测试
        load_test.run()
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()