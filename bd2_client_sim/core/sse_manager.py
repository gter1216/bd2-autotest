"""
Description: This module provides SSE (Server-Sent Events) management functionality.

Changelog:
- 2025-03-11: Initial creation.
"""

import os
import threading
import time
import requests
import logging
from datetime import datetime
from sseclient import SSEClient  # 从sseclient-py包导入SSEClient
from config.config import CONFIG
from .endpoint_manager import EndpointManager
from utils.logger_manager import LoggerManager
import json
from urllib.parse import urljoin

class SSEHandler:
    """处理单个 SSE 连接和日志记录"""
    def __init__(self, base_url, url, session_dir, sse_type):
        """初始化 SSE 处理器
        
        Args:
            base_url: 基础URL
            url: SSE端点URL
            session_dir: 会话日志目录
            sse_type: SSE类型（用于日志文件命名）
        """
        self.base_url = base_url
        self.url = url
        self.log_file = os.path.join(session_dir, f"{sse_type}.log")
        self.running = False
        self.sse_type = sse_type
        self.logger = LoggerManager.get_logger("SSEManager")  # 使用与SSEManager相同的logger
        self.ready_event = threading.Event()  # 添加就绪事件

    def start_listening(self):
        """开始监听SSE事件"""
        self.logger.debug(f"进入start_listening方法: {self.sse_type}")
        self.running = True
        
        while self.running:
            try:
                # 构建完整URL
                full_url = urljoin(self.base_url, self.url)
                self.logger.info(f"开始连接SSE端点: {full_url}")
                
                # 禁用SSL验证警告
                requests.packages.urllib3.disable_warnings(
                    requests.packages.urllib3.exceptions.InsecureRequestWarning
                )
                
                # 创建SSE客户端，禁用SSL验证
                self.client = SSEClient(
                    full_url,
                    verify=False,
                    headers={'Accept': 'text/event-stream'}
                )
                
                # 设置就绪事件
                self.ready_event.set()
                
                # 开始监听事件
                for event in self.client:
                    if not self.running:
                        break
                        
                    try:
                        # 解码事件数据
                        data = json.loads(event.data)
                        self.logger.debug(f"收到SSE事件: {data}")
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"解析SSE事件数据失败: {e}")
                        continue
                        
                    except Exception as e:
                        self.logger.error(f"处理SSE事件时发生错误: {e}")
                        continue
                        
            except requests.exceptions.RequestException as e:
                self.logger.error(f"SSE连接错误: {e}")
                if self.running:
                    time.sleep(1)  # 重连前等待
                continue
                
            except Exception as e:
                self.logger.error(f"SSE连接发生错误: {e}")
                if self.running:
                    time.sleep(1)  # 重连前等待
                continue
                
        self.logger.info("SSE监听结束")

    def stop(self):
        """停止监听"""
        self.logger.info(f"停止SSE监听: {self.sse_type}")
        self.running = False


