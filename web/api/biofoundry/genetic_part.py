from collections import namedtuple
from web.database.models import GeneticPartsModel
#from .serializers import GeneticPartSchema

_Model = GeneticPartsModel

class GeneticPart():
    def __init__(self, model: GeneticPartsModel):
        self._model = model
        self._model_id = model.id

    @classmethod
    def get_available_parts(cls, method=None):
        if method:
            return _Model.query().filter(_Model.assembly_method == method).all()
        else:
            return _Model.query().all()



    @classmethod
    def create_new(cls, name, obj_class, properties: list):
        property_collection = LabObjectPropertyCollection.from_dicts(properties)
        return cls(name, obj_class, property_collection)

    @classmethod
    def load_from_name(cls, name):
        try:
            _model = _Model.query.filter(_Model.name == name).one_or_none()
            _property_model = _model.properties.all()
        except AttributeError:
            return None

        properties = LabObjectPropertyCollection._from_model(_property_model)
        object_class = _model.obj_class
        name = _model.name
        return cls(name, object_class, properties, _model)

    def save(self):
        if not self._model:
            self._model = self._create_in_db(self.name,
                                             self.object_class,
                                             self.properties
                                             )
            return
        self._model.name = self.name
        self._model.obj_class = self.object_class
        self._model.properties = self.properties.as_model()
        
        self._model.save()

    def __repr__(self):
        return f'<LabObject: {self.name}>'