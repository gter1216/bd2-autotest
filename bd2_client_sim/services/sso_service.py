    def get_user_info(self):
        """获取用户信息"""
        self.logger.info("获取用户信息")
        status_code, response = self.get("/api/v1/user")
        if status_code == 200 and response:
            return response
        return None

    def update_user_info(self, user_data):
        """更新用户信息"""
        self.logger.info("更新用户信息")
        status_code, response = self.put("/api/v1/user", user_data)
        if status_code == 200 and response:
            return response
        return None

    def get_user_permissions(self):
        """获取用户权限"""
        self.logger.info("获取用户权限")
        status_code, response = self.get("/api/v1/user/permissions")
        if status_code == 200 and response:
            return response.get("permissions", [])
        return [] 