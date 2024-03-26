from typing import Literal, TypedDict

class _GurobiData(TypedDict):
    backend: Literal["gurobi"]
    runtime: float  # Elapsed solver runtime (seconds).
    work: float  # Elapsed solver work (work units).

class GurobiPresolve(_GurobiData):
    event_type: Literal["PRESOLVE"]
    pre_coldel: int
    pre_rowdel: int
    pre_senchg: int
    pre_bndchg: int
    pre_coechg: int

class GurobiSimplex(_GurobiData):
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
    event_type: Literal["MIP"]
    cutcnt: int
    nodlft: float
    itrcnt: float

class GurobiMipSol(_GurobiMipData):
    event_type: Literal["MIPSOL"]
    obj: float

class GurobiMipNode(_GurobiMipData):
    event_type: Literal["MIPNODE"]
    status: int

class GurobiMessage(_GurobiData):
    event_type: Literal["MESSAGE"]
    message: str

GurobiData = (
    GurobiPresolve
    | GurobiSimplex
    | GurobiMip
    | GurobiMipSol
    | GurobiMipNode
    | GurobiMessage
)
