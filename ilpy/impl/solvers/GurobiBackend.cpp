#include <config.h>

#ifdef HAVE_GUROBI

#include <sstream>
#include <stdexcept>

#include "GurobiBackend.h"

#define GRB_CHECK(call) \
        grbCheck(#call, __FILE__, __LINE__, call)

GurobiBackend::GurobiBackend() :
    _numVariables(0),
    _env(0),
    _model(0),
    _timeout(0),
    _gap(-1),
    _absoluteGap(false) {

    GRB_CHECK(GRBloadenv(&_env, NULL));
}

GurobiBackend::~GurobiBackend() {

    if (_model)
        GRBfreemodel(_model);

    if (_env)
        GRBfreeenv(_env);
}

void
GurobiBackend::initialize(
        unsigned int numVariables,
        VariableType variableType) {

    initialize(numVariables, variableType, std::map<unsigned int, VariableType>());
}

void
GurobiBackend::initialize(
        unsigned int                                numVariables,
        VariableType                                defaultVariableType,
        const std::map<unsigned int, VariableType>& specialVariableTypes) {

    // create a new model

    if (_model) {
        GRBfreemodel(_model);
    }
    GRB_CHECK(GRBnewmodel(_env, &_model, NULL, 0, NULL, NULL, NULL, NULL, NULL));

    // set parameters

    setVerbose(false);

    // add new variables to the model

    _numVariables = numVariables;

    // create arrays of  variable types and infinite lower bounds
    char* vtypes = new char[_numVariables];
    double* lbs = new double[_numVariables];
    for (unsigned int i = 0; i < _numVariables; i++) {

        VariableType type = defaultVariableType;
        if (specialVariableTypes.count(i))
            type = specialVariableTypes.at(i);
        char t = (type == Binary ? 'B' : (type == Integer ? 'I' : 'C'));

        vtypes[i] = t;
        lbs[i] = -GRB_INFINITY;
    }

    GRB_CHECK(GRBaddvars(
            _model,
            _numVariables,
            0,                // num non-zeros for constraint matrix (we set it later)
            NULL, NULL, NULL, // vbeg, vind, vval for constraint matrix
            NULL,             // obj (we set it later)
            lbs, NULL,        // lower and upper bound, set to -inf and inf
            vtypes,           // variable types
            NULL));           // names

    GRB_CHECK(GRBupdatemodel(_model));

    delete[] vtypes;
    delete[] lbs;
}

void
GurobiBackend::setObjective(const Objective& objective) {

    // set sense of objective
    if (objective.getSense() == Minimize) {
        GRB_CHECK(GRBsetintattr(_model, GRB_INT_ATTR_MODELSENSE, +1));
    } else {
        GRB_CHECK(GRBsetintattr(_model, GRB_INT_ATTR_MODELSENSE, -1));
    }

    // set the constant value of the objective
    GRB_CHECK(GRBsetdblattr(_model, GRB_DBL_ATTR_OBJCON, objective.getConstant()));

    GRB_CHECK(GRBsetdblattrarray(
            _model,
            GRB_DBL_ATTR_OBJ,
            0 /* start */, _numVariables,
            const_cast<double*>(&objective.getCoefficients()[0])));

    // remove all previous quadratic terms
    GRB_CHECK(GRBdelq(_model));

    // set the quadratic coefficients for all pairs of variables
    for (auto& pair : objective.getQuadraticCoefficients()) {

        const std::pair<unsigned int, unsigned int>& variables = pair.first;
        float value = pair.second;

        if (value != 0) {

            int row = variables.first;
            int col = variables.second;
            double val = value;
            GRB_CHECK(GRBaddqpterms(_model, 1, &row, &col, &val));
        }
    }

    GRB_CHECK(GRBupdatemodel(_model));
}

void
GurobiBackend::setConstraints(const Constraints &constraints)
{
    int numConstrs;

    // Get the number of constraints
    GRB_CHECK(GRBgetintattr(_model, GRB_INT_ATTR_NUMCONSTRS, &numConstrs));

    // Remove all constraints if there are any
    if (numConstrs > 0)
    {
        int *constraintIndicies = new int[numConstrs];
        for (unsigned int i = 0; i < numConstrs; i++)
            constraintIndicies[i] = i;

        GRB_CHECK(GRBdelconstrs(_model, numConstrs, constraintIndicies));
        delete[] constraintIndicies;

        GRB_CHECK(GRBupdatemodel(_model));
    }

    for (const Constraint &constraint : constraints)
        addConstraint(constraint);

    // Update the model to include new constraints
    GRB_CHECK(GRBupdatemodel(_model));
}

void
GurobiBackend::addConstraint(const Constraint& constraint) {

    // set the linear coefficients
    int numlNz = constraint.getCoefficients().size();

    int*    linds = new int[numlNz];
    double* lvals = new double[numlNz];

    int i = 0;
    for (auto& pair : constraint.getCoefficients()) {

        linds[i] = pair.first;
        lvals[i] = pair.second;
        i++;
    }

    // set the quadratic coefficients
    int numqNz = constraint.getQuadraticCoefficients().size();

    int*    qrows = new int[numqNz];
    int*    qcols = new int[numqNz];
    double* qvals = new double[numqNz];

    int qi = 0;
    for (auto& pair : constraint.getQuadraticCoefficients()) {

        qrows[qi] = pair.first.first;
        qcols[qi] = pair.first.second;
        qvals[qi] = pair.second;
        qi++;
    }

    GRB_CHECK(GRBaddqconstr(
            _model,
            numlNz,
            linds,
            lvals,
            numqNz,
            qrows,
            qcols,
            qvals,
            (constraint.getRelation() == LessEqual ? GRB_LESS_EQUAL :
                    (constraint.getRelation() == GreaterEqual ? GRB_GREATER_EQUAL :
                            GRB_EQUAL)),
            constraint.getValue(),
            NULL /* optional name */));

    delete[] linds;
    delete[] lvals;
    delete[] qrows;
    delete[] qcols;
    delete[] qvals;
}


const char* getEventTypeName(int where) {
    switch (where)
    {
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
int __stdcall GurobiBackend::eventCallback(CB_ARGS) {

    if (where == GRB_CB_POLLING){
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
    std::map<std::string, std::variant<std::string, double, int>> map;

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
        map["gap"] = 100 * (fabs(objbnd - objbst) / (std::numeric_limits<double>::epsilon() + fabs(objbst)));
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
        map["gap"] = 100 * (fabs(objbnd - objbst) / (std::numeric_limits<double>::epsilon() + fabs(objbst)));
    } else if (where == GRB_CB_MIPNODE){
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
        map["gap"] = 100 * (fabs(objbnd - objbst) / (std::numeric_limits<double>::epsilon() + fabs(objbst)));
    } else if (where == GRB_CB_MESSAGE) {
        // Printing a log message
        char* msg;
        GRBcbget(cbdata, where, GRB_CB_MSG_STRING, &msg);
        map["message"] = msg;
    }

    backend->emitEventData(map);
    return 0;
}

bool
GurobiBackend::solve(Solution& x, std::string& msg) {

    GRB_CHECK(GRBupdatemodel(_model));

    GRBenv* modelenv = GRBgetenv(_model);

    if (_timeout > 0) {

        GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_TIMELIMIT, _timeout));
    }

    if (_gap >= 0) {

        if (_absoluteGap)
            GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_MIPGAPABS, _gap));
        else
            GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_MIPGAP, _gap));
    }

    // Sets the strategy for handling non-convex quadratic objectives
    // or non-convex quadratic constraints. 
    // 0 = an error is reported if the original user model contains non-convex
    //     quadratic constructs.
    // 1 = an error is reported if non-convex quadratic constructs could not be
    //     discarded or linearized during presolve.
    // 2 = non-convex quadratic problems are solved by means of translating them
    //     into bilinear form and applying spatial branching.
    GRB_CHECK(GRBsetintparam(modelenv, GRB_INT_PAR_NONCONVEX, 2));

    // Set the callback function
    GRBsetcallbackfunc(_model, eventCallback, this);

    GRB_CHECK(GRBoptimize(_model));

    int status;
    GRB_CHECK(GRBgetintattr(_model, GRB_INT_ATTR_STATUS, &status));

    if (status != GRB_OPTIMAL) {

        msg = "Optimal solution *NOT* found";

        // see if a feasible solution exists

        if (status == GRB_TIME_LIMIT) {

            msg += " (timeout)";

            int numSolutions;
            GRB_CHECK(GRBgetintattr(_model, GRB_INT_ATTR_SOLCOUNT, &numSolutions));

            if (numSolutions == 0) {

                msg += ", no feasible solution found)";
                return false;
            }

        } else if (status == GRB_SUBOPTIMAL) {

            msg += " (suboptimal solution found)";

        } else {

            return false;
        }

    } else {

        msg = "Optimal solution found";
    }

    // extract solution
    x.resize(_numVariables);
    for (unsigned int i = 0; i < _numVariables; i++)
        // in case of several suboptimal solutions, the best-objective solution 
        // is read
        GRB_CHECK(GRBgetdblattrelement(_model, GRB_DBL_ATTR_X, i, &x[i]));

    // get current value of the objective
    double value;
    GRB_CHECK(GRBgetdblattr(_model, GRB_DBL_ATTR_OBJVAL, &value));
    x.setValue(value);

    return true;
}

