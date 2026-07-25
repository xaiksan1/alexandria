FROM nginx:1.31.3-alpine

COPY guacamole-proxy.conf /etc/nginx/conf.d/default.conf
COPY certs/guacamole.crt /etc/ssl/certs/guacamole.crt
COPY certs/guacamole.key /etc/ssl/private/guacamole.key

RUN chmod 644 /etc/ssl/certs/guacamole.crt && chmod 600 /etc/ssl/private/guacamole.key

EXPOSE 80 443
