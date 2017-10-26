FROM postgres:latest
RUN apt-get update
RUN apt-get install -yq python-pip python-dev build-essential
RUN pip install awscli
COPY pg_dump-to-s3 /home
RUN chmod +x /home/pg_dump-to-s3.sh /home/s3-autodelete.sh
RUN crontab /home/backup.txt
RUN service cron start
