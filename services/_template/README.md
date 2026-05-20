# 新服务接入模板

业务服务不入库，本机直接放就行。

## 步骤

1. **复制模板**

   ```bash
   cp -r services/_template services/<name>
   ```

2. **改 compose**：把所有 `myapp` 替换为服务名，修改 `image` 和 `Host(...)` 规则

3. **如需固定镜像版本**：编辑 `services/<name>/.env`，写入对应的 `<NAME>_TAG`

4. **启动**

   ```bash
   make up                       # 自动发现新服务并启动
   curl -H "Host: <name>.localhost" http://localhost
   ```

## 默认行为

- `make up/down/restart/pull` 自动作用于 `infra/*` 与 `services/*`（除 `_template`）
- `services/<name>/` 整体被 `.gitignore` 屏蔽，不会污染 git
- `**/.env`、运行时数据、密钥等：因为 `services/<name>/` 整体屏蔽，里面所有内容都不会入库

## 镜像版本约定

`image: <name>:${<NAME>_TAG:-latest}`。锁定版本：在 `services/<name>/.env` 写 `<NAME>_TAG=具体版本`。该 .env 不入库，仅本机生效。
