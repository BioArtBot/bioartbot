from ..user.exceptions import (InvalidUsage, error_template)

_DATA_ERROR = error_template('data_error', 'Submission not acceptable. May be duplicate or missing data')

class DataErrorException(InvalidUsage):
    def __init__(self):
        super().__init__(_DATA_ERROR, status_code=406)