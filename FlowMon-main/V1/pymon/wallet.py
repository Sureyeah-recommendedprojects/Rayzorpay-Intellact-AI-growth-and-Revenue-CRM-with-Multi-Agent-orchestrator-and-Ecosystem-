"""Wallet management for Monad blockchain transactions."""

import json
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from eth_account import Account
from web3 import Web3
import base64
from rich.console import Console

try:
    from .env_loader import get_wallet_from_env, get_env_config
except ImportError:
    get_wallet_from_env = lambda: None
    get_env_config = lambda: {}

console = Console()


class WalletManager:
    """Manage Monad wallets with encryption support."""
    
    def __init__(self):
        """Initialize wallet manager."""
        # Enable unaudited HD wallet features for account generation
        Account.enable_unaudited_hdwallet_features()
    
    def create_wallet(self, password: str, keystore_file: str = "pymon_key.json") -> str:
        """
        Create a new wallet and save encrypted keystore.
        
        Args:
            password: Password to encrypt the keystore
            keystore_file: Path to save the encrypted keystore
        
        Returns:
            Wallet address
        """
        # Generate a new private key
        private_key = secrets.token_hex(32)
        account = Account.from_key(private_key)
        
        # Create encrypted keystore
        self._save_encrypted_key(private_key, password, keystore_file)
        
        return account.address
    
    def load_wallet(self, keystore_file: str, password: str) -> str:
        """
        Load wallet from encrypted keystore.
        
        Args:
            keystore_file: Path to encrypted keystore
            password: Password to decrypt the keystore
        
        Returns:
            Wallet address
        """
        private_key = self._load_encrypted_key(keystore_file, password)
        account = Account.from_key(private_key)
        return account.address
    
    def get_private_key(self, keystore_file: str = None, password: str = None) -> str:
        """
        Get private key from environment variable, .env file, or keystore.
        
        Priority:
        1. PRIVATE_KEY environment variable
        2. PRIVATE_KEY in .env file  
        3. Encrypted keystore file
        
        Args:
            keystore_file: Path to encrypted keystore (optional)
            password: Password to decrypt keystore (optional)
        
        Returns:
            Private key as hex string
        """
        # First, try environment/.env file (using env_loader)
        env_key = get_wallet_from_env()
        if env_key:
            # Ensure it's properly formatted
            if not env_key.startswith("0x"):
                env_key = f"0x{env_key}"
            return env_key
        
        # Fall back to keystore file
        if keystore_file and password:
            return self._load_encrypted_key(keystore_file, password)
        
        # Try default keystores
        default_keystores = ["pymon_key.json", "avax_key.json"]
        for default_keystore in default_keystores:
            if Path(default_keystore).exists() and password:
                return self._load_encrypted_key(default_keystore, password)
        
        raise ValueError(
            "No private key found. Options:\n"
            "  1. Set PRIVATE_KEY in .env file (copy from .env.example)\n"
            "  2. Set PRIVATE_KEY environment variable\n"
            "  3. Create keystore: python -m pymon.cli wallet new"
        )
    
    def get_address_from_env(self) -> str:
        """Get wallet address from PRIVATE_KEY environment variable."""
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable not set")
        
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
        
        account = Account.from_key(private_key)
        return account.address
    
    def get_account(self, keystore_file: str = None, password: str = None) -> Account:
        """
        Get Web3 account object for signing transactions.
        
        Args:
            keystore_file: Path to encrypted keystore (optional)
            password: Password to decrypt keystore (optional)
        
        Returns:
            Web3 Account object
        """
        private_key = self.get_private_key(keystore_file, password)
        return Account.from_key(private_key)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _save_encrypted_key(self, private_key: str, password: str, keystore_file: str) -> None:
        """Save private key to encrypted keystore file."""
        # Generate salt for key derivation
        salt = os.urandom(16)
        
        # Derive encryption key from password
        key = self._derive_key(password, salt)
        
        # Encrypt private key
        f = Fernet(key)
        encrypted_key = f.encrypt(private_key.encode())
        
        # Save to file
        keystore_data = {
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "salt": base64.b64encode(salt).decode(),
            "version": 1
        }
        
        with open(keystore_file, 'w') as f:
            json.dump(keystore_data, f, indent=2)
        
        # Set secure file permissions (owner read/write only)
        os.chmod(keystore_file, 0o600)
    
    def _load_encrypted_key(self, keystore_file: str, password: str) -> str:
        """Load private key from encrypted keystore file."""
        if not Path(keystore_file).exists():
            raise FileNotFoundError(f"Keystore file '{keystore_file}' not found")
        
        try:
            with open(keystore_file) as f:
                keystore_data = json.load(f)
            
            # Extract data
            encrypted_key = base64.b64decode(keystore_data["encrypted_key"])
            salt = base64.b64decode(keystore_data["salt"])
            
            # Derive decryption key
            key = self._derive_key(password, salt)
            
            # Decrypt private key
            f = Fernet(key)
            private_key = f.decrypt(encrypted_key).decode()
            
            # Ensure proper formatting
            if not private_key.startswith("0x"):
                private_key = f"0x{private_key}"
            
            return private_key
        
        except Exception as e:
            raise ValueError(f"Failed to decrypt keystore: {e}")
    
    def _load_from_env_file(self) -> Optional[str]:
        """Load PRIVATE_KEY from .env file."""
        env_files = [".env", "../.env", "../../.env"]  # Check current and parent directories
        
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('PRIVATE_KEY='):
                                # Extract value after =, remove quotes if present
                                value = line.split('=', 1)[1]
                                value = value.strip('"\'')  # Remove quotes
                                if value:
                                    return value
                except Exception:
                    continue  # Try next file if this one fails
        
        return None
    
    def validate_private_key(self, private_key: str) -> bool:
        """Validate that a private key is properly formatted."""
        try:
            if not private_key.startswith("0x"):
                private_key = f"0x{private_key}"
            
            # Try to create account to validate
            Account.from_key(private_key)
            return True
        except Exception:
            return False