void
GurobiBackend::setMIPFocus(unsigned int focus) {

    GRBenv* modelenv = GRBgetenv(_model);
    GRB_CHECK(GRBsetintparam(modelenv, GRB_INT_PAR_MIPFOCUS, focus));
}

void
GurobiBackend::setNumThreads(unsigned int numThreads) {

    GRBenv* modelenv = GRBgetenv(_model);
    GRB_CHECK(GRBsetintparam(modelenv, GRB_INT_PAR_THREADS, numThreads));
}

void
GurobiBackend::setVerbose(bool verbose) {

    GRBenv* modelenv = GRBgetenv(_model);

    // setup GRB environment
    if (verbose) {
        GRB_CHECK(GRBsetintparam(modelenv, GRB_INT_PAR_OUTPUTFLAG, 1));
    } else {
        GRB_CHECK(GRBsetintparam(modelenv, GRB_INT_PAR_OUTPUTFLAG, 0));
    }
}

void
GurobiBackend::dumpProblem(std::string filename) {

    // append a random number to avoid overwrites by subsequent calls
    std::stringstream s;
    s << rand() << "_" << filename;

    GRB_CHECK(GRBwrite(_model, s.str().c_str()));
}

void
GurobiBackend::grbCheck(const char* call, const char* file, int line, int error) {

    if (error) {

        std::stringstream s;
        s << "Gurobi error in " << file << ":" << line << ": "
          << GRBgeterrormsg(_env);

        throw std::runtime_error(s.str());
    }
}

#endif // HAVE_GUROBI
