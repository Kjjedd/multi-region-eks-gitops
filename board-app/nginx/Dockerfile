FROM nginx:1.27-alpine

RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

# nginx:alpine ships an unprivileged variant; we replicate the bits we need.
RUN sed -i 's@/var/run/nginx.pid@/tmp/nginx.pid@' /etc/nginx/nginx.conf || true \
 && mkdir -p /var/cache/nginx /var/run \
 && chown -R nginx:nginx /var/cache/nginx /etc/nginx /var/run

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O- http://127.0.0.1:8080/healthz >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
