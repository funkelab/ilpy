#ifndef CANDIDATE_MC_SOLVER_BACKEND_FACTORY_H__
#define CANDIDATE_MC_SOLVER_BACKEND_FACTORY_H__

enum Preference { Any, Cplex, Gurobi, Scip };

// Function to convert Preference enum to string
std::string preferenceToString(Preference preference) {
    switch (preference) {
        case Any: return "Any";
        case Cplex: return "Cplex";
        case Gurobi: return "Gurobi";
        case Scip: return "Scip";
        default: return "Unknown";
    }
}

#endif // CANDIDATE_MC_SOLVER_BACKEND_FACTORY_H__

