class TransactionError(Exception):
    """Raised when an error related to a single transaction (e.g., test, request, API call) has been detected. Even that the processing of the transaction stopped, the whole program continues to run."""

    pass


class GlobalError(Exception):
    """Raised when an error related to a whole program has been detected. This should be raised only in situations, when the whole program cannot continue and must be stopped (e.g., database problem)."""

    pass
