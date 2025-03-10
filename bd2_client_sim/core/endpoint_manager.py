"""
Description: This module manages API endpoints and provides formatted URLs.

Changelog:
- 2025-03-07: Initial Creation.
"""

class EndpointManager:
    """Manage API endpoints"""

    ENDPOINTS = {
        "vm_login": "/api/v1/login",
        "sso_login": "/api/v1/sso_auth",
        "vehicle_status": "/api/v1/app/vehicle_health/status",
        # "auth_logout": "/auth/logout",
        # "flash_status": "/flash/status/{task_id}",
        # "diagnosis_run": "/diagnosis/run",
        "certificate_install": "/certificate/install",
        "certificate_uninstall": "/certificate/uninstall/{cert_id}",
    }

    @classmethod
    def get_endpoint(cls, name, **kwargs):
        """Get API endpoint and format URL"""
        if name in cls.ENDPOINTS:
            return cls.ENDPOINTS[name].format(**kwargs)
        raise ValueError(f"API endpoint not found: {name}")
