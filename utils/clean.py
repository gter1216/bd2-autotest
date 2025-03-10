#!/usr/bin/env python3
"""
清理工具：
1. 清除7天以前的日志文件
2. 清除Python缓存文件
"""

import os
import shutil
import time
from datetime import datetime, timedelta
import logging

def setup_logger():
    """设置日志器"""
    logger = logging.getLogger('cleaner')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def clean_old_logs(base_dir, days=7):
    """
    清除指定天数之前的日志
    :param base_dir: 日志根目录
    :param days: 保留的天数
    """
    logger = logging.getLogger('cleaner')
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
                        logger.info(f"删除过期日志目录: {date_path}")
                        shutil.rmtree(date_path)
                except ValueError:
                    logger.warning(f"跳过无效的日期目录: {date_path}")
                    continue
            
            # 如果环境目录为空，也删除它
            if not os.listdir(env_path):
                logger.info(f"删除空的环境目录: {env_path}")
                os.rmdir(env_path)
                
    except Exception as e:
        logger.error(f"清理日志时发生错误: {str(e)}")

def clean_python_cache(start_dir):
    """
    清除Python缓存文件
    :param start_dir: 开始清理的目录
    """
    logger = logging.getLogger('cleaner')
    
    patterns = ['__pycache__', '*.pyc', '*.pyo', '*.pyd', '.pytest_cache', '.coverage', '.mypy_cache']
    
    try:
        for root, dirs, files in os.walk(start_dir, topdown=True):
            # 清理目录
            for dir_name in dirs:
                if dir_name == '__pycache__' or dir_name.endswith('.egg-info'):
                    dir_path = os.path.join(root, dir_name)
                    logger.info(f"删除缓存目录: {dir_path}")
                    shutil.rmtree(dir_path)
            
            # 清理文件
            for file_name in files:
                if file_name.endswith(('.pyc', '.pyo', '.pyd')):
                    file_path = os.path.join(root, file_name)
                    logger.info(f"删除缓存文件: {file_path}")
                    os.remove(file_path)
    
    except Exception as e:
        logger.error(f"清理Python缓存时发生错误: {str(e)}")

def main():
    """主函数"""
    logger = setup_logger()
    
    # 获取项目根目录（假设clean.py在utils目录下）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, 'logs')
    
    logger.info("开始清理...")
    
    # 清理旧日志
    if os.path.exists(logs_dir):
        logger.info("清理7天前的日志...")
        clean_old_logs(logs_dir)
    else:
        logger.info("日志目录不存在，跳过日志清理")
    
    # 清理Python缓存
    logger.info("清理Python缓存文件...")
    clean_python_cache(project_root)
    
    logger.info("清理完成!")

if __name__ == '__main__':
    main() 