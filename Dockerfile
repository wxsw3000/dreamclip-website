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
COPY magicstar-platform/requirements.txt /app/req_platform.txt
COPY dreamclip-service/requirements.txt /app/req_dreamclip.txt

RUN pip install --no-cache-dir -r /app/req_platform.txt -r /app/req_dreamclip.txt

# 复制全部工程代码
COPY . /app

# 复制 supervisor 守护进程配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露主网关总入口端口 (80) 以及内部微服务端口 (8000, 8081)
EXPOSE 80 8000 8081

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
