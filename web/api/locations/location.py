from collections import namedtuple
from web.database.models import LocationModel

_Model = LocationModel

class Location():
    def __init__(self, model):
        self._model = model

    @classmethod
    def create(cls, name, description=None):
        return cls(_Model(name=name, description=description))
    
    @classmethod
    def get_by_id(cls, id):
        _Model = cls._Model()
        model = _Model.get_by_id(id)
        return cls(model) if model else None
    
    @classmethod
    def get_all(cls):
        return _Model.query.all()
    
    def delete(self):
        self._model.delete(commit=True)
        return True
    
    def update(self, **kwargs):
        if kwargs['name']: name = kwargs['name']
        if kwargs['description']: description = kwargs['description']
        self._model.update(commit=True, name=name, description=description)
        return True
    
    @property
    def name(self):
        return self._model.name
    
    @property
    def description(self):
        return self._model.description

    @property
    def id(self):
        return self._model.id

    def __repr__(self):
        return f'<Location: {self.name}>'