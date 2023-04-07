#include <config.h>

#ifdef HAVE_GUROBI

#include <sstream>
#include <stdexcept>

#include "GurobiBackend.h"

#define GRB_CHECK(call) \
		grbCheck(#call, __FILE__, __LINE__, call)

GurobiBackend::GurobiBackend() :
	_numVariables(0),
	_numConstraints(0),
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
		_numConstraints = 0;
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
GurobiBackend::setObjective(const LinearObjective& objective) {

	setObjective((QuadraticObjective)objective);
}

void
GurobiBackend::setObjective(const QuadraticObjective& objective) {

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
GurobiBackend::setConstraints(const LinearConstraints& constraints) {

	// delete all previous constraints

	if (_numConstraints > 0) {

		int* constraintIndicies = new int[_numConstraints];
		for (unsigned int i = 0; i < _numConstraints; i++)
			constraintIndicies[i] = i;
		GRB_CHECK(GRBdelconstrs(_model, _numConstraints, constraintIndicies));

		GRB_CHECK(GRBupdatemodel(_model));
	}

	_numConstraints = constraints.size();
	unsigned int j = 0;
	for (const LinearConstraint& constraint : constraints) {

		addConstraint(constraint);

		j++;
	}

	GRB_CHECK(GRBupdatemodel(_model));
}

void
GurobiBackend::addConstraint(const LinearConstraint& constraint) {

	int numNz = constraint.getCoefficients().size();

	int*    inds = new int[numNz];
	double* vals = new double[numNz];

	// set the coefficients
	int i = 0;
	for (auto& pair : constraint.getCoefficients()) {

		inds[i] = pair.first;
		vals[i] = pair.second;
		i++;
	}

	GRB_CHECK(GRBaddconstr(
			_model,
			numNz,
			inds,
			vals,
			(constraint.getRelation() == LessEqual ? GRB_LESS_EQUAL :
					(constraint.getRelation() == GreaterEqual ? GRB_GREATER_EQUAL :
							GRB_EQUAL)),
			constraint.getValue(),
			NULL /* optional name */));

	delete[] inds;
	delete[] vals;
}

void
GurobiBackend::addConstraint(const QuadraticConstraint& constraint) {

	// FIXME: code duplication with addConstraint(LinearConstraint) 

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

bool
GurobiBackend::solve(Solution& x, std::string& msg) {

	GRB_CHECK(GRBupdatemodel(_model));

	if (_timeout > 0) {

		GRBenv* modelenv = GRBgetenv(_model);
		GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_TIMELIMIT, _timeout));
	}

	if (_gap >= 0) {

		GRBenv* modelenv = GRBgetenv(_model);
		if (_absoluteGap)
			GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_MIPGAPABS, _gap));
		else
			GRB_CHECK(GRBsetdblparam(modelenv, GRB_DBL_PAR_MIPGAP, _gap));
	}

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
