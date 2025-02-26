# -*- coding: utf-8 -*-
"""
"""

from .. import monoidal, rigid, messages, tensor
from .. cat import AxiomError
from .. rigid import Ob, Ty, Diagram
from .. tensor import np, Dim, Tensor
from . circuit import (
    bit, qubit, Box, Sum, Swap, Discard, Measure, MixedState, Encode)
from . gates import Scalar


class CQ(Ty):
    """
    Implements the dimensions of classical-quantum systems.

    Parameters
    ----------
    classical : :class:`discopy.tensor.Dim`
        Classical dimension.
    quantum : :class:`discopy.tensor.Dim`
        Quantum dimension.


    Note
    ----

    In the category of monoids, :class:`CQ` is the product of :class:`C` and
    :class:`Q`, which are both isomorphic to :class:`discopy.tensor.Dim`.

    Examples
    --------
    >>> CQ(Dim(2), Dim(2))
    C(Dim(2)) @ Q(Dim(2))
    >>> CQ(Dim(2), Dim(2)) @ CQ(Dim(2), Dim(2))
    C(Dim(2, 2)) @ Q(Dim(2, 2))
    """
    def __init__(self, classical=Dim(1), quantum=Dim(1)):
        self.classical, self.quantum = classical, quantum
        types = [Ob("C({})".format(dim)) for dim in classical]\
            + [Ob("Q({})".format(dim)) for dim in quantum]
        super().__init__(*types)

    def __repr__(self):
        if not self:
            return "CQ()"
        if not self.classical:
            return "Q({})".format(repr(self.quantum))
        if not self.quantum:
            return "C({})".format(repr(self.classical))
        return "C({}) @ Q({})".format(repr(self.classical), repr(self.quantum))

    def __str__(self):
        return repr(self)

    def tensor(self, *others):
        classical = self.classical.tensor(*(x.classical for x in others))
        quantum = self.quantum.tensor(*(x.quantum for x in others))
        return CQ(classical, quantum)

    @property
    def l(self):
        return CQ(self.classical[::-1], self.quantum[::-1])

    @property
    def r(self):
        return self.l


class C(CQ):
    """
    Implements the classical dimension of a classical-quantum system,
    see :class:`CQ`.
    """
    def __init__(self, dim=Dim(1)):
        super().__init__(dim, Dim(1))


class Q(CQ):
    """
    Implements the quantum dimension of a classical-quantum system,
    see :class:`CQ`.
    """
    def __init__(self, dim=Dim(1)):
        super().__init__(Dim(1), dim)


