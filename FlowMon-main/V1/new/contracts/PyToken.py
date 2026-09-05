from pymon.py_contracts import PySmartContract

class PyToken(PySmartContract):
    """
    PyToken - ERC20-compatible token with public minting on Monad Blockchain.
    
    Features:
    - ERC20 standard compliance
    - Public minting (anyone can mint)
    - Maximum supply cap of 2000 tokens
    - Mint directly from Monad Explorer
    - Transfer, approve, and transferFrom functions
    - Burn functionality
    """
    
    def __init__(self):
        """Initialize PyToken with token parameters."""
        super().__init__()
        
        # Token metadata
        self.name = self.state_var("name", "PyToken")
        self.symbol = self.state_var("symbol", "PYT")
        self.decimals = self.state_var("decimals", 18)
        
        # Token supply management
        self.total_supply = self.state_var("total_supply", 0)
        self.max_supply = self.state_var("max_supply", 2000 * 10**18)  # 2000 tokens with 18 decimals
        
        # Balances and allowances (mappings)
        self.balances = self.state_var("balances", {})  # address -> balance
        self.allowances = self.state_var("allowances", {})  # owner -> spender -> amount
        
        # Minting tracking
        self.total_minted = self.state_var("total_minted", 0)
        self.mint_count = self.state_var("mint_count", 0)  # Track number of mints
        self.minters = self.state_var("minters", {})  # address -> amount minted
        
        # Optional: Mint limits per address
        self.max_mint_per_address = self.state_var("max_mint_per_address", 100 * 10**18)  # 100 tokens max per address
        self.mint_amount_per_call = self.state_var("mint_amount_per_call", 10 * 10**18)  # 10 tokens per mint call
        
        # Contract owner (for optional admin functions)
        self.owner = self.state_var("owner", msg.sender)
        
        # Pause state for emergency
        self.paused = self.state_var("paused", False)
    
    # ============ ERC20 Core Functions ============
    
    @view_function
    def totalSupply(self) -> int:
        """Returns the total token supply."""
        return self.total_supply
    
    @view_function
    def balanceOf(self, account: str) -> int:
        """Returns the balance of an account."""
        return self.balances.get(account, 0)
    
    @public_function
    def transfer(self, recipient: str, amount: int) -> bool:
        """
        Transfer tokens to a recipient.
        
        Args:
            recipient: Address to receive tokens
            amount: Amount of tokens to transfer
        
        Returns:
            True if successful
        """
        require(not self.paused, "Token transfers are paused")
        require(recipient != address(0), "Cannot transfer to zero address")
        require(amount > 0, "Transfer amount must be positive")
        
        sender = msg.sender
        sender_balance = self.balances.get(sender, 0)
        
        require(sender_balance >= amount, "Insufficient balance")
        
        # Update balances
        self.balances[sender] = sender_balance - amount
        self.balances[recipient] = self.balances.get(recipient, 0) + amount
        
        # Emit transfer event
        self.event("Transfer", sender, recipient, amount)
        
        return True
    
    @public_function
    def approve(self, spender: str, amount: int) -> bool:
        """
        Approve a spender to use tokens.
        
        Args:
            spender: Address allowed to spend tokens
            amount: Amount of tokens approved
        
        Returns:
            True if successful
        """
        require(not self.paused, "Token approvals are paused")
        require(spender != address(0), "Cannot approve zero address")
        
        owner = msg.sender
        
        # Set allowance
        if owner not in self.allowances:
            self.allowances[owner] = {}
        self.allowances[owner][spender] = amount
        
        # Emit approval event
        self.event("Approval", owner, spender, amount)
        
        return True
    
    @public_function
    def transferFrom(self, sender: str, recipient: str, amount: int) -> bool:
        """
        Transfer tokens on behalf of another account.
        
        Args:
            sender: Address to transfer from
            recipient: Address to receive tokens
            amount: Amount of tokens to transfer
        
        Returns:
            True if successful
        """
        require(not self.paused, "Token transfers are paused")
        require(recipient != address(0), "Cannot transfer to zero address")
        require(amount > 0, "Transfer amount must be positive")
        
        # Check allowance
        spender = msg.sender
        current_allowance = 0
        if sender in self.allowances and spender in self.allowances[sender]:
            current_allowance = self.allowances[sender][spender]
        
        require(current_allowance >= amount, "Insufficient allowance")
        
        # Check balance
        sender_balance = self.balances.get(sender, 0)
        require(sender_balance >= amount, "Insufficient balance")
        
        # Update balances
        self.balances[sender] = sender_balance - amount
        self.balances[recipient] = self.balances.get(recipient, 0) + amount
        
        # Update allowance (if not unlimited)
        if current_allowance != 2**256 - 1:  # Max uint256 means unlimited
            self.allowances[sender][spender] = current_allowance - amount
        
        # Emit transfer event
        self.event("Transfer", sender, recipient, amount)
        
        return True
    
    @view_function
    def allowance(self, owner: str, spender: str) -> int:
        """
        Check the allowance of a spender for an owner.
        
        Args:
            owner: Token owner address
            spender: Spender address
        
        Returns:
            Amount of tokens approved
        """
        if owner in self.allowances and spender in self.allowances[owner]:
            return self.allowances[owner][spender]
        return 0
    
    # ============ Minting Functions (PUBLIC - Anyone Can Mint!) ============
    
    @public_function
    def mint(self) -> bool:
        """
        PUBLIC MINT FUNCTION - Anyone can mint tokens!
        Mints a fixed amount of tokens to the caller.
        Can be called directly from Monad Explorer.
        
        Returns:
            True if successful
        """
        require(not self.paused, "Minting is paused")
        
        minter = msg.sender
        mint_amount = self.mint_amount_per_call  # 10 tokens per call
        
        # Check max supply
        require(self.total_supply + mint_amount <= self.max_supply, "Would exceed max supply")
        
        # Check per-address limit
        already_minted = self.minters.get(minter, 0)
        require(already_minted + mint_amount <= self.max_mint_per_address, "Exceeds per-address mint limit")
        
        # Mint tokens
        self.balances[minter] = self.balances.get(minter, 0) + mint_amount
        self.total_supply = self.total_supply + mint_amount
        self.total_minted = self.total_minted + mint_amount
        self.mint_count = self.mint_count + 1
        self.minters[minter] = already_minted + mint_amount
        
        # Emit mint event
        self.event("Mint", minter, mint_amount, self.total_supply)
        self.event("Transfer", address(0), minter, mint_amount)  # ERC20 standard
        
        return True
    
    @public_function
    def mintAmount(self, amount: int) -> bool:
        """
        Mint a specific amount of tokens (within limits).
        
        Args:
            amount: Amount of tokens to mint
        
        Returns:
            True if successful
        """
        require(not self.paused, "Minting is paused")
        require(amount > 0, "Amount must be positive")
        require(amount <= self.mint_amount_per_call, "Amount exceeds per-call limit")
        
        minter = msg.sender
        
        # Check max supply
        require(self.total_supply + amount <= self.max_supply, "Would exceed max supply")
        
        # Check per-address limit
        already_minted = self.minters.get(minter, 0)
        require(already_minted + amount <= self.max_mint_per_address, "Exceeds per-address mint limit")
        
        # Mint tokens
        self.balances[minter] = self.balances.get(minter, 0) + amount
        self.total_supply = self.total_supply + amount
        self.total_minted = self.total_minted + amount
        self.mint_count = self.mint_count + 1
        self.minters[minter] = already_minted + amount
        
        # Emit events
        self.event("Mint", minter, amount, self.total_supply)
        self.event("Transfer", address(0), minter, amount)
        
        return True
    
    # ============ Burn Functions ============
    
    @public_function
    def burn(self, amount: int) -> bool:
        """
        Burn tokens from caller's balance.
        
        Args:
            amount: Amount of tokens to burn
        
        Returns:
            True if successful
        """
        require(not self.paused, "Burning is paused")
        require(amount > 0, "Burn amount must be positive")
        
        burner = msg.sender
        burner_balance = self.balances.get(burner, 0)
        
        require(burner_balance >= amount, "Insufficient balance to burn")
        
        # Burn tokens
        self.balances[burner] = burner_balance - amount
        self.total_supply = self.total_supply - amount
        
        # Emit burn event
        self.event("Burn", burner, amount, self.total_supply)
        self.event("Transfer", burner, address(0), amount)  # ERC20 standard
        
        return True
    
    # ============ View Functions ============
    
    @view_function
    def name(self) -> str:
        """Returns the token name."""
        return self.name
    
    @view_function
    def symbol(self) -> str:
        """Returns the token symbol."""
        return self.symbol
    
    @view_function
    def decimals(self) -> int:
        """Returns the number of decimals."""
        return self.decimals
    
    @view_function
    def maxSupply(self) -> int:
        """Returns the maximum supply cap."""
        return self.max_supply
    
    @view_function
    def remainingMintable(self) -> int:
        """Returns how many tokens can still be minted."""
        return self.max_supply - self.total_supply
    
    @view_function
    def getMintInfo(self, account: str) -> dict:
        """
        Get minting information for an account.
        
        Args:
            account: Address to check
        
        Returns:
            Dictionary with mint info
        """
        already_minted = self.minters.get(account, 0)
        can_mint = self.max_mint_per_address - already_minted
        
        return {
            "already_minted": already_minted,
            "can_still_mint": can_mint,
            "mint_limit": self.max_mint_per_address,
            "mint_per_call": self.mint_amount_per_call,
            "total_remaining": self.remainingMintable()
        }
    
    @view_function
    def getTokenStats(self) -> dict:
        """Get overall token statistics."""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "total_supply": self.total_supply,
            "max_supply": self.max_supply,
            "total_minted": self.total_minted,
            "mint_count": self.mint_count,
            "remaining_mintable": self.remainingMintable(),
            "mint_per_call": self.mint_amount_per_call,
            "max_per_address": self.max_mint_per_address,
            "paused": self.paused
        }
    
    # ============ Optional Admin Functions ============
    
    @public_function
    def setMintAmountPerCall(self, amount: int):
        """Set the amount mintable per call (owner only)."""
        require(msg.sender == self.owner, "Only owner can set mint amount")
        require(amount > 0 and amount <= 100 * 10**18, "Invalid mint amount")
        
        old_amount = self.mint_amount_per_call
        self.mint_amount_per_call = amount
        
        self.event("MintAmountUpdated", old_amount, amount)
    
    @public_function
    def setMaxMintPerAddress(self, amount: int):
        """Set the maximum mint limit per address (owner only)."""
        require(msg.sender == self.owner, "Only owner can set limit")
        require(amount > 0 and amount <= self.max_supply, "Invalid limit")
        
        old_limit = self.max_mint_per_address
        self.max_mint_per_address = amount
        
        self.event("MintLimitUpdated", old_limit, amount)
    
    @public_function
    def pause(self):
        """Pause all token operations (owner only)."""
        require(msg.sender == self.owner, "Only owner can pause")
        require(not self.paused, "Already paused")
        
        self.paused = True
        self.event("Paused", msg.sender)
    
    @public_function
    def unpause(self):
        """Unpause token operations (owner only)."""
        require(msg.sender == self.owner, "Only owner can unpause")
        require(self.paused, "Not paused")
        
        self.paused = False
        self.event("Unpaused", msg.sender)
    
    # ============ Helper Functions ============
    
    @view_function
    def formatBalance(self, account: str) -> str:
        """
        Format balance in human-readable form.
        
        Args:
            account: Address to check
        
        Returns:
            Formatted balance string
        """
        balance = self.balances.get(account, 0)
        # Convert from wei to tokens (18 decimals)
        tokens = balance // 10**18
        decimals = (balance % 10**18) // 10**16  # Show 2 decimal places
        
        return f"{tokens}.{decimals:02d} {self.symbol}"
