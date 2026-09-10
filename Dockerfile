FROM nginx:alpine

# 将项目静态文件复制到 Nginx 默认静态文件目录
COPY . /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
