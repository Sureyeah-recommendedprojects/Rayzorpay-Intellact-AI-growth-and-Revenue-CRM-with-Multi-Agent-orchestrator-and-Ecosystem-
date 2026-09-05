from pymon.py_contracts import PySmartContract

class Counter(PySmartContract):
    """Counter contract written in Python."""
    
    def __init__(self):
        super().__init__()
        self.count = self.state_var("count", 0)
    
    @public_function
    def increment(self):
        """Increment counter."""
        self.count = self.count + 1
        self.event("Incremented", self.count)
    
    @public_function
    def decrement(self):
        """Decrement counter."""
        if self.count > 0:
            self.count = self.count - 1
            self.event("Decremented", self.count)
    
    @view_function
    def get_count(self) -> int:
        """Get current count."""
        return self.count
    
    @public_function
    def reset(self):
        """Reset counter to zero."""
        self.count = 0
        self.event("Reset")
