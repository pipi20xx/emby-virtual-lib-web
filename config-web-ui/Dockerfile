# 使用一个轻量的Python官方镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码到工作目录
COPY . .

# 声明容器将监听的端口
EXPOSE 5000

# 容器启动时运行的命令
CMD ["python", "app.py"]