# Stacks

本地 Docker 服务编排，使用 Traefik 作为反向代理统一管理各服务的路由。

## 架构

```
traefik (反向代理, :80)
├── traefik.localhost  → Traefik Dashboard
├── portainer.localhost → Portainer
└── *.localhost / 自定义域名 → 其他服务
```

所有服务通过共享的 `traefik-net` 网络通信，由 Traefik 自动发现并暴露。

## 目录结构

```
├── traefik/              # Traefik 反向代理
│   ├── docker-compose.yml
│   └── traefik.yml       # 静态配置
├── portainer/            # Portainer 容器管理面板
│   └── docker-compose.yml
└── example.docker-compose.yml  # 新服务接入模板
```

## 快速开始

```bash
# 1. 启动 Traefik
docker compose -f traefik/docker-compose.yml up -d

# 2. 启动 Portainer
docker compose -f portainer/docker-compose.yml up -d
```

启动后访问：

- Traefik Dashboard: http://traefik.localhost/dashboard/
- Portainer: http://portainer.localhost

## 添加新服务

参考 `example.docker-compose.yml`，关键步骤：

1. 加入 `traefik-net` 外部网络
2. 添加 Traefik labels 配置路由规则
3. 设置 `traefik.enable=true`

```yaml
services:
  myapp:
    image: myapp:latest
    networks:
      - traefik-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.localhost`)"
      - "traefik.http.routers.myapp.entrypoints=web"

networks:
  traefik-net:
    external: true
    name: traefik-net
```

## 配置说明

### Traefik

- 入口点：`:80` (HTTP)
- Docker provider：通过 socket 自动发现容器，默认不暴露（需 `traefik.enable=true`）
- 指定网络：`traefik-net`
- `insecureSkipVerify: true`：允许代理后端自签名证书的服务（如 Portainer）

### Portainer

- 使用 Portainer CE (sts 版本)
- 通过 Traefik 代理访问其 HTTPS 9443 端口
