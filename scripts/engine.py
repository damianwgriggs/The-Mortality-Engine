import json
import os
import requests
import time
from web3 import Web3
from datetime import datetime

# --- CONFIGURATION ---
DB_PATH = 'data/db.json'
# Your Treasury Address
WALLET_ADDRESS = "0x43CAF8c948235Ed5e08608D5A7642910E3f82Fb9" 
SNOWTRACE_API_KEY = os.environ.get('SNOWTRACE_API_KEY') 

# Game Rules
COST_POST = 0.02 # AVAX 
COST_HEAL = 0.01 # AVAX 
TOLERANCE = 0.001 
MAX_ENTROPY = 24  

# --- UTILS ---

def load_db():
    try:
        if not os.path.exists(DB_PATH):
            return []
        with open(DB_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        print("Error: DB Corrupted. Resetting.")
        return []

def save_db(data):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def decode_input_data(input_hex):
    if not input_hex or input_hex == '0x':
        return None
    try:
        return Web3.to_text(hexstr=input_hex)
    except:
        return None

def fetch_transactions():
    """Fetches transactions using Routescan (Reliable Fuji API)."""
    print(f"Fetching transactions for {WALLET_ADDRESS} on Fuji...")
    
    # --- THE FIX: Using Routescan's Etherscan-Compatible Endpoint for Fuji ---
    # Chain ID 43113 = Fuji
    url = "https://api.routescan.io/v2/network/testnet/evm/43113/etherscan/api"
    
    params = {
        "module": "account",
        "action": "txlist",
        "address": WALLET_ADDRESS,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc", # Newest first
        "page": 1,
        "offset": 20 
    }
    
    if SNOWTRACE_API_KEY:
        params["apikey"] = SNOWTRACE_API_KEY

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(url, params=params, headers=headers)
        
        # Debugging: Print the raw status code to the logs
        print(f"API Status Code: {r.status_code}")
        
        data = r.json()
        
        # Routescan/Etherscan uses status "1" for success
        if data['status'] == '1':
            print(f"Found {len(data['result'])} transactions.")
            return data['result']
        else:
            print(f"API Message: {data.get('message', 'No result')}")
            # If message is "No transactions found", that's fine.
            return []
            
    except Exception as e:
        print(f"Network Error: {e}")
        return []

# --- CORE LOGIC ---

def main():
    db = load_db()
    
    # 1. APPLY DECAY
    print("--- PHASE 1: ENTROPY ---")
    for item in db:
        if item['status'] == 'alive':
            item['entropy'] += 1
            print(f"Item {item['id']} entropy increased to {item['entropy']}")
            
            if item['entropy'] >= MAX_ENTROPY:
                item['status'] = 'dead'
                item['content'] = "[DATA_LOST_TO_ENTROPY]"
                print(f"Item {item['id']} has DIED.")

    # 2. PROCESS TRANSACTIONS
    print("--- PHASE 2: TRANSACTIONS ---")
    txs = fetch_transactions()
    
    existing_ids = [item.get('id') for item in db]
    # We process oldest to newest to maintain timeline order
    txs.reverse() 

    for tx in txs:
        tx_hash = tx['hash']
        
        # Skip if already processed
        if tx_hash in existing_ids:
            continue

        value_wei = int(tx['value'])
        value_avax = value_wei / 10**18
        input_data = tx['input']
        decoded_msg = decode_input_data(input_data)
        
        # LOGIC: POST ($0.02)
        if abs(value_avax - COST_POST) < TOLERANCE:
            if decoded_msg:
                print(f"NEW POST FOUND: {decoded_msg[:20]}...")
                msg_type = "image" if decoded_msg.startswith("http") else "text"
                new_post = {
                    "id": tx_hash, 
                    "content": decoded_msg,
                    "type": msg_type,
                    "entropy": 0,
                    "last_healed_ts": int(time.time()),
                    "status": "alive"
                }
                db.append(new_post)
                existing_ids.append(tx_hash)

        # LOGIC: HEAL ($0.01)
        elif abs(value_avax - COST_HEAL) < TOLERANCE:
            target_id = decoded_msg
            if target_id and target_id in existing_ids:
                for item in db:
                    if item['id'] == target_id and item['status'] == 'alive':
                        item['entropy'] = 0
                        print(f"HEALED item {target_id}")
            else:
                # Mercy Heal (Heal oldest alive item)
                candidates = [i for i in db if i['status'] == 'alive' and i['entropy'] > 0]
                if candidates:
                    victim = max(candidates, key=lambda x: x['entropy'])
                    victim['entropy'] = 0
                    print(f"Mercy Heal applied to {victim['id']}")

    save_db(db)
    print("--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    main()
