#/usr/bin/env bash

for dir in 'caddy-data' 'caddy-config'; do
    mkdir -p data/"$dir"
done

export SUBPATH=

docker compose up -d

echo "Vaultwarden instance started!"