class SSEManager:
    """管理 SSE 连接和日志记录"""
    def __init__(self, base_url, script_name=None):
        """初始化 SSE 管理器
        
        Args:
            base_url: 基础URL
            script_name: 脚本名称，如果为None则自动获取
        """
        self.base_url = base_url
        self.script_name = script_name or LoggerManager.get_current_script_env()
        self.session_dir = None
        self.sse_handlers = {}  # 存储所有 SSE 处理器
        self.threads = {}       # 存储所有 SSE 线程
        self.logger = LoggerManager.get_logger("SSEManager")  # 使用统一的日志管理
        self.all_ready_event = threading.Event()  # 添加所有SSE就绪事件

    def start_sse_logging(self, task_type, action, session_dir=None):
        """启动特定任务的 SSE 日志记录
        
        Args:
            task_type: 任务类型
            action: 具体操作
            session_dir: 会话目录路径，如果为None则创建新目录
            
        Returns:
            bool: 是否成功启动所有SSE监听
        """
        # 设置主线程名称
        if threading.current_thread() is threading.main_thread():
            threading.current_thread().name = "main"
            
        # 使用提供的会话目录或创建新目录
        self.session_dir = session_dir or LoggerManager.create_session_dir(self.script_name)
        self.logger.info(f"SSE日志目录: {self.session_dir}")
        
        # 获取该任务需要的 SSE URLs
        sse_urls = self.get_sse_urls(task_type, action)
        if not sse_urls:
            self.logger.info(f"任务 {task_type}.{action} 没有配置SSE端点")
            self.all_ready_event.set()  # 没有SSE需要等待，直接设置就绪
            return True
            
        self.logger.info(f"开始监听SSE端点: {list(sse_urls.keys())}")
        
        success = True
        # 为每个 SSE URL 创建处理器和线程
        for sse_type, url in sse_urls.items():
            try:
                self.logger.debug(f"准备创建SSE处理器: {sse_type}")
                handler = SSEHandler(
                    base_url=self.base_url,
                    url=url,
                    session_dir=self.session_dir,
                    sse_type=sse_type
                )
                self.sse_handlers[sse_type] = handler
                
                self.logger.debug(f"准备创建SSE线程: {sse_type}")
                # 创建并启动线程，使用统一的命名格式
                thread = threading.Thread(
                    target=handler.start_listening,
                    name=f"t:{sse_type}"  # 线程名称格式：t:{sse_type}
                )
                # thread.daemon = True  # 设为守护线程
                
                self.logger.debug(f"启动SSE线程: {sse_type}")
                thread.start()
                self.threads[sse_type] = thread
                
            except Exception as e:
                self.logger.error(f"创建SSE处理器或线程时发生错误: {sse_type}, 错误: {str(e)}")
                import traceback
                self.logger.error(f"错误详情:\n{traceback.format_exc()}")
                success = False
                
        if success:
            # 等待所有SSE连接就绪或超时
            timeout = 10  # 设置10秒超时
            ready_handlers = []
            for sse_type, handler in self.sse_handlers.items():
                if handler.ready_event.wait(timeout):
                    ready_handlers.append(sse_type)
                else:
                    self.logger.error(f"SSE连接超时: {sse_type}")
                    success = False
            
            if ready_handlers:
                self.logger.info(f"以下SSE连接已就绪: {ready_handlers}")
            
        self.all_ready_event.set()  # 设置所有SSE就绪事件
        return success

    def wait_for_ready(self, timeout=None):
        """等待所有SSE连接就绪
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否所有SSE都已就绪
        """
        return self.all_ready_event.wait(timeout)

    def get_sse_urls(self, task_type, action):
        """获取特定任务类型和操作需要的 SSE URLs
        
        从配置文件中获取该任务需要监听的 SSE URLs
        
        Args:
            task_type: 任务类型
            action: 具体操作
            
        Returns:
            dict: SSE类型到URL的映射
        """
        sse_config = CONFIG.get("sse.task_mappings", {})
        task_config = sse_config.get(task_type, {})
        action_config = task_config.get(action, [])
        
        self.logger.debug(f"SSE配置信息:")
        self.logger.debug(f"- 任务类型: {task_type}")
        self.logger.debug(f"- 操作: {action}")
        self.logger.debug(f"- 配置的SSE类型: {action_config}")
        
        urls = {}
        for sse_type in action_config:
            try:
                url = EndpointManager.get_endpoint(sse_type)
                if url:
                    urls[sse_type] = url
                    self.logger.debug(f"获取到SSE端点 - 类型: {sse_type}, URL: {url}")
                else:
                    self.logger.warning(f"未找到SSE端点配置: {sse_type}")
            except ValueError as e:
                self.logger.error(f"获取SSE端点失败: {str(e)}")
                
        if not urls:
            self.logger.warning(f"未找到任何匹配的SSE端点配置 - 任务类型: {task_type}, 操作: {action}")
        else:
            self.logger.info(f"成功获取到 {len(urls)} 个SSE端点配置")
            
        return urls

    def stop_all(self):
        """停止所有 SSE 处理器"""
        self.logger.info("停止所有SSE处理器")
        for sse_type, handler in self.sse_handlers.items():
            handler.stop()
            self.logger.debug(f"已停止SSE处理器: {sse_type}")
            
        for sse_type, thread in self.threads.items():
            thread.join(timeout=1.0)
            if thread.is_alive():
                self.logger.warning(f"SSE线程未能正常退出: {sse_type}") 