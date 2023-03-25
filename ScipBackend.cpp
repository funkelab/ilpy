#include <config.h>

#ifdef HAVE_SCIP

#include <sstream>

#include <scip/scipdefplugins.h>
#include <scip/cons_linear.h>

#include "ScipBackend.h"

ScipBackend::ScipBackend() :
		_scip(0) {

	SCIP_CALL_ABORT(SCIPcreate(&_scip));
	SCIP_CALL_ABORT(SCIPincludeDefaultPlugins(_scip));
	SCIP_CALL_ABORT(SCIPcreateProbBasic(_scip, "problem"));
}

ScipBackend::~ScipBackend() {

	freeVariables();
	freeConstraints();

	if (_scip != 0)
		SCIP_CALL_ABORT(SCIPfree(&_scip));
}

void
ScipBackend::initialize(
		unsigned int numVariables,
		VariableType variableType) {

	initialize(numVariables, variableType, std::map<unsigned int, VariableType>());
}

void
ScipBackend::initialize(
		unsigned int                                numVariables,
		VariableType                                defaultVariableType,
		const std::map<unsigned int, VariableType>& specialVariableTypes) {

	setVerbose(false);

	_numVariables = numVariables;

	// delete previous variables
	freeVariables();

	for (int i = 0; i < _numVariables; i++) {

		SCIP_VAR* v;
		std::string name("x");
		name += std::to_string(i);

		double lb, ub;
		SCIP_VARTYPE type = scipVarType(
				specialVariableTypes.count(i) ? specialVariableTypes.at(i) : defaultVariableType,
				lb, ub);

		SCIP_CALL_ABORT(SCIPcreateVarBasic(_scip, &v, name.c_str(), lb, ub, 0 /* obj */, type));
		SCIP_CALL_ABORT(SCIPaddVar(_scip, v));

		_variables.push_back(v);
	}

	for (SCIP_VAR* v : _variables)
		SCIP_CALL_ABORT(SCIPreleaseVar(_scip, &v));
}

void
ScipBackend::setObjective(const LinearObjective& objective) {

	setObjective((QuadraticObjective)objective);
}

void
ScipBackend::setObjective(const QuadraticObjective& objective) {

	// set sense of objective
	if (objective.getSense() == Minimize)
		SCIP_CALL_ABORT(SCIPsetObjsense(_scip, SCIP_OBJSENSE_MINIMIZE));
	else
		SCIP_CALL_ABORT(SCIPsetObjsense(_scip, SCIP_OBJSENSE_MAXIMIZE));

	// set the constant value of the objective

	double offset = SCIPgetOrigObjoffset(_scip);
	SCIP_CALL_ABORT(SCIPaddOrigObjoffset(_scip, objective.getConstant() - offset));

	for (unsigned int i = 0; i < _numVariables; i++) {

		SCIP_CALL_ABORT(SCIPchgVarObj(_scip, _variables[i], objective.getCoefficients()[i]));
	}

	// add quadratically constrained auxiliary variables for each quadratic
	// coefficients
	for (auto& pair : objective.getQuadraticCoefficients()) {

		const std::pair<unsigned int, unsigned int>& variables = pair.first;
		float value = pair.second;

		if (value != 0) {

			unsigned int i = variables.first;
			unsigned int j = variables.second;

			// create z_ij and add val * z_ij to objective

			SCIP_VAR* z_ij;
			std::string name("z");
			name += std::to_string(i) + "," + std::to_string(j);
			// z_ij cand be unbounded and real, it inherits all other
			// bounds/integrality from the x_i * x_j = z_ij constraint below
			double lb = -SCIPinfinity(_scip);
			double ub =  SCIPinfinity(_scip);
			SCIP_VARTYPE type = SCIP_VARTYPE_CONTINUOUS;
			SCIP_CALL_ABORT(SCIPcreateVarBasic(_scip, &z_ij, name.c_str(), lb, ub, value /* obj */, type));
			SCIP_CALL_ABORT(SCIPaddVar(_scip, z_ij));

			// add constraint x_i * x_j - z_ij = 0
			addMulEqualConstraint(i, j, z_ij);

			// decrease reference count (we are done with z_ij)
			SCIP_CALL_ABORT(SCIPreleaseVar(_scip, &z_ij));
		}
	}
}

void
ScipBackend::setConstraints(const LinearConstraints& constraints) {

	// remove previous constraints
	freeConstraints();

	// allocate memory for new constraints
	_constraints.reserve(constraints.size());

	unsigned int j = 0;
	for (const LinearConstraint& constraint : constraints) {

		addConstraint(constraint);

		j++;
	}
}

void
ScipBackend::addConstraint(const LinearConstraint& constraint) {

	addConstraint((QuadraticConstraint)constraint);
}

