"""Optional Solidity support module for PyMon.

This module provides backward compatibility for Solidity contracts if needed.
PyMon is Python-native by default, but this allows optional Solidity support.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

# Try to import py-solc-x, but make it optional
SOLIDITY_AVAILABLE = False
try:
    from solcx import compile_standard, install_solc, set_solc_version
    SOLIDITY_AVAILABLE = True
except ImportError:
    console.print("[yellow]Note: py-solc-x not installed. Solidity support disabled.[/yellow]")
    console.print("[yellow]PyMon works natively with Python contracts - no Solidity needed![/yellow]")
    console.print("[yellow]To enable Solidity support (optional): pip install py-solc-x[/yellow]")


def compile_solidity_contract(
    source_code: str,
    contract_name: str,
    solc_version: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Compile a Solidity contract if py-solc-x is available.
    
    Args:
        source_code: Solidity source code
        contract_name: Name of the contract
        solc_version: Specific Solidity compiler version to use
    
    Returns:
        Compilation result or None if Solidity not available
    """
    if not SOLIDITY_AVAILABLE:
        console.print("[red]Error: Solidity compilation requested but py-solc-x not installed.[/red]")
        console.print("[yellow]Install with: pip install py-solc-x[/yellow]")
        console.print("[green]Or better: Use PyMon's native Python contracts instead![/green]")
        return None
    
    try:
        # Install and set compiler version
        target_version = solc_version or "0.8.19"
        install_solc(target_version)
        set_solc_version(target_version)
        
        # Prepare compilation input
        compilation_input = {
            "language": "Solidity",
            "sources": {
                f"{contract_name}.sol": {"content": source_code}
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "evm.bytecode", "evm.deployedBytecode", "metadata"]
                    }
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            }
        }
        
        # Compile
        compiled = compile_standard(compilation_input)
        
        # Extract results
        contract_data = compiled["contracts"][f"{contract_name}.sol"][contract_name]
        
        return {
            "abi": contract_data["abi"],
            "bytecode": f"0x{contract_data['evm']['bytecode']['object']}",
            "metadata": json.loads(contract_data["metadata"]),
            "compiler_version": target_version
        }
        
    except Exception as e:
        console.print(f"[red]Solidity compilation failed: {e}[/red]")
        return None


def check_solidity_support() -> bool:
    """Check if Solidity support is available."""
    return SOLIDITY_AVAILABLE


def get_solidity_version() -> Optional[str]:
    """Get the current Solidity compiler version if available."""
    if not SOLIDITY_AVAILABLE:
        return None
    
    try:
        from solcx import get_solc_version
        return str(get_solc_version())
    except:
        return None


def suggest_python_alternative(solidity_code: str) -> str:
    """
    Suggest a Python alternative for Solidity code.
    
    Args:
        solidity_code: Solidity source code
    
    Returns:
        Suggested Python equivalent
    """
    suggestion = """
# PyMon Suggestion: Convert your Solidity contract to Python!
# Here's a template to get you started:

from pymon.py_contracts import PySmartContract

class YourContract(PySmartContract):
    \"\"\"Your contract description here.\"\"\"
    
    def __init__(self):
        super().__init__()
        # Define state variables
        self.my_variable = self.state_var("my_variable", 0)
    
    @public_function
    def my_function(self, value: int):
        \"\"\"Public function example.\"\"\"
        self.my_variable = value
        self.event("ValueChanged", value)
    
    @view_function
    def get_value(self) -> int:
        \"\"\"View function example.\"\"\"
        return self.my_variable

# Benefits of using Python:
# ✅ No need to learn Solidity
# ✅ Use Python syntax you already know
# ✅ Better error messages
# ✅ Faster development
# ✅ Direct transpilation to EVM bytecode
"""
    return suggestion
