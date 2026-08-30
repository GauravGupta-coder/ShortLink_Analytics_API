class ShortLinkException(Exception):
    """Base exception for ShortLink API"""
    pass

class DatabaseConnectionError(ShortLinkException):
    """Raised when there is an issue connecting to the database"""
    pass

class RedisConnectionError(ShortLinkException):
    """Raised when there is an issue connecting to Redis"""
    pass