void
ScipBackend::addConstraint(const QuadraticConstraint& constraint) {

	// create a list of variables and their coefficients
	std::vector<SCIP_VAR*> vars;
	std::vector<SCIP_Real> coefs;
	for (auto& p : constraint.getCoefficients()) {
		vars.push_back(_variables[p.first]);
		coefs.push_back(p.second);
	}

	// create the SCIP constraint lhs <= linear expr <= rhs
	SCIP_CONS* c;
	std::string name("c");
	name += std::to_string(_constraints.size());

	// set lhs and rhs according to constraint relation
	SCIP_Real lhs = constraint.getValue();
	SCIP_Real rhs = constraint.getValue();
	if (constraint.getRelation() == LessEqual)
		lhs = -SCIPinfinity(_scip);
	if (constraint.getRelation() == GreaterEqual)
		rhs = SCIPinfinity(_scip);

	SCIP_CALL_ABORT(SCIPcreateConsBasicLinear(
			_scip,
			&c,
			name.c_str(),
			vars.size(),
			&vars[0],
			&coefs[0],
			lhs,
			rhs));

	_constraints.push_back(c);

	SCIP_CALL_ABORT(SCIPaddCons(_scip, c));
	SCIP_CALL_ABORT(SCIPreleaseCons(_scip, &c));
}

void
ScipBackend::setTimeout(double timeout) {

	SCIP_CALL_ABORT(SCIPsetRealParam(_scip, "limits/time", timeout));
}

void
ScipBackend::setOptimalityGap(double gap, bool absolute) {

	if (absolute)
		SCIP_CALL_ABORT(SCIPsetRealParam(_scip, "limits/absgap", gap));
	else
		SCIP_CALL_ABORT(SCIPsetRealParam(_scip, "limits/gap", gap));
}

void
ScipBackend::setNumThreads(unsigned int numThreads) {

	SCIP_CALL_ABORT(SCIPsetIntParam(_scip, "lp/threads", numThreads));
}

bool
ScipBackend::solve(Solution& x, std::string& msg) {

	SCIP_CALL_ABORT(SCIPpresolve(_scip));
	SCIP_CALL_ABORT(SCIPsolve(_scip));

	if (SCIPgetNSols(_scip) == 0) {

		msg = "Optimal solution *NOT* found";
		return false;
	}

	// extract solution
	SCIP_SOL* sol = SCIPgetBestSol(_scip);

	x.resize(_numVariables);
	for (unsigned int i = 0; i < _numVariables; i++)
		x[i] = SCIPgetSolVal(_scip, sol, _variables[i]);

	// get current value of the objective
	x.setValue(SCIPgetSolOrigObj(_scip, sol));

	SCIP_CALL_ABORT(SCIPfreeTransform(_scip));

	return true;
}

void
ScipBackend::setVerbose(bool verbose) {

	int level = verbose ? 4 : 0;
	SCIP_CALL_ABORT(SCIPsetIntParam(_scip, "display/verblevel", level));
}

void
ScipBackend::addMulEqualConstraint(unsigned int i, unsigned int j, SCIP_VAR* z_ij) {

	// add the following quadratic constraint:
	// x_i * x_j - z_ij = 0

	SCIP_VAR* x_i = _variables[i];
	SCIP_VAR* x_j = _variables[j];
	SCIP_Real lin_coef = -1.0;
	SCIP_Real quad_coef = 1.0;

	// create the SCIP constraint lhs <= linear expr <= rhs
	SCIP_CONS* c;
	std::string name("c_z");
	name += std::to_string(i) + "," + std::to_string(j);

	// set lhs and rhs according to constraint relation
	SCIP_Real lhs = 0.0;
	SCIP_Real rhs = 0.0;

	SCIP_CALL_ABORT(SCIPcreateConsBasicQuadraticNonlinear(
			_scip,
			&c,
			name.c_str(),
			1, /* nlinvars */
			&z_ij, /* linvars */
			&lin_coef, /* lincoefs */
			1, /* nquadterms */
			&x_i, /* quadvars1 */
			&x_j, /* quadvars2 */
			&quad_coef, /* quadcoefs */
			lhs,
			rhs));

	SCIP_CALL_ABORT(SCIPaddCons(_scip, c));
	SCIP_CALL_ABORT(SCIPreleaseCons(_scip, &c));
}

void
ScipBackend::freeVariables() {

	// SCIPfree should free the variables for us
	_variables.clear();
}

void
ScipBackend::freeConstraints() {

	// SCIPfree should free the constraints for us
	_constraints.clear();
}

SCIP_VARTYPE
ScipBackend::scipVarType(VariableType type, double& lb, double& ub) {

	if (type == Binary) {

		lb = 0;
		ub = 1;
		return SCIP_VARTYPE_INTEGER;
	}

	if (type == Integer) {

		lb = -SCIPinfinity(_scip);
		ub =  SCIPinfinity(_scip);
		return SCIP_VARTYPE_INTEGER;
	}

	if (type == Continuous) {

		lb = -SCIPinfinity(_scip);
		ub =  SCIPinfinity(_scip);
		return SCIP_VARTYPE_CONTINUOUS;
	}

	assert(false);
}

#endif // HAVE_SCIP

