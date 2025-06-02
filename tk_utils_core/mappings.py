""" 
Map types utils
         
"""
from __future__ import annotations

import pprint as pp
from types import SimpleNamespace

from tk_utils_core.core.mappings import (
        map_dot_update,
        map_dot_get,
        map_dot_subset,
        deep_update,
        )

from tk_utils_core.defaults import defaults


class AttrDict(dict):
    """ 
    Dictionary with attribute access
    """

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    @classmethod
    def _from_dict(cls, base):
        """ 
        Return an instance from a dict

        Parameters
        ----------
        base : dict
            A (possibly nested) dictionary
        """
        if not isinstance(base, (dict, cls)):
            return base
        else:
            output = cls({})
            output.update({k:cls._from_dict(v) for k, v in base.items()})
            return output

    def __str__(self):
        if defaults.pp.pretty is True:
            return pp.pformat(self,
                              width=defaults.pp.width,
                              sort_dicts=defaults.pp.sort_dicts,
                              underscore_numbers=defaults.pp.underscore_numbers,
                              depth=defaults.pp.depth,
                              compact=defaults.pp.compact,
                              )
        else:
            return dict.__str__(self)



