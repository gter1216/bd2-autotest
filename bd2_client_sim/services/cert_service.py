"""
Description: This module provides certificate management functionality.

Changelog:
- 2025-03-10: Initial creation.
"""

import logging
from typing import Optional
import requests

from ..core.endpoint_manager import EndpointManager
from ..core.result import Result
from ..core.base_service import BaseService

class CertService(BaseService):
    """证书服务类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化证书服务
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
        
    def init_cert(self) -> Result:
        """初始化证书功能
        
        Returns:
            Result: 包含初始化结果的 Result 对象
        """
        self.logger.info("开始初始化证书功能")
        cert_init_url = EndpointManager.get_endpoint("cert_init")
        self.logger.debug(f"初始化证书功能: {cert_init_url}")
        
        try:
            # 设置超时时间为 5 秒
            status_code, response = self.post(cert_init_url, timeout=5)
            
            if status_code != 200:
                self.logger.error(f"证书功能初始化失败，状态码: {status_code}")
                return Result.error(
                    {"status_code": status_code, "response": response},
                    f"证书功能初始化失败，状态码: {status_code}"
                )
                
            if not response or not isinstance(response, dict):
                self.logger.error("证书功能初始化响应数据格式错误")
                return Result.error(
                    {"response": response},
                    "证书功能初始化响应数据格式错误"
                )
                
            status = response.get("status")
            message = response.get("message", "")
            
            if status == 1:
                self.logger.info("证书功能初始化成功")
                return Result.success(response)
            else:
                self.logger.error(f"证书功能初始化失败: {message}")
                return Result.error(
                    {"status": status, "message": message},
                    f"证书功能初始化失败: {message}"
                )
                
        except requests.Timeout:
            self.logger.error("证书功能初始化超时")
            return Result.error(
                {"timeout": True},
                "证书功能初始化超时（5秒）"
            )
        except Exception as e:
            self.logger.error(f"证书功能初始化异常: {str(e)}")
            return Result.error(
                {"exception": str(e)},
                f"证书功能初始化异常: {str(e)}"
            )