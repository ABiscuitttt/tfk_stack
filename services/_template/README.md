# 新服务接入模板

## 步骤

1. **新建分支**

   ```bash
   git checkout -b service/<name> main
   ```

2. **复制模板**

   ```bash
   mkdir -p services/<name>
   cp services/_template/docker-compose.yml services/<name>/docker-compose.yml
   ```

3. **改 compose**：将所有 `myapp` 替换为服务名，修改 image 与 Host 规则

4. **放开 .gitignore**：在 `.gitignore` 末尾追加一行

   ```
   !/services/<name>/
   ```

5. **加入 Makefile**：编辑根目录 `Makefile`，把 `services/<name>` 加到 `SERVICES` 变量

6. **如有可调环境变量**：新建 `services/<name>/.env.example`，列出可用的 `*_TAG` 等

7. **如有运行时数据目录**（数据库文件、上传等）：在根 `.gitignore` 添加对应规则

8. **启动并验证**

   ```bash
   make up
   curl -H "Host: <name>.localhost" http://localhost
   ```

9. **提交**

   ```bash
   git add .
   git commit -m "feat(<name>): integrate into services/"
   ```

## 镜像版本约定

统一使用 `image: <name>:${<NAME>_TAG:-latest}`，便于通过 `.env` 锁定版本。
