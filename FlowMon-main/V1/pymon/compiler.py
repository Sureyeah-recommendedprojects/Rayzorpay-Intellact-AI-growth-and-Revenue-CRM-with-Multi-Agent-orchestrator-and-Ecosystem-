"""Python Smart contract compiler for Monad deployments via PyMon."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console
from rich.table import Table

from .transpiler import transpile_python_contract
from .transpiler_enhanced import transpile_python_contract_enhanced

# Optional Solidity support (not required for PyMon's Python-native contracts)
try:
    from .solidity_support import compile_solidity_contract, check_solidity_support, SOLIDITY_AVAILABLE
except ImportError:
    SOLIDITY_AVAILABLE = False
    compile_solidity_contract = None
    check_solidity_support = lambda: False

console = Console()


def compile_contracts(
    contracts_dir: Path,
    output_dir: Path,
    solc_version: Optional[str] = None  # Keep for compatibility but ignore
) -> Dict[str, Dict[str, Any]]:
    """
    Compile all Python smart contracts in the given directory.
    
    Args:
        contracts_dir: Directory containing .py contract files
        output_dir: Directory to save compilation artifacts
        solc_version: Ignored (kept for compatibility)
    
    Returns:
        Dictionary with compilation results for each contract
    """
    results = {}
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .py files
    py_files = list(contracts_dir.glob("*.py"))
    sol_files = list(contracts_dir.glob("*.sol"))  # Check for Solidity files
    
    if not py_files:
        console.print(f"[yellow]No Python contract files (.py) found in {contracts_dir}[/yellow]")
        console.print("[yellow]Create a contract with PyMon's Python syntax and save it as a .py file[/yellow]")
        return results
    
    # If Solidity files found, inform about Python-native approach
    if sol_files and not SOLIDITY_AVAILABLE:
        console.print("[yellow]Note: Found Solidity files but py-solc-x not installed.[/yellow]")
        console.print("[green]PyMon recommends using Python contracts instead![/green]")
        console.print("[cyan]Convert your Solidity contracts to Python for better development experience.[/cyan]")
        console.print()
    
    console.print(f"[cyan]Found {len(py_files)} Python contract(s) to compile[/cyan]")
    console.print()
    
    # Process Python contracts
    for py_file in py_files:
        contract_name = py_file.stem
        
        # Skip __init__.py or test files
        if contract_name.startswith("__") or contract_name.startswith("test_"):
            continue
            
        console.print(f"[blue]📝 Compiling Python contract: {py_file.name}[/blue]")
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                py_source = f.read()
            
            # Check if it's a valid PyMon contract
            if "from pymon.py_contracts import PySmartContract" not in py_source:
                console.print(f"[yellow]  ⚠️  Skipping {py_file.name} - not a PyMon contract[/yellow]")
                console.print(f"[yellow]      (Must import from pymon.py_contracts)[/yellow]")
                continue
            
            # Transpile Python to EVM bytecode (using enhanced transpiler with proper ABI encoding)
            console.print(f"[blue]  🔄 Transpiling to EVM bytecode (Enhanced)...[/blue]")
            try:
                transpile_result = transpile_python_contract_enhanced(py_source)
            except Exception as e:
                console.print(f"[yellow]  ⚠️  Enhanced transpiler error, falling back to original: {str(e)}[/yellow]")
                transpile_result = transpile_python_contract(py_source)
            
            # Create output directory for this contract
            contract_output_dir = output_dir / contract_name
            contract_output_dir.mkdir(exist_ok=True)
            
            # Save main artifact file
            artifact_file = contract_output_dir / f"{contract_name}.json"
            with open(artifact_file, 'w') as f:
                json.dump({
                    "contractName": contract_name,
                    "sourceName": py_file.name,
                    "abi": transpile_result["abi"],
                    "bytecode": transpile_result["bytecode"],
                    "metadata": transpile_result["metadata"],
                    "compiler": {
                        "type": "pymon-transpiler",
                        "version": "2.0.0",
                        "language": "Python"
                    }
                }, f, indent=2)
            
            # Save separate ABI file for easy access
            abi_file = contract_output_dir / f"{contract_name}_abi.json"
            with open(abi_file, 'w') as f:
                json.dump(transpile_result["abi"], f, indent=2)
            
            # Save bytecode file
            bytecode_file = contract_output_dir / f"{contract_name}_bytecode.txt"
            with open(bytecode_file, 'w') as f:
                f.write(transpile_result["bytecode"])
            
            # Calculate bytecode size
            bytecode_size = len(transpile_result["bytecode"].replace("0x", "")) // 2
            
            results[contract_name] = {
                "success": True,
                "output_file": artifact_file,
                "abi_file": abi_file,
                "bytecode_file": bytecode_file,
                "abi": transpile_result["abi"],
                "bytecode": transpile_result["bytecode"],
                "bytecode_size": bytecode_size,
                "source_file": py_file.name,
                "contract_type": "python",
                "functions": transpile_result["metadata"].get("functions", []),
                "state_variables": transpile_result["metadata"].get("state_variables", [])
            }
            
            console.print(f"[green]  ✅ Successfully compiled {contract_name}[/green]")
            console.print(f"[green]      Bytecode size: {bytecode_size} bytes[/green]")
            console.print(f"[green]      Functions: {', '.join(transpile_result['metadata'].get('functions', []))}[/green]")
            
        except Exception as e:
            results[contract_name] = {
                "success": False,
                "error": str(e),
                "source_file": py_file.name,
                "contract_type": "python"
            }
            console.print(f"[red]  ❌ Failed to compile {contract_name}[/red]")
            console.print(f"[red]      Error: {e}[/red]")
    
    # Display summary
    if results:
        console.print()
        console.print("[cyan]═" * 60 + "[/cyan]")
        console.print("[cyan]Compilation Summary[/cyan]")
        console.print("[cyan]═" * 60 + "[/cyan]")
        
        successful = sum(1 for r in results.values() if r["success"])
        failed = len(results) - successful
        
        console.print(f"✅ Successful: {successful}")
        console.print(f"❌ Failed: {failed}")
        console.print(f"📁 Output directory: {output_dir}")
        
        if successful > 0:
            console.print()
            console.print("[green]Ready to deploy with:[/green]")
            console.print("[green]  python -m pymon.cli deploy <contract_name>[/green]")
    
    return results


def get_contract_artifacts(contract_name: str, build_dir: Path = Path("build")) -> Dict[str, Any]:
    """
    Load compiled Python contract artifacts.
    
    Args:
        contract_name: Name of the contract
        build_dir: Build directory containing artifacts
    
    Returns:
        Dictionary containing ABI and bytecode
    """
    contract_dir = build_dir / contract_name
    artifact_file = contract_dir / f"{contract_name}.json"
    
    if not artifact_file.exists():
        raise FileNotFoundError(
            f"Contract artifacts not found for {contract_name}. "
            f"Run 'python -m pymon.cli compile' first."
        )
    
    with open(artifact_file) as f:
        artifacts = json.load(f)
    
    # Verify it's a Python contract
    compiler_type = artifacts.get("compiler", {}).get("type", "")
    if "python" not in compiler_type.lower() and "pymon" not in compiler_type.lower():
        console.print(f"[yellow]Warning: {contract_name} may not be a Python contract[/yellow]")
    
    return {
        "abi": artifacts["abi"],
        "bytecode": artifacts["bytecode"],
        "metadata": artifacts.get("metadata", {}),
        "source_name": artifacts.get("sourceName", ""),
        "compiler": artifacts.get("compiler", {}),
        "contract_name": artifacts.get("contractName", contract_name)
    }


def validate_python_contract(source_code: str) -> bool:
    """
    Validate that the Python source code is a valid PyMon contract.
    
    Args:
        source_code: Python source code to validate
    
    Returns:
        True if valid PyMon contract, False otherwise
    """
    required_imports = [
        "from pymon.py_contracts import PySmartContract"
    ]
    
    for imp in required_imports:
        if imp not in source_code:
            return False
    
    # Check for class definition
    if "class " not in source_code:
        return False
    
    # Check for inheritance from PySmartContract
    if "(PySmartContract)" not in source_code:
        return False
    
    return True


def list_compiled_contracts(build_dir: Path = Path("build")) -> Dict[str, Dict[str, Any]]:
    """
    List all compiled contracts in the build directory.
    
    Args:
        build_dir: Build directory to search
    
    Returns:
        Dictionary of contract information
    """
    contracts = {}
    
    if not build_dir.exists():
        return contracts
    
    for contract_dir in build_dir.iterdir():
        if contract_dir.is_dir():
            artifact_file = contract_dir / f"{contract_dir.name}.json"
            if artifact_file.exists():
                try:
                    with open(artifact_file) as f:
                        data = json.load(f)
                    
                    contracts[contract_dir.name] = {
                        "source": data.get("sourceName", "unknown"),
                        "compiler": data.get("compiler", {}),
                        "bytecode_size": len(data.get("bytecode", "").replace("0x", "")) // 2,
                        "functions": data.get("metadata", {}).get("functions", []),
                        "path": str(artifact_file)
                    }
                except Exception:
                    pass
    
    return contracts
