import os
import sys
import importlib.util

# 添加项目根目录到 Python 路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# 使用绝对路径导入
bd2_client_sim_path = os.path.join(root_dir, "bd2_client_sim.py")
spec = importlib.util.spec_from_file_location("bd2_client_sim_module", bd2_client_sim_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BD2ClientSim = module.BD2ClientSim 