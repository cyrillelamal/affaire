class InappropriateInputException(Exception):
    pass


class UndefinedActionError(Exception):
    pass


class SettingsKeyError(Exception):
    pass


class HelpKeyError(SettingsKeyError):
    pass


class UnknownParameterException(Exception):
    pass


class UndefinedValueException(Exception):
    pass
