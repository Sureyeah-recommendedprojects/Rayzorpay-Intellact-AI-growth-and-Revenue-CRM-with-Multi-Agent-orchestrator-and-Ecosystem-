"""Utility functions for PyVax CLI."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def load_config(config_path: str = "avax_config.json") -> Dict[str, Any]:
    """Load configuration from file."""
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[red]Error:[/red] {config_path} not found. Run 'python -m avax_cli.cli init' first.")
        return {}
    
    with open(config_file) as f:
        return json.load(f)


def check_environment() -> bool:
    """Check if environment is properly set up."""
    issues = []
    
    # Check private key
    if not os.getenv('PRIVATE_KEY'):
        issues.append("PRIVATE_KEY environment variable not set")
    
    # Check config file
    if not Path("avax_config.json").exists():
        issues.append("avax_config.json not found")
    
    # Check contracts directory
    if not Path("contracts").exists():
        issues.append("contracts/ directory not found")
    
    if issues:
        console.print("[red]Environment Issues:[/red]")
        for issue in issues:
            console.print(f"  ❌ {issue}")
        return False
    
    console.print("[green]✅ Environment check passed![/green]")
    return True


def display_deployment_summary(deployments: Dict[str, Any], network: str = "fuji"):
    """Display a summary of deployed contracts."""
    if network not in deployments or not deployments[network]:
        console.print(f"[yellow]No contracts deployed on {network} network.[/yellow]")
        return
    
    table = Table(title=f"Deployed Contracts - {network.upper()}")
    table.add_column("Contract", style="cyan")
    table.add_column("Address", style="green")
    table.add_column("Gas Used", style="yellow")
    table.add_column("Block", style="blue")
    
    for contract_name, contract_info in deployments[network].items():
        table.add_row(
            contract_name,
            contract_info["address"],
            f"{contract_info['gas_used']:,}",
            str(contract_info["block_number"])
        )
    
    console.print(table)


def format_address(address: str) -> str:
    """Format address for display."""
    if len(address) > 10:
        return f"{address[:6]}...{address[-4:]}"
    return address


def format_amount(amount: int, decimals: int = 18, symbol: str = "AVAX") -> str:
    """Format token amount for display."""
    formatted = amount / (10 ** decimals)
    return f"{formatted:,.4f} {symbol}"


def create_shortcut_commands():
    """Create shortcut batch files for common commands."""
    shortcuts = {
        "compile.bat": "python -m avax_cli.cli compile",
        "deploy.bat": "python -m avax_cli.cli deploy %1",
        "info.bat": "python -m avax_cli.cli info %1",
        "interact.bat": "python -m avax_cli.cli interact %*"
    }
    
    for filename, command in shortcuts.items():
        with open(filename, "w") as f:
            f.write(f"@echo off\n{command}\n")
    
    console.print("[green]✅ Shortcut commands created:[/green]")
    for filename in shortcuts.keys():
        console.print(f"  📄 {filename}")


def validate_contract_name(name: str) -> bool:
    """Validate contract name."""
    if not name.isalnum():
        console.print("[red]Contract name must be alphanumeric[/red]")
        return False
    
    if not name[0].isupper():
        console.print("[red]Contract name should start with uppercase letter[/red]")
        return False
    
    return True


def get_network_info(network: str) -> Dict[str, Any]:
    """Get network configuration."""
    networks = {
        "fuji": {
            "name": "Avalanche Fuji Testnet",
            "rpc_url": "https://api.avax-test.network/ext/bc/C/rpc",
            "chain_id": 43113,
            "explorer": "https://testnet.snowtrace.io",
            "faucet": "https://faucet.avax.network"
        },
        "mainnet": {
            "name": "Avalanche Mainnet",
            "rpc_url": "https://api.avax.network/ext/bc/C/rpc",
            "chain_id": 43114,
            "explorer": "https://snowtrace.io",
            "faucet": None
        }
    }
    
    return networks.get(network, networks["fuji"])
