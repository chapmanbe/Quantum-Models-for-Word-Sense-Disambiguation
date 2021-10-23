# -*- coding: utf-8 -*-

""" DisCoPy quantum submodule: cqmap, circuit, gates, tk and zx. """

from . import cqmap, circuit, gates, zx
from . cqmap import C, Q, CQ, CQMap
from . circuit import (
    bit, qubit, Circuit, Id, Box, Sum, Swap, CircuitFunctor,
    Discard, MixedState, Measure, Encode, IQPansatz, random_tiling)
from  . gates import (
    SWAP, ClassicalGate, QuantumGate, Ket, Bra, Bits, Copy, Match,
    Rx, Ry, Rz, CU1, CRz, CRy, CRx, CZ, CX, X, Y, Z, H, S, T, scalar, sqrt)

