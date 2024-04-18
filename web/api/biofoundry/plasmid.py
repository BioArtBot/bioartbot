from collections import namedtuple
from web.api.biofoundry.genetic_part import GeneticPart
from web.database.models import PlasmidModel, ApplicationModel, SubmissionStatus
from web.extensions import db

from .validators import ANTIBIOTICS

def bioart_application():
    return ApplicationModel.query.filter(ApplicationModel.name=='bioart').one_or_none()

_Model = PlasmidModel

def _get_global_id(self):
        """Global ID standard follows iGEM conventions
           https://parts.igem.org/Help:Plasmids/Nomenclature
           Last number is an incrementer instead of version number
        """
        last_id = _Model.query.order_by(_Model.id.desc()).first().id or 0        

        prefix = 'pBAB_'
        ori_code = '1' #TODO: Match the ORI properly
        resistance_code = ANTIBIOTICS[self.antibiotic_resistance]
        next_id = str(last_id + 1).zfill(4)

        return prefix + ori_code + resistance_code + next_id


class Plasmid():
    def __init__(self, model: _Model):
        self._model = model
        self._model_id = model.id
        
        self.id = self._model.global_id
        self.name = self._model.name

    @classmethod
    def get_available(cls, application=None):
        if application:
            return _Model.query.filter(_Model.application == application).all()
        else:
            return _Model.query.all()

    @classmethod
    def get_by_id(self, id):
        """load plasmid from its global_id"""
        return _Model.query.filter(_Model.global_id == id).one_or_none()

    @classmethod
    def create(cls, **kwargs):
        """Build a Plasmid object"""

        if 'friendly_name' not in kwargs: kwargs['friendly_name'] = kwargs['name']
        kwargs['application'] = bioart_application()
        try:
            kwargs['status'] = SubmissionStatus(kwargs('status'))
        except: #assume plasmid is built unless told otherwise
            kwargs['status'] = SubmissionStatus.processed

        model = _Model(**kwargs)

        with db.session.no_autoflush:
            model.global_id = _get_global_id(model)

        return cls(model)

    @classmethod
    def create_from_parts(cls, name: str, description: str, inserts: list, status='Processed', submitter=None):
        """builds a Plasmid object from the parts that are built into it"""

        data = dict()

        # Currently only supporting KanR.
        # Need to implement a way of inferring resistance from backbone
        data['antibiotic_resistance'] = 'kanamycin'
        
        data['name'] = name
        data['description'] = description
        data['friendly_name'] = name
        data['status'] = status
        data['application'] = bioart_application()
        data['source'] = 'CRI + Freegenes'
        if submitter: data['source'] += f'. Designer: {submitter}'

        data['inserts'] = [GeneticPart.get_by_id(id) for id in inserts]

        data['sequence'] = ''
        data['sequence_of_interest'] = ''
        for insert in data['inserts']:
            data['sequence'] += insert.sequence[:-4]
            if insert.part_type != 'vector':
                data['sequence_of_interest'] += insert.sequence[:-4]
                if insert == data['inserts'][-1]: #we want both ends of the SoI
                    data['sequence_of_interest'] += insert.sequence[-4:]

        return cls.create(**data)

    def save(self):
        self._model.save(commit=True)
        return self

    def update(self, **kwargs):
        self._model.update(**kwargs, commit=True)

    def delete(self):
        self._model.delete()

    def set_application(self, application):
        self.application = application
        self._model.application = self.application
        self._model.save()

    def __repr__(self):
        return f'<Plasmid: {self.name}>'