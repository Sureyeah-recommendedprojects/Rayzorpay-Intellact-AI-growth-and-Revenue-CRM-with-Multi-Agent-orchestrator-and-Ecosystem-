"""Smart contract interaction utilities for Monad blockchain."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from web3 import Web3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .compiler import get_contract_artifacts
from .deployer import get_web3_connection
from .wallet import WalletManager

console = Console()


class ContractInteractor:
    """Interact with deployed smart contracts."""
    
    def __init__(self, config: Dict[str, Any], wallet: WalletManager):
        self.config = config
        self.wallet = wallet
        self.w3 = get_web3_connection(config)
        self.account = wallet.get_account()
        
    def get_deployed_contract(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Get deployed contract info from deployments.json."""
        deployments_file = Path("deployments.json")
        if not deployments_file.exists():
            console.print("[red]No deployments.json found. Deploy a contract first.[/red]")
            return None
            
        with open(deployments_file) as f:
            deployments = json.load(f)
            
        network = self.config["network"]
        if network not in deployments or contract_name not in deployments[network]:
            console.print(f"[red]Contract {contract_name} not found on {network} network.[/red]")
            return None
            
        return deployments[network][contract_name]
    
    def get_contract_instance(self, contract_name: str):
        """Get Web3 contract instance for interaction."""
        # Get deployment info
        deployment_info = self.get_deployed_contract(contract_name)
        if not deployment_info:
            return None
            
        # Get contract artifacts
        try:
            artifacts = get_contract_artifacts(contract_name)
        except FileNotFoundError:
            console.print(f"[red]Contract artifacts not found for {contract_name}. Compile first.[/red]")
            return None
            
        # Create contract instance
        contract = self.w3.eth.contract(
            address=deployment_info["address"],
            abi=artifacts["abi"]
        )
        
        return contract, deployment_info
    
    def call_view_function(self, contract_name: str, function_name: str, *args) -> Any:
        """Call a view function on the contract."""
        result = self.get_contract_instance(contract_name)
        if not result:
            return None
            
        contract, deployment_info = result
        
        try:
            # Call view function
            func = getattr(contract.functions, function_name)
            result = func(*args).call()
            
            console.print(Panel(
                f"[cyan]Function:[/cyan] {function_name}({', '.join(map(str, args))})\n"
                f"[green]Result:[/green] {result}\n"
                f"[blue]Contract:[/blue] {deployment_info['address']}",
                title=f"{contract_name} - View Call",
                border_style="cyan"
            ))
            
            return result
            
        except Exception as e:
            console.print(f"[red]Error calling {function_name}: {e}[/red]")
            return None
    
    def send_transaction(self, contract_name: str, function_name: str, *args, **kwargs) -> Optional[str]:
        """Send a transaction to the contract."""
        result = self.get_contract_instance(contract_name)
        if not result:
            return None
            
        contract, deployment_info = result
        
        try:
            # Get function
            func = getattr(contract.functions, function_name)
            
            # Build transaction
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            try:
                gas_estimate = func(*args).estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 1.2)  # 20% buffer
            except Exception as e:
                console.print(f"[yellow]Gas estimation failed: {e}. Using default gas limit.[/yellow]")
                gas_limit = 200000
            
            # Build transaction
            transaction = func(*args).build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.config["chain_id"]
            })
            
            # Sign and send
            console.print(f"[blue]Sending transaction to {function_name}...[/blue]")
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            console.print(f"[yellow]Transaction sent: {tx_hash.hex()}[/yellow]")
            console.print("[blue]Waiting for confirmation...[/blue]")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                console.print(Panel(
                    f"[green]✓ Transaction successful![/green]\n\n"
                    f"[cyan]Function:[/cyan] {function_name}({', '.join(map(str, args))})\n"
                    f"[blue]Transaction:[/blue] {tx_hash.hex()}\n"
                    f"[blue]Gas used:[/blue] {receipt.gasUsed:,}\n"
                    f"[blue]Block:[/blue] {receipt.blockNumber}\n"
                    f"[blue]Contract:[/blue] {deployment_info['address']}",
                    title=f"{contract_name} - Transaction Success",
                    border_style="green"
                ))
                return tx_hash.hex()
            else:
                console.print(f"[red]Transaction failed![/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]Error sending transaction to {function_name}: {e}[/red]")
            return None
    
    def get_contract_info(self, contract_name: str):
        """Display contract information and available functions."""
        result = self.get_contract_instance(contract_name)
        if not result:
            return
            
        contract, deployment_info = result
        
        # Create info table
        table = Table(title=f"{contract_name} Contract Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Address", deployment_info["address"])
        table.add_row("Network", deployment_info["network"])
        table.add_row("Deployer", deployment_info["deployer"])
        table.add_row("Block", str(deployment_info["block_number"]))
        table.add_row("Gas Used", f"{deployment_info['gas_used']:,}")
        
        console.print(table)
        
        # Show available functions
        functions_table = Table(title="Available Functions")
        functions_table.add_column("Function", style="yellow")
        functions_table.add_column("Type", style="blue")
        functions_table.add_column("Inputs", style="magenta")
        
        for func in contract.abi:
            if func["type"] == "function":
                inputs = ", ".join([f"{inp['type']} {inp['name']}" for inp in func["inputs"]])
                func_type = func.get("stateMutability", "nonpayable")
                functions_table.add_row(func["name"], func_type, inputs)
        
        console.print(functions_table)


def interact_with_contract(
    contract_name: str,
    function_name: str,
    args: List[Any],
    config: Dict[str, Any],
    wallet: WalletManager,
    is_view: bool = False
) -> Any:
    """Main function to interact with deployed contracts."""
    interactor = ContractInteractor(config, wallet)
    
    if is_view:
        return interactor.call_view_function(contract_name, function_name, *args)
    else:
        return interactor.send_transaction(contract_name, function_name, *args)


def show_contract_info(contract_name: str, config: Dict[str, Any], wallet: WalletManager):
    """Show contract information and available functions."""
    interactor = ContractInteractor(config, wallet)
    interactor.get_contract_info(contract_name)
