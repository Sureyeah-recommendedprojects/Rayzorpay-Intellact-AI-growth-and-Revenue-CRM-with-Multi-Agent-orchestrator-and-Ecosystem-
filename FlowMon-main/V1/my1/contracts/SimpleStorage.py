from pymon.py_contracts import PySmartContract

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
