
#include <gurobi_c.h>

#include "GurobiBackend.h"

const char* getEventTypeName(int where) {
    switch (where) {
        case GRB_CB_POLLING: return "POLLING";
        case GRB_CB_PRESOLVE: return "PRESOLVE";
        case GRB_CB_SIMPLEX: return "SIMPLEX";
        case GRB_CB_MIP: return "MIP";
        case GRB_CB_MIPSOL: return "MIPSOL";
        case GRB_CB_MIPNODE: return "MIPNODE";
        case GRB_CB_MESSAGE: return "MESSAGE";
        case GRB_CB_BARRIER: return "BARRIER";
        case GRB_CB_MULTIOBJ: return "MULTIOBJ";
        case GRB_CB_IIS: return "IIS";
        // Add other cases here
        default: return "UNKNOWN";
    }
}


/**
 * Callback function for Gurobi events.
 * Pulls out data as described in the Gurobi documentation.
 * https://www.gurobi.com/documentation/current/refman/cb_codes.html
 */
int __stdcall eventCallback(CB_ARGS) {
    if (where == GRB_CB_POLLING) {
        // POLLING callback is an optional callback that is only invoked
        // if other callbacks have not been called in a while.
        // It does not allow any progress information to be retrieved.
        // It is simply provided to allow interactive applications to
        // regain control frequently, so that they can maintain application responsiveness.
        return 0;
    }

    // Cast usrdata back to a GurobiBackend pointer
    GurobiBackend* backend = static_cast<GurobiBackend*>(usrdata);
    // don't bother collecting the data if no one is listening
    if (!backend->hasEventCallback()) {
        return 0;
    }

    // Create a map to store the event data
    EventDataMap map;

    // all events will have these fields
    double runtime, work;
    const char* event_name = getEventTypeName(where);
    GRBcbget(cbdata, where, GRB_CB_RUNTIME, &runtime);
    GRBcbget(cbdata, where, GRB_CB_WORK, &work);
    map["event_type"] = event_name;
    map["backend"] = "gurobi";
    map["runtime"] = runtime;
    map["work"] = work;

    if (where == GRB_CB_PRESOLVE) {
        // Currently performing presolve
        int pre_coldel, pre_rowdel, pre_senchg, pre_bndchg, pre_coechg;
        GRBcbget(cbdata, where, GRB_CB_PRE_COLDEL, &pre_coldel);
        GRBcbget(cbdata, where, GRB_CB_PRE_ROWDEL, &pre_rowdel);
        GRBcbget(cbdata, where, GRB_CB_PRE_SENCHG, &pre_senchg);
        GRBcbget(cbdata, where, GRB_CB_PRE_BNDCHG, &pre_bndchg);
        GRBcbget(cbdata, where, GRB_CB_PRE_COECHG, &pre_coechg);
        map["pre_coldel"] = pre_coldel;
        map["pre_rowdel"] = pre_rowdel;
        map["pre_senchg"] = pre_senchg;
        map["pre_bndchg"] = pre_bndchg;
        map["pre_coechg"] = pre_coechg;
    } else if (where == GRB_CB_SIMPLEX) {
        // Currently in simplex
        double objval, priminf, dualinf, itrcnt;
        int ispert;
        GRBcbget(cbdata, where, GRB_CB_SPX_ITRCNT, &itrcnt);
        GRBcbget(cbdata, where, GRB_CB_SPX_OBJVAL, &objval);
        GRBcbget(cbdata, where, GRB_CB_SPX_PRIMINF, &priminf);
        GRBcbget(cbdata, where, GRB_CB_SPX_DUALINF, &dualinf);
        GRBcbget(cbdata, where, GRB_CB_SPX_ISPERT, &ispert);
        map["itrcnt"] = itrcnt;
        map["objval"] = objval;
        map["priminf"] = priminf;
        map["dualinf"] = dualinf;
        map["ispert"] = ispert;
    } else if (where == GRB_CB_MIP) {
        // Currently in MIP
        double objbst, objbnd, nodcnt, solcnt, cutcnt, nodlft, itrcnt;
        int openscenarios, phase;
        GRBcbget(cbdata, where, GRB_CB_MIP_OBJBST, &objbst);
        GRBcbget(cbdata, where, GRB_CB_MIP_OBJBND, &objbnd);
        GRBcbget(cbdata, where, GRB_CB_MIP_NODCNT, &nodcnt);
        GRBcbget(cbdata, where, GRB_CB_MIP_SOLCNT, &solcnt);
        GRBcbget(cbdata, where, GRB_CB_MIP_CUTCNT, &cutcnt);
        GRBcbget(cbdata, where, GRB_CB_MIP_NODLFT, &nodlft);
        GRBcbget(cbdata, where, GRB_CB_MIP_ITRCNT, &itrcnt);
        GRBcbget(cbdata, where, GRB_CB_MIP_OPENSCENARIOS, &openscenarios);
        GRBcbget(cbdata, where, GRB_CB_MIP_PHASE, &phase);
        map["objbst"] = objbst;
        map["objbnd"] = objbnd;
        map["nodcnt"] = nodcnt;
        map["solcnt"] = solcnt;
        map["cutcnt"] = cutcnt;
        map["nodlft"] = nodlft;
        map["itrcnt"] = itrcnt;
        map["openscenarios"] = openscenarios;
        map["phase"] = phase;
        // special keys to match similar ones in SCIP.
        map["primalbound"] = objbst;
        map["dualbound"] = objbnd;
        map["gap"] = 100 * (fabs(objbnd - objbst) /
                            (std::numeric_limits<double>::epsilon() + fabs(objbst)));
    } else if (where == GRB_CB_MIPSOL) {
        // Found a new MIP incumbent
        double obj, objbst, objbnd;
        int nodcnt, solcnt, openscenarios, phase;
        // GRBcbget(cbdata, where, GRB_CB_MIPSOL_SOL, &obj); ... this is a vector
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_OBJ, &obj);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_OBJBST, &objbst);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_OBJBND, &objbnd);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_NODCNT, &nodcnt);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_SOLCNT, &solcnt);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_OPENSCENARIOS, &openscenarios);
        GRBcbget(cbdata, where, GRB_CB_MIPSOL_PHASE, &phase);
        map["obj"] = obj;
        map["objbst"] = objbst;
        map["objbnd"] = objbnd;
        map["nodcnt"] = nodcnt;
        map["solcnt"] = solcnt;
        map["openscenarios"] = openscenarios;
        map["phase"] = phase;
        // special keys to match similar ones in SCIP.
        map["primalbound"] = objbst;
        map["dualbound"] = objbnd;
        map["gap"] = 100 * (fabs(objbnd - objbst) /
                            (std::numeric_limits<double>::epsilon() + fabs(objbst)));
    } else if (where == GRB_CB_MIPNODE) {
        // Currently exploring a MIP node
        double objbst, objbnd, nodcnt;
        int solcnt, openscenarios, phase, status;
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_STATUS, &status);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_OBJBST, &objbst);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_OBJBND, &objbnd);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_NODCNT, &nodcnt);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_SOLCNT, &solcnt);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_OPENSCENARIOS, &openscenarios);
        GRBcbget(cbdata, where, GRB_CB_MIPNODE_PHASE, &phase);
        map["status"] = status;
        map["objbst"] = objbst;
        map["objbnd"] = objbnd;
        map["nodcnt"] = nodcnt;
        map["solcnt"] = solcnt;
        map["openscenarios"] = openscenarios;
        map["phase"] = phase;
        // special keys to match similar ones in SCIP.
        map["primalbound"] = objbst;
        map["dualbound"] = objbnd;
        map["gap"] = 100 * (fabs(objbnd - objbst) /
                            (std::numeric_limits<double>::epsilon() + fabs(objbst)));
    } else if (where == GRB_CB_MESSAGE) {
        // Printing a log message
        char* msg;
        GRBcbget(cbdata, where, GRB_CB_MSG_STRING, &msg);
        map["message"] = msg;
    }

    backend->emitEventData(map);
    return 0;
}
