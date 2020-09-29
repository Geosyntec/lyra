class SQLQueryError(Exception):
    """Raised when query returns no data"""

    def __init__(self, message: str, data: dict):
        super().__init__(message)
        self.message = message
        self.data = data

    def __str__(self):
        return ": ".join([self.message, str(self.data)])
