from pymon.py_contracts import PySmartContract

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
