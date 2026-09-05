"""Main CLI interface for PyMon tool."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .compiler import compile_contracts
from .deployer import deploy_contract, estimate_gas
from .wallet import WalletManager
from .interactor import interact_with_contract, show_contract_info
from .env_loader import display_env_status, create_env_template, check_env_setup
from pymon.transpiler import transpile_python_contract
from pymon.auditor import audit_contract_file, display_audit_report

app = typer.Typer(
    name="pymon",
    help="Python-powered smart contract deployment tool for Monad blockchain",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the project to initialize"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing project"),
) -> None:
    """Initialize a new Monad project with Python smart contracts."""
    project_path = Path(project_name)
    
    if project_path.exists() and not force:
        console.print(f"[red]Error:[/red] Project '{project_name}' already exists. Use --force to overwrite.")
        raise typer.Exit(1)
    
    # Create project structure
    project_path.mkdir(exist_ok=True)
    (project_path / "contracts").mkdir(exist_ok=True)
    (project_path / "build").mkdir(exist_ok=True)
    (project_path / "scripts").mkdir(exist_ok=True)
    
    # Create Monad Testnet config (no network selection needed)
    config = {
        "network": "monad-testnet",
        "rpc_url": "https://testnet-rpc.monad.xyz/",
        "chain_id": 10143,
        "explorer_url": "https://testnet.monadexplorer.com/",
        "faucet_url": "https://discord.gg/monaddev"
    }
    
    with open(project_path / "pymon_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Create sample Python smart contract
    python_contract = '''from pymon.py_contracts import PySmartContract

class SimpleStorage(PySmartContract):
    """Simple storage contract for Monad blockchain."""
    
    def __init__(self):
        super().__init__()
        self.stored_data = self.state_var("stored_data", 0)
    
    @public_function
    def set(self, value: int):
        """Set stored data."""
        self.stored_data = value
        self.event("DataStored", value)
    
    @view_function  
    def get(self) -> int:
        """Get stored data."""
        return self.stored_data
'''
    
    # Create additional Python contract example
    counter_contract = '''from pymon.py_contracts import PySmartContract

class Counter(PySmartContract):
    """Counter contract for Monad blockchain."""
    
    def __init__(self):
        super().__init__()
        self.count = self.state_var("count", 0)
        self.owner = self.state_var("owner", msg.sender)
    
    @public_function
    def increment(self):
        """Increment the counter."""
        self.count = self.count + 1
        self.event("Incremented", self.count, msg.sender)
    
    @public_function
    def decrement(self):
        """Decrement the counter."""
        require(self.count > 0, "Counter cannot go below zero")
        self.count = self.count - 1
        self.event("Decremented", self.count, msg.sender)
    
    @view_function
    def get_count(self) -> int:
        """Get current count."""
        return self.count
    
    @view_function
    def get_owner(self) -> str:
        """Get contract owner."""
        return self.owner
'''
    
    with open(project_path / "contracts" / "SimpleStorage.py", "w") as f:
        f.write(python_contract)
        
    with open(project_path / "contracts" / "Counter.py", "w") as f:
        f.write(counter_contract)
    
    # Create sample deploy script
    deploy_script = f'''#!/usr/bin/env python3
"""Deploy script for {project_name} contracts on Monad."""

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
        print(f"Address: {{result['address']}}")
        print(f"Transaction: {{result['tx_hash']}}")
        print(f"Gas used: {{result['gas_used']}}")
        print(f"Explorer: {{config['explorer_url']}}/address/{{result['address']}}")


if __name__ == "__main__":
    main()
'''
    
    with open(project_path / "scripts" / "deploy.py", "w") as f:
        f.write(deploy_script)
    
    # Make deploy script executable
    os.chmod(project_path / "scripts" / "deploy.py", 0o755)
    
    console.print(Panel(
        f"[green]✓[/green] Project '{project_name}' initialized successfully!\n\n"
        f"[cyan]Network:[/cyan] Monad Testnet\n"
        f"[cyan]Chain ID:[/cyan] 10143\n"
        f"[cyan]RPC:[/cyan] https://testnet-rpc.monad.xyz/\n\n"
        f"[yellow]Next steps:[/yellow]\n"
        f"1. cd {project_name}\n"
        f"2. pymon wallet new  # Create a new wallet\n"
        f"3. Get testnet MON from Discord: https://discord.gg/monaddev\n"
        f"4. pymon compile     # Compile Python contracts\n"
        f"5. pymon deploy SimpleStorage  # Deploy to Monad Testnet",
        title="Project Initialized",
        border_style="green"
    ))


@app.command()
def compile(
    contracts_dir: str = typer.Option("contracts", "--contracts", "-c", help="Contracts directory"),
    output_dir: str = typer.Option("build", "--output", "-o", help="Output directory for compiled artifacts"),
    solc_version: Optional[str] = typer.Option(None, "--solc-version", help="Ignored - PyMon uses Python only"),
) -> None:
    """Compile Python smart contracts to EVM bytecode."""
    contracts_path = Path(contracts_dir)
    output_path = Path(output_dir)
    
    if not contracts_path.exists():
        console.print(f"[red]Error:[/red] Contracts directory '{contracts_dir}' not found.")
        raise typer.Exit(1)
    
    try:
        with console.status("[bold green]Compiling contracts..."):
            results = compile_contracts(contracts_path, output_path, solc_version)
        
        if results:
            table = Table(title="Compilation Results")
            table.add_column("Contract", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Output", style="yellow")
            
            for contract_name, result in results.items():
                status = "✓ Success" if result["success"] else "✗ Failed"
                output_file = result.get("output_file", "N/A")
                table.add_row(contract_name, status, str(output_file))
            
            console.print(table)
            console.print(f"[green]Compilation completed![/green] Artifacts saved to '{output_dir}'")
        else:
            console.print("[yellow]No contracts found to compile.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Compilation failed:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def deploy(
    contract_name: str = typer.Argument(..., help="Name of the contract to deploy"),
    constructor_args: Optional[str] = typer.Option(None, "--args", help="Constructor arguments as JSON array"),
    config_file: str = typer.Option("pymon_config.json", "--config", help="Configuration file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate gas without deploying"),
) -> None:
    """Deploy a compiled contract to Monad Testnet."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file '{config_file}' not found.")
        console.print("Run 'pymon init <project_name>' to create a project with default config.")
        raise typer.Exit(1)
    
    # Load configuration (no network override needed - always Monad Testnet)
    with open(config_path) as f:
        config = json.load(f)
    
    # Parse constructor arguments
    args = []
    if constructor_args:
        try:
            args = json.loads(constructor_args)
            if not isinstance(args, list):
                raise ValueError("Constructor arguments must be a JSON array")
        except json.JSONDecodeError as e:
            console.print(f"[red]Error:[/red] Invalid JSON in constructor arguments: {e}")
            raise typer.Exit(1)
    
    # Initialize wallet
    wallet = WalletManager()
    
    try:
        if dry_run:
            with console.status("[bold yellow]Estimating gas..."):
                gas_estimate = estimate_gas(contract_name, args, config, wallet)
            
            console.print(Panel(
                f"[yellow]Gas Estimation for {contract_name}[/yellow]\n\n"
                f"Estimated gas: {gas_estimate:,}\n"
                f"Network: Monad Testnet (Chain ID: {config['chain_id']})\n"
                f"RPC URL: {config['rpc_url']}",
                title="Dry Run Results",
                border_style="yellow"
            ))
        else:
            with console.status(f"[bold green]Deploying {contract_name} to Monad Testnet..."):
                result = deploy_contract(contract_name, args, config, wallet)
            
            if result:
                console.print(Panel(
                    f"[green]✓ Contract deployed successfully![/green]\n\n"
                    f"Contract: {contract_name}\n"
                    f"Address: {result['address']}\n"
                    f"Transaction: {result['tx_hash']}\n"
                    f"Gas used: {result['gas_used']:,}\n"
                    f"Network: Monad Testnet (Chain ID: {config['chain_id']})\n"
                    f"Explorer: {config.get('explorer_url', 'https://testnet.monadexplorer.com')}/address/{result['address']}",
                    title="Deployment Successful",
                    border_style="green"
                ))
            else:
                console.print("[red]Deployment failed. Check logs for details.[/red]")
                raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Deployment error:[/red] {str(e)}")
        raise typer.Exit(1)


