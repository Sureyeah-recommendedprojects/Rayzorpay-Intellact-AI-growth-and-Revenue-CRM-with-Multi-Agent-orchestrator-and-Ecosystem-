"""
VotingContract - A simple voting system in Python
Perfect for beginners - no Solidity needed!
"""

from pymon.py_contracts import PySmartContract

class VotingContract(PySmartContract):
    """A simple voting contract where people can vote for candidates."""
    
    def __init__(self):
        """Set up the voting system."""
        super().__init__()
        
        # Who created this contract (the admin)
        self.admin = self.state_var("admin", self.msg_sender())
        
        # Is voting currently open?
        self.voting_open = self.state_var("voting_open", True)
        
        # List of candidates (their names)
        self.candidates = self.state_var("candidates", [])
        
        # Count votes for each candidate
        self.vote_counts = self.state_var("vote_counts", {})
        
        # Track who has already voted (prevent double voting)
        self.has_voted = self.state_var("has_voted", {})
    
    @public_function
    def add_candidate(self, name: str):
        """Add a new candidate (only admin can do this)."""
        sender = self.msg_sender()
        
        if sender != self.admin:
            raise Exception("Only admin can add candidates!")
        
        if name in self.candidates:
            raise Exception("Candidate already exists!")
        
        # Add the candidate
        self.candidates.append(name)
        self.vote_counts[name] = 0
        
        self.event("CandidateAdded", name)
    
    @public_function
    def vote(self, candidate_name: str):
        """Vote for a candidate."""
        sender = self.msg_sender()
        
        # Check if voting is open
        if not self.voting_open:
            raise Exception("Voting is closed!")
        
        # Check if person already voted
        if self.has_voted.get(sender, False):
            raise Exception("You already voted!")
        
        # Check if candidate exists
        if candidate_name not in self.candidates:
            raise Exception("Candidate does not exist!")
        
        # Record the vote
        self.vote_counts[candidate_name] += 1
        self.has_voted[sender] = True
        
        self.event("VoteCast", sender, candidate_name)
    
    @view_function
    def get_candidates(self) -> list:
        """Get list of all candidates."""
        return self.candidates
    
    @view_function
    def get_vote_count(self, candidate_name: str) -> int:
        """Get number of votes for a candidate."""
        return self.vote_counts.get(candidate_name, 0)
    
    @view_function
    def get_winner(self) -> str:
        """Get the candidate with most votes."""
        if not self.candidates:
            return "No candidates"
        
        winner = ""
        max_votes = -1
        
        for candidate in self.candidates:
            votes = self.vote_counts.get(candidate, 0)
            if votes > max_votes:
                max_votes = votes
                winner = candidate
        
        return winner
    
    @view_function
    def is_voting_open(self) -> bool:
        """Check if voting is currently open."""
        return self.voting_open
    
    @view_function
    def did_vote(self, voter: str) -> bool:
        """Check if someone already voted."""
        return self.has_voted.get(voter, False)
    
    @public_function
    def close_voting(self):
        """Close the voting (only admin can do this)."""
        sender = self.msg_sender()
        
        if sender != self.admin:
            raise Exception("Only admin can close voting!")
        
        self.voting_open = False
        self.event("VotingClosed")