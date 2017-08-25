from __future__ import print_function, division

from nose.tools import *
from nose.plugins.attrib import attr

import math as m
import numpy as np

from sisl import Geometry, Atom, SuperCell, SuperCellChild
from sisl import BrillouinZone, PathBZ
from sisl import MonkhorstPackBZ


@attr('brillouinzone')
@attr('bz')
class TestBrillouinZone(object):

    def setUp(self):
        self.s1 = SuperCell(1, nsc=[3, 3, 1])
        self.s2 = SuperCell([2, 2, 10, 90, 90, 60], [5, 5, 1])

    def test_bz1(self):
        bz = BrillouinZone(1.)
        bz.weight
        bz = BrillouinZone(self.s1)
        assert_equal(len(bz), 1)
        assert_true(np.allclose(bz.tocartesian([0, 0, 0]), [0] * 3))
        assert_true(np.allclose(bz.tocartesian([0.5, 0, 0]), [m.pi, 0, 0]))
        assert_true(np.allclose(bz.toreduced([0, 0, 0]), [0] * 3))
        assert_true(np.allclose([0.5, 0, 0], bz.tocartesian(bz.toreduced([0.5, 0, 0]))))
        for k in bz:
            assert_true(np.allclose(k, np.zeros(3)))

    def test_class1(self):
        class Test(SuperCellChild):
            def __init__(self, sc):
                self.set_supercell(sc)
            def eigh(self, k, *args, **kwargs):
                return np.arange(3)
            def eig(self, k, *args, **kwargs):
                return np.arange(3) - 1
        bz = BrillouinZone(Test(self.s1))
        assert_true(np.allclose(bz.eigh(), np.arange(3)))
        assert_true(np.allclose(bz.eig(), np.arange(3)-1))

    def test_class2(self):
        class Test(SuperCellChild):
            def __init__(self, sc):
                self.set_supercell(sc)
            def eigh(self, k, *args, **kwargs):
                return np.arange(3)
            def eig(self, k, *args, **kwargs):
                return np.arange(3) - 1
        bz = BrillouinZone(Test(self.s1))
        # Yields
        bz.yields()
        for val in bz.eigh():
            assert_true(np.allclose(val, np.arange(3)))
        for val in bz.eig():
            assert_true(np.allclose(val, np.arange(3) - 1))
        # Average
        assert_true(np.allclose(bz.average().eigh(), np.arange(3)))

    def test_mp1(self):
        bz = MonkhorstPackBZ(self.s1, [2] * 3)
        assert_equal(len(bz), 8)
        assert_equal(bz.weight[0], 1. / 8)

    def test_mp2(self):
        bz1 = MonkhorstPackBZ(self.s1, [2] * 3)
        assert_equal(len(bz1), 8)
        bz2 = MonkhorstPackBZ(self.s1, [2] * 3, displacement=[.5] * 3)
        assert_equal(len(bz2), 8)
        assert_false(np.allclose(bz1.k, bz2.k))

    def test_mp3(self):
        bz1 = MonkhorstPackBZ(self.s1, [2] * 3, size=0.5)
        assert_equal(len(bz1), 8)
        assert_true(np.all(bz1.k < 0.25))

    def test_pbz1(self):
        bz = PathBZ(self.s1, [[0]*3, [.5]*3], 300)
        assert_equal(len(bz), 300)

        bz2 = PathBZ(self.s1, [[0]*2, [.5]*2], 300, ['A', 'C'])
        assert_equal(len(bz), 300)

        bz3 = PathBZ(self.s1, [[0]*2, [.5]*2], [150] * 2)
        assert_equal(len(bz), 300)
        bz.lineartick()
        bz.lineark()
        bz.lineark(True)

    def test_pbz2(self):
        bz = PathBZ(self.s1, [[0]*3, [.25]*3, [.5]*3], 300)
        assert_equal(len(bz), 300)
