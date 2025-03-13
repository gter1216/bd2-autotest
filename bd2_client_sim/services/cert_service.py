"""
Description: This module provides certificate management functionality.

Changelog:
- 2025-03-10: Initial creation.
"""

from typing import Optional, Dict, Any
import requests
import time
import os
import json
from datetime import datetime

from ..core.endpoint_manager import EndpointManager
from ..core.result import Result
from ..core.base_service import BaseService
from utils.logger_manager import LoggerManager

class CertService(BaseService):
    """证书服务类"""
    
    def __init__(self, base_url, cs_log: bool = False):
        """初始化证书服务
        
        Args:
            base_url: 基础URL
            cs_log: 是否启用 CS 日志
        """
        super().__init__(base_url)
        self.logger = self._get_logger()
        self.cs_log = cs_log
        
    def _write_to_cs_log(self, content: str):
        """将内容写入 console.log 文件
        
        Args:
            content: 要写入的内容
        """
        try:
            session_dir = LoggerManager.get_session_dir()
            if session_dir:
                log_file = os.path.join(session_dir, 'console.log')
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{content}\n")
        except Exception as e:
            self.logger.error(f"写入 cs.log 失败: {str(e)}")
            
    def _handle_cs_log(self):
        """处理 CS 日志
        
        如果启用了 cs_log，获取并记录控制台日志
        """
        if self.cs_log:
            try:
                console_logs_url = EndpointManager.get_endpoint("cert_console_logs")
                _, logs_response = self.get(console_logs_url, no_log=True)
                
                if logs_response and 'logs' in logs_response and logs_response['logs']:
                    for log in logs_response['logs']:
                        timestamp = log.get('timestamp', '')
                        log_type = log.get('type', '')
                        data = log.get('data', [])
                        
                        # 将每条日志写入文件
                        for msg in data:
                            self._write_to_cs_log(f"[{timestamp}][{log_type}] {msg}")
            except Exception as e:
                self.logger.error(f"获取控制台日志失败: {str(e)}")
            
    def init_cert(self) -> Result:
        """初始化证书功能
        
        Returns:
            Result: 包含初始化结果的 Result 对象
        """
        self.logger.info("开始初始化证书功能")
        cert_init_url = EndpointManager.get_endpoint("cert_init")
        self.logger.debug(f"初始化证书功能: {cert_init_url}")
        
        try:
            # 发送初始化请求，设置5秒超时
            status_code, response = self.post(cert_init_url, timeout=5)
            
            # 如果状态码不是200，直接返回错误
            if status_code != 200:
                self.logger.error(f"证书功能初始化失败，状态码: {status_code}")
                self._handle_cs_log()
                return Result.error(
                    {"status_code": status_code},
                    f"证书功能初始化失败，状态码: {status_code}"
                )
                
            # 处理 CS 日志
            self._handle_cs_log()
            
            return Result.success({"status_code": status_code})
                
        except requests.Timeout:
            self.logger.error("证书功能初始化超时")
            self._handle_cs_log()
            return Result.error(
                {"timeout": True},
                "证书功能初始化超时（5秒）"
            )
        except Exception as e:
            self.logger.error(f"证书功能初始化异常: {str(e)}")
            self._handle_cs_log()
            return Result.error(
                {"exception": str(e)},
                f"证书功能初始化异常: {str(e)}"
            )
            
    def get_cert_st(self, ecu: Optional[str] = None) -> Result:
        """获取证书状态
        
        Args:
            ecu: 可选的 ECU 名称，如果提供则只返回该 ECU 的状态
        
        Returns:
            Result: 包含证书状态的 Result 对象，格式为：
            {
                "code": result.code,
                "message": result.message,
                "current_group": result.current_group,
                "current_operation": result.current_operation,
                "ecus": [
                    {
                        "ecu": ecu.ecu,
                        "group": ecu.group,
                        "online": ecu.online,
                        "rd_status": ecu.rd_status,
                        "certs": [
                            {
                                "type": cert.type,
                                "name": cert.name,
                                "state": cert.state,
                                "start_time": cert.start_time
                            }
                        ]
                    }
                ]
            }
        """
        self.logger.info("开始获取证书状态")
        
        try:
            ecus_url = EndpointManager.get_endpoint("cert_ecus")
            status_code, ecus_response = self.get(ecus_url)
            
            if status_code != 200:
                self.logger.error(f"获取证书状态失败，状态码: {status_code}")
                self._handle_cs_log()
                return Result.error(
                    {"status_code": status_code},
                    f"获取证书状态失败，状态码: {status_code}"
                )
            
            if not ecus_response:
                self.logger.error("获取证书状态失败：响应为空")
                self._handle_cs_log()
                return Result.error({"error": "获取证书状态失败：响应为空"})
            
            # 提取需要的信息
            result = ecus_response.get('result', {})
            ecus = ecus_response.get('ecus', [])
            
            # 如果指定了 ECU，过滤结果
            if ecu:
                ecus = [e for e in ecus if e.get('ecu', '').lower() == ecu.lower()]
                if not ecus:
                    self._handle_cs_log()
                    return Result.error(
                        {"error": f"未找到 ECU: {ecu}"},
                        f"未找到 ECU: {ecu}"
                    )
            
            # 记录 ECU 信息
            for ecu_info in ecus:
                ecu_log = [
                    f"\nECU: {ecu_info.get('ecu')}",
                    f"Group: {ecu_info.get('group')}",
                    f"Online: {ecu_info.get('online')}",
                    f"RD Status: {ecu_info.get('rd_status')}",
                    "Certificates:"
                ]
                
                for cert in ecu_info.get('certs', []):
                    cert_log = [
                        f"  - Type: {cert.get('type')}",
                        f"    Name: {cert.get('name')}",
                        f"    State: {cert.get('state')}",
                        f"    Start Time: {cert.get('start_time')}"
                    ]
                    ecu_log.extend(cert_log)
                
                self.logger.info("\n".join(ecu_log))
            
            # 处理 CS 日志
            self._handle_cs_log()
            
            # 构造返回结果
            return Result.success({
                "code": result.get('code'),
                "message": result.get('message'),
                "current_group": result.get('current_group'),
                "current_operation": result.get('current_operation'),
                "ecus": [{
                    "ecu": ecu_info.get('ecu'),
                    "group": ecu_info.get('group'),
                    "online": ecu_info.get('online'),
                    "rd_status": ecu_info.get('rd_status'),
                    "certs": [{
                        "type": cert.get('type'),
                        "name": cert.get('name'),
                        "state": cert.get('state'),
                        "start_time": cert.get('start_time')
                    } for cert in ecu_info.get('certs', [])]
                } for ecu_info in ecus]
            })
            
        except Exception as e:
            self.logger.error(f"获取证书状态异常: {str(e)}")
            self._handle_cs_log()
            return Result.error({"error": f"获取证书状态异常: {str(e)}"})

    def deploy_cert(self, ecu: str) -> Result:
        """部署证书到指定 ECU
        
        Args:
            ecu: ECU 类型 (ccc, zone_front, zone_rear, all)
            
        Returns:
            Result: 包含部署结果的 Result 对象
        """
        self.logger.info(f"开始部署证书到 {ecu}")
        
        try:
            # 根据 ECU 类型确定 x 值
            x_map = {
                'all': -1,
                'ccc': 0,
                'zone_front': 1,
                'zone_rear': 2
            }
            
            if ecu not in x_map:
                self._handle_cs_log()
                return Result.error(
                    {"error": f"无效的 ECU 类型: {ecu}"},
                    f"无效的 ECU 类型: {ecu}"
                )
                
            x = x_map[ecu]
            
            # 发送部署请求
            cert_flash_url = EndpointManager.get_endpoint("cert_flash")
            status_code, response = self.post(cert_flash_url, {
                "group": x,
            })
            
            if status_code != 202:
                self._handle_cs_log()
                return Result.error(
                    {"status_code": status_code},
                    f"部署证书失败，状态码: {status_code}"
                )
            
            # 循环检查部署状态
            failed_ecus = []
            start_time = time.time()
            timeout = 600  # 10分钟超时
            
            while True:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    self.logger.warning("部署证书超时（600秒）")
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus, "timeout": True},
                            f"部署证书超时，部分 ECU 失败: {failed_ecus}"
                        )
                    return Result.error(
                        {"timeout": True},
                        "部署证书超时（600秒）"
                    )
                
                time.sleep(2)  # 等待 2 秒
                
                # 获取证书状态
                # status_code, ecus_response = self.get(EndpointManager.get_endpoint("cert_ecus"), no_log=True)
                status_code, ecus_response = self.get(EndpointManager.get_endpoint("cert_ecus"))

                if status_code != 200:
                    self._handle_cs_log()
                    return Result.error(
                        {"status_code": status_code},
                        f"获取证书状态失败，状态码: {status_code}"
                    )
                
                result = ecus_response.get('result', {})
                code = result.get('code')
                
                # 检查每个 ECU 的证书状态
                for ecu_info in ecus_response.get('ecus', []):
                    for cert in ecu_info.get('certs', []):
                        if cert.get('state') == 3:  # 证书状态为 3 表示失败
                            # 检查是否已经记录过这个失败的证书
                            cert_info = {
                                'ecu': ecu_info.get('ecu'),
                                'cert_name': cert.get('name'),
                                'state': cert.get('state')
                            }
                            if cert_info not in failed_ecus:
                                failed_ecus.append(cert_info)
                
                # 根据操作状态决定是否继续
                if code == 0:  # 正在进行
                    continue
                elif code == 1:  # 成功
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus},
                            f"部分 ECU 证书部署失败: {failed_ecus}"
                        )
                    return Result.success({"message": "证书部署成功"})
                elif code == 2:  # 失败
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus},
                            f"证书部署失败: {failed_ecus}"
                        )
                    return Result.error(
                        {"error": "证书部署失败"},
                        "证书部署失败"
                    )
                    
        except Exception as e:
            self.logger.error(f"部署证书异常: {str(e)}")
            self._handle_cs_log()
            return Result.error(
                {"error": f"部署证书异常: {str(e)}"}
            )

    def revoke_cert(self, ecu: str) -> Result:
        """撤销指定 ECU 的证书
        
        Args:
            ecu: ECU 类型 (ccc, zone_front, zone_rear)
            
        Returns:
            Result: 包含撤销结果的 Result 对象
        """
        self.logger.info(f"开始撤销 {ecu} 的证书")
        
        try:
            # 根据 ECU 类型确定 x 值
            x_map = {
                'ccc': 0,
                'zone_front': 1,
                'zone_rear': 2
            }
            
            if ecu not in x_map:
                self._handle_cs_log()
                return Result.error(
                    {"error": f"无效的 ECU 类型: {ecu}"},
                    f"无效的 ECU 类型: {ecu}"
                )
                
            x = x_map[ecu]
            
            # 发送撤销请求
            cert_revoke_url = EndpointManager.get_endpoint("cert_revoke")
            status_code, response = self.post(cert_revoke_url, {
                "group": x
            })
            
            if status_code != 202:
                self._handle_cs_log()
                return Result.error(
                    {"status_code": status_code},
                    f"撤销证书失败，状态码: {status_code}"
                )
            
            # 循环检查撤销状态
            failed_ecus = []
            start_time = time.time()
            timeout = 600  # 10分钟超时
            
            while True:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    self.logger.warning("撤销证书超时（600秒）")
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus, "timeout": True},
                            f"撤销证书超时，部分 ECU 失败: {failed_ecus}"
                        )
                    return Result.error(
                        {"timeout": True},
                        "撤销证书超时（600秒）"
                    )
                
                time.sleep(2)  # 等待 2 秒
                
                # 获取证书状态
                # status_code, ecus_response = self.get(EndpointManager.get_endpoint("cert_ecus"), no_log=True)
                status_code, ecus_response = self.get(EndpointManager.get_endpoint("cert_ecus"))

                if status_code != 200:
                    self._handle_cs_log()
                    return Result.error(
                        {"status_code": status_code},
                        f"获取证书状态失败，状态码: {status_code}"
                    )
                
                result = ecus_response.get('result', {})
                code = result.get('code')
                
                # 检查每个 ECU 的证书状态
                for ecu_info in ecus_response.get('ecus', []):
                    for cert in ecu_info.get('certs', []):
                        if cert.get('state') == 3:  # 证书状态为 3 表示失败
                            # 检查是否已经记录过这个失败的证书
                            cert_info = {
                                'ecu': ecu_info.get('ecu'),
                                'cert_name': cert.get('name'),
                                'state': cert.get('state')
                            }
                            if cert_info not in failed_ecus:
                                failed_ecus.append(cert_info)
                
                # 根据操作状态决定是否继续
                if code == 0:  # 正在进行
                    continue
                elif code == 1:  # 成功
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus},
                            f"部分 ECU 证书撤销失败: {failed_ecus}"
                        )
                    return Result.success({"message": "证书撤销成功"})
                elif code == 2:  # 失败
                    self._handle_cs_log()
                    if failed_ecus:
                        return Result.error(
                            {"failed_ecus": failed_ecus},
                            f"证书撤销失败: {failed_ecus}"
                        )
                    return Result.error(
                        {"error": "证书撤销失败"},
                        "证书撤销失败"
                    )
                    
        except Exception as e:
            self.logger.error(f"撤销证书异常: {str(e)}")
            self._handle_cs_log()
            return Result.error(
                {"error": f"撤销证书异常: {str(e)}"}
            )