from web.database.models import StrainModel, ApplicationModel
#from .serializers import StrainSchema

def bioart_application():
    return ApplicationModel.query.filter(ApplicationModel.name=='bioart').one_or_none()

_Model = StrainModel

class Strain():
    def __init__(self, model: _Model):
        self._model = model
        self._model_id = model.id

    @classmethod
    def get_available(cls, application=None):
        if application:
            return _Model.query.filter(_Model.application == application).all()
        else:
            return _Model.query.all()

    @classmethod
    def get_by_id(self, id):
        """load strain from its global_id"""
        return _Model.query.filter(_Model.global_id == id).one_or_none()

    @classmethod
    def create(cls, **kwargs):
        """Build a strain object"""

        if 'friendly_name' not in kwargs: kwargs['friendly_name'] = kwargs['name']
        kwargs['application'] = bioart_application()

        model = _Model(**kwargs)

        return cls(model)

    @classmethod
    def create_from_plasmid(cls, plasmid: list):
        """builds a strain object from the plasmid in it"""
        pass #TODO make this do the thing it says it will do
  
    def save(self):
        self._model.save()

    def update(self, **kwargs):
        self._model.update(**kwargs, commit=True)

    def delete(self):
        self._model.delete()

    def set_application(self, application):
        self.application = application
        self._model.application = self.application
        self._model.save()

    def __repr__(self):
        return f'<Strain: {self.name}>'