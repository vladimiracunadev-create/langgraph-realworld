FROM nginx:1.27.3-alpine@sha256:29669528d228c290a1804938a9d16f881079d865520a06df52e728e93297a77e

# Install permissions for non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

COPY . /usr/share/nginx/html

WORKDIR /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080 || exit 1
