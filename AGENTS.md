# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库定位

本机 Docker 服务编排（不是应用代码库）。Traefik 做反向代理，`stacks.py` 是唯一入口，遍历 `infra/*` 与 `services/*` 下的 compose 目录做统一启停。依赖只有 Docker（含 compose v2）和 uv。

## 常用命令

`stacks.py` 是 uv 单文件脚本（首行 `#!/usr/bin/env -S uv run --script`），已 `chmod +x`，直接调用即可，等价 `uv run stacks.py`。

```bash
./stacks.py up                                  # 全量按序启（网络 → traefik → 其他 infra → services）
./stacks.py up services/hermes                  # 单起
./stacks.py up services/hermes services/trilium # 多起
./stacks.py down                                # 全量反序停（traefik 最后停）
./stacks.py restart [SVC ...]                   # 先 down 再 up
./stacks.py pull [SVC ...]                      # 拉镜像
./stacks.py ps    infra/traefik                 # 单服务状态
./stacks.py logs  infra/traefik                 # 单服务日志（-f --tail 200）
./stacks.py doctor                              # 环境自检：docker/compose/80 端口/*.localhost DNS/网络/stack 清单
```

无 lint / test：这是编排仓库，只有 compose 与一个薄脚本。改 compose 后 `./stacks.py restart <svc>`，再用 `curl -H "Host: <name>.localhost" http://localhost` 验证路由；改 `stacks.py` 后跑 `up`/`down`/`doctor` 验证。

## stacks.py 行为细节

- **启动顺序由 `discover_services()` 决定**（`stacks.py:28`）：`infra/*-net`（网络 stack）→ `infra/traefik` → 其他 `infra/*` → `services/*`（排除 `_template`）。`down` 时反转，保证网络 stack 最后销毁。改这个顺序会影响所有依赖。
- **批量执行遇错继续**（`batch()`）：单个 stack 失败不中断后续 stack，最终返回最大的非零退出码。
- **未知服务名**：打印可用服务清单后以 exit 2 退出。
- **`ps` / `logs` 只接受单个服务**，与 up/down/restart/pull 的多服务参数不同。
- **保持零依赖**：脚本是 PEP 723 单文件（`dependencies = []`），只用 stdlib，不要引入第三方包。

## 架构关键点

**网络生命周期与业务解耦**：`traefik-net` 与 `sandbox-net` 各由一个专用 stack（`infra/traefik-net`、`infra/sandbox-net`）管理，与任何业务容器的启停无关（若把网络定义揉进 traefik 的 compose，停 traefik 会把业务依赖的网顺带销毁）。每个网络 stack 附一个 busybox anchor 容器（`sleep infinity`）占位——纯 networks 的 compose 没有可运行的服务，anchor 让 `up` 真正把网建出来。业务 compose 用 `networks.default: {name: traefik-net, external: true}` 接入，不定义网络本身。

| stack | 网络 | 子网 | 用途 |
| --- | --- | --- | --- |
| `infra/traefik-net` | `traefik-net` | Docker 默认 | 反代主网络，traefik / portainer / 业务服务接入 |
| `infra/sandbox-net` | `sandbox-net` | `172.30.0.0/16`（桥 `lab0`） | 临时测试、隔离环境，与主网络无交叉，业务不要接 |

**Traefik 暴露规则**：`exposedByDefault=false`（见 `infra/traefik/traefik.yml`），业务服务必须显式打 `traefik.enable=true` 才被反代；`serversTransport.insecureSkipVerify=true` 允许后端自签 TLS（例如 Portainer 的 9443）。入口只有 `:80`（HTTP），访问走 `*.localhost`。

启动后入口：

- Traefik Dashboard: http://traefik.localhost/dashboard/ （路由规则含 `PathPrefix(/dashboard || /api)`）
- Portainer: http://portainer.localhost （后端 9443 自签 HTTPS，走 `scheme=https` label）

**镜像版本约定**：`image: <name>:${<NAME>_TAG:-默认值}`。
- infra 服务的 `.env` **入库**（`.gitignore` 里 `!infra/**/.env` 显式放行），锁定所有人一致版本。
- 业务服务的 `.env` **不入库**，本机自管。

**仓库跟踪范围**：`.gitignore` 用 `/services/*` + `!/services/_template/` 把所有业务服务目录整体屏蔽，只跟踪 `infra/`、`services/_template/`、`images/`、根目录脚本。新增业务服务是 `cp -r services/_template services/<name>` 然后本机放着，不入库。`images/<name>/` 是自构建镜像的构建上下文（目前只有 devkit），不是 compose stack（stacks.py 不会发现它）；`images/devkit/` 改动后需 `docker build -t local/devkit:latest images/devkit/` 重建才生效。

**新增业务服务模板**：`services/_template/docker-compose.yml` + `services/_template/README.md`。里面的 `myapp` 是占位，复制后全量替换服务名即可。模板已带 `extra_hosts: host.docker.internal:host-gateway`，容器内可访问宿主机。

## compose 编写约定

- **`container_name` 固定为服务名**：`doctor` 用 `docker ps --filter name=^traefik$` 精确匹配来判断 80 端口是否被 traefik 正常占用，改名会让 doctor 误报。
- **命名卷显式指定 `name:`**（如 `portainer_data`），避免卷名随 compose 项目名（目录名）前缀漂移。
- **新增 infra 服务的清单**：`.env` 入库锁版本；打 `traefik.enable=true` + Host 规则接入反代；若是新网络或要纳入端口/DNS 检查，同步改 `cmd_doctor()` 里的检查列表。

## 用户记忆

`docs/superpowers/` 下的 spec/plan 属于 Superpowers 工作产物，**不要 git add / commit**。
