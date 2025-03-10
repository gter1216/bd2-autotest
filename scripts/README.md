# BD2 Client 凭据管理说明

## 凭据管理方案

BD2 Client 支持三种凭据管理方式，按优先级从高到低排序：

1. 个人凭据（推荐）
   - 存储位置：`config/hosts/<hostname>/auth.enc`
   - 特点：按主机名区分，每台机器独立配置
   - 适用场景：在特定机器上使用个人账号

2. 项目凭据
   - 存储位置：`config/auth.enc`
   - 特点：所有用户共享，通常是公共测试账号
   - 适用场景：自动化测试、CI/CD 等场景

3. 明文配置（不推荐）
   - 存储位置：`config.yaml`
   - 特点：配置简单但不安全
   - 适用场景：仅用于开发调试

## 目录结构

```
config/
├── auth.enc          # 项目凭据（加密）
├── auth.key          # 项目凭据密钥
└── hosts/           # 个人凭据目录（按主机名区分）
    ├── laptop-01/   # 某台机器的个人凭据
    │   ├── auth.enc # 个人凭据（加密）
    │   └── auth.key # 个人凭据密钥
    └── laptop-02/   # 另一台机器的个人凭据
        ├── auth.enc
        └── auth.key
```

## 安全性说明

1. 加密存储
   - 所有凭据都使用 Fernet 对称加密算法加密存储
   - 密钥和加密数据分开存储
   - 个人凭据：密钥存储在 `config/hosts/<hostname>/auth.key`
   - 项目凭据：密钥存储在 `config/auth.key`

2. 访问控制
   - 个人凭据：按主机名隔离，不同机器互不影响
   - 项目凭据：所有项目成员可访问
   - 登出时自动清理个人凭据

## 使用方法

### 1. 查看当前使用的凭据
```bash
python scripts/manage_auth.py show
```

### 2. 设置项目凭据（需要权限）
```bash
python scripts/manage_auth.py set-project
```
注意：这会更新所有用户共享的项目凭据，请谨慎操作。

### 3. 设置个人凭据
```bash
python scripts/manage_auth.py set-personal
```
这会在 `config/hosts/<hostname>/` 目录下创建加密的个人凭据。

### 4. 删除个人凭据
```bash
python scripts/manage_auth.py remove-personal
```
删除后会自动回退到使用项目凭据。

## 最佳实践

1. 日常使用
   - 在每台新机器上首次使用时设置个人凭据：`manage_auth.py set-personal`
   - 密码变更时在所有使用的机器上更新个人凭据
   - 可以随时查看使用的是哪个凭据：`manage_auth.py show`

2. 自动化测试
   - 使用项目凭据（自动加载）
   - 不需要额外配置
   - 如果需要更新项目凭据：`manage_auth.py set-project`

3. 安全建议
   - 优先使用个人凭据
   - 不要在代码或配置文件中明文存储密码
   - 定期更新密码时及时更新所有机器上的凭据

## 常见问题

1. 找不到凭据？
   - 使用 `manage_auth.py show` 查看当前使用的凭据
   - 确保已经在当前机器上设置了个人凭据或存在项目凭据

2. 密码已更改？
   - 在所有使用的机器上运行 `manage_auth.py set-personal` 更新个人凭据
   - 如果是项目凭据，联系管理员更新

3. 想切换到项目凭据？
   - 使用 `manage_auth.py remove-personal` 删除当前机器的个人凭据
   - 系统会自动切换到使用项目凭据

4. 凭据文件在哪里？
   - 个人凭据：`config/hosts/<hostname>/auth.enc` 和 `auth.key`
   - 项目凭据：`config/auth.enc` 和 `auth.key`

5. 在多台机器上使用？
   - 每台机器都需要单独配置个人凭据
   - 个人凭据按主机名存储，互不影响
   - 项目凭据所有机器共享 