'''
Description: 
version: 
Author: YL.ik
Date: 2023-11-24 10:49:49
'''
from .exception import IkValidateException
from .http import IkErrJsonResponse, IkJsonResponse, IkSccJsonResponse


class Boolean2:
    def __init__(self, trueFalse=True, data=None):
        self.__trueFalse = trueFalse
        self.__data = data

    @property
    def value(self) -> bool:
        return self.__trueFalse

    @property
    def data(self) -> object:
        return self.__data

    @property
    def dataStr(self) -> str:
        return None if self.__data is None else str(self.__data)

    def update(self, trueFalse, data=None) -> None:
        self.__trueFalse = trueFalse
        self.__data = data

    def addMessageData(self, message, newLine=True) -> None:
        if message:
            if self.__data is not None and type(self.__data) != str:
                raise IkValidateException('Cannot append a string message to a [%s] object.' % type(self.__data))
            elif type(message) != str:
                raise IkValidateException('The message parameter should be a string, but get [%s].' % type(self.__data))
            if self.__data == None:
                self.__data = message
            else:
                if newLine:
                    self.__data += '\n'
                self.__data += message

    def toIkJsonResponse1(self) -> IkJsonResponse:
        '''
            convert data to string
            return IkSccJsonResponse(message = msg)/IkErrJsonResponse(message = msg)
        '''
        msg = None if self.data is None else str(self.data)
        if isinstance(msg, Exception):
            msg = str(msg)
        if self.__trueFalse:
            return IkSccJsonResponse(message=msg)
        else:
            return IkErrJsonResponse(message=msg)

    def toIkJsonResponse2(self) -> IkJsonResponse:
        '''
            if true:
                reurn IkSccJsonResponse(data = self.data)
            else:
                return IkErrJsonResponse(message = msg)
        '''
        if self.__trueFalse:
            return IkSccJsonResponse(data=self.data)
        else:
            msg = self.data
            if isinstance(msg, Exception):
                msg = str(msg)
            return IkErrJsonResponse(message=msg)

    def __str__(self):
        return 'bool=' + str(self.__trueFalse) + ', data=' + str(self.dataStr)

    @staticmethod
    def TRUE(data: any = None) -> 'Boolean2':
        return Boolean2(True, data)
    
    @staticmethod
    def FALSE(data: any = None) -> 'Boolean2':
        return Boolean2(False, data)
    