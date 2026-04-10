class AuthException(Exception):
    """Base authentication exception"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UserNotFoundException(AuthException):
    """Exception raised when a user is not found"""

    def __init__(self, user_id: str | None = None, email: str | None = None):
        if user_id:
            message = f"User with id {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        else:
            message = "User not found"
        super().__init__(message)


class InvalidCredentialsException(AuthException):
    """Exception raised when login credentials are invalid"""

    def __init__(self):
        message = "Invalid email or password"
        super().__init__(message)


class TokenValidationException(AuthException):
    """Exception raised when token validation fails"""

    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message)
