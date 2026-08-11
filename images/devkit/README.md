# devkit

开发容器镜像定义。基于 `mcr.microsoft.com/devcontainers/base:noble`（已内置 common-utils 基础包 / zsh / Oh My Zsh / `vscode` 用户 uid=1000 + NOPASSWD sudo），增量：Go、Node（nvm LTS）、Rust、uv、Claude CLI、clang/cmake/gdb、tmux/neovim/rg/fd/bat/fzf 等。

## 构建

```bash
docker build -t local/devkit:latest images/devkit/   # 从 stacks 仓库根
```

## 运行

```bash
docker run --rm -it --network traefik-net local/devkit:latest
```

- 默认进 `zsh -l`；命令追加在镜像名后可跑一次性任务
- 需要持久化自行挂卷（如 `-v devkit-workspaces:/workspaces`），否则退出即丢
- 升级工具链：改 Dockerfile 顶部 ARG（`GO_VERSION` / `NVM_VERSION`）后重新 build
