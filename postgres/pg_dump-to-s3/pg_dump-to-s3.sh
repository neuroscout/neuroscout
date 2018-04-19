#!/bin/bash
PATH=/usr/lib/postgresql/9.6/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

set -e

# Database credentials
PG_HOST="postgres"
PG_USER="postgres"


# S3
S3_PATH="neuroscout-backup"

# get databases list
dbs=("$@")

# Vars
NOW=$(date +"%m-%d-%Y-at-%H-%M-%S")
DIR=/home

for db in "${dbs[@]}"; do
    # Dump database
    pg_dump -Fc -h $PG_HOST -U $PG_USER $db > /tmp/"$NOW"_"$db".dump

    # Copy to S3
    aws s3 cp /tmp/"$NOW"_"$db".dump s3://$S3_PATH/"$NOW"_"$db".dump --storage-class STANDARD_IA

    # Delete local file
    rm /tmp/"$NOW"_"$db".dump

    # Log
    echo "* Database $db is archived"
done

# Delere old files
echo "* Delete old backups";
$DIR/s3-autodelete.sh $S3_PATH "7 days"
