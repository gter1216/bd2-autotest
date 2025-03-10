"""
Description: This module provides a base service for handling HTTP API requests.

Changelog:
- 2025-03-07: Initial Creation.
"""

import os
import json
import requests
from datetime import datetime
import pickle
import logging


class BaseService:
    """Base HTTP service to handle API requests"""

    # 类变量，所有实例共享同一个会话
    _shared_session = None
    _session_file = None
    _logger = None

    @classmethod
    def _get_logger(cls):
        """获取logger实例"""
        if cls._logger is None:
            from utils.logger_manager import LoggerManager
            cls._logger = LoggerManager.get_logger(__file__)
        return cls._logger

    def _log_request(self, method, url, headers, data):
        """记录请求信息"""
        logger = self._get_logger()
        message = [
            f"\n{'='*20} HTTP Request {'='*20}",
            f"{method} {url}",
            "Headers:"
        ]
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
            # 在项目根目录下创建.session目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            session_dir = os.path.join(project_root, '.session')
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
                        cls._shared_session = requests.Session()
                        cls._shared_session.cookies.update(session_data.get('cookies', {}))
                        return True
            except Exception:
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
            BaseService._shared_session = requests.Session()
            # 禁用 SSL 验证
            BaseService._shared_session.verify = False
            # 禁用 SSL 验证警告
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
            # 尝试加载已保存的会话
            self._load_session()
        self.session = BaseService._shared_session

    def _get_headers(self, headers=None):
        """Construct request headers"""
        default_headers = {
            "Accept": "application/json,text/plain,*/*",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "local/win32/PRTKF00WBK00NN/1.3.1/5CG4375BR5"
        }
        if headers:
            default_headers.update(headers)
        return default_headers

    def _send_request(self, method, endpoint, data=None, headers=None, ignore_401=False):
        """Generic HTTP request method"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(headers)
        
        # 记录请求信息
        self._log_request(method, url, headers, data)
        
        try:
            response = self.session.request(
                method, url, json=data, headers=headers
            )
            
            # 记录响应信息
            self._log_response(response)
            
            # 处理Set-Cookie头
            if 'Set-Cookie' in response.headers:
                cookie_header = response.headers['Set-Cookie']
                if 'Max-Age=' in cookie_header:
                    max_age = cookie_header.split('Max-Age=')[1].split(';')[0]
                    self._save_session(response.cookies, max_age)
                else:
                    self._save_session(response.cookies)
            
            # 检查响应状态
            if response.status_code == 401 and not ignore_401:  # Unauthorized
                print("\n会话已过期或无效，请先执行登录命令：")
                print("python bd2_client_sim.py auth login\n")
                return None
                
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 401 and ignore_401:
                    return e.response.json()
                elif e.response.status_code == 401:
                    print("\n会话已过期或无效，请先执行登录命令：")
                    print("python bd2_client_sim.py auth login\n")
            else:
                print(f"\n请求失败: {str(e)}\n")
            return None

    def post(self, endpoint, data=None, headers=None, ignore_401=False):
        """Send POST request"""
        return self._send_request("POST", endpoint, data, headers, ignore_401)

    def get(self, endpoint, headers=None):
        """Send GET request"""
        # self.logger.log_info(f"GET {endpoint}")
        return self._send_request("GET", endpoint, None, headers)

    def put(self, endpoint, data=None, headers=None):
        """Send PUT request"""
        # self.logger.log_info(f"PUT {endpoint} - DATA: {data}")
        return self._send_request("PUT", endpoint, data, headers)

    def delete(self, endpoint, headers=None):
        """Send DELETE request"""
        # self.logger.log_info(f"DELETE {endpoint}")
        return self._send_request("DELETE", endpoint, None, headers)
