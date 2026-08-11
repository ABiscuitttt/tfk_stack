# devkit

开发容器镜像定义。基于 `mcr.microsoft.com/devcontainers/base:noble`（已内置 common-utils 基础包 / zsh / Oh My Zsh / `vscode` 用户 uid=1000 + NOPASSWD sudo），增量：Go、Node（nvm LTS）、Rust、uv、clang/cmake/gdb、tmux/rg/fd/bat/fzf 等。apt、PyPI 与 Node.js 默认使用 USTC 镜像。

## 构建

```bash
docker build -t local/devkit:latest images/devkit/   # 从 stacks 仓库根
```

## 运行

```bash
docker run --rm -it --network traefik-net local/devkit:latest
```

或带上宿主终端变量，让容器内 CLI 能识别当前终端程序与主题：

```bash
docker run --rm -it \
  -e TERM_PROGRAM \
  -e TERM_PROGRAM_VERSION \
  -e COLORFGBG \
  --network traefik-net \
  -v devkit-workspaces:/workspaces \
  local/devkit:latest
```

- 默认进 `zsh -l`；命令追加在镜像名后可跑一次性任务
- `TERM=xterm-256color` / `COLORTERM=truecolor` 已在镜像内固定，无需再传，避免宿主编码能力与容器 terminfo 不匹配导致命令行显示错乱
- 需要持久化自行挂卷（如 `-v devkit-workspaces:/workspaces`），否则退出即丢
- 升级工具链：改 Dockerfile 顶部 ARG（`GO_VERSION` / `NVM_VERSION`）后重新 build
