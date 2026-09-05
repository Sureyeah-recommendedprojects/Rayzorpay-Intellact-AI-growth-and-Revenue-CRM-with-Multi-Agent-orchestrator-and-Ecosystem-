#!/usr/bin/env python3
"""
PyMon examples for interacting with deployed contracts on Monad testnet.
Demonstrates staking, transfers, and rewards functionality.
"""

import json
import os
import time
from pathlib import Path
from web3 import Web3
from eth_account import Account

class StakeTokenInteractor:
    """Helper class for interacting with StakeToken contract."""
    
    def __init__(self):
        # Load deployment info
        with open("../deployments.json") as f:
            deployments = json.load(f)
        
        self.contract_info = deployments["monad-testnet"]["StakeToken"]
        self.contract_address = self.contract_info["address"]
        
        # Load contract ABI
        with open("../build/StakeToken/StakeToken.json") as f:
            contract_data = json.load(f)
        
        self.abi = contract_data["abi"]
        
        # Connect to Monad testnet
        self.w3 = Web3(Web3.HTTPProvider("https://testnet-rpc.monad.xyz/"))
        
        # Setup account
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable required")
        
        self.account = Account.from_key(private_key)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        
        print(f"🔗 Connected to StakeToken at: {self.contract_address}")
        print(f"👤 Using account: {self.account.address}")
    
    def get_balances(self):
        """Get current balances for the account."""
        avax_balance = self.w3.eth.get_balance(self.account.address)
        token_balance = self.contract.functions.balanceOf(self.account.address).call()
        staked_balance = self.contract.functions.stakedBalance(self.account.address).call()
        reward_balance = self.contract.functions.getReward(self.account.address).call()
        
        return {
            'avax': self.w3.from_wei(avax_balance, 'ether'),
            'tokens': token_balance / 10**18,
            'staked': staked_balance / 10**18,
            'rewards': reward_balance / 10**18
        }
    
    def send_transaction(self, function_call, gas_limit=200000):
        """Helper to send a transaction."""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        gas_price = self.w3.eth.gas_price
        
        tx = function_call.build_transaction({
            'from': self.account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 43113
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📤 Transaction sent: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print(f"✅ Transaction successful!")
            return tx_hash.hex()
        else:
            print(f"❌ Transaction failed!")
            return None
    
    def mint_tokens(self, amount_tokens):
        """Mint new tokens (owner only)."""
        print(f"\n🪙 Minting {amount_tokens:,.0f} STK tokens...")
        amount_wei = int(amount_tokens * 10**18)
        
        owner = self.contract.functions.owner().call()
        if self.account.address.lower() != owner.lower():
            print(f"❌ Only owner can mint tokens")
            return None
        
        return self.send_transaction(self.contract.functions.mint(amount_wei))
    
    def transfer_tokens(self, to_address, amount_tokens):
        """Transfer tokens to another address."""
        print(f"\n💸 Transferring {amount_tokens:,.2f} STK to {to_address}...")
        amount_wei = int(amount_tokens * 10**18)
        
        return self.send_transaction(self.contract.functions.transfer(to_address, amount_wei))
    
    def stake_tokens(self, amount_tokens):
        """Stake tokens to earn rewards."""
        print(f"\n🔒 Staking {amount_tokens:,.2f} STK tokens...")
        amount_wei = int(amount_tokens * 10**18)
        
        return self.send_transaction(self.contract.functions.stake(amount_wei))
    
    def unstake_tokens(self, amount_tokens):
        """Unstake tokens and claim rewards."""
        print(f"\n🔓 Unstaking {amount_tokens:,.2f} STK tokens...")
        amount_wei = int(amount_tokens * 10**18)
        
        return self.send_transaction(self.contract.functions.unstake(amount_wei))
    
    def set_reward_rate(self, new_rate):
        """Set new reward rate (owner only)."""
        print(f"\n⚙️ Setting reward rate to {new_rate}%...")
        
        owner = self.contract.functions.owner().call()
        if self.account.address.lower() != owner.lower():
            print(f"❌ Only owner can set reward rate")
            return None
        
        return self.send_transaction(self.contract.functions.setRewardRate(new_rate))
    
    def pause_contract(self):
        """Pause the contract (owner only)."""
        print(f"\n⏸️ Pausing contract...")
        
        owner = self.contract.functions.owner().call()
        if self.account.address.lower() != owner.lower():
            print(f"❌ Only owner can pause contract")
            return None
        
        return self.send_transaction(self.contract.functions.pause())
    
    def unpause_contract(self):
        """Unpause the contract (owner only)."""
        print(f"\n▶️ Unpausing contract...")
        
        owner = self.contract.functions.owner().call()
        if self.account.address.lower() != owner.lower():
            print(f"❌ Only owner can unpause contract")
            return None
        
        return self.send_transaction(self.contract.functions.unpause())


def example_1_basic_operations():
    """Example 1: Basic token operations."""
    print("=" * 60)
    print("📋 EXAMPLE 1: Basic Token Operations")
    print("=" * 60)
    
    interactor = StakeTokenInteractor()
    
    # Check initial balances
    print("\n📊 Initial Balances:")
    balances = interactor.get_balances()
    print(f"   AVAX: {balances['avax']:.4f}")
    print(f"   STK Tokens: {balances['tokens']:,.2f}")
    print(f"   Staked: {balances['staked']:,.2f}")
    print(f"   Rewards: {balances['rewards']:,.6f}")
    
    # Mint some tokens (if owner)
    interactor.mint_tokens(500)
    
    # Transfer some tokens
    burn_address = "0x000000000000000000000000000000000000dEaD"
    interactor.transfer_tokens(burn_address, 10)
    
    # Check final balances
    print("\n📊 Final Balances:")
    balances = interactor.get_balances()
    print(f"   STK Tokens: {balances['tokens']:,.2f}")
    print(f"   Staked: {balances['staked']:,.2f}")
    print(f"   Rewards: {balances['rewards']:,.6f}")


def example_2_staking_workflow():
    """Example 2: Complete staking workflow."""
    print("\n" + "=" * 60)
    print("🔒 EXAMPLE 2: Staking Workflow")
    print("=" * 60)
    
    interactor = StakeTokenInteractor()
    
    # Check balances before staking
    print("\n📊 Before Staking:")
    balances = interactor.get_balances()
    print(f"   Available Tokens: {balances['tokens']:,.2f} STK")
    print(f"   Currently Staked: {balances['staked']:,.2f} STK")
    
    # Stake some tokens
    if balances['tokens'] >= 100:
        interactor.stake_tokens(100)
        
        # Wait a moment to accumulate some rewards
        print("\n⏳ Waiting 30 seconds to accumulate rewards...")
        time.sleep(30)
        
        # Check rewards
        balances = interactor.get_balances()
        print(f"\n🎁 Rewards after 30 seconds: {balances['rewards']:,.6f} STK")
        
        # Unstake half
        interactor.unstake_tokens(50)
        
        # Check final state
        print("\n📊 After Partial Unstaking:")
        balances = interactor.get_balances()
        print(f"   Available Tokens: {balances['tokens']:,.2f} STK")
        print(f"   Still Staked: {balances['staked']:,.2f} STK")
        print(f"   Remaining Rewards: {balances['rewards']:,.6f} STK")
    else:
        print("❌ Not enough tokens to demonstrate staking")


def example_3_admin_functions():
    """Example 3: Admin functions (owner only)."""
    print("\n" + "=" * 60)
    print("⚙️ EXAMPLE 3: Admin Functions")
    print("=" * 60)
    
    interactor = StakeTokenInteractor()
    
    # Check if we're the owner
    owner = interactor.contract.functions.owner().call()
    is_owner = interactor.account.address.lower() == owner.lower()
    
    print(f"\n👤 Contract Owner: {owner}")
    print(f"👤 Current Account: {interactor.account.address}")
    print(f"🔑 Is Owner: {is_owner}")
    
    if is_owner:
        # Change reward rate
        current_rate = interactor.contract.functions.rewardRate().call()
        print(f"\n📊 Current reward rate: {current_rate}%")
        
        # Set new rate
        interactor.set_reward_rate(15)
        
        # Verify change
        new_rate = interactor.contract.functions.rewardRate().call()
        print(f"📊 New reward rate: {new_rate}%")
        
        # Test pause/unpause
        is_paused = interactor.contract.functions.isPaused().call()
        print(f"\n⏸️ Contract paused: {is_paused}")
        
        if not is_paused:
            interactor.pause_contract()
            is_paused = interactor.contract.functions.isPaused().call()
            print(f"⏸️ Contract paused: {is_paused}")
            
            interactor.unpause_contract()
            is_paused = interactor.contract.functions.isPaused().call()
            print(f"▶️ Contract paused: {is_paused}")
    else:
        print("⚠️ Admin functions require owner privileges")


def main():
    """Run all examples."""
    print("🚀 StakeToken Contract Interaction Examples")
    print("🌐 Network: Avalanche Fuji Testnet")
    
    try:
        # Run examples
        example_1_basic_operations()
        example_2_staking_workflow()
        example_3_admin_functions()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
