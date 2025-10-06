"""
Custom exceptions for value betting module
"""


class ValueBettingError(Exception):
    """Base exception for value betting module"""
    pass


class InsufficientOddsDataError(ValueBettingError):
    """Raised when there's not enough odds data to calculate value"""
    pass


class InvalidProbabilityError(ValueBettingError):
    """Raised when probabilities are invalid (e.g., sum > 1 or < 0)"""
    pass


class NoArbitrageOpportunityError(ValueBettingError):
    """Raised when no arbitrage opportunity exists"""
    pass


class InvalidBankrollError(ValueBettingError):
    """Raised when bankroll is invalid (e.g., negative or zero)"""
    pass
