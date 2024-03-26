#ifndef INFERENCE_SOLVER_BACKEND_H__
#define INFERENCE_SOLVER_BACKEND_H__

#include <Python.h>
#include <variant>

#include "Objective.h"
#include "Constraints.h"
#include "Solution.h"
#include "VariableType.h"


PyObject* mapToPyObject(const std::map<std::string, std::variant<std::string, double>>& map) {
    PyObject* dict = PyDict_New();
    if (!dict) return nullptr; // check for successful allocation

    for (const auto& pair : map) {
		PyObject* pyValue;
		if (auto val = std::get_if<std::string>(&pair.second)) {
			pyValue = PyUnicode_FromString(val->c_str());
		} else if (auto val = std::get_if<double>(&pair.second)) {
			pyValue = PyFloat_FromDouble(*val);
		} else {
			Py_DECREF(dict);
			throw std::runtime_error("Unsupported type");
		}
		if (!pyValue) {
			Py_DECREF(dict);
			throw std::runtime_error("Failed to create Python object");
		}
        
		PyObject* pyKey = PyUnicode_FromString(pair.first.c_str());
		if (!pyKey) {
			Py_DECREF(pyValue);
			Py_DECREF(dict);
			throw std::runtime_error("Failed to create Python string");
		}
		
		if (PyDict_SetItem(dict, pyKey, pyValue) == -1) {
			Py_DECREF(pyKey);
			Py_DECREF(pyValue);
			Py_DECREF(dict);
			throw std::runtime_error("Failed to add item to Python dictionary");
		}
		Py_DECREF(pyKey);
		Py_DECREF(pyValue);
    }

    return dict;
}

class SolverBackend {

private:
	PyObject* _callback = nullptr;
	// double _last_gap = 0.0;

public:

	virtual ~SolverBackend() {
		Py_XDECREF(_callback);
	}

	/**
	 * Initialise the linear solver for the given type of variables.
	 *
	 * @param numVariables The number of variables in the problem.
	 * @param variableType The type of the variables (Continuous, Integer,
	 *                     Binary).
	 */
	virtual void initialize(
			unsigned int numVariables,
			VariableType variableType) = 0;

	/**
	 * Initialise the linear solver for the given type of variables.
	 *
	 * @param numVariables
	 *             The number of variables in the problem.
	 * 
	 * @param defaultVariableType
	 *             The default type of the variables (Continuous, Integer, 
	 *             Binary).
	 *
	 * @param specialVariableTypes
	 *             A map of variable numbers to variable types to override the 
	 *             default.
	 */
	virtual void initialize(
			unsigned int                                numVariables,
			VariableType                                defaultVariableType,
			const std::map<unsigned int, VariableType>& specialVariableTypes) = 0;

	/**
	 * Set the objective.
	 *
	 * @param objective A linear objective.
	 */
	virtual void setObjective(const Objective& objective) = 0;

	/**
	 * Set the linear (in)equality constraints.
	 *
	 * @param constraints A set of linear constraints.
	 */
	virtual void setConstraints(const Constraints& constraints) = 0;

	/**
	 * Add a single constraint.
	 *
	 * @param constraint A linear constraints.
	 */
	virtual void addConstraint(const Constraint& constraint) = 0;

	/**
	 * Set a timeout in seconds for subsequent solve calls.
	 */
	virtual void setTimeout(double timeout) = 0;

	/**
	 * Set the solver's optimality gap. The solver will terminate with an 
	 * "optimal" solution as soon as the gap between the upper and lower bound 
	 * is less than the given value times the upper bound.
	 *
	 * @param gap
	 *             The optimality gap.
	 *
	 * @param absolute
	 *             If set to true, a solution is considered optimal if the gap 
	 *             between the upper and lower bound is smaller than the given 
	 *             value.
	 */
	virtual void setOptimalityGap(double gap, bool absolute=false) = 0;

	/**
	 * Set the number of threads the solver can use.
	 *
	 * @param numThreads
	 *             The number of threads to use. Defaults to 0, which leaves the 
	 *             decision to the solver.
	 */
	virtual void setNumThreads(unsigned int numThreads) = 0;

	/**
	 * Turn verbose logging on or off.
	 *
	 * @param verbose
	 *             If set to true, verbose logging is enabled.
	 */
    virtual void setVerbose(bool verbose) = 0;
	
	/**
	 * Set a callback function to be called on various events.
	 * 
	*/
	virtual void setEventCallback(PyObject* callback) {
		Py_XDECREF(_callback);
		if (callback == Py_None) {
			_callback = nullptr;
		} else {
			_callback = callback;
			Py_INCREF(_callback);
		}
	}

	/**
	 * Get the event callback function or nullptr if no callback is set.
	 * 
	*/
	void emitEventData(
		const std::map<std::string, std::variant<std::string, double>>& map) {
		
		// auto it = map.find("gap");
		// if (it != map.end()) {
		// 	double gap = std::get<double>(it->second);
		// 	if (gap == _last_gap) return;
		// 	_last_gap = gap;
		// }

		if (_callback == nullptr) return;

		if (PyCallable_Check(_callback)) {
			PyObject* dict = mapToPyObject(map);
			if (!dict) return;

			PyObject* result = PyObject_CallFunctionObjArgs(_callback, dict, nullptr);
			if (result == nullptr) {
				PyErr_Print();
			}
			Py_XDECREF(result);
			Py_DECREF(dict);
		} else {
			throw std::runtime_error("Callback is not callable");
		}
	}

	/**
	 * Solve the problem.
	 *
	 * @param solution A solution object to write the solution to.
	 * @param value The optimal value of the objective.
	 * @param message A status message from the solver.
	 * @return true, if the optimal value was found.
	 */
	virtual bool solve(Solution& solution, std::string& message) = 0;


};

#endif // INFERENCE_SOLVER_BACKEND_H__

