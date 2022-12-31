#/usr/bin/env bash

for dir in 'caddy-data' 'caddy-config'; do
    mkdir -p data/"$dir"
done

export SUBPATH='/example-subpath' # must start with '/'

docker compose up -d
