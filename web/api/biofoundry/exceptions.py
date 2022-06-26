from ..user.exceptions import (InvalidUsage, error_template)
from web.database.models import SubmissionStatus

_ANTIBIOTIC_ERROR = error_template('antibiotic_error', 'Reported antibiotic is not in the system')
_STATUS_ERROR = error_template('status_error', f'Bad status. Must be one of {[status.value for status in SubmissionStatus]}')
_PLASMID_NUMBER_ERROR = error_template('plasmid_number_error', 'Only one plasmid per strain is supported at this time')
_DATA_ERROR = error_template('data_error', 'Submission not acceptable. May be duplicate or missing data')
_FILE_ERROR = error_template('file_error', 'This file is not parsable by the CSV parser.')
_LENGTH_ERROR = error_template('datalength_error', 'At least one of the submissions has more characters than is supported by this database')
_SYNTAX_ERROR = error_template('syntax_error', 'The submission is not in the correct format for the API endpoint. See docs for more information')

class AntibioticException(InvalidUsage):
    def __init__(self):
        super().__init__(_ANTIBIOTIC_ERROR, 422)

class StatusException(InvalidUsage):
    def __init__(self):
        super().__init__(_STATUS_ERROR, 422)

class ReferenceException(InvalidUsage):
    def __init__(self, object_type):
        error_message = error_template('reference_error', f'Reported {object_type} is not in the system')
        super().__init__(error_message, 422)

class PlasmidNumberException(InvalidUsage):
    def __init__(self):
        super().__init__(_PLASMID_NUMBER_ERROR, 422)

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