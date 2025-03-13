"""
Description: This module provides a base service for handling HTTP API requests.

Changelog:
- 2025-03-07: Initial Creation.
- 2025-03-13: Added SSE manager support.
"""

import os
import json
import requests
from datetime import datetime
import pickle
import logging
from .sse_manager import SSEManager


class BaseService:
    """Base HTTP service to handle API requests"""

    # 类变量，所有实例共享同一个会话
    _shared_session = None
    _session_file = None
    _logger = None
    _sse_manager = None  # SSE 管理器实例

    @classmethod
    def _get_logger(cls):
        """获取logger实例"""
        if cls._logger is None:
            from utils.logger_manager import LoggerManager
            cls._logger = LoggerManager.get_logger(__file__)
        return cls._logger

    @classmethod
    def get_sse_manager(cls):
        """获取 SSE 管理器实例"""
        if cls._sse_manager is None and cls._shared_session is not None:
            cls._sse_manager = SSEManager(cls._shared_session)
        return cls._sse_manager

    def _log_request(self, method, url, headers, data):
        """记录请求信息"""
        logger = self._get_logger()
        message = [
            f"\n{'='*20} HTTP Request {'='*20}",
            f"{method} {url}",
            "Headers:"
        ]
        # 显示所有请求头，包括 Cookie
        for key, value in headers.items():
            message.append(f"    {key}: {value}")
        if data:
            message.append("Body:")
            message.append(f"    {json.dumps(data, ensure_ascii=False, indent=4)}")
        message.append("="*50)
        logger.debug("\n".join(message))

    def _log_response(self, response):
        """记录响应信息"""
        logger = self._get_logger()
        message = [
            f"\n{'='*20} HTTP Response {'='*20}",
            f"Status: {response.status_code} {response.reason}",
            "Headers:"
        ]
        for key, value in response.headers.items():
            message.append(f"    {key}: {value}")
        if response.text:
            message.append("Body:")
            try:
                # 尝试格式化 JSON 响应
                body = json.dumps(response.json(), ensure_ascii=False, indent=4)
            except:
                body = response.text
            message.append(f"    {body}")
        message.append("="*50)
        logger.debug("\n".join(message))

    @classmethod
    def _init_session_file(cls):
        """初始化会话文件路径"""
        if cls._session_file is None:
            # 在 var/session 目录下存储会话文件
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            session_dir = os.path.join(project_root, 'var', 'session')
            os.makedirs(session_dir, exist_ok=True)
            cls._session_file = os.path.join(session_dir, 'session.pkl')

    @classmethod
    def _load_session(cls):
        """从文件加载会话"""
        cls._init_session_file()
        if os.path.exists(cls._session_file):
            try:
                with open(cls._session_file, 'rb') as f:
                    session_data = pickle.load(f)
                    if session_data.get('expires_at', datetime.now()) > datetime.now():
                        # 创建新的 session
                        session = requests.Session()
                        session.verify = False  # 禁用 SSL 验证
                        session.trust_env = False  # 禁用环境变量中的代理设置
                        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
                        # 更新 cookie
                        cookies = session_data.get('cookies', {})
                        session.cookies.update(cookies)
                        # 更新类变量
                        cls._shared_session = session
                        # 添加调试日志
                        logger = cls._get_logger()
                        logger.debug(f"从文件加载会话成功，cookies: {cookies}")
                        return True
            except Exception as e:
                logger = cls._get_logger()
                logger.error(f"加载会话失败: {str(e)}")
                pass
        return False

    @classmethod
    def _save_session(cls, cookies, max_age=None):
        """保存会话到文件"""
        cls._init_session_file()
        try:
            expires_at = datetime.now()
            if max_age:
                from datetime import timedelta
                expires_at += timedelta(seconds=int(max_age))
            
            session_data = {
                'cookies': dict(cookies),
                'expires_at': expires_at
            }
            
            with open(cls._session_file, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            print(f"保存会话信息失败: {str(e)}")

    def __init__(self, base_url):
        self.base_url = base_url
        # 使用共享会话
        if BaseService._shared_session is None:
            # 先尝试加载已保存的会话
            if not BaseService._load_session():
                # 如果没有已保存的会话，创建新的
                BaseService._shared_session = requests.Session()
                # 禁用 SSL 验证
                BaseService._shared_session.verify = False
                # 禁用环境变量中的代理设置
                BaseService._shared_session.trust_env = False
                # 禁用 SSL 验证警告
                requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        self.session = BaseService._shared_session
        # 设置 base_url 属性（用于 SSE 管理器）
        self.session.base_url = base_url

    def _get_headers(self, headers=None):
        """Construct request headers"""
        default_headers = {
            "Accept": "application/json,text/plain,*/*",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "local/win32/PRTKF00WBK00NN/1.3.1/5CG4375BR5"
        }
        # 添加 cookie 到请求头
        if self.session.cookies:
            cookie_str = '; '.join([f"{cookie.name}={cookie.value}" for cookie in self.session.cookies])
            default_headers["Cookie"] = cookie_str
        if headers:
            default_headers.update(headers)
        return default_headers

    def _send_request(self, method, endpoint, data=None, headers=None, no_log=False, **kwargs):
        """Generic HTTP request method
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            data: 请求数据
            headers: 请求头
            no_log: 是否禁用请求和响应的日志记录
            **kwargs: 其他参数，如 timeout
            
        Returns:
            tuple: (status_code, response_data)
                - status_code: HTTP 状态码
                - response_data: 响应数据，可能是 JSON 对象或 None
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(headers)
        
        # 记录请求信息
        if not no_log:
            self._log_request(method, url, headers, data)
        
        try:
            response = self.session.request(
                method, url, json=data, headers=headers, **kwargs
            )
            
            # 记录响应信息
            if not no_log:
                self._log_response(response)
            
            # 处理Set-Cookie头
            if 'Set-Cookie' in response.headers:
                cookie_header = response.headers['Set-Cookie']
                if 'Max-Age=' in cookie_header:
                    max_age = cookie_header.split('Max-Age=')[1].split(';')[0]
                    self._save_session(response.cookies, max_age)
                else:
                    self._save_session(response.cookies)
            
            # 尝试解析响应数据
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {str(e)}")
            raise

    def post(self, endpoint, data=None, headers=None, **kwargs):
        """Send POST request"""
        return self._send_request("POST", endpoint, data, headers, **kwargs)

    def get(self, endpoint, headers=None, no_log=False, **kwargs):
        """Send GET request"""
        return self._send_request("GET", endpoint, None, headers, no_log, **kwargs)

    def put(self, endpoint, data=None, headers=None, **kwargs):
        """Send PUT request"""
        return self._send_request("PUT", endpoint, data, headers, **kwargs)

    def delete(self, endpoint, headers=None, **kwargs):
        """Send DELETE request"""
        return self._send_request("DELETE", endpoint, None, headers, **kwargs)
