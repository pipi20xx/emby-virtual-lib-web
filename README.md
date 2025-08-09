
# Emby 虚拟媒体库 (`emby-virtual-lib`) Web 配置工具

本工具是为 [emby-virtual-lib](https://github.com/EkkoG/emby-virtual-lib) 项目开发的专属图形化配置界面。

如果您正在使用 `emby-virtual-lib`，那么这个 Web UI 将帮助您在一个简单直观的网页上完成所有 `config.yaml` 的参数配置，彻底告别手动编辑 YAML 文件的繁琐与易错。


---

## ✨ 主要功能

- **图形化配置**：在一个清爽的网页中完成所有 `config.yaml` 的参数配置。
- **一键部署**：通过 `docker-compose` 命令，一键启动Web UI和 `emby-virtual-lib` 主程序。
- **动态加载**：在Web UI中修改并保存配置后，可自动重启 `emby-virtual-lib` 容器，使新配置即时生效。
- **Emby数据联动**：输入Emby Server和API Key后，可从Emby服务器直接拉取并选择`合集`、`类型`、`标签`等资源，无需手动查找ID。
- **傻瓜式操作**：无需学习YAML语法，无需SSH连接服务器，点点鼠标即可完成所有配置。

---

## 🚀 快速开始：一键部署

本项目推荐使用 Docker Compose 进行部署，方便快捷。

**前提条件**:
1.  您的系统中已经安装了 [Docker](https://www.docker.com/)。
2.  您的系统中已经安装了 [Docker Compose](https://docs.docker.com/compose/install/)。

**部署步骤**:


## 🐳 一键部署文件 (`docker-compose-pro.yml`)

这是用于一键部署的核心文件，它同时管理 `config-web-ui` 和 `emby-virtual-lib` 两个服务。

```yaml
# 这个 Compose 文件用于运行一个已经手动构建好的本地镜像。

services:
  # 服务名称可以任意取，这里我们还叫它 config-web-ui
  config-web-ui:
    # 关键：直接指定您手动构建的本地镜像的名称和标签
    image: config-web-ui:latest
    
    # 为容器命名，方便管理
    container_name: config-web-ui
    
    # 端口映射：将服务器的 8003 端口映射到容器的 5000 端口
    ports:
      - "8003:5000"
      
    # 卷挂载：
    volumes:
      # 挂载配置目录，用于读写 config.yaml
      - ./config:/config
      # (可选) 如果您使用了图片功能，请保留此行
      - ./images:/app/images
      # (可选) 如果需要“自动重启emby-virtual-lib”功能，请保留此行
      - /var/run/docker.sock:/var/run/docker.sock
      
    # 重启策略
    restart: unless-stopped

  # emby-virtual-lib 服务
  emby-virtual-lib:
    # 镜像地址
    image: ekkog/emby-virtual-lib:latest
    
    # 容器名称
    container_name: emby-virtual-lib
    
    # 卷挂载
    volumes:
      # 挂载配置文件
      - ./config/config.yaml:/app/config/config.yaml
      # 挂载日志文件
      - ./logs:/app/logs
      
    # 重启策略
    restart: unless-stopped
    
    # 依赖关系：确保在 emby-virtual-lib 启动前，config-web-ui 已经启动
    # 注意：这只保证启动顺序，不保证服务内部完全就绪
    depends_on:
      - config-web-ui
      
    # (可选) 如果您的 Emby 服务器也在同一个 Docker 网络中，
    # 可以使用 network_mode: host 或者自定义网络来简化网络连接。
    # network_mode: host
    
    # (可选) 如果需要，可以设置环境变量
    # environment:
    #   - PUID=1000
    #   - PGID=1000
    #   - TZ=Asia/Shanghai
```

```

---

## 🤝 贡献

欢迎对本项目进行贡献！如果您有任何建议或发现任何问题，请随时提交 [Issues](https://github.com/EkkoG/emby-virtual-lib-web/issues) 或 [Pull Requests](https://github.com/EkkoG/emby-virtual-lib-web/pulls)。
