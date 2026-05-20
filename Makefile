# ============================================================
# Stacks 统一启停入口
#
# 用法：
#   make up              拉起本分支所有 SERVICES
#   make down            停止所有
#   make restart         先 down 再 up
#   make pull            拉取最新镜像
#   make ps   S=<dir>    查看某个服务状态，如 make ps S=infra/traefik
#   make logs S=<dir>    跟随某个服务日志
#   make help            显示此帮助
#
# SERVICES 列出本分支启用的所有 docker-compose 项目目录。
# 业务服务分支（service/*）会在自己的 Makefile 里追加自身。
# ============================================================

SERVICES := infra/traefik infra/portainer
COMPOSE  := docker compose

.PHONY: up down restart pull ps logs help

up:
	@for s in $(SERVICES); do \
		echo ">> up $$s"; \
		$(COMPOSE) -f $$s/docker-compose.yml up -d; \
	done

down:
	@for s in $(SERVICES); do \
		echo ">> down $$s"; \
		$(COMPOSE) -f $$s/docker-compose.yml down; \
	done

restart: down up

pull:
	@for s in $(SERVICES); do \
		echo ">> pull $$s"; \
		$(COMPOSE) -f $$s/docker-compose.yml pull; \
	done

ps:
	@if [ -z "$(S)" ]; then echo "用法: make ps S=infra/traefik"; exit 1; fi
	$(COMPOSE) -f $(S)/docker-compose.yml ps

logs:
	@if [ -z "$(S)" ]; then echo "用法: make logs S=infra/traefik"; exit 1; fi
	$(COMPOSE) -f $(S)/docker-compose.yml logs -f --tail=200

help:
	@echo "Stacks Makefile"
	@echo "  make up | down | restart | pull"
	@echo "  make ps   S=<dir>"
	@echo "  make logs S=<dir>"
	@echo ""
	@echo "当前 SERVICES = $(SERVICES)"
