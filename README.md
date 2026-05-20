# Stacks

本地 Docker 服务编排，Traefik 做反向代理统一管理路由。

## 仓库结构

```
stacks/
├── .gitignore
├── Makefile
├── infra/
│   ├── traefik/         # 反向代理 + Dashboard（含 .env 锁定版本）
│   └── portainer/       # 容器管理面板（含 .env 锁定版本）
└── services/
    └── _template/       # 新服务接入模板
```

## 仓库跟踪范围

仓库只跟踪基础设施（`infra/`）与模板（`services/_template/`）。`services/` 下的真实业务服务**不入库**——你在本机按需 `cp services/_template/ services/<name>/` 放进去就行。

`Makefile` 会自动发现 `infra/*` 与 `services/*`（排除 `_template`）下的 compose 目录，无需手动登记。

## 快速开始

```bash
# 启动本机所有服务（infra + services 下所有非 _template 目录）
make up

# 查看某服务日志
make logs S=infra/traefik

# 查看某服务状态
make ps S=infra/portainer

# 停止全部
make down

# 拉取镜像更新
make pull
```

启动后访问：

- Traefik Dashboard: http://traefik.localhost/dashboard/
- Portainer: http://portainer.localhost

## 镜像版本

所有 compose 使用 `image: <name>:${<NAME>_TAG:-默认值}` 形式。

- **infra 服务**（traefik、portainer）：版本锁在 `infra/<name>/.env`，**入库**，所有人拿到一致版本。
- **业务服务**（services/&lt;name&gt;）：版本锁在 `services/<name>/.env`，**不入库**，本机自管。

## 添加新服务

参见 [services/_template/README.md](services/_template/README.md)。

## 不会被提交的内容（见 .gitignore）

- 运行时数据：`**/trilium-data/`、`**/portainer_data/`、`**/letsencrypt/`、`**/acme.json`
- 密钥：`credentials.json`、`config.json`（保留 `config.example.json`）、`*.pem`、`*.key`
- 环境变量真实值：`**/.env`（infra 下的 `.env` 例外，会入库）
- 个人 IDE 配置：`.claude/settings.local.json`、`.vscode/`、`.idea/`

## Traefik 关键配置

- 入口：`:80` (HTTP)
- Docker provider：`exposedByDefault=false`，需 `traefik.enable=true` 才暴露
- 网络：`traefik-net`（由 traefik compose 创建，business 服务以 external 方式接入）
- `insecureSkipVerify=true`：允许后端自签 TLS（如 Portainer 的 9443）