wallet_app = typer.Typer(help="Wallet management commands")
app.add_typer(wallet_app, name="wallet")

env_app = typer.Typer(help="Environment configuration commands")
app.add_typer(env_app, name="env")

audit_app = typer.Typer(help="Smart contract security audit commands")
app.add_typer(audit_app, name="audit")


@env_app.command()
def setup():
    """Create .env file from template."""
    console.print("[cyan]Setting up PyMon environment...[/cyan]\n")
    
    if create_env_template():
        console.print("\n[green]Next steps:[/green]")
        console.print("1. Edit .env file and add your PRIVATE_KEY")
        console.print("2. Or create a new wallet: python -m pymon.cli wallet new")
        console.print("3. Get testnet MON from: https://discord.gg/monaddev")
    else:
        console.print("[yellow]To start fresh, delete .env and run this command again[/yellow]")


@env_app.command()
def status():
    """Show current environment configuration."""
    display_env_status()


@wallet_app.command()
def new(
    password: Optional[str] = typer.Option(None, "--password", help="Wallet password (will prompt if not provided)"),
    keystore_file: str = typer.Option("pymon_key.json", "--keystore", help="Keystore file path"),
) -> None:
    """Generate a new wallet and save encrypted keystore."""
    if password is None:
        password = typer.prompt("Enter password for new wallet", hide_input=True)
        confirm_password = typer.prompt("Confirm password", hide_input=True)
        
        if password != confirm_password:
            console.print("[red]Error:[/red] Passwords do not match.")
            raise typer.Exit(1)
    
    try:
        wallet_manager = WalletManager()
        address = wallet_manager.create_wallet(password or "", keystore_file)
        
        console.print(Panel(
            f"[green]✓ New wallet created successfully![/green]\n\n"
            f"Address: {address}\n"
            f"Keystore: {keystore_file}\n\n"
            f"[yellow]⚠️  Important:[/yellow]\n"
            f"• Keep your password safe - it cannot be recovered\n"
            f"• Back up your keystore file\n"
            f"• Fund your wallet with MON before deploying contracts\n"
            f"• Get testnet MON from: https://discord.gg/monaddev",
            title="Wallet Created",
            border_style="green"
        ))
    
    except Exception as e:
        console.print(f"[red]Error creating wallet:[/red] {str(e)}")
        raise typer.Exit(1)


