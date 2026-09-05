"""Python Smart contract compiler for Monad deployments via PyMon."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console

from .transpiler import transpile_python_contract

console = Console()


def get_solc_version(version: Optional[str] = None) -> str:
    """Get and install the appropriate Solidity compiler version."""
    if version:
        target_version = version
    else:
        # Default to a stable version
        target_version = "0.8.19"
    
    try:
        # Install the version if not available
        install_solc(target_version)
        set_solc_version(target_version)
        return target_version
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not install Solidity {target_version}: {e}")
        # Fall back to a known stable version
        fallback_version = "0.8.19"
        install_solc(fallback_version)
        set_solc_version(fallback_version)
        return fallback_version


def compile_contracts(
    contracts_dir: Path,
    output_dir: Path,
    solc_version: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Compile all Solidity contracts in the given directory.
    
    Args:
        contracts_dir: Directory containing .sol files
        output_dir: Directory to save compilation artifacts
        solc_version: Specific Solidity compiler version to use
    
    Returns:
        Dictionary with compilation results for each contract
    """
    results = {}
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get Solidity compiler version
    try:
        used_version = get_solc_version(solc_version)
        console.print(f"[blue]Using Solidity compiler version:[/blue] {used_version}")
    except Exception as e:
        console.print(f"[red]Error setting up Solidity compiler:[/red] {e}")
        return results
    
    # Find all .sol and .py files
    sol_files = list(contracts_dir.glob("*.sol"))
    py_files = list(contracts_dir.glob("*.py"))
    
    if not sol_files and not py_files:
        console.print(f"[yellow]No .sol or .py files found in {contracts_dir}[/yellow]")
        return results
    
    # Process Python contracts first
    for py_file in py_files:
        console.print(f"[blue]Transpiling Python contract: {py_file.name}[/blue]")
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                py_source = f.read()
            
            # Transpile Python to EVM bytecode
            transpile_result = transpile_python_contract(py_source)
            
            contract_name = py_file.stem
            contract_output_dir = output_dir / contract_name
            contract_output_dir.mkdir(exist_ok=True)
            
            # Save transpilation artifacts
            artifact_file = contract_output_dir / f"{contract_name}.json"
            with open(artifact_file, 'w') as f:
                json.dump({
                    "contractName": contract_name,
                    "sourceName": py_file.name,
                    "abi": transpile_result["abi"],
                    "bytecode": transpile_result["bytecode"],
                    "metadata": transpile_result["metadata"],
                    "compiler": {
                        "type": "python-transpiler",
                        "version": "0.1.0"
                    }
                }, f, indent=2)
            
            # Save separate ABI file
            abi_file = contract_output_dir / f"{contract_name}_abi.json"
            with open(abi_file, 'w') as f:
                json.dump(transpile_result["abi"], f, indent=2)
            
            # Save bytecode file
            bytecode_file = contract_output_dir / f"{contract_name}_bytecode.txt"
            with open(bytecode_file, 'w') as f:
                f.write(transpile_result["bytecode"])
            
            results[contract_name] = {
                "success": True,
                "output_file": artifact_file,
                "abi_file": abi_file,
                "bytecode_file": bytecode_file,
                "abi": transpile_result["abi"],
                "bytecode": transpile_result["bytecode"],
                "source_file": py_file.name,
                "contract_type": "python"
            }
            
            console.print(f"[green]✓[/green] Transpiled {contract_name} from {py_file.name}")
            
        except Exception as e:
            results[contract_name] = {
                "success": False,
                "error": str(e),
                "source_file": py_file.name,
                "contract_type": "python"
            }
            console.print(f"[red]✗[/red] Failed to transpile {contract_name}: {e}")
    
    # Process Solidity contracts
    sources = {}  # Initialize sources to avoid scope issues
    if sol_files:
        # Prepare compilation input for Solidity
        for sol_file in sol_files:
            with open(sol_file, 'r', encoding='utf-8') as f:
                sources[sol_file.name] = {"content": f.read()}
    
    # Only compile Solidity if we have sources
    if sources:
        # Compilation settings
        compilation_input = {
            "language": "Solidity",
            "sources": sources,
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
        
        try:
            # Compile contracts
            compiled_sol = compile_standard(compilation_input)
        
            # Process compilation results
            for source_file, contracts in compiled_sol["contracts"].items():
                for contract_name, contract_data in contracts.items():
                    try:
                        # Extract compilation artifacts
                        abi = contract_data["abi"]
                        bytecode = contract_data["evm"]["bytecode"]["object"]
                        metadata = json.loads(contract_data["metadata"])
                        
                        # Create output files
                        contract_output_dir = output_dir / contract_name
                        contract_output_dir.mkdir(exist_ok=True)
                        
                        # Save ABI
                        abi_file = contract_output_dir / f"{contract_name}.json"
                        with open(abi_file, 'w') as f:
                            json.dump({
                                "contractName": contract_name,
                                "sourceName": source_file,
                                "abi": abi,
                                "bytecode": f"0x{bytecode}",
                                "metadata": metadata,
                                "compiler": {
                                    "version": used_version
                                }
                            }, f, indent=2)
                        
                        # Save separate ABI file for easier access
                        abi_only_file = contract_output_dir / f"{contract_name}_abi.json"
                        with open(abi_only_file, 'w') as f:
                            json.dump(abi, f, indent=2)
                        
                        # Save bytecode
                        bytecode_file = contract_output_dir / f"{contract_name}_bytecode.txt"
                        with open(bytecode_file, 'w') as f:
                            f.write(f"0x{bytecode}")
                        
                        results[contract_name] = {
                            "success": True,
                            "output_file": abi_file,
                            "abi_file": abi_only_file,
                            "bytecode_file": bytecode_file,
                            "abi": abi,
                            "bytecode": f"0x{bytecode}",
                            "source_file": source_file,
                            "contract_type": "solidity"
                        }
                        
                        console.print(f"[green]✓[/green] Compiled {contract_name} from {source_file}")
                    
                    except Exception as e:
                        results[contract_name] = {
                            "success": False,
                            "error": str(e),
                            "source_file": source_file,
                            "contract_type": "solidity"
                        }
                        console.print(f"[red]✗[/red] Failed to process {contract_name}: {e}")
        
        except Exception as e:
            console.print(f"[red]Compilation failed:[/red] {e}")
            # Mark all found contracts as failed
            for sol_file in sol_files:
                contract_name = sol_file.stem
                results[contract_name] = {
                    "success": False,
                    "error": str(e),
                    "source_file": sol_file.name
                }
    
    return results


def get_contract_artifacts(contract_name: str, build_dir: Path = Path("build")) -> Dict[str, Any]:
    """
    Load compiled contract artifacts.
    
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
            f"Run 'avax-cli compile' first."
        )
    
    with open(artifact_file) as f:
        artifacts = json.load(f)
    
    return {
        "abi": artifacts["abi"],
        "bytecode": artifacts["bytecode"],
        "metadata": artifacts.get("metadata", {}),
        "source_name": artifacts.get("sourceName", ""),
        "compiler_version": artifacts.get("compiler", {}).get("version", "unknown")
    }