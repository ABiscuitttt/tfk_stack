# Stacks

本地 Docker 服务编排，Traefik 做反向代理统一管理路由。

## 仓库结构

```
stacks/
├── .gitignore
├── stacks.py            # uv 单文件脚本，统一启停入口
├── infra/
│   ├── traefik/         # 反向代理 + Dashboard（含 .env 锁定版本）
│   └── portainer/       # 容器管理面板（含 .env 锁定版本）
└── services/
    └── _template/       # 新服务接入模板
```

## 仓库跟踪范围

仓库只跟踪基础设施（`infra/`）与模板（`services/_template/`）。`services/` 下的真实业务服务**不入库**——你在本机按需 `cp services/_template/ services/<name>/` 放进去就行。

`stacks.py` 会自动发现 `infra/*` 与 `services/*`（排除 `_template`）下的 compose 目录，无需手动登记。

## 依赖

- Docker（含 `docker compose` v2）
- [uv](https://docs.astral.sh/uv/)（脚本首行 `#!/usr/bin/env -S uv run --script`，无需额外安装 Python 依赖）

## 快速开始

脚本已 `chmod +x`，可直接 `./stacks.py <cmd>`，等价 `uv run stacks.py <cmd>`。

```bash
# 启动本机所有服务（infra + services 下所有非 _template 目录，traefik 优先）
./stacks.py up

# 只启单个（或几个）服务
./stacks.py up services/hermes
./stacks.py up services/hermes services/trilium

# 停止全部（反序，traefik 最后停）
./stacks.py down

# 只停某几个
./stacks.py down services/hermes

# 先 down 再 up（可带服务参数）
./stacks.py restart
./stacks.py restart services/hermes

# 拉取镜像
./stacks.py pull
./stacks.py pull services/hermes

# 单服务状态 / 日志
./stacks.py ps infra/traefik
./stacks.py logs infra/traefik

# 帮助
./stacks.py -h
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

- 整个 `services/<name>/`（除 `_template`）— 业务服务的 compose、配置、运行时数据、密钥统统在这层一并屏蔽
- `**/.env`（`infra/` 下的 `.env` 例外，入库以锁定版本）
- 个人 IDE 配置：`.claude/settings.local.json`、`.vscode/`、`.idea/`

## Traefik 关键配置

- 入口：`:80` (HTTP)
- Docker provider：`exposedByDefault=false`，需 `traefik.enable=true` 才暴露
- 网络：`traefik-net`（由 traefik compose 创建，business 服务以 external 方式接入）
- `insecureSkipVerify=true`：允许后端自签 TLS（如 Portainer 的 9443）
