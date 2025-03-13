"""
Description: This module manages API endpoints and provides formatted URLs.

Changelog:
- 2025-03-07: Initial Creation.
"""

class EndpointManager:
    """Manage API endpoints"""

    ENDPOINTS = {
        # 认证相关
        "vm_login": "/api/v1/login",
        "sso_login": "/api/v1/sso_auth",
        "vehicle_status": "/api/v1/app/vehicle_health/status",
        
        # 证书相关
        "cert_init": "/api/v1/app/cert/init",
        "cert_flash": "/api/v1/app/cert/flash",
        "cert_revoke": "/api/v1/app/cert/revoke",
        "cert_ecus": "/api/v1/app/cert/ecus",
        "cert_console_logs": "/api/v1/app/cert/logs",

        # 通用 SSE 日志相关
        "basic_vehicle_service_log": "/api/v1/log/basic_vehicle_service_log",
        "uds_log": "/api/v1/log/udservice",
        # "event_log": "/api/v1/event",
        "appl_log": "/api/v1/log/appllog",
    }

    @classmethod
    def get_endpoint(cls, name, **kwargs):
        """Get API endpoint and format URL"""
        if name in cls.ENDPOINTS:
            return cls.ENDPOINTS[name].format(**kwargs)
        raise ValueError(f"API endpoint not found: {name}")
