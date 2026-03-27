class BetterPOSError(Exception):
    pass


class PermissionDeniedError(BetterPOSError):
    pass


class InvalidStateError(BetterPOSError):
    pass


class ValidationError(BetterPOSError):
    pass
