FROM nginx:1.27.3-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Non-root: nginx user already exists in nginx:alpine
# Adjust log dir permissions for non-root use
RUN chown -R nginx:nginx /var/log/nginx /var/cache/nginx /var/run \
    && chmod -R 755 /var/log/nginx

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

USER nginx
