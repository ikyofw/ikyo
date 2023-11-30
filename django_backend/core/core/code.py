from enum import Enum


class IkCode:

    I0 = 0  # False, Failed
    '''
        0. False, Failed.
    '''

    I1 = 1  # True, Success
    '''
        1. True, Success.
    '''

    I2 = 2  # System error.
    '''
        2. System error.
    '''

    E10001 = 100001  # Please login first
    '''
        100001: Error: Please login first.
    '''

    E10002 = 100002  # Permission deny

    '''
        100002: Error: Permission deny.
    '''


class MessageType(Enum):
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    FATAL = 'fatal'
    EXCEPTION = 'exception'
