# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from dataclasses import dataclass, field
from numbers import Integral
import numpy as np

from ._composite import composite_geometry
from sisl._internal import set_module
from sisl import geom, Atom, Geometry

__all__ = [
    'nanoribbon', 'graphene_nanoribbon', 'agnr', 'zgnr',
    'heteroribbon', 'graphene_heteroribbon'
]


@set_module("sisl.geom")
def nanoribbon(bond, atoms, width, kind='armchair'):
    r""" Construction of a nanoribbon unit cell of type armchair or zigzag.

    The geometry is oriented along the :math:`x` axis.

    Parameters
    ----------
    bond : float
       bond length between atoms in the honeycomb lattice
    atoms : Atom
       atom (or atoms) in the honeycomb lattice
    width : int
       number of atoms in the transverse direction
    kind : {'armchair', 'zigzag'}
       type of ribbon

    See Also
    --------
    honeycomb : honeycomb lattices
    graphene : graphene geometry
    graphene_nanoribbon : graphene nanoribbon
    agnr : armchair graphene nanoribbon
    zgnr : zigzag graphene nanoribbon
    """
    if not isinstance(width, Integral):
        raise ValueError(f"nanoribbon: width needs to be a postive integer ({width})!")

    # Width characterization
    width = max(width, 1)
    n, m = width // 2, width % 2

    ribbon = geom.honeycomb(bond, atoms, orthogonal=True)

    kind = kind.lower()
    if kind == "armchair":
        # Construct armchair GNR
        if m == 1:
            ribbon = ribbon.repeat(n + 1, 1)
            ribbon = ribbon.remove(3 * (n + 1)).remove(0)
        else:
            ribbon = ribbon.repeat(n, 1)

    elif kind == "zigzag":
        # Construct zigzag GNR
        ribbon = ribbon.rotate(90, [0, 0, -1])
        if m == 1:
            ribbon = ribbon.tile(n + 1, 0)
            ribbon = ribbon.remove(-1).remove(-1)
        else:
            ribbon = ribbon.tile(n, 0)
        # Invert y-coordinates
        ribbon.xyz[:, 1] *= -1
        # Set lattice vectors strictly orthogonal
        ribbon.cell[:, :] = np.diag([ribbon.cell[1, 0], -ribbon.cell[0, 1], ribbon.cell[2, 2]])
        # Sort along x, then y
        ribbon = ribbon.sort(axis=(0, 1))

    else:
        raise ValueError(f"nanoribbon: kind must be armchair or zigzag ({kind})")

    # Separate ribbons along y-axis
    ribbon.cell[1, 1] += 20.

    # Move inside unit cell
    xyz = ribbon.xyz.min(axis=0) * [1, 1, 0]

    return ribbon.move(-xyz + [0, 10, 0])


@set_module("sisl.geom")
def graphene_nanoribbon(width, bond=1.42, atoms=None, kind='armchair'):
    r""" Construction of a graphene nanoribbon

    Parameters
    ----------
    width : int
       number of atoms in the transverse direction
    bond : float, optional
       C-C bond length. Defaults to 1.42
    atoms : Atom, optional
       atom (or atoms) in the honeycomb lattice. Defaults to ``Atom(6)``
    kind : {'armchair', 'zigzag'}
       type of ribbon

    See Also
    --------
    honeycomb : honeycomb lattices
    graphene : graphene geometry
    nanoribbon : honeycomb nanoribbon (used for this method)
    agnr : armchair graphene nanoribbon
    zgnr : zigzag graphene nanoribbon
    """
    if atoms is None:
        atoms = Atom(Z=6, R=bond * 1.01)
    return nanoribbon(bond, atoms, width, kind=kind)


@set_module("sisl.geom")
def agnr(width, bond=1.42, atoms=None):
    r""" Construction of an armchair graphene nanoribbon

    Parameters
    ----------
    width : int
       number of atoms in the transverse direction
    bond : float, optional
       C-C bond length. Defaults to 1.42
    atoms : Atom, optional
       atom (or atoms) in the honeycomb lattice. Defaults to ``Atom(6)``

    See Also
    --------
    honeycomb : honeycomb lattices
    graphene : graphene geometry
    nanoribbon : honeycomb nanoribbon
    graphene_nanoribbon : generic graphene nanoribbon
    zgnr : zigzag graphene nanoribbon
    """
    return graphene_nanoribbon(width, bond, atoms, kind='armchair')


