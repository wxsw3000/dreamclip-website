FROM python:3.12-slim

WORKDIR /app

# 设置时区与基础环境
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# 安装 supervisor 与基础工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装依赖
COPY mcp-base/requirements.txt /app/req_base.txt
COPY mcp-service-universe/requirements.txt /app/req_univ.txt
COPY mcp-portal/requirements.txt /app/req_portal.txt

RUN pip install --no-cache-dir -r /app/req_base.txt -r /app/req_univ.txt -r /app/req_portal.txt

# 复制全部工程代码
COPY . /app

# 复制 supervisor 守护进程配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露 80 端口 (对外门户主入口) 以及内部微服务端口
EXPOSE 80 8000 8081

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
