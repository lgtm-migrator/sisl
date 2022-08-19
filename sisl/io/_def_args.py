# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from functools import wraps

from sisl import Geometry

__all__ = ["wrap_read_geometry"]

def wrap_read_geometry(func):
    """ Wraps the `read_geometry` method by adding a set of default arguments and flags

    This unifies the arguments for the various codes IO handling such that
    one can expect the same from all of them

    The following arguments are added:

    - atoms
      A replacement argument for the `atoms` in the returned geometry.
    - sc
      A replacement argument for the `sc` in the returned geometry.

    The `read_geometry` should then instead of returning a `Geometry`
    return a tuple consisting of `sc, atoms, xyz` then the wrapped
    method will coherently replace the required details and create
    the `Geometry`
    """

    # We should also add keyword arguments to the documentation of func
    @wraps(func)
    def _func(*args, **kwargs):
        user_sc = kwargs.pop("sc", None)
        user_atoms = kwargs.pop("atoms", None)

        sc, atoms, xyz = func(*args, **kwargs)

        if user_sc is not None:
            sc = user_sc
        if user_atoms is not None:
            atoms = user_atoms

        return Geometry(xyz, atoms, sc=sc)

    return _func

        
        
    
