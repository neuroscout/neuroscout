docker-compose exec postgres psql -h postgres -U postgres -c "drop database neuroscout"
docker-compose exec postgres psql -h postgres -U postgres -c "create database neuroscout"
docker-compose exec web bash scripts/init_reset.sh
