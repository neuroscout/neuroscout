FROM postgres:12
RUN apt-get update && apt-get install -y dos2unix
RUN apt-get install -yq python3-pip python-dev build-essential
RUN apt-get install -yq cron
RUN pip install awscli
COPY pg_dump-to-s3 /home
RUN chmod +x /home/pg_dump-to-s3.sh /home/s3-autodelete.sh
RUN crontab /home/backup.txt
RUN service cron start
RUN dos2unix /home/pg_dump-to-s3.sh
RUN dos2unix /home/s3-autodelete.sh
