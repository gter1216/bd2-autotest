    def get_vm_list(self):
        """获取虚拟机列表"""
        self.logger.info("获取虚拟机列表")
        status_code, response = self.get("/api/v1/vms")
        if status_code == 200 and response:
            return response.get("vms", [])
        return []

    def get_vm_info(self, vm_id):
        """获取虚拟机信息"""
        self.logger.info(f"获取虚拟机信息: {vm_id}")
        status_code, response = self.get(f"/api/v1/vms/{vm_id}")
        if status_code == 200 and response:
            return response
        return None

    def create_vm(self, vm_data):
        """创建虚拟机"""
        self.logger.info("创建虚拟机")
        status_code, response = self.post("/api/v1/vms", vm_data)
        if status_code == 200 and response:
            return response
        return None

    def update_vm(self, vm_id, vm_data):
        """更新虚拟机"""
        self.logger.info(f"更新虚拟机: {vm_id}")
        status_code, response = self.put(f"/api/v1/vms/{vm_id}", vm_data)
        if status_code == 200 and response:
            return response
        return None

    def delete_vm(self, vm_id):
        """删除虚拟机"""
        self.logger.info(f"删除虚拟机: {vm_id}")
        status_code, response = self.delete(f"/api/v1/vms/{vm_id}")
        if status_code == 200:
            return True
        return False 