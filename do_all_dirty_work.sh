#!/bin/bash
set -ev

docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

docker network rm iroha-network
docker network create iroha-network

docker run --name some-postgres \
-e POSTGRES_USER=postgres \
-e POSTGRES_PASSWORD=mysecretpassword \
-p 5432:5432 \
--network=iroha-network \
-d postgres:9.5

docker volume rm blockstore
docker volume create blockstore

docker run -it --name iroha \
-p 50051:50051 \
-v $(pwd)/ledger_config:/opt/iroha_data  \
-v blockstore:/tmp/block_store \
--network=iroha-network \
--entrypoint=/bin/bash \
hyperledger/iroha:latest

# inside docker:
# irohad --config config.docker --genesis_block genesis.block --keypair_name node0 --overwrite_ledger
