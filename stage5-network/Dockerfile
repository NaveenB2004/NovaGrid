FROM ubuntu:22.04

RUN apt-get update && apt-get install -y vsftpd && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /srv/ftp && chown -R ftp:ftp /srv/ftp

COPY vsftpd.conf /etc/vsftpd.conf
COPY ftp_share/ /srv/ftp/

EXPOSE 21 21100-21110

CMD ["/usr/sbin/vsftpd", "/etc/vsftpd.conf"]
