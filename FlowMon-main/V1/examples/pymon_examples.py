#!/usr/bin/env python3
"""
PyMon Examples - Smart Contract Interactions on Monad Testnet

This file demonstrates how to use PyMon to interact with deployed contracts
on the Monad blockchain testnet.
"""

import json
import os
from pathlib import Path
from web3 import Web3
from eth_account import Account

class PyMonContractInteractor:
    """Helper class for interacting with contracts deployed via PyMon."""
    
    def __init__(self, contract_name: str):
        """
        Initialize contract interactor.
        
        Args:
            contract_name: Name of the deployed contract
        """
        self.contract_name = contract_name
        
        # Load PyMon configuration
        with open("pymon_config.json") as f:
            self.config = json.load(f)
        
        # Load deployment info
        deployments_file = Path("deployments.json")
        if deployments_file.exists():
            with open(deployments_file) as f:
                deployments = json.load(f)
                if "monad-testnet" in deployments and contract_name in deployments["monad-testnet"]:
                    self.contract_info = deployments["monad-testnet"][contract_name]
                    self.contract_address = self.contract_info["address"]
                else:
                    raise ValueError(f"Contract {contract_name} not found in deployments")
        else:
            raise FileNotFoundError("No deployments.json found. Deploy a contract first with: pymon deploy")
        
        # Load contract ABI
        abi_path = Path(f"build/{contract_name}/{contract_name}.json")
        if abi_path.exists():
            with open(abi_path) as f:
                contract_data = json.load(f)
                self.abi = contract_data["abi"]
        else:
            raise FileNotFoundError(f"ABI not found. Compile first with: pymon compile")
        
        # Connect to Monad testnet
        self.w3 = Web3(Web3.HTTPProvider(self.config["rpc_url"]))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Monad testnet at {self.config['rpc_url']}")
        
        # Setup account
        private_key = os.getenv('PRIVATE_KEY')
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            # Try to load from keystore
            keystore_path = Path("pymon_key.json")
            if keystore_path.exists():
                password = input("Enter keystore password: ")
                with open(keystore_path) as f:
                    keystore = json.load(f)
                    self.account = Account.from_key(Account.decrypt(keystore, password))
            else:
                raise ValueError("No private key found. Set PRIVATE_KEY env var or create wallet with: pymon wallet new")
        
        # Create contract instance
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        
        print(f"🚀 PyMon connected to {contract_name} at: {self.contract_address}")
        print(f"🌐 Network: Monad Testnet (Chain ID: {self.config['chain_id']})")
        print(f"💰 Account: {self.account.address}")
        print(f"💎 Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether'):.4f} MON")
        print()

    def call_view_function(self, function_name: str, *args):
        """
        Call a view function (no transaction required).
        
        Args:
            function_name: Name of the function to call
            *args: Function arguments
        
        Returns:
            Function result
        """
        func = self.contract.functions[function_name](*args)
        result = func.call()
        print(f"📖 {function_name}({', '.join(map(str, args))}) = {result}")
        return result

    def send_transaction(self, function_name: str, *args, value=0):
        """
        Send a transaction to modify contract state.
        
        Args:
            function_name: Name of the function to call
            *args: Function arguments
            value: Amount of MON to send (in wei)
        
        Returns:
            Transaction receipt
        """
        func = self.contract.functions[function_name](*args)
        
        # Build transaction
        tx = func.build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 0,  # Will estimate
            'gasPrice': self.w3.eth.gas_price,
            'value': value,
            'chainId': self.config['chain_id']
        })
        
        # Estimate gas
        gas_estimate = self.w3.eth.estimate_gas(tx)
        tx['gas'] = int(gas_estimate * 1.2)  # 20% buffer
        
        print(f"📝 Sending transaction: {function_name}({', '.join(map(str, args))})")
        print(f"⛽ Gas estimate: {gas_estimate:,}")
        
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"🔄 Transaction sent: {tx_hash.hex()}")
        print(f"⏳ Waiting for confirmation...")
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Transaction confirmed in block {receipt.blockNumber}")
            print(f"🔍 View on explorer: {self.config['explorer_url']}/tx/{tx_hash.hex()}")
        else:
            print(f"❌ Transaction failed!")
        
        return receipt

    def get_events(self, event_name: str, from_block=0, to_block='latest'):
        """
        Get contract events.
        
        Args:
            event_name: Name of the event
            from_block: Starting block
            to_block: Ending block
        
        Returns:
            List of events
        """
        event = self.contract.events[event_name]
        events = event.create_filter(fromBlock=from_block, toBlock=to_block).get_all_entries()
        
        print(f"📊 Found {len(events)} {event_name} events")
        for e in events:
            print(f"  Block {e.blockNumber}: {dict(e.args)}")
        
        return events


