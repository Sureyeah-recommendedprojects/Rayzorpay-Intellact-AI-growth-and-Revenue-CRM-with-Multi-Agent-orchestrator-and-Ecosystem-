#!/usr/bin/env python3
"""Deploy script for my1 contracts on Monad."""

import json
import os
from pathlib import Path

from pymon.deployer import deploy_contract
from pymon.wallet import WalletManager


def main():
    """Deploy SimpleStorage contract to Monad Testnet."""
    # Load configuration
    with open("pymon_config.json") as f:
        config = json.load(f)
    
    # Initialize wallet
    wallet = WalletManager()
    
    # Deploy contract with constructor parameter
    constructor_args = [42]  # Initial value for SimpleStorage
    
    result = deploy_contract(
        contract_name="SimpleStorage",
        constructor_args=constructor_args,
        config=config,
        wallet=wallet
    )
    
    if result:
        print(f"Contract deployed successfully!")
        print(f"Address: {result['address']}")
        print(f"Transaction: {result['tx_hash']}")
        print(f"Gas used: {result['gas_used']}")
        print(f"Explorer: {config['explorer_url']}/address/{result['address']}")


if __name__ == "__main__":
    main()
