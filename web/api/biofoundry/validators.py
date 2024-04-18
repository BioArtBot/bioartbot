from .exceptions import AntibioticException, StatusException, ReferenceException
from web.database.models import SubmissionStatus

# Global codes. Might consider putting this into the DB
ANTIBIOTICS = {
    'ampicillin': 'A',
    'chloramphenicol': 'C',
    'erythromycin': 'E',
    'gentamycin': 'G',
    'kanamycin': 'K',
    'neomycin': 'N',
    'nalidixic acid': 'Na',
    'rifampicin': 'R',
    'spectinomycin': 'S',
    'streptomycin': 'St',
    'tetracycline': 'T',
    'trimethoprim': 'Tm',
    'zeocin': 'Z'
}

def validate_antibiotic_resistance(antibiotic_resistance):
    try:
        assert antibiotic_resistance in ANTIBIOTICS
    except:
        raise AntibioticException

def validate_status(status):
    try:
        SubmissionStatus(status)
    except:
        raise StatusException

def validate_object_ids_exist(object_class, inserts):
    try:
        for insert in inserts: 
            biofoundry_object = object_class.get_by_id(insert)
            assert biofoundry_object is not None
    except:
        raise ReferenceException(object_class.__name__)