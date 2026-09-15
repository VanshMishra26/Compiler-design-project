class CompilerError(Exception):
    def __init__(self, message: str, line: int, column: int, phase: str):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.phase = phase

    def to_payload(self) -> dict:
        return {
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "phase": self.phase,
        }