class CQMap(Tensor):
    """
    Implements classical-quantum maps.

    Parameters
    ----------
    dom : :class:`CQ`
        Domain.
    cod : :class:`CQ`
        Codomain.
    array : list, optional
        Array of size :code:`product(utensor.dom @ utensor.cod)`.
    utensor : :class:`discopy.tensor.Tensor`, optional
        Underlying tensor with domain
        :code:`dom.classical @ dom.quantum ** 2` and codomain
        :code:`cod.classical @ cod.quantum ** 2``.
    """
    @property
    def utensor(self):
        """ Underlying tensor. """
        return Tensor(self._udom, self._ucod, self.array)

    def __init__(self, dom, cod, array=None, utensor=None):
        if array is None and utensor is None:
            raise ValueError("One of array or utensor must be given.")
        if utensor is None:
            udom = dom.classical @ dom.quantum @ dom.quantum
            ucod = cod.classical @ cod.quantum @ cod.quantum
        else:
            udom, ucod = utensor.dom, utensor.cod
        super().__init__(udom, ucod, utensor.array if array is None else array)
        self._dom, self._cod, self._udom, self._ucod = dom, cod, udom, ucod

    def __repr__(self):
        return super().__repr__().replace("Tensor", "CQMap")

    def __add__(self, other):
        if other == 0:
            return self
        if (self.dom, self.cod) != (other.dom, other.cod):
            raise AxiomError(messages.cannot_add(self, other))
        return CQMap(self.dom, self.cod, self.array + other.array)

    def __radd__(self, other):
        return self.__add__(other)

    @staticmethod
    def id(dom):
        utensor = Tensor.id(dom.classical @ dom.quantum @ dom.quantum)
        return CQMap(dom, dom, utensor=utensor)

    def then(self, *others):
        if len(others) != 1:
            return monoidal.Diagram.then(self, *others)
        other, = others
        return CQMap(
            self.dom, other.cod, utensor=self.utensor >> other.utensor)

    def dagger(self):
        return CQMap(self.cod, self.dom, utensor=self.utensor.dagger())

    def tensor(self, *others):
        if len(others) != 1:
            return monoidal.Diagram.tensor(self, *others)
        other, = others
        f = rigid.Box('f', Ty('c00', 'q00', 'q00'), Ty('c10', 'q10', 'q10'))
        g = rigid.Box('g', Ty('c01', 'q01', 'q01'), Ty('c11', 'q11', 'q11'))
        above = Diagram.id(f.dom[:1] @ g.dom[:1] @ f.dom[1:2])\
            @ Diagram.swap(g.dom[1:2], f.dom[2:]) @ Diagram.id(g.dom[2:])\
            >> Diagram.id(f.dom[:1]) @ Diagram.swap(g.dom[:1], f.dom[1:])\
            @ Diagram.id(g.dom[1:])
        below =\
            Diagram.id(f.cod[:1]) @ Diagram.swap(f.cod[1:], g.cod[:1])\
            @ Diagram.id(g.cod[1:])\
            >> Diagram.id(f.cod[:1] @ g.cod[:1] @ f.cod[1:2])\
            @ Diagram.swap(f.cod[2:], g.cod[1:2]) @ Diagram.id(g.cod[2:])
        diagram2tensor = tensor.Functor(
            ob={Ty("{}{}{}".format(a, b, c)):
                z.__getattribute__(y).__getattribute__(x)
                for a, x in zip(['c', 'q'], ['classical', 'quantum'])
                for b, y in zip([0, 1], ['dom', 'cod'])
                for c, z in zip([0, 1], [self, other])},
            ar={f: self.utensor.array, g: other.utensor.array})
        return CQMap(self.dom @ other.dom, self.cod @ other.cod,
                     utensor=diagram2tensor(above >> f @ g >> below))

    @staticmethod
    def swap(left, right):
        utensor = Tensor.swap(left.classical, right.classical)\
            @ Tensor.swap(left.quantum, right.quantum)\
            @ Tensor.swap(left.quantum, right.quantum)
        return CQMap(left @ right, right @ left, utensor=utensor)

    @staticmethod
    def measure(dim, destructive=True):
        """ Measure a quantum dimension into a classical dimension. """
        if not dim:
            return CQMap(CQ(), CQ(), np.array(1))
        if len(dim) == 1:
            if destructive:
                array = np.array([
                    int(i == j == k)
                    for i in range(dim[0])
                    for j in range(dim[0])
                    for k in range(dim[0])])
                return CQMap(Q(dim), C(dim), array)
            array = np.array([
                int(i == j == k == l == m)
                for i in range(dim[0])
                for j in range(dim[0])
                for k in range(dim[0])
                for l in range(dim[0])
                for m in range(dim[0])])
            return CQMap(Q(dim), C(dim) @ Q(dim), array)
        return CQMap.measure(dim[:1], destructive=destructive)\
            @ CQMap.measure(dim[1:], destructive=destructive)

    @staticmethod
    def encode(dim, constructive=True):
        """ Encode a classical dimension into a quantum dimension. """
        return CQMap.measure(dim, destructive=constructive).dagger()

    @staticmethod
    def pure(utensor):
        """ Takes a tensor, returns a pure quantum CQMap. """
        return CQMap(Q(utensor.dom), Q(utensor.cod),
                     (utensor.conjugate() @ utensor).array)

    @staticmethod
    def classical(utensor):
        """ Takes a tensor, returns a classical CQMap. """
        return CQMap(C(utensor.dom), C(utensor.cod), utensor.array)

    @staticmethod
    def discard(dom):
        """ Discard a quantum dimension or take the marginal distribution. """
        array = np.tensordot(
            np.ones(dom.classical), Tensor.id(dom.quantum).array, 0)
        return CQMap(dom, CQ(), array)

    @staticmethod
    def cups(left, right):
        return CQMap.classical(Tensor.cups(left.classical, right.classical))\
            @ CQMap.pure(Tensor.cups(left.quantum, right.quantum))

    @staticmethod
    def caps(left, right):
        return CQMap.cups(left, right).dagger()

    def round(self, decimals=0):
        """ Rounds the entries of a CQMap up to a number of decimals. """
        return CQMap(self.dom, self.cod, utensor=self.utensor.round(decimals))


class Functor(rigid.Functor):
    """
    Implements functors into :class:`CQMap`.
    """
    def __init__(self, ob=None, ar=None):
        ob, ar = ob or {bit: C(Dim(2)), qubit: Q(Dim(2))}, ar or {}
        super().__init__(ob, ar, ob_factory=CQ, ar_factory=CQMap)

    def __repr__(self):
        return super().__repr__().replace("Functor", "cqmap.Functor")

    def __call__(self, box):
        if isinstance(box, Sum) or not isinstance(box, Box):
            return super().__call__(box)
        if isinstance(box, Swap):
            return CQMap.swap(self(box.dom[:1]), self(box.dom[1:]))
        if isinstance(box, Discard):
            return CQMap.discard(self(box.dom))
        if isinstance(box, Measure):
            measure = CQMap.measure(
                self(box.dom).quantum, destructive=box.destructive)
            measure = measure @ CQMap.discard(self(box.dom).classical)\
                if box.override_bits else measure
            return measure
        if isinstance(box, (MixedState, Encode)):
            return self(box.dagger()).dagger()
        if isinstance(box, Scalar):
            return CQMap(CQ(), CQ(), abs(box.array[0]) ** 2)
        if not box.is_mixed and box.classical:
            return CQMap(self(box.dom), self(box.cod), box.array)
        if not box.is_mixed:
            dom, cod = self(box.dom).quantum, self(box.cod).quantum
            return CQMap.pure(Tensor(dom, cod, box.array))
        return CQMap(self(box.dom), self(box.cod), box.array)
