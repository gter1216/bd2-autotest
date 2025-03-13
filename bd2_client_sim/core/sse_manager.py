"""
Description: This module manages SSE (Server-Sent Events) connections.

Changelog:
- 2025-03-13: Initial creation.
"""

import json
import threading
import os
from sseclient import SSEClient
from utils.logger_manager import LoggerManager
from .endpoint_manager import EndpointManager

class SSEManager:
    """管理 SSE 连接的类"""
    
    def __init__(self, session):
        """初始化 SSE 管理器
        
        Args:
            session: 当前的 HTTP 会话
        """
        self.session = session
        self.logger = LoggerManager.get_logger(__file__)
        self.sse_threads = {}  # 存储 SSE 线程
        self._stop_events = {}  # 存储停止事件

    def _write_to_uds_log(self, msg):
        """将消息写入 uds.log 文件
        
        Args:
            msg: 要写入的消息
        """
        try:
            session_dir = LoggerManager.get_session_dir()
            if session_dir:
                log_file = os.path.join(session_dir, 'uds.log')
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{msg}\n")
        except Exception as e:
            self.logger.error(f"写入 uds.log 失败: {str(e)}")

    def _sse_worker(self, sse_type, url, stop_event):
        """SSE 工作线程
        
        Args:
            sse_type: SSE 类型（basic_vehicle_service_log/uds_log/appl_log）
            url: SSE 连接 URL
            stop_event: 停止事件
        """
        thread_logger = LoggerManager.get_logger(__file__)
        thread_logger.info(f"启动 {sse_type} SSE 监听线程")
        
        try:
            response = self.session.get(url, stream=True)
            client = SSEClient(response)
            
            for event in client.events():
                if stop_event.is_set():
                    break
                    
                # 记录事件信息
                log_msg = [
                    f"\n{'='*20} SSE Event ({sse_type}) {'='*20}",
                    f"Event ID: {event.id}",
                    f"Event Type: {event.event}", 
                    f"Event Retry: {event.retry}",
                    f"Event Data: {event.data}"
                ]
                
                # 尝试解析 event.data 为 JSON
                try:
                    data = json.loads(event.data)
                    log_msg.append("\nParsed JSON Data:")
                    log_msg.append(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # 如果是 uds_log 类型且解析成功，将 msg 字段写入 uds.log
                    if sse_type == 'uds_log' and 'msg' in data:
                        self._write_to_uds_log(data['msg'])
                except json.JSONDecodeError:
                    log_msg.append("\nRaw Data:")
                    log_msg.append(event.data)
                    
                log_msg.append("="*50)
                thread_logger.debug("\n".join(log_msg))
                
        except Exception as e:
            thread_logger.error(f"{sse_type} SSE 连接异常: {str(e)}")
            thread_logger.error(f"异常详情: {type(e).__name__}: {str(e)}")
        finally:
            thread_logger.info(f"停止 {sse_type} SSE 监听线程")

    def start_sse(self, sse_type):
        """启动指定类型的 SSE 监听
        
        Args:
            sse_type: SSE 类型（basic_vehicle_service_log/uds_log/appl_log）
        """
        if sse_type in self.sse_threads and self.sse_threads[sse_type].is_alive():
            self.logger.warning(f"{sse_type} SSE 监听已在运行")
            return
            
        # 获取 SSE URL
        try:
            url = self.session.base_url + EndpointManager.get_endpoint(sse_type)
        except ValueError as e:
            self.logger.error(f"获取 {sse_type} SSE URL 失败: {str(e)}")
            return
            
        # 创建停止事件
        stop_event = threading.Event()
        self._stop_events[sse_type] = stop_event
        
        # 创建并启动线程
        thread = threading.Thread(
            target=self._sse_worker,
            args=(sse_type, url, stop_event),
            name=f"SSE-{sse_type}",
            daemon=True  # 设置为守护线程，这样主程序退出时线程会自动结束
        )
        thread.start()
        
        self.sse_threads[sse_type] = thread
        self.logger.info(f"已启动 {sse_type} SSE 监听")

    def stop_sse(self, sse_type):
        """停止指定类型的 SSE 监听
        
        Args:
            sse_type: SSE 类型（basic_vehicle_service_log/uds_log/appl_log）
        """
        if sse_type in self._stop_events:
            self._stop_events[sse_type].set()
            if sse_type in self.sse_threads:
                self.sse_threads[sse_type].join(timeout=5)
                del self.sse_threads[sse_type]
            del self._stop_events[sse_type]
            self.logger.info(f"已停止 {sse_type} SSE 监听")

    def stop_all(self):
        """停止所有 SSE 监听"""
        for sse_type in list(self._stop_events.keys()):
            self.stop_sse(sse_type) 