@set_module("sisl.geom")
def zgnr(width, bond=1.42, atoms=None):
    r""" Construction of a zigzag graphene nanoribbon

    Parameters
    ----------
    width : int
       number of atoms in the transverse direction
    bond : float, optional
       C-C bond length. Defaults to 1.42
    atoms : Atom, optional
       atom (or atoms) in the honeycomb lattice. Defaults to ``Atom(6)``

    See Also
    --------
    honeycomb : honeycomb lattices
    graphene : graphene geometry
    nanoribbon : honeycomb nanoribbon
    graphene_nanoribbon : generic graphene nanoribbon
    agnr : armchair graphene nanoribbon
    """
    return graphene_nanoribbon(width, bond, atoms, kind='zigzag')


@set_module("sisl.geom")
@dataclass
class _nanoribbon_section(composite_geometry.Section):
    """
    Parameters
    ----------
    W: int
        The width of the section.
    L: int, optional
        The number of units of the section. Note that a "unit" is
        not a unit cell, but half of it. I.e. a transversal string of
        atoms.
    shift: int, optional
        The shift of this section with respect to the previous one.
        It can be both positive (upwards shift) or negative (downwards shift).
    align: {"bottom"/"b", "top"/"t", "center"/"c", "auto"/"a"}
        Indicates how the section should be aligned with respect to the
        previous one.

        If automatic alignment is requested, sections are aligned:
         - If both sections are odd: On their center.
         - If previous section is even: On its open edge (top or bottom)
         - If previous section is odd and incoming section is even: On the bottom.
    atoms: Atom
        Value to pass to the `atoms` argument of `nanoribbon`. If not provided,
        it defaults to the `atoms` argument passed to this function.
    bond: float
        The bond length of the ribbon.
    kind: {'armchair', 'zigzag'}
        The kind of ribbon that this section should be.
    shift_quantum: bool, optional
        Whether the implementation will assist avoiding lone atoms (< 2 neighbours).

        If ``False``, sections are just shifted (`shift`) number of atoms.

        If ``True``, shifts are quantized in the sense that shifts that produce 
        lone atoms (< 2 neighbours) are ignored. Then:
            - ``shift = 0`` means aligned.
            - ``shift = -1`` means first possible downwards shift (if available).
            - ``shift = 1`` means first possible upwards shift (if available).
        If this is set to `True`, `on_lone_atom` is overwritten to `"raise"`.
    on_lone_atom: {'ignore', 'warn', 'raise'}
        What to do when a junction between sections produces lone atoms (< 2 neighbours)

        Messages contain hopefully useful explanations to understand what
        to do to fix it.
    invert_first: bool, optional
        Whether, if this is the first section, it should be inverted with respect 
        to the one provided by `sisl.geom.nanoribbon`.
    """
    W: int
    L: int = 1
    shift: int = 0
    align: str = "bottom"
    atoms: Atom = None
    bond: float = None
    # Assert that the rest are argument names only.
    # This asserts that we can add and re-arrange arguments
    # first added in 3.10 :(
    #_: dataclasses.KW_ONLY
    kind: str = "armchair"
    shift_quantum: bool = False
    on_lone_atom: str = field(default="ignore", repr=False)
    invert_first: bool = field(default=False, repr=False)

    def __post_init__(self):
        if self.kind == "armchair":
            self.long_ax, self.trans_ax = 0, 1
        elif self.kind == "zigzag":
            self.long_ax, self.trans_ax = 1, 0
        else:
            raise ValueError(f"Unknown kind={kind}, must be one of zigzag or armchair")

        if self.shift_quantum:
            self.on_lone_atom = "raise"

        self._open_borders = [False, False]

        # Now create the geometry that we will move and attach
        # It will be *pristine* in the sense that nothing will be
        # done to it.
        # TODO consider whether this one should actually
        # be the finally attached geometry? That would mean they could be much
        # easier referenced?
        # Given that users may end up doing:
        #  S1 = heteroribbon.Section(7, 4)
        #  S2 = heteroribbon.Section(9, 4)
        #  S3 = heteroribbon.Section(11, 4)
        #  heteroribbon([S1, S2, S1, S3])
        # then we need to figure out another way of checking coordinates
        # While it will work in this linear addition example, I think it is
        # not a viable approach.
        # Another problem of the above is that defaults are not passed down...
        # I don't know how this should be handled...

        self.geometry = nanoribbon(
            bond=self.bond, atoms=self.atoms,
            width=self.W, kind=self.kind
        )

    def _junction_error(self, what, prev, msg):
        """Helper function to raise an error if the junction is not valid.

        It extends the error by specifying details about the sections that
        are being joined.
        """
        msg = f"Error at junction between sections {prev} and {self}. {msg}"
        self.create_error_handler(what)(msg)

    def _shift_unit_cell(self, geometry):
        """Changes the border used for a ribbon.

        It does so by shifting half unit cell. This must be done before any
        tiling of the geometry.
        """
        geometry = geometry.move(geometry.cell[self.long_ax] / 2)
        geometry.xyz = (geometry.fxyz % 1).dot(geometry.cell)
        return geometry

    def _align_check(self, previous, geom_add):
        """Helper function to align the sections.

        It returns the offset to apply to the incoming section in order to
        align it to the previous one.
        """
        align = self.align.lower()
        if previous is None:
            return align, 0, True

        # short-hand
        geom_xyz = geom_add.xyz

        W = self.W
        W_diff = W - previous.W
        if align in ("a", "auto"):
            if W % 2 == 1 and W_diff % 2 == 0:
                # Both ribbons are odd, so we align on the center
                align = "c"
            elif previous.W % 2 == 0:
                # The previous section is even, so it dictates how to align.
                # We should align on its open edge.
                align = {True: "t", False: "b"}[previous._open_borders[1]]
            else:
                # We have an incoming even section and we can align it however we wish.
                # We will align them on the bottom.
                align = "b"

        # TODO could we not simply use the previous.geometry and self.geometry to
        # figure these things out? That would mean we don't need the XYZ storage?
        if align in ("c", "center"):
            if W_diff % 2 == 1:
                self._junction_error("raise",
                                     previous,
                                     "Different parity sections can not be aligned by their centers")
            return (align,
                    previous.xyz[:, self.trans_ax].mean() - geom_xyz[:, self.trans_ax].mean(),
                    # When sections are aligned by the center or the top, it is very easy to check if
                    # they match.
                    (not previous._open_borders[1]) == (W_diff % 4 == 0)
                    )
        elif align in ("t", "top"):
            return (align,
                    previous.xyz[:, self.trans_ax].max() - geom_xyz[:, self.trans_ax].max(),
                    # top aligned is easy
                    not previous._open_borders[1]
                    )
        elif align in ("b", "bottom"):
            last_bot_edge_open = (previous.W % 2 == 1) == previous._open_borders[1]
            this_bot_edge_open = self.W % 2 == 0
            return (align,
                    previous.xyz[:, self.trans_ax].min() - geom_xyz[:, self.trans_ax].min(),
                    # check for same bottom
                    last_bot_edge_open == this_bot_edge_open
                    )

        raise ValueError(f"Invalid value for 'align': {align}. Must be one of"
                         " {'c', 'center', 't', 'top', 'b', 'bottom', 'a', 'auto'}")

    def _offset_from_center(self, align, previous):
        align = align.lower()[0]
        W_diff = self.W - previous.W

        # Number of atoms that hang out if we align on the center
        if align == "t":
            return - W_diff // 2
        elif align == "b":
            return W_diff // 2

        return 0

    def build_section(self, previous, **kwargs):
        new_section = self.geometry

        if previous is None:
            if self.invert_first:
                new_section = self._shift_unit_cell(new_section)
                self._open_borders[0] = not self._open_borders[0]

        else:
            # there is something behind it
            if not isinstance(previous, _nanoribbon_section):
                self._junction_error(ValueError, previous, f"{self.__class__.__name__} can not be appended to {type(previous).__name__}")
            if self.kind != previous.kind:
                self._junction_error(NotImplementedError, previous, f"Ribbons must be of same type.")
            if self.bond != previous.bond:
                self._junction_error(NotImplementedError, previous, f"Ribbons must have same bond length.")

            align, offset, aligned_match = self._align_check(previous, new_section)
            shift = self._parse_shift(self.shift, previous, align)

            # Get the distance of an atom shift. (sin(60) = 3**.5 / 2)
            atom_shift = self.bond * 3**.5 / 2

            # if (last_W % 2 == 1 and W < last_W) and last_open:
            # _junction_error(i, "DANGLING BONDS: Previous odd section, which has an open end,"
            #     " is wider than the incoming one. A wider odd section must always"
            #     " have a closed end. You can solve this by making the previous section"
            #     " one unit smaller or larger (L = L +- 1).", on_lone_atom
            # )

            # Shift the incoming section if the vertical shift makes them not match.
            if aligned_match == (shift % 2 == 1):
                new_section = self._shift_unit_cell(new_section)
                self._open_borders[0] = not self._open_borders[0]

            # Apply the offset that we have calculated.
            move = np.zeros(3)
            move[self.trans_ax] = offset + shift * atom_shift
            new_section = new_section.move(move)

        # Check how many times we have to tile the unit cell (tiles) and whether
        # we have to cut the last string of atoms (cut_last)
        tiles, res = divmod(self.L + 1, 2)
        cut_last = res == 0

        # Tile the current section unit cell
        new_section = new_section.tile(tiles, self.long_ax)
        # Cut the last string of atoms.
        if cut_last:
            new_section.cell[0, 0] *= self.L / (self.L + 1)
            # Remove everything from (here, \infty)
            new_section = new_section.remove({"xy"[self.long_ax]:
                                                (new_section.cell[self.long_ax, self.long_ax] - 0.01, None)})

        self._open_borders[1] = self._open_borders[0] != cut_last

        # TODO, see discussion in __post_init__
        self.xyz = new_section.xyz
        return new_section

    def add_section(self, geometry, previous, **kwargs):
        """ Returns the composite geometry of `other.geometry` and `self.geometry` as defined in this section class """
        # this section addition only uses the last added method
        if len(previous) > 0:
            previous = previous[-1]
        else:
            previous = None

        # Create the new section to be added...
        new_section = self.build_section(previous, **kwargs)
        if geometry is None:
            return new_section

        # Avoid going out of the cell in the transversal direction
        new_min = new_section.xyz[:, self.trans_ax].min()
        new_max = new_section.xyz[:, self.trans_ax].max()
        if new_min < 0:
            cell_offset = - new_min + 14
            geometry = geometry.add_vacuum(cell_offset, self.trans_ax)
            move = np.zeros(3)
            move[self.trans_ax] = cell_offset
            geometry = geometry.move(move)
            new_section = new_section.move(move)
        if new_max > geometry.cell[1, 1]:
            geometry = geometry.add_vacuum(new_max - geometry.cell[self.trans_ax, self.trans_ax] + 14, self.trans_ax)

        # TODO, see discussion in __post_init__
        self.xyz = new_section.xyz
        # Finally, we can safely append the geometry.
        return geometry.append(new_section, self.long_ax)

    def _parse_shift(self, shift, previous, align):
        if self.on_lone_atom == "ignore":
            return shift

        W = self.W

        # Check that we are not joining an open odd ribbon with
        # a smaller ribbon, since no matter what the shift is there will
        # always be dangling bonds.
        if (previous.W % 2 == 1 and W < previous.W) and previous._open_borders[1]:
            self._junction_error("raise", previous, "LONE ATOMS: Previous odd section, which has an open end,"
                " is wider than the incoming one. A wider odd section must always"
                " have a closed end. You can solve this by making the previous section"
                " one unit smaller or larger (L = L +- 1)."
            )

        # Get the difference in width between the previous and this ribbon section
        W_diff = W - previous.W
        # And also the mod(4) because there are certain differences if the width differs
        # on 1, 2, 3 or 4 atoms. After that, the cycle just repeats (e.g. 5 == 1, etc).
        diff_mod = W_diff % 4

        # Now, we need to calculate the offset that we have to apply to the incoming
        # section depending on several factors.
        if diff_mod % 2 == 0 and W % 2 == 1:
            # Both sections are odd

            if W < previous.W:
                # The incoming section is thinner than the last one. Note that at this point
                # we are sure that the last section has a closed border, otherwise we
                # would have raised an error. At this point, centers can differ by any
                # integer number of atoms without leaving dangling bonds.

                # Shift limits are a bit complicated and are different for even and odd shifts.
                # This is because a closed incoming section can shift until there is no connection
                # between ribbons, while an open one needs to stop before its edge goes outside
                # the previous section.
                shift_lims = {
                    "closed": previous.W // 2 + W // 2 - 2,
                    "open": previous.W // 2 - W // 2 - 1
                }

                shift_pars = {
                    lim % 2: lim for k, lim in shift_lims.items()
                }

                # Build an array with all the valid shifts.
                valid_shifts = np.sort([*np.arange(0, shift_pars[0] + 1, 2), *np.arange(1, shift_pars[1] + 1, 2)])
                valid_shifts = np.array([*(np.flip(-valid_shifts)[:-1]),  *valid_shifts])

                # Update the valid shift limits if the sections are aligned on any of the edges.
                shift_offset = self._offset_from_center(align, previous)
                valid_shifts += shift_offset
            elif previous.W == W:
                valid_shifts = np.array([0])
            else:
                # At this point, we already know that the incoming section is wider and
                # therefore it MUST have a closed start, otherwise there will be dangling bonds.
                if diff_mod == 2 and previous._open_borders[1] or diff_mod == 0 and not previous._open_borders[1]:
                    # In these cases, centers must match or differ by an even number of atoms.
                    # And this is the limit for the shift from the center.
                    shift_lim = ((W_diff // 2) // 2) * 2
                else:
                    # Otherwise, centers must differ by an odd number of atoms.
                    # And these are the limits for the shift from the center
                    if previous._open_borders[1]:
                        # To avoid the current open section leaving dangling bonds.
                        shift_lim = (W_diff // 2) - 1
                    else:
                        # To avoid sections being disconnected.
                        shift_lim = W_diff // 2 + ((previous.W // 2) - 1) * 2

                # Update the shift limits if the sections are aligned on any of the edges.
                shift_offset = self._offset_from_center(align, previous)

                # Apply the offsets and calculate the maximum and minimum shifts.
                min_shift, max_shift = -shift_lim + shift_offset, shift_lim + shift_offset

                valid_shifts = np.arange(min_shift, max_shift + 1, 2)
        else:
            # There is at least one even section.

            # We have to make sure that the open edge of the even ribbons (however
            # many there are) is always shifted towards the center. Shifting in the
            # opposite direction would result in dangling bonds.

            # We will calculate all the valid shifts from a bottom alignment perspective.
            # Then convert if needed.
            special_shifts = []

            if diff_mod % 2 == 0:
                # Both ribbons are even
                if previous._open_borders[1]:
                    special_shifts = [previous.W - W]
                    min_shift = previous.W - W + 1
                    max_shift = previous.W - 1
                else:
                    special_shifts = [0]
                    min_shift = - W + 1
                    max_shift = -1

            elif W % 2 == 1:
                # Last section was even, incoming section is odd.
                if W < previous.W:
                    if previous._open_borders[1]:
                        special_shifts = [previous.W - W]
                        min_shift = previous.W - W
                        max_shift = previous.W - W + 1 + ((W - 2) // 2)*2
                    else:
                        special_shifts = [0]
                        min_shift = -1 - ((W - 2) // 2)*2
                        max_shift = -1
                else:
                    if previous._open_borders[1]:
                        min_shift = 0
                        max_shift = previous.W - 2
                    else:
                        max_shift = -1
                        min_shift = - (W - 2)
            else:
                # Last section was odd, incoming section is even.
                if previous._open_borders[1]:
                    special_shifts = [0, previous.W - W]
                    min_shift = None
                else:
                    min_shift = [1, - (W - 2)]
                    max_shift = [previous.W - 2, previous.W - W - 1]

            # We have gone over all possible situations, now just build the
            # array of valid shifts.
            valid_shifts = [*special_shifts]
            if isinstance(min_shift, int):
                valid_shifts.extend(np.arange(min_shift, max_shift + 1, 2))
            elif isinstance(min_shift, list):
                for (m, mx) in zip(min_shift, max_shift):
                    valid_shifts.extend(np.arange(m, mx + 1, 2))

            # Apply offset on shifts based on the actual alignment requested
            # for the sections.
            shift_offset = 0
            if align[0] == "t":
                shift_offset = W_diff
            elif align[0] == "c":
                shift_offset = - self._offset_from_center("b", previous)
            valid_shifts = np.array(valid_shifts) + shift_offset

        # Finally, check if the provided shift value is valid or not.
        valid_shifts = np.sort(valid_shifts)
        if self.shift_quantum:
            n_valid_shifts = len(valid_shifts)
            # Find out if it is possible to perfectly align.
            if np.any(valid_shifts == 0):
                aligned_shift = np.where(valid_shifts == 0)[0][0]
            else:
                # If not, we have to find the smallest shift.
                # What flip does is prioritize upwards shifts.
                # That is, if both "-1" and "1" shifts are valid,
                # "1" will be picked as the reference.
                aligned_shift = n_valid_shifts - 1 - np.argmin(np.abs(np.flip(valid_shifts)))

            # Calculate which index we really need to retrieve
            corrected_shift = aligned_shift + shift

            if corrected_shift < 0 or corrected_shift >= n_valid_shifts:
                self._junction_error(self.on_lone_atom, previous, f"LONE ATOMS: Shift must be between {-aligned_shift}"
                    f" and {n_valid_shifts - aligned_shift - 1}, but {shift} was provided.")

            # And finally get the shift value
            shift = valid_shifts[corrected_shift]
        else:
            if shift not in valid_shifts:
                self._junction_error(self.on_lone_atom, previous, f"LONE ATOMS: Shift must be one of {valid_shifts}"
                    f" but {shift} was provided.")

        return shift


@set_module("sisl.geom")
def heteroribbon(sections, **kwargs):
    """Build a nanoribbon consisting of several nanoribbons of different widths.

    This function basically uses `composite_geometry`, but defaulting to the usage
    of `heteroribbon.Section` as the section class.

    See `heteroribbon.Section` and `composite_geometry` for arguments.

    Returns
    -------
    sisl.Geometry:
        The final structure of the heteroribbon.

    Notes
    -----
    It only works for armchair ribbons for now.

    Examples
    --------
    >>> # A simple 7-11-AGNR with the sections aligned on the center
    >>> heteroribbon([(7, 2), (11, 2)], bond=1.42, atoms="C")
    >>> # The same AGNR but shifted up
    >>> heteroribbon([(7, 2), (11, 2, 1)], bond=1.42, atoms="C")
    >>> # And down
    >>> heteroribbon([(7, 2), (11, 2, -1)], bond=1.42, atoms="C")
    >>> # The same AGNR but with a bigger 11 section and a 9-atom bridge
    >>> heteroribbon([(7, 1), (9,1), (11, 4), (9,1), (7,1)], bond=1.42, atoms="C")
    >>> # One that you have probably never seen before
    >>> heteroribbon([(7, 1j), (10, 2), (9, 1), (8, 2j, -1)], bond=1.42, atoms="C")

    See also
    --------
    composite_geometry: Underlying method used to build the heteroribbon.
    _nanoribbon_section: The class that describes each section.
    nanoribbon : method used to create the segments
    graphene_heteroribbon: same as this function, but with defaults for graphene GNR's
    """
    return composite_geometry(sections, section_cls=heteroribbon.Section, **kwargs)


# attach the section by default
heteroribbon.Section = _nanoribbon_section


@set_module("sisl.geom")
def graphene_heteroribbon(sections, bond=1.42, atoms=None, **kwargs):
    """Build a graphene nanoribbon consisting of several nanoribbons of different widths

    Please see `heteroribbon` for arguments, the only difference is that the `bond` and `atoms`
    arguments default to ``bond=1.42`` and ``Atoms(Z=6, R=bond*1.01)``, respectively.

    See also
    ----------
    `heteroribbon` : for argument details and how it behaves
    """
    if atoms is None:
        atoms = Atom(Z=6, R=bond * 1.01)
    return composite_geometry(sections, section_cls=heteroribbon.Section, bond=bond, atoms=atoms, **kwargs)
