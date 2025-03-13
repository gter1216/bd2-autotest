import pytest
from .common import BD2ClientSim

@pytest.fixture(scope="session")
def login_fixture():
    """登录 fixture"""
    client = BD2ClientSim(task_type="auth", action="login")
    result = client.execute()
    assert result['success'] is True, f"Login failed: {result.get('error', 'Unknown error')}"
    return client

@pytest.fixture(scope="session")
def vehicle_status_fixture(login_fixture):
    """获取车辆状态 fixture"""
    client = BD2ClientSim(task_type="auth", action="get_vehicle_st")
    result = client.execute()
    assert result['success'] is True, f"Get vehicle status failed: {result.get('error', 'Unknown error')}"
    return client 