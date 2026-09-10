FROM nginx:alpine

# 复制自定义 Nginx 配置（支持多域名响应）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 将项目静态文件复制到 Nginx 默认静态文件目录
COPY . /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