# Example usage functions
def example_simple_storage():
    """Example: Interact with SimpleStorage contract."""
    print("=" * 60)
    print("SimpleStorage Contract Example")
    print("=" * 60)
    
    # Initialize interactor
    storage = PyMonContractInteractor("SimpleStorage")
    
    # Read current value
    current_value = storage.call_view_function("get")
    
    # Set new value
    new_value = 42
    print(f"\n🔧 Setting value to {new_value}...")
    receipt = storage.send_transaction("set", new_value)
    
    # Read updated value
    updated_value = storage.call_view_function("get")
    print(f"\n✨ Value updated from {current_value} to {updated_value}")


def example_token():
    """Example: Interact with Token contract."""
    print("=" * 60)
    print("Token Contract Example")
    print("=" * 60)
    
    # Initialize interactor
    token = PyMonContractInteractor("Token")
    
    # Check balance
    my_balance = token.call_view_function("balanceOf", token.account.address)
    print(f"💰 My balance: {my_balance}")
    
    # Transfer tokens
    recipient = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8"  # Example address
    amount = 100
    
    print(f"\n📤 Transferring {amount} tokens to {recipient[:10]}...")
    receipt = token.send_transaction("transfer", recipient, amount)
    
    # Check new balance
    new_balance = token.call_view_function("balanceOf", token.account.address)
    print(f"💰 New balance: {new_balance}")
    
    # Get transfer events
    token.get_events("Transfer")


def example_batch_operations():
    """Example: Perform batch operations efficiently on Monad."""
    print("=" * 60)
    print("Batch Operations Example (Optimized for Monad)")
    print("=" * 60)
    
    # This demonstrates how to leverage Monad's high throughput
    # by batching multiple operations in quick succession
    
    storage = PyMonContractInteractor("SimpleStorage")
    
    print("🚀 Sending 5 transactions rapidly (Monad handles 10,000 TPS!)...")
    
    receipts = []
    for i in range(5):
        print(f"\n📝 Transaction {i+1}/5: Setting value to {i*10}")
        receipt = storage.send_transaction("set", i * 10)
        receipts.append(receipt)
    
    print("\n✅ All transactions confirmed!")
    print(f"📊 Gas used total: {sum(r.gasUsed for r in receipts):,}")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║                    PyMon Examples                         ║
║         Smart Contract Interactions on Monad              ║
╚═══════════════════════════════════════════════════════════╝

Select an example to run:
1. SimpleStorage interaction
2. Token contract interaction  
3. Batch operations (Monad optimized)
""")
    
    choice = input("Enter choice (1-3): ")
    
    try:
        if choice == "1":
            example_simple_storage()
        elif choice == "2":
            example_token()
        elif choice == "3":
            example_batch_operations()
        else:
            print("Invalid choice!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Deployed a contract with: pymon deploy <contract>")
        print("2. Set PRIVATE_KEY env var or created wallet with: pymon wallet new")
        print("3. Funded your wallet with MON from: https://discord.gg/monaddev")
