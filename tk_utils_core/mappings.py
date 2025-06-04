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


from tk_utils_core.options import options


__all__ = [
    'map_dot_update',
    'map_dot_get',
    'map_dot_subset',
    'deep_update',
    'AttrDict',
    ]



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
        if options.pp.pretty is True:
            return pp.pformat(self,
                              width=options.pp.width,
                              sort_dicts=options.pp.sort_dicts,
                              underscore_numbers=options.pp.underscore_numbers,
                              depth=options.pp.depth,
                              compact=options.pp.compact,
                              )
        else:
            return dict.__str__(self)



