import json
import os
import requests
import time
from web3 import Web3
from datetime import datetime

# --- CONFIGURATION ---
DB_PATH = 'data/db.json'
WALLET_ADDRESS = "0x52dffcd5a5e817d6f2529d77b48ab63c9b2a1e4e"
SNOWTRACE_API_KEY = os.environ.get('SNOWTRACE_API_KEY') # Optional, works without it often

# Game Rules
COST_POST = 0.02 # AVAX (approx)
COST_HEAL = 0.01 # AVAX (approx)
TOLERANCE = 0.001 # Allow slight price variance
MAX_ENTROPY = 24  # Hours until death

# --- UTILS ---

def load_db():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_db(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def decode_input_data(input_hex):
    """Decodes the transaction input data (Hex -> Text)."""
    if not input_hex or input_hex == '0x':
        return None
    try:
        # Web3.py or simple hex decode
        return Web3.to_text(hexstr=input_hex)
    except:
        return None

def fetch_transactions():
    """Fetches normal transactions for the wallet from Snowtrace."""
    print(f"Fetching transactions for {WALLET_ADDRESS}...")
    
    # Using the standard Etherscan-compatible endpoint for Avalanche
    url = "https://api.snowtrace.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": WALLET_ADDRESS,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc", # Newest first
        "page": 1,
        "offset": 20 # Only check last 20 txs to save time
    }
    
    if SNOWTRACE_API_KEY:
        params["apikey"] = SNOWTRACE_API_KEY

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        if data['status'] == '1':
            return data['result']
        else:
            print(f"API Error: {data.get('message')}")
            return []
    except Exception as e:
        print(f"Network Error: {e}")
        return []

# --- CORE LOGIC ---

def main():
    db = load_db()
    
    # 1. APPLY DECAY (The Rot)
    # We increase entropy for every item that is currently alive
    print("--- PHASE 1: ENTROPY ---")
    for item in db:
        if item['status'] == 'alive':
            item['entropy'] += 1
            print(f"Item {item['id']} entropy increased to {item['entropy']}")
            
            if item['entropy'] >= MAX_ENTROPY:
                item['status'] = 'dead'
                item['content'] = "[DATA_LOST_TO_ENTROPY]"
                print(f"Item {item['id']} has DIED.")

    # 2. PROCESS TRANSACTIONS (The Heal/Post)
    print("--- PHASE 2: TRANSACTIONS ---")
    txs = fetch_transactions()
    
    # We need to track processed TXs to avoid duplicates. 
    # In a real DB, we'd store tx_hash. For this JSON MVP, we check if ID exists.
    existing_ids = [item.get('id') for item in db]
    
    # Sort oldest to newest so we process in order
    txs.reverse() 

    for tx in txs:
        tx_hash = tx['hash']
        
        # Check value (convert Wei to AVAX)
        value_wei = int(tx['value'])
        value_avax = value_wei / 10**18
        
        # Check Input Data (Message)
        input_data = tx['input']
        decoded_msg = decode_input_data(input_data)
        
        # LOGIC: POST NEW CONTENT ($0.02)
        if abs(value_avax - COST_POST) < TOLERANCE:
            if tx_hash not in existing_ids:
                if decoded_msg:
                    print(f"NEW POST FOUND: {decoded_msg[:20]}...")
                    
                    # Determine type (Image URL or Text)
                    msg_type = "image" if decoded_msg.startswith("http") else "text"
                    
                    new_post = {
                        "id": tx_hash, # Use Hash as ID
                        "content": decoded_msg,
                        "type": msg_type,
                        "entropy": 0,
                        "last_healed_ts": int(time.time()),
                        "status": "alive"
                    }
                    db.append(new_post)
                    existing_ids.append(tx_hash)

        # LOGIC: HEAL CONTENT ($0.01)
        elif abs(value_avax - COST_HEAL) < TOLERANCE:
            # Healing requires the user to put the 'ID' (Tx Hash of original post) in the memo?
            # Or we just heal EVERYTHING? 
            # ARCHITECT CHOICE: For simplicity ($0.01 is cheap), let's say $0.01 heals the OLDEST rotting item.
            # OR: If the memo contains an ID, heal that ID.
            
            target_id = decoded_msg
            
            if target_id and target_id in existing_ids:
                # Heal specific
                for item in db:
                    if item['id'] == target_id and item['status'] == 'alive':
                        item['entropy'] = 0
                        item['last_healed_ts'] = int(time.time())
                        print(f"HEALED item {target_id}")
            else:
                # Heal random/oldest alive item with high entropy
                print("Global Heal initiated...")
                candidates = [i for i in db if i['status'] == 'alive' and i['entropy'] > 0]
                if candidates:
                    # Heal the one closest to death
                    victim = max(candidates, key=lambda x: x['entropy'])
                    victim['entropy'] = 0
                    print(f"Mercy Heal applied to {victim['id']}")

    save_db(db)
    print("--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    main()
