"""
Description: This module provides a common result class for API responses.

Changelog:
- 2025-03-10: Initial creation.
"""

from typing import Optional, Dict, Any

class Result:
    """通用结果类，用于统一 API 响应格式"""
    
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """初始化结果对象
        
        Args:
            success: 是否成功
            data: 响应数据
            error: 错误信息
        """
        self.success = success
        self.data = data or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 包含 success、data 和 error 的字典
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }

    @classmethod
    def success(cls, data: Optional[Dict[str, Any]] = None) -> 'Result':
        """创建成功结果
        
        Args:
            data: 响应数据
            
        Returns:
            Result: 成功结果对象
        """
        return cls(success=True, data=data)

    @classmethod
    def error(cls, error: str) -> 'Result':
        """创建错误结果
        
        Args:
            error: 错误信息
            
        Returns:
            Result: 错误结果对象
        """
        return cls(success=False, error=error) 