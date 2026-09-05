"""Environment variable loader for PyMon.

This module handles loading configuration from .env files and environment variables.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console

console = Console()


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file (default: .env in current directory)
    
    Returns:
        Dictionary of environment variables
    """
    if env_path is None:
        env_path = Path(".env")
    
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
        
        return env_vars
    
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load .env file: {e}[/yellow]")
        return {}


def get_env_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables or .env file.
    
    Priority:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values
    
    Returns:
        Dictionary with configuration
    """
    # Load .env file
    env_vars = load_env_file()
    
    # Helper function to get value (env var > .env file > default)
    def get_value(key: str, default: Any = None) -> Any:
        return os.getenv(key, env_vars.get(key, default))
    
    config = {
        # Wallet configuration
        "private_key": get_value("PRIVATE_KEY"),
        "keystore_file": get_value("KEYSTORE_FILE", "pymon_key.json"),
        "keystore_password": get_value("KEYSTORE_PASSWORD"),
        
        # Network configuration
        "network": get_value("NETWORK", "monad-testnet"),
        "rpc_url": get_value("RPC_URL", "https://testnet-rpc.monad.xyz/"),
        "chain_id": int(get_value("CHAIN_ID", "10143")),
        "explorer_url": get_value("EXPLORER_URL", "https://testnet.monadexplorer.com/"),
        
        # Gas configuration
        "gas_limit": get_value("GAS_LIMIT"),
        "gas_price_gwei": get_value("GAS_PRICE_GWEI"),
        "max_gas_price_gwei": get_value("MAX_GAS_PRICE_GWEI"),
        "gas_buffer_percent": float(get_value("GAS_BUFFER_PERCENT", "20")),
        
        # Developer options
        "debug": get_value("DEBUG", "").lower() == "true",
        "dry_run": get_value("DRY_RUN", "").lower() == "true",
        "auto_confirm": get_value("AUTO_CONFIRM", "").lower() == "true",
        
        # Resources
        "faucet_url": get_value("FAUCET_URL", "https://discord.gg/monaddev"),
        "block_explorer": get_value("BLOCK_EXPLORER", "https://testnet.monadexplorer.com/"),
    }
    
    return config


def check_env_setup() -> bool:
    """
    Check if environment is properly configured.
    
    Returns:
        True if wallet is configured, False otherwise
    """
    config = get_env_config()
    
    has_private_key = config.get("private_key") and config["private_key"] != "your_private_key_here_64_hex_characters"
    has_keystore = Path(config.get("keystore_file", "pymon_key.json")).exists()
    
    return has_private_key or has_keystore


def display_env_status():
    """Display current environment configuration status."""
    config = get_env_config()
    env_file_exists = Path(".env").exists()
    
    console.print("\n[cyan]═══ PyMon Environment Status ═══[/cyan]\n")
    
    # Check .env file
    if env_file_exists:
        console.print("[green]✓[/green] .env file found")
    else:
        console.print("[yellow]○[/yellow] No .env file (using defaults)")
        console.print("  [dim]Create from template: cp .env.example .env[/dim]")
    
    console.print()
    
    # Check wallet configuration
    console.print("[cyan]Wallet Configuration:[/cyan]")
    
    has_private_key = config.get("private_key") and config["private_key"] != "your_private_key_here_64_hex_characters"
    has_keystore = Path(config.get("keystore_file", "pymon_key.json")).exists()
    
    if has_private_key:
        console.print("[green]✓[/green] Private key configured (PRIVATE_KEY)")
        key_preview = config["private_key"][:8] + "..." + config["private_key"][-8:]
        console.print(f"  [dim]Key: {key_preview}[/dim]")
    else:
        console.print("[yellow]○[/yellow] No private key in environment")
    
    if has_keystore:
        console.print(f"[green]✓[/green] Keystore file exists: {config['keystore_file']}")
    else:
        console.print(f"[yellow]○[/yellow] No keystore file found")
    
    if not has_private_key and not has_keystore:
        console.print("\n[yellow]⚠️  No wallet configured![/yellow]")
        console.print("[yellow]Choose one:[/yellow]")
        console.print("  1. Add PRIVATE_KEY to .env file")
        console.print("  2. Create keystore: python -m pymon.cli wallet new")
    
    console.print()
    
    # Network configuration
    console.print("[cyan]Network Configuration:[/cyan]")
    console.print(f"[green]✓[/green] Network: {config['network']}")
    console.print(f"[green]✓[/green] Chain ID: {config['chain_id']}")
    console.print(f"[green]✓[/green] RPC URL: {config['rpc_url']}")
    console.print(f"[green]✓[/green] Explorer: {config['explorer_url']}")
    
    console.print()


def validate_private_key(private_key: str) -> bool:
    """
    Validate that private key is in correct format.
    
    Args:
        private_key: Private key to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not private_key:
        return False
    
    # Remove 0x prefix if present
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    # Check length (64 hex characters)
    if len(private_key) != 64:
        return False
    
    # Check if all characters are hex
    try:
        int(private_key, 16)
        return True
    except ValueError:
        return False


def get_wallet_from_env() -> Optional[str]:
    """
    Get wallet private key from environment.
    
    Returns:
        Private key if found and valid, None otherwise
    """
    config = get_env_config()
    private_key = config.get("private_key")
    
    if private_key and private_key != "your_private_key_here_64_hex_characters":
        if validate_private_key(private_key):
            return private_key
        else:
            console.print("[red]Error: Invalid PRIVATE_KEY format in environment![/red]")
            console.print("[yellow]Private key must be 64 hex characters (with or without 0x prefix)[/yellow]")
    
    return None


def create_env_template():
    """Create .env file from template if it doesn't exist."""
    env_path = Path(".env")
    template_path = Path(".env.example")
    
    if env_path.exists():
        console.print("[yellow].env file already exists![/yellow]")
        return False
    
    if not template_path.exists():
        console.print("[red]Error: .env.example template not found![/red]")
        return False
    
    try:
        import shutil
        shutil.copy(template_path, env_path)
        console.print("[green]✓ Created .env file from template[/green]")
        console.print("[yellow]Edit .env and add your private key or keystore settings[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]Error creating .env: {e}[/red]")
        return False
