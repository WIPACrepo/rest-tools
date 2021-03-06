# config.py
"""Module to provide configuration support."""

import os
from typing import cast, Dict, Mapping, Optional, Sequence, Union

RetVal = Union[str, int, float, bool]
OptionalDict = Mapping[str, Optional[RetVal]]
KeySpec = Union[str, Sequence[str], OptionalDict]


def _typecast(source: str, type_: type) -> RetVal:
    if type_ == bool:
        # NOTE - could use distutils.strtobool (but wouldn't be backwards-compatible)
        return source.lower() in ("true", "t", "1", "yes", "y")
    elif type_ == int:
        return int(source)
    elif type_ == float:
        return float(source)
    else:
        return source


def from_environment(keys: KeySpec) -> Dict[str, RetVal]:
    """Obtain configuration values from the OS environment.

    keys - Specify the configuration values to obtain.

           This can be a string, specifying a single key, such as:

               config_dict = from_environment("LANGUAGE")

           This can be a list of strings, specifying multiple keys,
           such as:

               config_dict = from_environment(["HOME", "LANGUAGE"])

           This can be a dictionary that provides some default values,
           and will accept overrides from the environment:

               default_config = {
                   "HOST": "localhost",
                   "PORT": "8080",
                   "REQUIRED_FROM_ENVIRONMENT": None
               }
               config_dict = from_environment(default_config)

           Note in this case that if 'HOST' or 'PORT' were defined in the
           environment, those values would be returned in config_dict. If
           the values were not defined in the environment, the default values
           from default_config would be returned in config_dict.

           Also note, that if 'REQUIRED_FROM_ENVIRONMENT' is not defined,
           an OSError will be raised. The sentinel value of None indicates
           that the configuration parameter MUST be sourced from the
           environment.

    Returns a dictionary mapping configuration keys to configuration values.

    If a configuration value is requested and no default value is provided
    (via a dict), then an OSError will be raised to indicate that the
    component's configuration is incomplete due to missing data from the OS.
    """
    if isinstance(keys, str):
        keys = {keys: None}
    elif isinstance(keys, list):
        keys = dict.fromkeys(keys, None)
    elif not isinstance(keys, dict):
        raise TypeError("keys: Expected string, list or dict")

    config = keys.copy()

    for key in config:
        if key in os.environ:
            if config[key] is not None:
                config[key] = _typecast(os.environ[key], type(config[key]))
            else:
                config[key] = os.environ[key]

        elif config[key] is None:
            raise OSError(f"Missing environment variable '{key}'")

    return cast(Dict[str, RetVal], config)
