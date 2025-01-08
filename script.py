import json
import os
import sys
from eth_account import Account

def generate_wallet():
    account = Account.create()
    return {
        "address": account.address,
        "private_key": '0x' + account._private_key.hex()
    }

def generate_wallets(count):
    return [generate_wallet() for _ in range(count)]

def save_wallets_to_json(wallets):
    with open("wallets.json", "w") as json_file:
        json.dump(wallets, json_file, indent=4)
    print("Generated wallets saved to wallets.json")

rpcs = {
    "1": {
        "rpc": "https://ethereum-rpc.publicnode.com",
        "fallbackRPCs": [
            "https://rpc.ankr.com/eth",
            "https://1rpc.io/eth",
            "https://eth.api.onfinality.io/public"
        ],
        "chainId": 1,
        "network": "mainnet",
        "chunkSize": 100
    },
    "10": {
        "rpc": "https://mainnet.optimism.io",
        "fallbackRPCs": [
            "https://optimism-mainnet.public.blastapi.io",
            "https://rpc.ankr.com/optimism",
            "https://optimism-rpc.publicnode.com"
        ],
        "chainId": 10,
        "network": "optimism",
        "chunkSize": 100
    },
    "137": {
        "rpc": "https://polygon-rpc.com/",
        "fallbackRPCs": [
            "https://polygon-mainnet.public.blastapi.io",
            "https://1rpc.io/matic",
            "https://rpc.ankr.com/polygon"
        ],
        "chainId": 137,
        "network": "polygon",
        "chunkSize": 100
    },
    "23294": {
        "rpc": "https://sapphire.oasis.io",
        "fallbackRPCs": [
            "https://1rpc.io/oasis/sapphire"
        ],
        "chainId": 23294,
        "network": "sapphire",
        "chunkSize": 100
    },
    "23295": {
        "rpc": "https://testnet.sapphire.oasis.io",
        "chainId": 23295,
        "network": "sapphire-testnet",
        "chunkSize": 100
    },
    "11155111": {
        "rpc": "https://eth-sepolia.public.blastapi.io",
        "fallbackRPCs": [
            "https://1rpc.io/sepolia",
            "https://eth-sepolia.g.alchemy.com/v2/demo"
        ],
        "chainId": 11155111,
        "network": "sepolia",
        "chunkSize": 100
    },
    "11155420": {
        "rpc": "https://sepolia.optimism.io",
        "fallbackRPCs": [
            "https://endpoints.omniatech.io/v1/op/sepolia/public",
            "https://optimism-sepolia.blockpi.network/v1/rpc/public"
        ],
        "chainId": 11155420,
        "network": "optimism-sepolia",
        "chunkSize": 100
    }
}

rpcs_json = json.dumps(rpcs)

def create_ocean_node_compose(wallet, i, ip_address):
    http_api_port = 12002 + i
    p2p_tcp_port = 13002 + i
    p2p_ws_port = 14002 + i
    docker_compose_template = f"""
services:
  ocean-node{i}:
    image: oceanprotocol/ocean-node:latest
    pull_policy: always
    container_name: ocean-node-{i}
    restart: on-failure
    ports:
      - "{12002 + i}:{12002 + i}"
      - "{13002 + i}:{13002 + i}"
      - "{14002 + i}:{14002 + i}"
      - "{15002 + i}:{15002 + i}"
      - "{16002 + i}:{16002 + i}"
    environment:
      PRIVATE_KEY: '{wallet['private_key']}'
      RPCS: '{rpcs_json}'
      DB_URL: 'http://typesense:8108/?apiKey=xyz'
      IPFS_GATEWAY: 'https://ipfs.io/'
      ARWEAVE_GATEWAY: 'https://arweave.net/'
      INTERFACES: '["HTTP","P2P"]'
      ALLOWED_ADMINS: '["{wallet['address']}"]'
      HTTP_API_PORT: '{http_api_port}'
      DASHBOARD: 'false'
      P2P_ENABLE_IPV4: 'true'
      P2P_ipV4BindAddress: '0.0.0.0'
      P2P_ipV4BindTcpPort: '{p2p_tcp_port}'
      P2P_ipV4BindWsPort: '{p2p_ws_port}'
      P2P_ANNOUNCE_ADDRESSES: '["/ip4/{ip_address}/tcp/{p2p_tcp_port}", "/ip4/{ip_address}/ws/tcp/{p2p_ws_port}"]'
      P2P_ANNOUNCE_PRIVATE: 'True'
      P2P_pubsubPeerDiscoveryInterval: '10000'
      P2P_dhtMaxInboundStreams: '500'
      P2P_dhtMaxOutboundStreams: '500'
      P2P_ENABLE_DHT_SERVER: 'false'
      P2P_mDNSInterval: '20000'
      P2P_connectionsMaxParallelDials: '150'
      P2P_connectionsDialTimeout: '10000'
      P2P_ENABLE_UPNP: 'True'
      P2P_ENABLE_AUTONAT: 'True'
      P2P_ENABLE_CIRCUIT_RELAY_SERVER: 'True'
      P2P_ENABLE_CIRCUIT_RELAY_CLIENT: '0'
      P2P_MIN_CONNECTIONS: '1'
      P2P_MAX_CONNECTIONS: '300'
      P2P_AUTODIALPEERRETRYTHRESHOLD: '1000 * 120'
      P2P_AUTODIALCONCURRENCY: '5'
      P2P_MAXPEERADDRSTODIAL: '5'
      P2P_AUTODIALINTERVAL: '5000'
      P2P_ENABLE_NETWORK_STATS: 'getP2pNetworkStats'
    networks:
      - ocean_network
    depends_on:
      - typesense
  typesense:
    image: typesense/typesense:26.0
    container_name: typesense
    ports:
      - "8108:8108"
    networks:
      - ocean_network
    volumes:
      - typesense-data:/data
    command: '--data-dir /data --api-key=xyz'

volumes:
  typesense-data:
    driver: local

networks:
  ocean_network:
    driver: bridge
"""
    save_docker_compose_file(docker_compose_template, i + 1)
    print(f"Generated docker-compose{i + 1}.yaml for ocean-node-{i}")

def save_docker_compose_file(content, i):
    filename = f'docker-compose{i}.yaml'
    with open(filename, 'w') as file:
        file.write(content)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <IP_ADDRESS> <NUM_NODES>")
        sys.exit(1)

    ip_address = sys.argv[1]
    num_files = int(sys.argv[2])

    wallets = generate_wallets(num_files)
    save_wallets_to_json(wallets)

    for i, wallet in enumerate(wallets, start=1):
        create_ocean_node_compose(wallet, i, ip_address)

if __name__ == "__main__":
    main()
