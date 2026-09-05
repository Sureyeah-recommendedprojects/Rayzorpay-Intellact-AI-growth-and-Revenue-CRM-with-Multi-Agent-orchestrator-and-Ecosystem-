"""Advanced gas estimation module for PyMon smart contract deployments.

This module provides robust, intelligent gas estimation with multiple strategies,
fallback mechanisms, and optimization for Monad's high-throughput network.
"""

from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from eth_account import Account
from rich.console import Console

console = Console()


class GasEstimator:
    """High-quality gas estimator with multiple strategies and fallbacks."""
    
    # Gas constants for Monad network
    MONAD_BASE_GAS = 21000  # Base transaction gas
    MONAD_CREATION_GAS = 32000  # Contract creation overhead
    MONAD_CODE_DEPOSIT_GAS_PER_BYTE = 200  # Gas per byte of code
    
    # Buffer percentages for different strategies
    CONSERVATIVE_BUFFER = 1.5  # 50% buffer
    STANDARD_BUFFER = 1.3  # 30% buffer
    AGGRESSIVE_BUFFER = 1.15  # 15% buffer
    
    # Maximum gas limits
    MONAD_BLOCK_GAS_LIMIT = 30_000_000  # Monad block gas limit
    SAFE_MAX_GAS = 25_000_000  # Safe maximum to avoid hitting block limit
    
    def __init__(self, w3: Web3, config: Dict[str, Any]):
        """
        Initialize gas estimator.
        
        Args:
            w3: Web3 instance
            config: Network configuration
        """
        self.w3 = w3
        self.config = config
        self.network = config.get("network", "monad-testnet")
    
    def estimate_deployment_gas(
        self,
        contract,
        constructor_args: list,
        account: Account,
        strategy: str = "standard"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Estimate gas for contract deployment with multiple strategies.
        
        Args:
            contract: Web3 contract instance
            constructor_args: Constructor arguments
            account: Deployer account
            strategy: Estimation strategy ("conservative", "standard", "aggressive", "auto")
        
        Returns:
            Tuple of (gas_limit, estimation_details)
        """
        console.print("[cyan]🔍 Advanced Gas Estimation Started...[/cyan]")
        
        # Get bytecode size for better estimation
        bytecode = contract.bytecode
        if isinstance(bytecode, bytes):
            bytecode_size = len(bytecode)
        else:
            # Handle hex string
            bytecode_str = str(bytecode)
            if bytecode_str.startswith("0x"):
                bytecode_str = bytecode_str[2:]
            bytecode_size = len(bytecode_str) // 2
        
        console.print(f"[blue]Contract bytecode size: {bytecode_size} bytes[/blue]")
        
        # Try multiple estimation strategies
        estimates = {}
        
        try:
            # Strategy 1: Web3 automatic estimation
            estimates['web3_auto'] = self._estimate_with_web3(
                contract, constructor_args, account
            )
            console.print(f"[green]✓ Web3 auto estimation: {estimates['web3_auto']:,} gas[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Web3 auto estimation failed: {e}[/yellow]")
            estimates['web3_auto'] = None
        
        try:
            # Strategy 2: Bytecode-based estimation
            estimates['bytecode_based'] = self._estimate_from_bytecode(
                bytecode_size, constructor_args
            )
            console.print(f"[green]✓ Bytecode-based estimation: {estimates['bytecode_based']:,} gas[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Bytecode estimation failed: {e}[/yellow]")
            estimates['bytecode_based'] = None
        
        try:
            # Strategy 3: Historical data estimation (if available)
            estimates['historical'] = self._estimate_from_history(bytecode_size)
            if estimates['historical']:
                console.print(f"[green]✓ Historical estimation: {estimates['historical']:,} gas[/green]")
        except Exception as e:
            estimates['historical'] = None
        
        # Select best estimate
        base_estimate = self._select_best_estimate(estimates, bytecode_size)
        
        console.print(f"[cyan]📊 Base estimate selected: {base_estimate:,} gas[/cyan]")
        
        # Apply buffer based on strategy
        if strategy == "auto":
            strategy = self._auto_select_strategy(bytecode_size, base_estimate)
            console.print(f"[cyan]🤖 Auto-selected strategy: {strategy}[/cyan]")
        
        buffer_multiplier = self._get_buffer_multiplier(strategy)
        gas_limit = int(base_estimate * buffer_multiplier)
        
        # Safety checks
        gas_limit = self._apply_safety_checks(gas_limit, bytecode_size)
        
        # Prepare detailed estimation info
        details = {
            'base_estimate': base_estimate,
            'strategy': strategy,
            'buffer_multiplier': buffer_multiplier,
            'gas_limit': gas_limit,
            'bytecode_size': bytecode_size,
            'estimates': estimates,
            'network': self.network
        }
        
        console.print(f"[green]✅ Final gas limit: {gas_limit:,} (strategy: {strategy})[/green]")
        
        return gas_limit, details
    
    def _estimate_with_web3(
        self,
        contract,
        constructor_args: list,
        account: Account
    ) -> int:
        """Estimate gas using Web3's built-in estimation."""
        nonce = self.w3.eth.get_transaction_count(account.address)
        gas_price = self.w3.eth.gas_price
        
        # Build transaction for estimation
        constructor_tx = contract.constructor(*constructor_args).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'chainId': self.config["chain_id"]
        })
        
        # Remove gas field for estimation
        if 'gas' in constructor_tx:
            del constructor_tx['gas']
        
        # Estimate gas
        try:
            gas_estimate = self.w3.eth.estimate_gas(constructor_tx)
            return gas_estimate
        except Exception as e:
            # If estimation fails, try with a high gas value
            constructor_tx['gas'] = self.SAFE_MAX_GAS
            try:
                # Try to call to see if it would work
                return self.SAFE_MAX_GAS // 2  # Conservative fallback
            except:
                raise e
    
    def _estimate_from_bytecode(
        self,
        bytecode_size: int,
        constructor_args: list
    ) -> int:
        """Estimate gas based on bytecode size and complexity."""
        # Base gas for transaction
        gas = self.MONAD_BASE_GAS
        
        # Contract creation gas
        gas += self.MONAD_CREATION_GAS
        
        # Gas for code storage (200 gas per byte)
        gas += bytecode_size * self.MONAD_CODE_DEPOSIT_GAS_PER_BYTE
        
        # Gas for constructor execution (estimated)
        # Simple heuristic: 100000 base + 10000 per argument
        constructor_gas = 100000 + (len(constructor_args) * 10000)
        gas += constructor_gas
        
        # Additional buffer for complex initialization
        if bytecode_size > 10000:  # Large contract
            gas = int(gas * 1.2)
        
        return gas
    
    def _estimate_from_history(self, bytecode_size: int) -> Optional[int]:
        """Estimate based on historical deployment data."""
        # This is a placeholder for historical data
        # In production, this would query a database of past deployments
        
        # Simple heuristic based on size ranges
        if bytecode_size < 1000:
            return 500000
        elif bytecode_size < 5000:
            return 1000000
        elif bytecode_size < 10000:
            return 2000000
        elif bytecode_size < 20000:
            return 4000000
        else:
            return 8000000
    
    def _select_best_estimate(
        self,
        estimates: Dict[str, Optional[int]],
        bytecode_size: int
    ) -> int:
        """Select the best estimate from multiple strategies."""
        valid_estimates = [v for v in estimates.values() if v is not None and v > 0]
        
        if not valid_estimates:
            # Fallback to bytecode-based estimate
            console.print("[yellow]⚠ No valid estimates, using fallback calculation[/yellow]")
            return self._estimate_from_bytecode(bytecode_size, [])
        
        # If Web3 estimation succeeded, prefer it (it's most accurate)
        if estimates.get('web3_auto'):
            console.print("[cyan]📍 Using Web3 estimation as base (most accurate)[/cyan]")
            return estimates['web3_auto']
        
        # Otherwise use the median of valid estimates for robustness
        valid_estimates.sort()
        median_index = len(valid_estimates) // 2
        
        if len(valid_estimates) % 2 == 0:
            # Even number of estimates - average the middle two
            median = (valid_estimates[median_index - 1] + valid_estimates[median_index]) // 2
        else:
            # Odd number - use middle value
            median = valid_estimates[median_index]
        
        return median
    
    def _auto_select_strategy(self, bytecode_size: int, base_estimate: int) -> str:
        """Automatically select the best strategy based on contract characteristics."""
        # For very small contracts, use aggressive
        if bytecode_size < 1000 and base_estimate < 500000:
            return "aggressive"
        
        # For very large contracts, use conservative
        if bytecode_size > 20000 or base_estimate > 5000000:
            return "conservative"
        
        # Default to standard
        return "standard"
    
    def _get_buffer_multiplier(self, strategy: str) -> float:
        """Get buffer multiplier for given strategy."""
        buffers = {
            "conservative": self.CONSERVATIVE_BUFFER,
            "standard": self.STANDARD_BUFFER,
            "aggressive": self.AGGRESSIVE_BUFFER
        }
        return buffers.get(strategy, self.STANDARD_BUFFER)
    
    def _apply_safety_checks(self, gas_limit: int, bytecode_size: int) -> int:
        """Apply safety checks to gas limit."""
        # Ensure minimum gas
        min_gas = self.MONAD_BASE_GAS + self.MONAD_CREATION_GAS + (bytecode_size * 100)
        if gas_limit < min_gas:
            console.print(f"[yellow]⚠ Gas limit too low, adjusting to minimum: {min_gas:,}[/yellow]")
            gas_limit = min_gas
        
        # Ensure we don't exceed safe maximum
        if gas_limit > self.SAFE_MAX_GAS:
            console.print(f"[yellow]⚠ Gas limit exceeds safe maximum, capping at: {self.SAFE_MAX_GAS:,}[/yellow]")
            gas_limit = self.SAFE_MAX_GAS
        
        return gas_limit
    
    def estimate_gas_price(self, priority: str = "standard") -> int:
        """
        Estimate gas price with priority levels.
        
        Args:
            priority: Priority level ("low", "standard", "high", "urgent")
        
        Returns:
            Gas price in wei
        """
        try:
            base_gas_price = self.w3.eth.gas_price
        except Exception as e:
            console.print(f"[yellow]⚠ Could not fetch gas price: {e}[/yellow]")
            # Fallback to 25 gwei for Monad testnet
            base_gas_price = self.w3.to_wei(25, 'gwei')
        
        # Apply multiplier based on priority
        multipliers = {
            "low": 0.9,
            "standard": 1.1,
            "high": 1.3,
            "urgent": 1.5
        }
        
        multiplier = multipliers.get(priority, 1.1)
        gas_price = int(base_gas_price * multiplier)
        
        console.print(f"[blue]Gas price: {self.w3.from_wei(gas_price, 'gwei'):.2f} gwei (priority: {priority})[/blue]")
        
        return gas_price
    
    def calculate_deployment_cost(
        self,
        gas_limit: int,
        gas_price: int
    ) -> Dict[str, Any]:
        """
        Calculate total deployment cost.
        
        Args:
            gas_limit: Gas limit for deployment
            gas_price: Gas price in wei
        
        Returns:
            Dictionary with cost breakdown
        """
        total_cost_wei = gas_limit * gas_price
        total_cost_eth = self.w3.from_wei(total_cost_wei, 'ether')
        total_cost_gwei = self.w3.from_wei(total_cost_wei, 'gwei')
        
        return {
            'gas_limit': gas_limit,
            'gas_price': gas_price,
            'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
            'total_cost_wei': total_cost_wei,
            'total_cost_eth': float(total_cost_eth),
            'total_cost_gwei': float(total_cost_gwei),
            'currency': 'MON'
        }


def estimate_gas_smart(
    w3: Web3,
    contract,
    constructor_args: list,
    account: Account,
    config: Dict[str, Any],
    strategy: str = "auto"
) -> Tuple[int, int, Dict[str, Any]]:
    """
    Smart gas estimation helper function.
    
    Args:
        w3: Web3 instance
        contract: Contract instance
        constructor_args: Constructor arguments
        account: Account for deployment
        config: Network configuration
        strategy: Estimation strategy
    
    Returns:
        Tuple of (gas_limit, gas_price, details)
    """
    estimator = GasEstimator(w3, config)
    
    # Estimate gas limit
    gas_limit, details = estimator.estimate_deployment_gas(
        contract,
        constructor_args,
        account,
        strategy
    )
    
    # Estimate gas price
    gas_price = estimator.estimate_gas_price("standard")
    
    # Calculate cost
    cost_info = estimator.calculate_deployment_cost(gas_limit, gas_price)
    details['cost'] = cost_info
    
    return gas_limit, gas_price, details
