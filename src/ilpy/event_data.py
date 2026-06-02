"""Typed payloads delivered to `ilpy.Solver` event callbacks."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

__all__ = ["CuOptData", "EventData", "GurobiData", "SCIPData"]

if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    GurobiEventType: TypeAlias = Literal[
        "PRESOLVE", "SIMPLEX", "MIP", "MIPSOL", "MIPNODE", "MESSAGE", "UNKNOWN"
    ]
    """The set of event types emitted by the Gurobi backend."""
    SCIPEventType: TypeAlias = Literal["PRESOLVEROUND", "BESTSOLFOUND"]
    """The set of event types emitted by the SCIP backend."""
    CuOptEventType: TypeAlias = Literal["MIPSOL", "SOLVED"]
    """The set of event types emitted by the cuOpt backend."""
    EventType: TypeAlias = GurobiEventType | SCIPEventType | CuOptEventType
    """Union of all event types emitted by any supported backend."""


class _GurobiData(TypedDict, total=False):
    backend: Literal["gurobi"]
    runtime: float  # Elapsed solver runtime (seconds).
    work: float  # Elapsed solver work (work units).


class GurobiPresolve(_GurobiData):
    """Event payload emitted by Gurobi during presolve."""

    event_type: Literal["PRESOLVE"]
    pre_coldel: int
    pre_rowdel: int
    pre_senchg: int
    pre_bndchg: int
    pre_coechg: int


class GurobiSimplex(_GurobiData):
    """Event payload emitted by Gurobi from the simplex method."""

    event_type: Literal["SIMPLEX"]
    itrcnt: float
    objval: float
    priminf: float
    dualinf: float
    ispert: int


class _GurobiMipData(_GurobiData):
    objbst: float
    objbnd: float
    nodcnt: float
    solcnt: int
    openscenarios: int
    phase: int
    primalbound: float  # alias for objbst
    dualbound: float  # alias for objbnd
    gap: float  # calculated manually from objbst and objbnd


class GurobiMip(_GurobiMipData):
    """Event payload emitted by Gurobi during MIP search."""

    event_type: Literal["MIP"]
    cutcnt: int
    nodlft: float
    itrcnt: float


class GurobiMipSol(_GurobiMipData):
    """Event payload emitted by Gurobi when a new MIP solution is found."""

    event_type: Literal["MIPSOL"]
    obj: float


class GurobiMipNode(_GurobiMipData):
    """Event payload emitted by Gurobi when a MIP node is processed."""

    event_type: Literal["MIPNODE"]
    status: int


class GurobiMessage(_GurobiData):
    """Event payload wrapping a textual log message from Gurobi."""

    event_type: Literal["MESSAGE"]
    message: str


GurobiData = Union[
    GurobiPresolve, GurobiSimplex, GurobiMip, GurobiMipSol, GurobiMipNode, GurobiMessage
]
"""Union of all Gurobi event payload types."""


class _SCIPData(TypedDict, total=False):
    backend: Literal["scip"]
    deterministictime: float


class SCIPPresolve(_SCIPData):
    """Event payload emitted by SCIP during a presolve round."""

    event_type: Literal["PRESOLVEROUND"]
    nativeconss: int
    nbinvars: int
    nintvars: int
    nimplvars: int
    # nenabledconss: int
    upperbound: float
    nactiveconss: int
    cutoffbound: float
    nfixedvars: int


class SCIPBestSol(_SCIPData):
    """Event payload emitted by SCIP when a new best solution is found."""

    event_type: Literal["BESTSOLFOUND"]
    avgdualbound: float
    avglowerbound: float
    dualbound: float
    gap: float
    lowerbound: float
    nactiveconss: int
    nbestsolsfound: int
    nenabledconss: int
    nlimsolsfound: int
    nsolsfound: int
    primalbound: float
    transgap: float
    nlps: int
    nnzs: int


SCIPData = Union[SCIPPresolve, SCIPBestSol]
"""Union of all SCIP event payload types."""


class _CuOptData(TypedDict, total=False):
    backend: Literal["cuopt"]
    runtime: float  # Elapsed wall time since the cuOpt solve was dispatched.


class CuOptMipSol(_CuOptData):
    """Payload emitted by cuOpt when the MIP solver reports a new incumbent.

    cuOpt invokes the registered ``GetSolutionCallback.get_solution`` hook
    once per incumbent during branch-and-bound; we forward each call as
    one event. ``obj`` is the incumbent's objective value, ``solution_bound``
    is the dual bound at the time of the callback, and ``gap`` is computed
    from the two (matching the convention used by ``GurobiMipSol``).
    """

    event_type: Literal["MIPSOL"]
    obj: float
    solution_bound: float
    gap: float


class CuOptSolved(_CuOptData):
    """Payload emitted by cuOpt once at the end of every solve.

    LP-only problems do not trigger the per-incumbent callback (the MIP
    callback API is MILP-specific), and pure-presolve solutions also bypass
    it; this terminal event guarantees at least one payload per ``solve()``
    call so callers can count on receiving progress data.
    """

    event_type: Literal["SOLVED"]
    obj: float
    status: int


CuOptData = Union[CuOptMipSol, CuOptSolved]
"""Union of all cuOpt event payload types."""

EventData = Union[GurobiData, SCIPData, CuOptData]
"""Union of every event payload emitted by any supported backend."""