@wallet_app.command()
def show(
    keystore_file: str = typer.Option("pymon_key.json", "--keystore", help="Keystore file path"),
) -> None:
    """Show wallet address and balance information."""
    try:
        wallet_manager = WalletManager()
        
        # Try to get address from environment variable first
        if os.getenv("PRIVATE_KEY"):
            address = wallet_manager.get_address_from_env()
            source = "Environment variable (PRIVATE_KEY)"
        else:
            if not Path(keystore_file).exists():
                console.print(f"[red]Error:[/red] Keystore file '{keystore_file}' not found.")
                console.print("Run 'pymon wallet new' to create a new wallet.")
                raise typer.Exit(1)
            
            password = typer.prompt(f"Enter password for {keystore_file}", hide_input=True)
            address = wallet_manager.load_wallet(keystore_file, password)
            source = f"Keystore file ({keystore_file})"
        
        console.print(Panel(
            f"[cyan]Wallet Information[/cyan]\n\n"
            f"Address: {address}\n"
            f"Source: {source}\n\n"
            f"[yellow]Note:[/yellow] Balance checking requires RPC connection.\n"
            f"Use 'pymon deploy --dry-run' to test connectivity.\n"
            f"Get testnet MON from: https://discord.gg/monaddev",
            title="Wallet Details",
            border_style="cyan"
        ))
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def interact(
    contract_name: str = typer.Argument(..., help="Name of the deployed contract"),
    function_name: str = typer.Argument(..., help="Function to call"),
    args: Optional[str] = typer.Option(None, "--args", "-a", help="Function arguments (comma-separated)"),
    view: bool = typer.Option(False, "--view", "-v", help="Call as view function (no transaction)"),
) -> None:
    """Interact with deployed smart contracts on Monad."""
    try:
        # Load configuration
        config_file = Path("pymon_config.json")
        if not config_file.exists():
            console.print("[red]Error:[/red] pymon_config.json not found. Run 'pymon init' first.")
            raise typer.Exit(1)
        
        with open(config_file) as f:
            config = json.load(f)
        
        # Initialize wallet
        wallet_manager = WalletManager()
        
        # Parse arguments
        parsed_args = []
        if args:
            parsed_args = [arg.strip() for arg in args.split(",")]
            # Try to convert to appropriate types
            for i, arg in enumerate(parsed_args):
                try:
                    # Try int first
                    if arg.isdigit():
                        parsed_args[i] = int(arg)
                    # Try float
                    elif "." in arg and arg.replace(".", "").isdigit():
                        parsed_args[i] = float(arg)
                    # Keep as string otherwise
                except ValueError:
                    pass
        
        # Call function
        result = interact_with_contract(
            contract_name=contract_name,
            function_name=function_name,
            args=parsed_args,
            config=config,
            wallet=wallet_manager,
            is_view=view
        )
        
        if result is None and not view:
            console.print("[red]Transaction failed![/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def info(
    contract_name: str = typer.Argument(..., help="Name of the deployed contract"),
) -> None:
    """Show information about a deployed contract on Monad."""
    try:
        # Load configuration
        config_file = Path("pymon_config.json")
        if not config_file.exists():
            console.print("[red]Error:[/red] pymon_config.json not found. Run 'pymon init' first.")
            raise typer.Exit(1)
        
        with open(config_file) as f:
            config = json.load(f)
        
        # Initialize wallet
        wallet_manager = WalletManager()
        
        # Show contract info
        show_contract_info(contract_name, config, wallet_manager)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@audit_app.command()
