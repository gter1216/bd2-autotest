#!/usr/bin/env python3
"""
清理工具：
1. 清除指定天数以前的日志文件（默认7天）
2. 清除Python缓存文件

用法：
    python clean.py [--days DAYS]
    
示例：
    python clean.py              # 清除7天前的日志
    python clean.py --days 30    # 清除30天前的日志
"""

import os
import shutil
import argparse
from datetime import datetime, timedelta

def clean_old_logs(base_dir, days=7):
    """
    清除指定天数之前的日志
    :param base_dir: 日志根目录
    :param days: 保留的天数
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        # 遍历日志根目录下的所有环境目录
        for env_name in os.listdir(base_dir):
            env_path = os.path.join(base_dir, env_name)
            if not os.path.isdir(env_path):
                continue
                
            # 遍历环境目录下的日期目录
            for date_dir in os.listdir(env_path):
                date_path = os.path.join(env_path, date_dir)
                if not os.path.isdir(date_path):
                    continue
                    
                try:
                    # 将日期字符串转换为datetime对象
                    dir_date = datetime.strptime(date_dir, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        print(f"删除过期日志目录: {date_path}")
                        shutil.rmtree(date_path)
                except ValueError:
                    print(f"跳过无效的日期目录: {date_path}")
                    continue
            
            # 如果环境目录为空，也删除它
            if not os.listdir(env_path):
                print(f"删除空的环境目录: {env_path}")
                os.rmdir(env_path)
                
    except Exception as e:
        print(f"清理日志时发生错误: {str(e)}")

def clean_python_cache(start_dir):
    """
    清除Python缓存文件
    :param start_dir: 开始清理的目录
    """
    try:
        for root, dirs, files in os.walk(start_dir, topdown=True):
            # 清理目录
            dirs_to_remove = []
            for dir_name in dirs:
                if (dir_name == '__pycache__' or 
                    dir_name.endswith('.egg-info') or 
                    dir_name in ['.pytest_cache', '.coverage', '.mypy_cache']):
                    dir_path = os.path.join(root, dir_name)
                    print(f"删除缓存目录: {dir_path}")
                    shutil.rmtree(dir_path)
                    dirs_to_remove.append(dir_name)
            
            # 从dirs列表中移除已删除的目录，避免继续遍历它们
            for dir_name in dirs_to_remove:
                dirs.remove(dir_name)
            
            # 清理文件
            for file_name in files:
                if file_name.endswith(('.pyc', '.pyo', '.pyd')):
                    file_path = os.path.join(root, file_name)
                    print(f"删除缓存文件: {file_path}")
                    os.remove(file_path)
    
    except Exception as e:
        print(f"清理Python缓存时发生错误: {str(e)}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="清理工具：清除指定天数前的日志和Python缓存文件")
    parser.add_argument("--days", type=int, default=7,
                      help="清除多少天以前的日志（默认：7天）")
    args = parser.parse_args()
    
    # 获取项目根目录（当前目录，因为脚本在根目录下）
    project_root = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(project_root, 'logs')
    
    print("开始清理...")
    
    # 清理旧日志
    if os.path.exists(logs_dir):
        print(f"清理{args.days}天前的日志...")
        clean_old_logs(logs_dir, args.days)
    else:
        print("日志目录不存在，跳过日志清理")
    
    # 清理Python缓存
    print("清理Python缓存文件...")
    clean_python_cache(project_root)
    
    print("清理完成!")

if __name__ == '__main__':
    main() 