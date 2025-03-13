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

@pytest.fixture(scope="session")
def cert_init_fixture(vehicle_status_fixture):
    """证书初始化 fixture"""
    client = BD2ClientSim(task_type="auth", action="cert_init")
    result = client.execute()
    assert result['success'] is True, f"Certificate initialization failed: {result.get('error', 'Unknown error')}"
    return client

@pytest.fixture(scope="session")
def cert_deploy_fixture(cert_init_fixture):
    """证书部署 fixture"""
    client = BD2ClientSim(task_type="auth", action="cert_deploy")
    result = client.execute()
    assert result['success'] is True, f"Certificate deployment failed: {result.get('error', 'Unknown error')}"
    return client

def test_cert_init(cert_init_fixture):
    """测试证书初始化功能"""
    assert cert_init_fixture is not None

def test_cert_deploy(cert_deploy_fixture):
    """测试证书部署功能"""
    assert cert_deploy_fixture is not None

def test_cert_status(cert_init_fixture):
    """测试证书状态功能"""
    assert cert_init_fixture is not None 