def contract(
    contract_name: str = typer.Argument(..., help="Name of the contract to audit"),
    fix: bool = typer.Option(False, "--fix", help="Automatically fix simple issues"),
    output: str = typer.Option(None, "--output", "-o", help="Save audit report to file")
):
    """Audit a smart contract for security vulnerabilities."""
    try:
        # Find contract file
        contract_file = Path(f"contracts/{contract_name}.py")
        if not contract_file.exists():
            console.print(f"[red]Contract '{contract_name}' not found in contracts/ directory[/red]")
            raise typer.Exit(1)
        
        console.print(Panel.fit(
            f"[bold cyan]🔍 Auditing Contract: {contract_name}[/bold cyan]\n"
            f"[yellow]Checking for security vulnerabilities...[/yellow]",
            title="Security Audit"
        ))
        
        # Perform audit
        report = audit_contract_file(str(contract_file))
        
        # Display report
        display_audit_report(report)
        
        # Save report if requested
        if output:
            report_data = {
                "contract": report.contract_name,
                "score": report.score,
                "passed": report.passed,
                "summary": report.summary,
                "findings": [
                    {
                        "type": f.vulnerability_type.value,
                        "severity": f.severity.value,
                        "location": f.location,
                        "line": f.line_number,
                        "description": f.description,
                        "recommendation": f.recommendation
                    }
                    for f in report.findings
                ]
            }
            
            output_file = Path(output)
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            console.print(f"[green]Audit report saved to {output_file}[/green]")
        
        # Exit with appropriate code
        if not report.passed:
            console.print("\n[red]⚠️ Contract has security issues that should be fixed before deployment![/red]")
            raise typer.Exit(1)
        else:
            console.print("\n[green]✅ Contract passed security audit![/green]")
    
    except Exception as e:
        console.print(f"[red]Audit error:[/red] {str(e)}")
        raise typer.Exit(1)


@audit_app.command()
def all():
    """Audit all contracts in the contracts/ directory."""
    try:
        contracts_dir = Path("contracts")
        if not contracts_dir.exists():
            console.print("[red]No contracts/ directory found[/red]")
            raise typer.Exit(1)
        
        contract_files = list(contracts_dir.glob("*.py"))
        if not contract_files:
            console.print("[yellow]No Python contracts found[/yellow]")
            return
        
        console.print(Panel.fit(
            f"[bold cyan]🔍 Auditing {len(contract_files)} Contracts[/bold cyan]",
            title="Batch Security Audit"
        ))
        
        results = []
        for contract_file in contract_files:
            contract_name = contract_file.stem
            console.print(f"\n[cyan]Auditing {contract_name}...[/cyan]")
            
            try:
                report = audit_contract_file(str(contract_file))
                results.append({
                    "contract": contract_name,
                    "score": report.score,
                    "passed": report.passed,
                    "issues": sum(report.summary.values())
                })
                
                # Show brief summary
                status = "✅" if report.passed else "❌"
                console.print(f"  {status} {contract_name}: Score {report.score}/100, {sum(report.summary.values())} issues")
                
            except Exception as e:
                console.print(f"  ❌ {contract_name}: Error - {str(e)}")
                results.append({
                    "contract": contract_name,
                    "score": 0,
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary table
        console.print("\n")
        summary_table = Table(title="Audit Summary")
        summary_table.add_column("Contract", style="cyan")
        summary_table.add_column("Score", style="yellow")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Issues", style="red")
        
        for result in results:
            status = "✅ Passed" if result.get("passed") else "❌ Failed"
            issues = str(result.get("issues", "Error"))
            summary_table.add_row(
                result["contract"],
                f"{result['score']}/100",
                status,
                issues
            )
        
        console.print(summary_table)
        
        # Overall summary
        passed_count = sum(1 for r in results if r.get("passed"))
        total_count = len(results)
        
        if passed_count == total_count:
            console.print(f"\n[green]✅ All {total_count} contracts passed audit![/green]")
        else:
            console.print(f"\n[yellow]⚠️ {passed_count}/{total_count} contracts passed audit[/yellow]")
            console.print("[red]Fix security issues in failed contracts before deployment[/red]")
    
    except Exception as e:
        console.print(f"[red]Batch audit error:[/red] {str(e)}")
        raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
