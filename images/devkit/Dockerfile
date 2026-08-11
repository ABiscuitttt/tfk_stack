# syntax=docker/dockerfile:1.7
# 通用开发容器。基于 devcontainers/base:noble，增量安装工具链。
FROM mcr.microsoft.com/devcontainers/base:noble

ARG GO_VERSION=1.23.4
ARG NVM_VERSION=v0.40.1

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    COLORTERM=truecolor \
    UV_DEFAULT_INDEX=https://mirrors.ustc.edu.cn/pypi/simple \
    NVM_NODEJS_ORG_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/ \
    RUSTUP_DIST_SERVER=https://mirrors.tuna.tsinghua.edu.cn/rustup

USER root

# apt: USTC 镜像
RUN cat > /etc/apt/sources.list.d/ubuntu.sources <<'EOF'
Types: deb
URIs: https://mirrors.ustc.edu.cn/ubuntu
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb
URIs: https://mirrors.ustc.edu.cn/ubuntu
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

# PyPI: USTC 镜像
RUN cat > /etc/pip.conf <<'EOF'
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
EOF

# 扩展系统包
RUN apt-get update && apt-get -y install --no-install-recommends \
        bubblewrap socat \
        tmux ripgrep fd-find bat fzf \
        clang lld lldb clang-format clang-tidy cmake gdb \
        git-lfs direnv dnsutils \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# fd/bat 命令名在 Ubuntu 中不同，建软链
RUN ln -s /usr/bin/fdfind /usr/local/bin/fd \
 && ln -s /usr/bin/batcat /usr/local/bin/bat

# Go
RUN ARCH=$(dpkg --print-architecture) \
 && case "$ARCH" in amd64) GOARCH=amd64 ;; arm64) GOARCH=arm64 ;; *) echo "unsupported arch $ARCH" && exit 1 ;; esac \
 && curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" | tar -C /usr/local -xz
ENV PATH=/usr/local/go/bin:${PATH}

# 预建目录并修正权限
RUN mkdir -p /workspaces /commandhistory \
 && chown vscode:vscode /workspaces /commandhistory

USER vscode
WORKDIR /home/vscode

# Oh My Zsh 插件 + zshrc
RUN git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions   ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions \
 && git clone --depth=1 https://github.com/zsh-users/zsh-completions       ~/.oh-my-zsh/custom/plugins/zsh-completions \
 && git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
COPY --chown=vscode:vscode zshrc /home/vscode/.zshrc

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# nvm + Node LTS
ENV NVM_DIR=/home/vscode/.nvm
RUN mkdir -p $NVM_DIR \
 && curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash \
 && bash -lc '. "$NVM_DIR/nvm.sh" && nvm install --lts && nvm alias default lts/*'

# Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain stable --profile default --no-modify-path
ENV PATH=/home/vscode/.cargo/bin:${PATH}

WORKDIR /workspaces
CMD ["zsh", "-l"]
