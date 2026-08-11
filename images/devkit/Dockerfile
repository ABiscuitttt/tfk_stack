# syntax=docker/dockerfile:1.7
# 通用 daily driver 开发容器，直接基于 devcontainers 官方 base 镜像。
# mcr.microsoft.com/devcontainers/base:noble 已内置（无需手工再做）：
#   - buildpack-deps:noble-curl 底层（预置常见 native 依赖）
#   - 官方 common-utils 基础包清单 + zsh + Oh My Zsh
#   - 非 root 用户 vscode（uid=1000，NOPASSWD sudo；自带 ubuntu 用户官方已删）
#   - LANG=C.UTF-8 / tzdata
# 本文件只做增量：扩展 apt 包、Go/Node/Rust/uv 工具链。
FROM mcr.microsoft.com/devcontainers/base:noble

ARG GO_VERSION=1.23.4
ARG NVM_VERSION=v0.40.1

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

USER root

# ---------- 增量系统包（只装 common-utils 清单之外的扩展） ----------
RUN apt-get update && apt-get -y install --no-install-recommends \
        bubblewrap socat \
        tmux neovim ripgrep fd-find bat fzf \
        clang lld lldb clang-format clang-tidy cmake gdb \
        git-lfs direnv dnsutils \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# fd 和 bat 在 Debian/Ubuntu 里叫 fdfind/batcat，建标准名 symlink
RUN ln -s /usr/bin/fdfind /usr/local/bin/fd \
 && ln -s /usr/bin/batcat /usr/local/bin/bat

# ---------- Go（官方 tarball，比 apt 版新且干净） ----------
RUN ARCH=$(dpkg --print-architecture) \
 && case "$ARCH" in amd64) GOARCH=amd64 ;; arm64) GOARCH=arm64 ;; *) echo "unsupported arch $ARCH" && exit 1 ;; esac \
 && curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" | tar -C /usr/local -xz
ENV PATH=/usr/local/go/bin:${PATH}

# ---------- 目录预建（挂卷时权限对；zshrc 的 HISTFILE 指向 /commandhistory） ----------
RUN mkdir -p /workspaces /commandhistory \
 && chown vscode:vscode /workspaces /commandhistory

USER vscode
WORKDIR /home/vscode

# ---------- Oh My Zsh base 已装好，只补三个插件 + 静态 zshrc ----------
RUN git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions   ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions \
 && git clone --depth=1 https://github.com/zsh-users/zsh-completions       ~/.oh-my-zsh/custom/plugins/zsh-completions \
 && git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
COPY --chown=vscode:vscode zshrc /home/vscode/.zshrc

# ---------- uv（官方 installer 装到 ~/.local） ----------
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# ---------- nvm + Node LTS + Claude CLI ----------
ENV NVM_DIR=/home/vscode/.nvm
RUN mkdir -p $NVM_DIR \
 && curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash \
 && bash -lc '. "$NVM_DIR/nvm.sh" && nvm install --lts && nvm alias default lts/* && npm i -g @anthropic-ai/claude-code'

# ---------- Rust ----------
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain stable --profile default --no-modify-path
ENV PATH=/home/vscode/.cargo/bin:${PATH}

WORKDIR /workspaces
CMD ["zsh", "-l"]
