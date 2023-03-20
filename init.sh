#/usr/bin/env bash

for dir in 'caddy-data' 'caddy-config' 'postgres'; do
    mkdir -p data/"$dir"
done

# export SUBPATH='/example-subpath' # must start with '/'

# export POSTGRES_PASSWORD='foobarbaz' # replace with a strong password

# docker compose up -d

terraform apply
