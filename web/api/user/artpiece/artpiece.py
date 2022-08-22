from collections import namedtuple
from time import time
import io
import json
import datetime as dt
import math
import re
import os
from PIL import Image, ImageDraw
from slugify import slugify
from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from web.api.file_manager import file_manager
from web.database.models import ArtpieceModel, SubmissionStatus
from web.api.user.colors import get_available_color_mapping

def _decode_to_image(pixel_art_color_encoding, color_mapping
    , canvas_size, scale=600):
    ratio = (1, canvas_size['y']/canvas_size['x'])
    pixel_size = (ratio[0] * scale / canvas_size['x']
                 , ratio[1] * scale / canvas_size['y'])
    total_size = (math.ceil(ratio[0] * scale + pixel_size[0])
                 , math.ceil(ratio[1] * scale + pixel_size[1]))
    im = Image.new('RGBX',total_size,(255,255,255,1))
    draw = ImageDraw.Draw(im)
    for color in pixel_art_color_encoding:
        # pixels are given as [y,x]
        for pixel_y, pixel_x in pixel_art_color_encoding[color]:
            origin = (pixel_size[0] * pixel_x, pixel_size[1] * pixel_y)
            far_corner = (pixel_size[0] + origin[0], pixel_size[1] + origin[1])
            draw.rectangle([origin, far_corner], fill=color_mapping[color])
    with io.BytesIO() as output:
        im.save(output, format='JPEG')
        image_file = output.getvalue()
    return (image_file)

def _create_unique_slug(title):
    slug = slugify(title)
    search = f'{slug}#%'
    artpiece_with_slug = (ArtpieceModel.query.filter(
            ArtpieceModel.slug.like(search))
            .order_by(ArtpieceModel.submit_date.desc())
            .first())
    postfix = 1
    if artpiece_with_slug is not None:
        m = re.search(r'\d$', artpiece_with_slug.slug)
        postfix = int(m.group(0)) + 1
    return f'{slug}#{postfix}'


_Model = ArtpieceModel
_fm = file_manager()

class Artpiece():
    def __init__(self, model):
        self._model = model
        self._model_id = model.id

    def refresh(self):
        self._model = _Model.get_by_id(self._model_id)

    @classmethod
    def create(cls, user_id, title, art, canvas_size):
        submit_date = dt.datetime.now()
        slug = _create_unique_slug(title)
        image_as_bytes = _decode_to_image(art, get_available_color_mapping(), canvas_size)
        image_uri = _fm.store_file(io.BytesIO(image_as_bytes), f'{slug}_{int(submit_date.timestamp()*1000)}.jpg')
        
        return cls(
                _Model(slug=slug, title=title, submit_date=submit_date, art=art
                    , canvas_size=canvas_size, status=SubmissionStatus.submitted
                    , image_uri=image_uri, user_id=user_id, confirmed=False)
                .save())

    @classmethod
    def get_by_id(cls, id):
        model = _Model.get_by_id(id)
        return None if model is None else cls(_Model.get_by_id(id))

    @classmethod
    def get_printable(cls, unprinted_only=False, confirmed_only=True):
        statuses= [SubmissionStatus.submitted]
        if not unprinted_only:
            statuses += [SubmissionStatus.processing, SubmissionStatus.processed]
        query_filter = (ArtpieceModel.status.in_(statuses),)
        if confirmed_only: query_filter += (ArtpieceModel.confirmed == True,)
        model = (
            _Model.query.filter(*query_filter)
            .order_by(ArtpieceModel.status.asc())
            .order_by(ArtpieceModel.submit_date.asc())
            .all())
        return model

    @property
    def creator(self):
        from ..user import User
        return User.get_by_id(self._model.user_id)

    def get_image_as_jpg(self):
        with io.BytesIO() as output:
            key = _fm.parse_uri(self._model.image_uri)[-1]
            _fm.get_file(output, key)
            image_file = output.getvalue()
        return image_file

    def get_image_url(self):
        key = _fm.parse_uri(self._model.image_uri)[-1]
        loc = _fm.get_file_url(key)
        return loc

    def get_confirmation_token(self, expires_in=60*60*72):
        return create_access_token(
                identity = {'confirm_artpiece': self._model.id, 'exp': time() + expires_in},
                expires_delta = dt.timedelta(seconds = expires_in)
                )

    def verify_confirmation_token(self, token):
        id = decode_token(token, allow_expired=False)['sub']['confirm_artpiece']
        if self._model_id != id:
            raise TokenIDMismatchError()

    def confirm(self):
        self._model.confirmed = True

    def is_confirmed(self):
        return self._model.confirmed

    def update_status(self, status):
        status_enum = SubmissionStatus[status]
        return self._model.update(status=status_enum, commit=True)

    def delete(self):
        self._model.delete(commit=True)
        return True

    @property
    def title(self):
        return self._model.title

    @property
    def id(self):
        return self._model_id

    @staticmethod
    def total_submission_count_since(date):
        return _Model.query.filter(_Model.submit_date >= date).count()

class TokenIDMismatchError(Exception):
    """ Artpiece id from token does not match """
    pass
