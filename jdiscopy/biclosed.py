# -*- coding: utf-8 -*-

"""
Implements the free biclosed monoidal category.
"""

from . import messages, monoidal, rigid
from . cat import AxiomError


class Ty(monoidal.Ty):
    """
    Objects in a free biclosed monoidal category.
    Generated by the following grammar:

        ty ::= Ty(name) | ty @ ty | ty >> ty | ty << ty

    Examples
    --------
    >>> x, y = Ty('x'), Ty('y')
    >>> print(y << x >> y)
    ((y << x) >> y)
    >>> print((y << x >> y) @ x)
    ((y << x) >> y) @ x
    """
    @staticmethod
    def upgrade(old):
        if len(old) == 1 and isinstance(old[0], (Over, Under)):
            return old[0]
        return Ty(*old.objects)

    def __init__(self, *objects, left=None, right=None):
        self.left, self.right = left, right
        super().__init__(*objects)

    def __lshift__(self, other):
        return Over(self, other)

    def __rshift__(self, other):
        return Under(self, other)


class Over(Ty):
    """ Forward slash types. """
    def __init__(self, left=None, right=None):
        super().__init__(self, left=left, right=right)

    def __repr__(self):
        return "Over({}, {})".format(repr(self.left), repr(self.right))

    def __str__(self):
        return "({} << {})".format(self.left, self.right)

    def __eq__(self, other):
        if not isinstance(other, Over):
            return False
        return self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(repr(self))


class Under(Ty):
    """ Backward slash types. """
    def __init__(self, left=None, right=None):
        super().__init__(self, left=left, right=right)

    def __repr__(self):
        return "Under({}, {})".format(repr(self.left), repr(self.right))

    def __str__(self):
        return "({} >> {})".format(self.left, self.right)

    def __eq__(self, other):
        if not isinstance(other, Under):
            return False
        return self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(repr(self))


@monoidal.diagram_subclass
class Diagram(monoidal.Diagram):
    """ Diagrams in a biclosed monoidal category. """
    @staticmethod
    def id(dom):
        return Id(dom)

    @staticmethod
    def fa(left, right):
        """ Forward application. """
        if left.right != right:
            raise AxiomError(messages.are_not_adjoints(left, right))
        return FA(left)

    @staticmethod
    def ba(left, right):
        """ Backward application. """
        if right.left != left:
            raise AxiomError(messages.are_not_adjoints(left, right))
        return BA(right)

    @staticmethod
    def fc(left, middle, right):
        """ Forward composition. """
        return FC(left << middle, middle << right)

    @staticmethod
    def curry(diagram, n_wires=1, left=False):
        """ Diagram currying. """
        return Curry(diagram, n_wires, left)


class Id(monoidal.Id, Diagram):
    """ Identity diagram in a biclosed monoidal category. """


class Box(monoidal.Box, Diagram):
    """ Boxes in a biclosed monoidal category. """


class Curry(Box):
    """
    Curried diagram.

    Parameters
    ----------
    diagram : :class:`Diagram`
        to curry.
    n_wires : int, optional
        Number :code:`<= len(diagram.dom)` of wires to curry,
        default is :code:`1`.
    left : bool, optional
        Whether to curry to the left, default is :code:`False`.
    """
    def __init__(self, diagram, n_wires=1, left=False):
        if left:
            dom = diagram.dom[n_wires:]
            cod = diagram.dom[:n_wires] >> diagram.cod
        else:
            dom = diagram.dom[:-n_wires]
            cod = diagram.cod << diagram.dom[-n_wires or len(diagram.dom):]
        name = "Curry({}{}{})".format(
            diagram, ", n_wires={}".format(n_wires) if n_wires != 1 else "",
            ", left=True" if left else "")
        self.diagram, self.n_wires, self.left = diagram, n_wires, left
        super().__init__(name, dom, cod)


class FA(Box):
    """ Forward application box. """
    def __init__(self, over):
        if not isinstance(over, Over):
            raise TypeError(messages.type_err(Over, over))
        dom, cod = over @ over.right, over.left
        super().__init__("FA{}".format(over), dom, cod)

    def __repr__(self):
        return "FA({})".format(repr(self.dom[:1]))


class BA(Box):
    """ Backward application box. """
    def __init__(self, under):
        if not isinstance(under, Under):
            raise TypeError(Under, under)
        dom, cod = under.left @ under, under.right
        super().__init__("BA{}".format(under), dom, cod)

    def __repr__(self):
        return "BA({})".format(repr(self.dom[1:]))


class FC(Box):
    """ Forward composition box. """
    def __init__(self, left, right):
        if not isinstance(left, Over):
            raise TypeError(messages.type_err(Over, left))
        if not isinstance(right, Over):
            raise TypeError(messages.type_err(Over, right))
        name = "FC({}, {})".format(left, right)
        dom, cod = left @ right, left.left << right.right
        super().__init__(name, dom, cod)


class Functor(monoidal.Functor):
    """
    Functors into biclosed monoidal categories.

    Examples
    --------
    >>> from discopy import rigid
    >>> x, y = Ty('x'), Ty('y')
    >>> F = Functor(
    ...     ob={x: x, y: y}, ar={},
    ...     ob_factory=rigid.Ty,
    ...     ar_factory=rigid.Diagram)
    >>> print(F(y >> x << y))
    y.r @ x @ y.l
    >>> assert F((y >> x) << y) == F(y >> (x << y))
    """
    def __init__(self, ob, ar, ob_factory=Ty, ar_factory=Diagram):
        super().__init__(ob, ar, ob_factory, ar_factory)

    def __call__(self, diagram):
        if isinstance(diagram, Over):
            return self(diagram.left) << self(diagram.right)
        if isinstance(diagram, Under):
            return self(diagram.left) >> self(diagram.right)
        if isinstance(diagram, Ty) and len(diagram) > 1:
            return self.ob_factory.tensor(*[
                self(diagram[i: i + 1]) for i in range(len(diagram))])
        if isinstance(diagram, Curry):
            n_wires = len(self(getattr(
                diagram.cod, 'left' if diagram.left else 'right')))
            return self.ar_factory.curry(
                self(diagram.diagram), n_wires, diagram.left)
        for cls, method in [(FA, 'fa'), (BA, 'ba')]:
            if isinstance(diagram, cls):
                return getattr(self.ar_factory, method)(
                    self(diagram.dom[:1]), self(diagram.dom[1:]))
        for cls, method in [(FC, 'fc')]:
            if isinstance(diagram, cls):
                left, right = diagram.dom[:1].left, diagram.dom[1:].right
                middle = diagram.dom[:1].right
                return getattr(self.ar_factory, method)(
                    self(left), self(middle), self(right))
        return super().__call__(diagram)


biclosed2rigid_ob = Functor(
    ob=lambda x: rigid.Ty(x[0].name), ar={}, ob_factory=rigid.Ty)
biclosed2rigid = Functor(
    ob=biclosed2rigid_ob,
    ar=lambda f: rigid.Box(
        f.name, biclosed2rigid_ob(f.dom), biclosed2rigid_ob(f.cod)),
    ob_factory=rigid.Ty, ar_factory=rigid.Diagram)
