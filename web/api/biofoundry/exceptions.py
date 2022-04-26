from ..user.exceptions import (InvalidUsage, error_template)

_DATA_ERROR = error_template('data_error', 'Submission not acceptable. May be duplicate or missing data')
_FILE_ERROR = error_template('file_error', 'This file is not parsable by the CSV parser.')
_LENGTH_ERROR = error_template('datalength_error', 'At least one of the submissions has more characters than is supported by this database')
_SYNTAX_ERROR = error_template('syntax_error', 'The submission is not in the correct format for the API endpoint. See docs for more information')

class DataErrorException(InvalidUsage):
    def __init__(self):
        super().__init__(_DATA_ERROR, status_code=406)

class FileErrorException(InvalidUsage):
    def __init__(self):
        super().__init__(_FILE_ERROR, status_code=406)

class DataLengthException(InvalidUsage):
    def __init__(self):
        super().__init__(_LENGTH_ERROR, status_code=406)

class DataSyntaxError(InvalidUsage):
    def __init__(self):
        super().__init__(_SYNTAX_ERROR, status_code=406)

class DBError(InvalidUsage):
    def __init__(self, error):
        clean_error = error.orig
        error_message = error_template('database_error', f'Submitted data caused a database error: {clean_error}')
        super().__init__(error_message, status_code=406)