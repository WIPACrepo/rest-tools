"""Some JSON encoding and decoding utilities."""

# fmt:off
# pylint: skip-file

import ast
import base64
import json
import logging
import zlib
from datetime import date, datetime, time
from typing import Any, Optional, Union

from tornado.escape import recursive_unicode

logger = logging.getLogger('jsonUtil')


JSONType = Any


class json_compressor:
    """Used for files and other large things sent over json.

    Great for log files.
    """
    @staticmethod
    def compress(obj):
        return base64.b64encode(zlib.compress(obj)) if obj else b''

    @staticmethod
    def uncompress(obj):
        return zlib.decompress(base64.b64decode(obj)).decode('utf-8') if obj else ''


class datetime_converter:
    @staticmethod
    def dumps(obj):
        return obj.isoformat()

    @staticmethod
    def loads(obj,name=None):
        if ':' in obj:
            if 'T' in obj or ' ' in obj:
                center = ' '
                if 'T' in obj:
                    center = 'T'
                # must be datetime
                if '.' in obj:
                    return datetime.strptime(obj, "%Y-%m-%d"+center+"%H:%M:%S.%f")
                else:
                    return datetime.strptime(obj, "%Y-%m-%d"+center+"%H:%M:%S")
            else:
                # must be time
                if '.' in obj:
                    return datetime.strptime(obj, "%H:%M:%S.%f")
                else:
                    return datetime.strptime(obj, "%H:%M:%S")
        else:
            # must be date
            return datetime.strptime(obj, "%Y-%m-%d")


class date_converter(datetime_converter):
    @staticmethod
    def loads(obj,name=None):
        d = datetime_converter.loads(obj)
        return date(d.year,d.month,d.day)


class time_converter(datetime_converter):
    @staticmethod
    def loads(obj,name=None):
        d = datetime_converter.loads(obj)
        return time(d.hour,d.minute,d.second,d.microsecond)


class binary_converter:
    """note that is is really only for decode of json, since python bytes are
    strings."""
    @staticmethod
    def dumps(obj,name=None):
        return base64.b64encode(obj)

    @staticmethod
    def loads(obj,name=None):
        return base64.b64decode(obj).decode('utf-8')


class bytearray_converter:
    @staticmethod
    def dumps(obj,name=None):
        return base64.b64encode(str(obj))

    @staticmethod
    def loads(obj,name=None):
        return bytearray(base64.b64decode(obj))


class set_converter:
    @staticmethod
    def dumps(obj):
        return list(obj)

    @staticmethod
    def loads(obj,name=None):
        return set(obj)


# do some default conversions


class repr_converter:
    @staticmethod
    def dumps(obj):
        return repr(obj)

    @staticmethod
    def loads(obj,name=None):
        parts = obj.split('(',1)
        type = parts[0]
        if type not in globals():
            raise Exception()
        parts2 = parts[1].rsplit(')',1)
        args = ast.literal_eval(parts2[0])
        if isinstance(args,tuple):
            ret = globals()['type'](*args)
        else:
            ret = globals()['type'](args)
        return ret


JSONConverters = {
    'datetime':datetime_converter,
    'date':date_converter,
    'time':time_converter,
    'binary':binary_converter,
    'bytearray':bytearray_converter,
    'OrderedDict':repr_converter,
    'set':set_converter,
}


def objToJSON(obj):
    if isinstance(obj,(dict,list,tuple,str,int,float,bool)) or obj is None:
        return obj
    else:
        name = obj.__class__.__name__
        if name in JSONConverters:
            return {'__jsonclass__':[name,JSONConverters[name].dumps(obj)]}
        else:
            logger.error('name: %s, obj: %r', name, obj)
            raise Exception('Cannot encode %s class to JSON'%name)


def JSONToObj(obj):
    ret = obj
    if isinstance(obj,dict) and '__jsonclass__' in obj:
        logger.info('try unpacking class')
        try:
            name = obj['__jsonclass__'][0]
            if name not in JSONConverters:
                raise Exception('class %r not found in converters'%name)
            obj_repr = obj['__jsonclass__'][1]
            ret = JSONConverters[name].loads(obj_repr,name=name)
        except Exception as e:
            logger.warning('error making json class: %r',e,exc_info=True)
    return ret


def json_encode(value: JSONType, indent: Optional[Union[int, str]] = None) -> str:
    """JSON-encodes the given Python object."""
    string = json.dumps(
        recursive_unicode(value),
        default=objToJSON,
        separators=(",", ":"),
        indent=indent,
    )
    return string.replace("</", "<\\/")


def json_decode(value: Union[str, bytes, bytearray]) -> JSONType:
    """Return Python objects for the given JSON string."""
    return json.loads(value, object_hook=JSONToObj)
