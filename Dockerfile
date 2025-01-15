FROM odoo:16.0

COPY ./etc/odoo.conf /etc/odoo/odoo.conf
COPY ./addons /mnt/extra-addons

COPY ./entrypoint.sh /entrypoint.sh

ENV HOST odoo-db
ENV TOKEN 610f25e22dbccb07171886c016103a86
ENV PASSWORD odoo16@2022


EXPOSE 8069

CMD ["/entrypoint.sh"]