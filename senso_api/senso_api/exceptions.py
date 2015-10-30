import json
from django import forms

class ErrorCode(object):
    UNEXPECTED_ERROR = 1
    INPUT_FORMAT_ERROR = 2
    HTTP_METHOD_NOT_ALLOWED = 3
    CHANNEL_NOT_FOUND = 4
    CHANNEL_CREATE_ERROR = 5
    CHANNEL_UPDATE_ERROR = 6
    CHANNEL_DELETE_ERROR = 7

class ApiError(Exception):
    def __str__(self):
        return self.debug
    def __init__(self, msg='', debug=''):
        self.msg = msg
        self.debug = debug

class ApiUnexpectedError(ApiError):
    value = ErrorCode.UNEXPECTED_ERROR
    def __init__(self, msg="Unknown error", debug="Unknown error"):
        super(ApiUnexpectedError, self).__init__(msg, debug)

class ApiInputFormatError(ApiError):
    value = ErrorCode.INPUT_FORMAT_ERROR

    def __init__(self,
                 msg="Input format is invalid.",
                 debug="Input format is invalid.",
                 *args, **kwargs):
        super(ApiInputFormatError, self).__init__(*args, **kwargs)
        self.msg = unicode(msg)
        self.debug = debug

class ApiHttpMethodNotAllowed(ApiError):
    value = ErrorCode.HTTP_METHOD_NOT_ALLOWED
    def __init__(self,
                 msg="Http Method Not Allowed",
                 debug="Http Method Not Allowed"):
        super(ApiHttpMethodNotAllowed, self).__init__(msg, debug)

class ApiChannelNotFound(ApiError):
    value = ErrorCode.CHANNEL_NOT_FOUND
    def __init__(self, msg="Channel Not Found", debug="Channel Not Found"):
        super(ApiChannelNotFound, self).__init__(msg, debug)

class ApiCreateChannelError(ApiError):
    value = ErrorCode.CHANNEL_CREATE_ERROR
    def __init__(self, msg="Channel create fail", debug="Channel create fail"):
        super(ApiCreateChannelError, self).__init__(msg, debug)

class ApiUpdateChannelError(ApiError):
    value = ErrorCode.CHANNEL_UPDATE_ERROR
    def __init__(self, msg="Channel update fail", debug="Channel update fail"):
        super(ApiUpdateChannelError, self).__init__(msg, debug)

class ApiDeletehannelError(ApiError):
    value = ErrorCode.CHANNEL_DELETE_ERROR
    def __init__(self, msg="Channel delete fail", debug="Channel delete fail"):
        super(ApiDeleteChannelError, self).__init__(msg, debug)


