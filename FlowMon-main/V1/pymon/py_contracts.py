"""Python smart contract base classes and examples."""

from typing import Any, Dict
from dataclasses import dataclass


class PySmartContract:
    """Enhanced base class for Python smart contracts with DeFi support."""
    
    def __init__(self):
        self._state = {}
        self._storage_slots = {}
        self._slot_counter = 0
    
    def state_var(self, name: str, initial_value: Any = 0):
        """Declare a state variable."""
        slot = self._slot_counter
        self._storage_slots[name] = slot
        self._state[name] = initial_value
        self._slot_counter += 1
        setattr(self, name, initial_value)
        return initial_value
    
    def public_function(self, func):
        """Decorator for public functions."""
        func._is_public = True
        return func
    
    def view_function(self, func):
        """Decorator for view functions."""
        func._is_view = True
        return func
    
    def event(self, name: str, *params):
        """Emit an event."""
        pass  # Events are handled during transpilation
    
    def msg_sender(self) -> str:
        """Get message sender address (simulated)."""
        return "0x0000000000000000000000000000000000000000"  # Placeholder
    
    def block_number(self) -> int:
        """Get current block number (simulated)."""
        return 1  # Placeholder
    
    def require(self, condition: bool, message: str = "Requirement failed"):
        """Require condition to be true, otherwise revert."""
        if not condition:
            raise Exception(message)


# Example Python smart contracts

class SimpleStorage(PySmartContract):
    """Simple storage contract example."""
    
    def __init__(self):
        super().__init__()
        self.stored_data = self.state_var("stored_data", 0)
    
    @PySmartContract.public_function
    def set(self, value: int):
        """Set stored data."""
        self.stored_data = value
        self.event("DataStored", value)
    
    @PySmartContract.view_function
    def get(self) -> int:
        """Get stored data."""
        return self.stored_data


class Counter(PySmartContract):
    """Counter contract example."""
    
    def __init__(self):
        super().__init__()
        self.count = self.state_var("count", 0)
        self.owner = self.state_var("owner", 0)  # Will be set to msg.sender
    
    @PySmartContract.public_function
    def increment(self):
        """Increment counter."""
        self.count = self.count + 1
        self.event("Incremented", self.count)
    
    @PySmartContract.public_function
    def decrement(self):
        """Decrement counter."""
        if self.count > 0:
            self.count = self.count - 1
            self.event("Decremented", self.count)
    
    @PySmartContract.view_function
    def get_count(self) -> int:
        """Get current count."""
        return self.count
    
    @PySmartContract.public_function
    def reset(self):
        """Reset counter to zero."""
        self.count = 0
        self.event("Reset")


class BasicToken(PySmartContract):
    """Basic token contract example."""
    
    def __init__(self):
        super().__init__()
        self.total_supply = self.state_var("total_supply", 1000000)
        self.name = "PyToken"
        self.symbol = "PYT"
        # Note: In a real implementation, balances would be a mapping
        # For simplicity, we'll use single balance for demo
        self.balance = self.state_var("balance", 1000000)
    
    @PySmartContract.view_function
    def get_total_supply(self) -> int:
        """Get total token supply."""
        return self.total_supply
    
    @PySmartContract.view_function
    def get_balance(self) -> int:
        """Get token balance."""
        return self.balance
    
    @PySmartContract.public_function
    def transfer(self, amount: int):
        """Transfer tokens (simplified)."""
        if self.balance >= amount:
            self.balance = self.balance - amount
            self.event("Transfer", amount)


class DeFiContract(PySmartContract):
    """Enhanced DeFi contract with mapping support."""
    
    def __init__(self):
        super().__init__()
        self.admin = self.state_var("admin", self.msg_sender())
        self.balances = self.state_var("balances", {})
        self.total_deposits = self.state_var("total_deposits", 0)
        self.interest_rate = self.state_var("interest_rate", 5)
    
    @PySmartContract.public_function
    def deposit(self, amount: int):
        """Deposit tokens into the pool."""
        sender = self.msg_sender()
        self.require(amount > 0, "Amount must be positive")
        
        current_balance = self.balances.get(sender, 0)
        self.balances[sender] = current_balance + amount
        self.total_deposits = self.total_deposits + amount
        
        self.event("Deposit", sender, amount)
    
    @PySmartContract.public_function
    def withdraw(self, amount: int):
        """Withdraw tokens from the pool."""
        sender = self.msg_sender()
        current_balance = self.balances.get(sender, 0)
        
        self.require(current_balance >= amount, "Insufficient balance")
        
        self.balances[sender] = current_balance - amount
        self.total_deposits = self.total_deposits - amount
        
        self.event("Withdraw", sender, amount)
    
    @PySmartContract.view_function
    def balance_of(self, user: str) -> int:
        """Get user balance."""
        return self.balances.get(user, 0)
    
    @PySmartContract.view_function
    def get_total_deposits(self) -> int:
        """Get total deposits."""
        return self.total_deposits
    
    @PySmartContract.public_function
    def set_interest_rate(self, new_rate: int):
        """Set new interest rate (admin only)."""
        sender = self.msg_sender()
        self.require(sender == self.admin, "Only admin can set rate")
        self.interest_rate = new_rate
        self.event("RateChanged", new_rate)


def get_sample_contracts() -> Dict[str, str]:
    """Get sample Python smart contract source code."""
    
    simple_storage_source = '''
class SimpleStorage(PySmartContract):
    """Simple storage contract in Python."""
    
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
    
    defi_contract_source = '''
class DeFiContract(PySmartContract):
    """Enhanced DeFi contract with mapping support."""
    
    def __init__(self):
        super().__init__()
        self.admin = self.state_var("admin", self.msg_sender())
        self.balances = self.state_var("balances", {})
        self.total_deposits = self.state_var("total_deposits", 0)
        self.interest_rate = self.state_var("interest_rate", 5)
    
    @public_function
    def deposit(self, amount: int):
        """Deposit tokens into the pool."""
        sender = self.msg_sender()
        self.require(amount > 0, "Amount must be positive")
        
        current_balance = self.balances.get(sender, 0)
        self.balances[sender] = current_balance + amount
        self.total_deposits = self.total_deposits + amount
        
        self.event("Deposit", sender, amount)
    
    @public_function
    def withdraw(self, amount: int):
        """Withdraw tokens from the pool."""
        sender = self.msg_sender()
        current_balance = self.balances.get(sender, 0)
        
        self.require(current_balance >= amount, "Insufficient balance")
        
        self.balances[sender] = current_balance - amount
        self.total_deposits = self.total_deposits - amount
        
        self.event("Withdraw", sender, amount)
    
    @view_function
    def balance_of(self, user: str) -> int:
        """Get user balance."""
        return self.balances.get(user, 0)
    
    @view_function
    def get_total_deposits(self) -> int:
        """Get total deposits."""
        return self.total_deposits
    
    @public_function
    def set_interest_rate(self, new_rate: int):
        """Set new interest rate (admin only)."""
        sender = self.msg_sender()
        self.require(sender == self.admin, "Only admin can set rate")
        self.interest_rate = new_rate
        self.event("RateChanged", new_rate)
'''
    
    return {
        "SimpleStorage": simple_storage_source,
        "DeFiContract": defi_contract_source
    }