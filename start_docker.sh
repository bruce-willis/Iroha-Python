#!/bin/bash
set -ev

p_host="postgres-iroha"
p_user="postgres"
p_pass="mysecretpassword"

docker network create iroha-network

docker volume create blockstore

docker run --name $p_host \
-e POSTGRES_USER=$p_user \
-e POSTGRES_PASSWORD=$p_pass \
-p 5432:5432 \
--network=iroha-network \
-d postgres:9.5


docker run -it --name iroha \
-p 50051:50051 \
-v $(pwd)/ledger_config:/opt/iroha_data \
-v blockstore:/tmp/block_store \
--network=iroha-network \
--entrypoint=/bin/bash \
hyperledger/iroha:latest
