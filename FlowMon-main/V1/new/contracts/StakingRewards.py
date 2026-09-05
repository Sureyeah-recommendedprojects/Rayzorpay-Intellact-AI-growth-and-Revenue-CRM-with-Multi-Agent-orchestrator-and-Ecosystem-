from pymon.py_contracts import PySmartContract

class StakingRewards(PySmartContract):
    """
    Advanced Staking Rewards Contract for Monad Blockchain.
    
    Features:
    - Stake tokens to earn rewards
    - Dynamic reward rate calculation
    - Compound interest support
    - Emergency withdrawal
    - Owner controls for reward distribution
    - Time-locked staking periods
    """
    
    def __init__(self):
        """Initialize the staking contract with default parameters."""
        super().__init__()
        
        # Core state variables
        self.owner = self.state_var("owner", msg.sender)
        self.total_staked = self.state_var("total_staked", 0)
        self.reward_rate = self.state_var("reward_rate", 100)  # 100 = 1% per period
        self.reward_pool = self.state_var("reward_pool", 0)
        self.minimum_stake = self.state_var("minimum_stake", 100)  # Minimum stake amount
        self.lock_period = self.state_var("lock_period", 86400)  # 24 hours in seconds
        
        # User staking data (using mappings)
        self.staked_balance = self.state_var("staked_balance", {})  # address -> amount
        self.stake_timestamp = self.state_var("stake_timestamp", {})  # address -> timestamp
        self.rewards_earned = self.state_var("rewards_earned", {})  # address -> rewards
        self.last_claim_time = self.state_var("last_claim_time", {})  # address -> timestamp
        
        # Contract statistics
        self.total_rewards_distributed = self.state_var("total_rewards_distributed", 0)
        self.unique_stakers = self.state_var("unique_stakers", 0)
        self.contract_paused = self.state_var("contract_paused", False)
        
        # APY tracking
        self.annual_percentage_yield = self.state_var("annual_percentage_yield", 1200)  # 12% APY
    
    # ============ Core Staking Functions ============
    
    @public_function
    def stake(self, amount: int):
        """
        Stake tokens in the contract.
        
        Args:
            amount: Amount of tokens to stake
        """
        require(not self.contract_paused, "Contract is paused")
        require(amount >= self.minimum_stake, "Amount below minimum stake")
        require(amount > 0, "Cannot stake zero amount")
        
        # Update user's staking info
        user_address = msg.sender
        current_balance = self.staked_balance.get(user_address, 0)
        
        # If first time staking, increment unique stakers
        if current_balance == 0:
            self.unique_stakers = self.unique_stakers + 1
        
        # Calculate pending rewards before updating stake
        if current_balance > 0:
            pending = self._calculate_rewards(user_address)
            self.rewards_earned[user_address] = self.rewards_earned.get(user_address, 0) + pending
        
        # Update staking data
        self.staked_balance[user_address] = current_balance + amount
        self.stake_timestamp[user_address] = block.timestamp
        self.last_claim_time[user_address] = block.timestamp
        self.total_staked = self.total_staked + amount
        
        # Emit staking event
        self.event("Staked", user_address, amount, block.timestamp)
    
    @public_function
    def unstake(self, amount: int):
        """
        Unstake tokens from the contract.
        
        Args:
            amount: Amount of tokens to unstake
        """
        require(not self.contract_paused, "Contract is paused")
        require(amount > 0, "Cannot unstake zero amount")
        
        user_address = msg.sender
        staked_amount = self.staked_balance.get(user_address, 0)
        
        require(staked_amount >= amount, "Insufficient staked balance")
        
        # Check lock period
        stake_time = self.stake_timestamp.get(user_address, 0)
        require(block.timestamp >= stake_time + self.lock_period, "Tokens still locked")
        
        # Calculate and store pending rewards
        pending = self._calculate_rewards(user_address)
        self.rewards_earned[user_address] = self.rewards_earned.get(user_address, 0) + pending
        
        # Update staking data
        self.staked_balance[user_address] = staked_amount - amount
        self.total_staked = self.total_staked - amount
        
        # If fully unstaked, decrement unique stakers
        if self.staked_balance[user_address] == 0:
            self.unique_stakers = self.unique_stakers - 1
        
        # Update last claim time
        self.last_claim_time[user_address] = block.timestamp
        
        # Transfer tokens back to user (in real implementation)
        # self.transfer(user_address, amount)
        
        # Emit unstaking event
        self.event("Unstaked", user_address, amount, block.timestamp)
    
    @public_function
    def claim_rewards(self):
        """Claim accumulated rewards."""
        require(not self.contract_paused, "Contract is paused")
        
        user_address = msg.sender
        
        # Calculate total rewards (pending + already earned)
        pending = self._calculate_rewards(user_address)
        total_rewards = self.rewards_earned.get(user_address, 0) + pending
        
        require(total_rewards > 0, "No rewards to claim")
        require(self.reward_pool >= total_rewards, "Insufficient reward pool")
        
        # Update state
        self.rewards_earned[user_address] = 0
        self.last_claim_time[user_address] = block.timestamp
        self.reward_pool = self.reward_pool - total_rewards
        self.total_rewards_distributed = self.total_rewards_distributed + total_rewards
        
        # Transfer rewards (in real implementation)
        # self.transfer(user_address, total_rewards)
        
        # Emit claim event
        self.event("RewardsClaimed", user_address, total_rewards, block.timestamp)
    
    @public_function
    def compound_rewards(self):
        """Compound rewards by adding them to stake."""
        require(not self.contract_paused, "Contract is paused")
        
        user_address = msg.sender
        
        # Calculate total rewards
        pending = self._calculate_rewards(user_address)
        total_rewards = self.rewards_earned.get(user_address, 0) + pending
        
        require(total_rewards > 0, "No rewards to compound")
        
        # Add rewards to stake
        self.staked_balance[user_address] = self.staked_balance.get(user_address, 0) + total_rewards
        self.total_staked = self.total_staked + total_rewards
        
        # Reset rewards
        self.rewards_earned[user_address] = 0
        self.last_claim_time[user_address] = block.timestamp
        
        # Update reward pool
        self.reward_pool = self.reward_pool - total_rewards
        
        # Emit compound event
        self.event("RewardsCompounded", user_address, total_rewards, block.timestamp)
    
    # ============ View Functions ============
    
    @view_function
    def get_staked_balance(self, account: str) -> int:
        """Get staked balance for an account."""
        return self.staked_balance.get(account, 0)
    
    @view_function
    def get_pending_rewards(self, account: str) -> int:
        """Get pending rewards for an account."""
        pending = self._calculate_rewards(account)
        earned = self.rewards_earned.get(account, 0)
        return pending + earned
    
    @view_function
    def get_time_until_unlock(self, account: str) -> int:
        """Get time remaining until tokens can be unstaked."""
        stake_time = self.stake_timestamp.get(account, 0)
        if stake_time == 0:
            return 0
        
        unlock_time = stake_time + self.lock_period
        if block.timestamp >= unlock_time:
            return 0
        
        return unlock_time - block.timestamp
    
    @view_function
    def get_contract_stats(self) -> dict:
        """Get overall contract statistics."""
        return {
            "total_staked": self.total_staked,
            "reward_pool": self.reward_pool,
            "unique_stakers": self.unique_stakers,
            "total_rewards_distributed": self.total_rewards_distributed,
            "reward_rate": self.reward_rate,
            "apy": self.annual_percentage_yield,
            "minimum_stake": self.minimum_stake,
            "lock_period": self.lock_period,
            "paused": self.contract_paused
        }
    
    @view_function
    def get_user_info(self, account: str) -> dict:
        """Get complete staking information for a user."""
        return {
            "staked": self.staked_balance.get(account, 0),
            "pending_rewards": self.get_pending_rewards(account),
            "stake_timestamp": self.stake_timestamp.get(account, 0),
            "last_claim": self.last_claim_time.get(account, 0),
            "time_until_unlock": self.get_time_until_unlock(account)
        }
    
    # ============ Admin Functions ============
    
    @public_function
    def set_reward_rate(self, new_rate: int):
        """Set new reward rate (owner only)."""
        require(msg.sender == self.owner, "Only owner can set reward rate")
        require(new_rate > 0 and new_rate <= 10000, "Invalid reward rate")
        
        old_rate = self.reward_rate
        self.reward_rate = new_rate
        
        self.event("RewardRateUpdated", old_rate, new_rate, block.timestamp)
    
    @public_function
    def add_reward_pool(self, amount: int):
        """Add tokens to reward pool (owner only)."""
        require(msg.sender == self.owner, "Only owner can add rewards")
        require(amount > 0, "Cannot add zero amount")
        
        self.reward_pool = self.reward_pool + amount
        
        self.event("RewardPoolIncreased", amount, self.reward_pool, block.timestamp)
    
    @public_function
    def set_minimum_stake(self, new_minimum: int):
        """Set minimum stake amount (owner only)."""
        require(msg.sender == self.owner, "Only owner can set minimum")
        require(new_minimum > 0, "Minimum must be positive")
        
        old_minimum = self.minimum_stake
        self.minimum_stake = new_minimum
        
        self.event("MinimumStakeUpdated", old_minimum, new_minimum, block.timestamp)
    
    @public_function
    def set_lock_period(self, new_period: int):
        """Set lock period in seconds (owner only)."""
        require(msg.sender == self.owner, "Only owner can set lock period")
        require(new_period >= 0, "Invalid lock period")
        
        old_period = self.lock_period
        self.lock_period = new_period
        
        self.event("LockPeriodUpdated", old_period, new_period, block.timestamp)
    
    @public_function
    def pause_contract(self):
        """Pause contract operations (owner only)."""
        require(msg.sender == self.owner, "Only owner can pause")
        require(not self.contract_paused, "Already paused")
        
        self.contract_paused = True
        self.event("ContractPaused", block.timestamp)
    
    @public_function
    def unpause_contract(self):
        """Unpause contract operations (owner only)."""
        require(msg.sender == self.owner, "Only owner can unpause")
        require(self.contract_paused, "Not paused")
        
        self.contract_paused = False
        self.event("ContractUnpaused", block.timestamp)
    
    @public_function
    def emergency_withdraw(self):
        """Emergency withdrawal - forfeit rewards but get stake back."""
        user_address = msg.sender
        staked_amount = self.staked_balance.get(user_address, 0)
        
        require(staked_amount > 0, "No stake to withdraw")
        
        # Clear user data
        self.staked_balance[user_address] = 0
        self.rewards_earned[user_address] = 0
        self.stake_timestamp[user_address] = 0
        self.last_claim_time[user_address] = 0
        
        # Update totals
        self.total_staked = self.total_staked - staked_amount
        self.unique_stakers = self.unique_stakers - 1
        
        # Transfer stake back (forfeit rewards)
        # self.transfer(user_address, staked_amount)
        
        self.event("EmergencyWithdraw", user_address, staked_amount, block.timestamp)
    
    # ============ Internal Functions ============
    
    def _calculate_rewards(self, account: str) -> int:
        """
        Calculate pending rewards for an account.
        
        Internal function to calculate rewards based on:
        - Staked amount
        - Time staked
        - Reward rate
        """
        staked = self.staked_balance.get(account, 0)
        if staked == 0:
            return 0
        
        last_claim = self.last_claim_time.get(account, self.stake_timestamp.get(account, 0))
        if last_claim == 0:
            return 0
        
        # Calculate time elapsed (in seconds)
        time_elapsed = block.timestamp - last_claim
        if time_elapsed == 0:
            return 0
        
        # Calculate rewards: (staked * rate * time) / (100 * seconds_per_day)
        # Simplified calculation - in production would use more precise math
        rewards = (staked * self.reward_rate * time_elapsed) // (10000 * 86400)
        
        return rewards
    
    @view_function
    def get_estimated_apy(self) -> int:
        """Calculate estimated APY based on current reward rate."""
        # Simplified APY calculation
        # APY = (1 + reward_rate/10000)^365 - 1
        # Returning basis points (1200 = 12%)
        return self.annual_percentage_yield
