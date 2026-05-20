# Stacks

本地 Docker 服务编排，Traefik 做反向代理统一管理路由。

## 仓库结构

```
stacks/
├── .env.example
├── .gitignore
├── Makefile
├── infra/
│   ├── traefik/         # 反向代理 + Dashboard
│   └── portainer/       # 容器管理面板
└── services/
    └── _template/       # 新服务接入模板
```

## 分支策略

- **main**：仅基础设施（infra/）+ 模板（services/_template/）
- **service/&lt;name&gt;**：单个业务服务（如 `service/trilium`、`service/kirors`），从 main 切出，仅在自己分支放开 `services/<name>/`

操作某个业务服务时切到对应分支。多服务并存可用 git worktree。

## 快速开始

```bash
# 启动 main 分支基础设施（traefik + portainer）
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

所有 compose 使用 `image: <name>:${<NAME>_TAG:-默认值}` 形式。复制 `.env.example` 为 `.env` 锁定版本：

```bash
cp .env.example .env
# 编辑 .env，例如 TRAEFIK_TAG=v3.7
```

## 添加新服务

参见 [services/_template/README.md](services/_template/README.md)。

## 不会被提交的内容（见 .gitignore）

- 运行时数据：`**/trilium-data/`、`**/portainer_data/`、`**/letsencrypt/`、`**/acme.json`
- 密钥：`credentials.json`、`config.json`（保留 `config.example.json`）、`*.pem`、`*.key`
- 环境变量真实值：`.env`（保留 `.env.example`）
- 个人 IDE 配置：`.claude/settings.local.json`、`.vscode/`、`.idea/`

## Traefik 关键配置

- 入口：`:80` (HTTP)
- Docker provider：`exposedByDefault=false`，需 `traefik.enable=true` 才暴露
- 网络：`traefik-net`（由 traefik compose 创建，business 服务以 external 方式接入）
- `insecureSkipVerify=true`：允许后端自签 TLS（如 Portainer 的 9443）
