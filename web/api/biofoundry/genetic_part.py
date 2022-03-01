from collections import namedtuple
from web.database.models import GeneticPartsModel
#from .serializers import GeneticPartSchema

_Model = GeneticPartsModel

class GeneticPart():
    def __init__(self, model: _Model):
        self._model = model
        self._model_id = model.id

        self.sequence = self._model.sequence
        self.part_type = self._model.part_type

    @classmethod
    def get_available_parts(cls, method=None):
        if method:
            return _Model.query.filter(_Model.assembly_method == method).all()
        else:
            return _Model.query.all()

    @classmethod
    def get_by_id(self, id):
        """load part from its global_id"""
        return _Model.query.filter(_Model.global_id == id).one_or_none()

    @classmethod
    def create(cls, **kwargs):
        """Build a GeneticPart object"""

        if 'friendly_name' not in kwargs: kwargs['friendly_name'] = kwargs['name']
        kwargs['assembly_method'] = 'golden_gate_moclo'

        model = _Model(**kwargs)

        return cls(model)

    def save(self):
        self._model.save()
    
    def update(self, **kwargs):
        self._model.update(**kwargs, commit=True)

    def delete(self):
        self._model.delete()

    def __repr__(self):
        return f'<GeneticPart: {self.name}>'