#!/usr/bin/env python3
"""
BD2 Client 凭据管理工具
用于管理项目凭据和个人凭据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bd2_client_sim.services.auth_service import AuthService
import argparse
import getpass

def show_current_credentials(auth_service):
    """显示当前使用的凭据信息"""
    print("\n当前凭据信息：")
    print("-" * 50)
    print(auth_service.get_current_credentials_info())
    print("-" * 50)

def save_project_credentials(auth_service):
    """保存/更新项目凭据"""
    print("\n设置项目凭据（用于自动化测试的公共账号）")
    print("-" * 50)
    print("注意：这将更新 config/auth.enc 中的项目级凭据")
    confirm = input("是否继续？[y/N]: ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    vm_username = input("请输入VM用户名: ")
    vm_password = getpass.getpass("请输入VM密码: ")
    sso_username = input("请输入SSO用户名: ")
    sso_password = getpass.getpass("请输入SSO密码: ")
    
    try:
        auth_service.save_project_credentials(
            vm_username=vm_username,
            vm_password=vm_password,
            sso_username=sso_username,
            sso_password=sso_password
        )
        print("\n项目凭据已更新")
        
    except Exception as e:
        print(f"\n保存凭据时出错: {str(e)}")

def save_personal_credentials(auth_service):
    """保存/更新个人凭据"""
    print("\n设置个人凭据（保存在用户主目录下）")
    print("-" * 50)
    vm_username = input("请输入VM用户名: ")
    vm_password = getpass.getpass("请输入VM密码: ")
    sso_username = input("请输入SSO用户名: ")
    sso_password = getpass.getpass("请输入SSO密码: ")
    
    try:
        auth_service.save_user_credentials(
            vm_username=vm_username,
            vm_password=vm_password,
            sso_username=sso_username,
            sso_password=sso_password
        )
        print("\n个人凭据已更新")
        
    except Exception as e:
        print(f"\n保存凭据时出错: {str(e)}")

def remove_personal_credentials(auth_service):
    """删除个人凭据"""
    try:
        if auth_service.user_config_path.exists():
            auth_service.user_config_path.unlink()
        if auth_service.user_key_path.exists():
            auth_service.user_key_path.unlink()
        print("\n个人凭据已删除")
    except Exception as e:
        print(f"\n删除凭据时出错: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="BD2 Client 凭据管理工具")
    parser.add_argument('action', choices=['show', 'set-project', 'set-personal', 'remove-personal'], 
                       help='''操作类型：
                           show = 显示当前凭据信息
                           set-project = 设置项目凭据（需要权限）
                           set-personal = 设置个人凭据
                           remove-personal = 删除个人凭据''')
    
    args = parser.parse_args()
    
    # 初始化服务
    auth_service = AuthService("https://your-server-url")  # 替换为实际的服务器地址
    
    if args.action == 'show':
        show_current_credentials(auth_service)
    elif args.action == 'set-project':
        save_project_credentials(auth_service)
        show_current_credentials(auth_service)
    elif args.action == 'set-personal':
        save_personal_credentials(auth_service)
        show_current_credentials(auth_service)
    elif args.action == 'remove-personal':
        remove_personal_credentials(auth_service)
        show_current_credentials(auth_service)

if __name__ == "__main__":
    main() 