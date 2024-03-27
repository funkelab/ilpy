#include <Python.h>

#include <stdexcept>

#include "objscip/objscip.h"

// TODO: narrow these down to the ones we actually need
const char* getEventTypeName(SCIP_EVENTTYPE eventtype) {
    switch (eventtype) {
        case SCIP_EVENTTYPE_PRESOLVEROUND: return "PRESOLVEROUND";
        case SCIP_EVENTTYPE_BESTSOLFOUND: return "BESTSOLFOUND";

        // We're not currently using these
        // case SCIP_EVENTTYPE_DISABLED: return "DISABLED";
        // case SCIP_EVENTTYPE_VARADDED: return "VARADDED";
        // case SCIP_EVENTTYPE_VARDELETED: return "VARDELETED";
        // case SCIP_EVENTTYPE_VARFIXED: return "VARFIXED";
        // case SCIP_EVENTTYPE_VARUNLOCKED: return "VARUNLOCKED";
        // case SCIP_EVENTTYPE_OBJCHANGED: return "OBJCHANGED";
        // case SCIP_EVENTTYPE_GLBCHANGED: return "GLBCHANGED";
        // case SCIP_EVENTTYPE_GUBCHANGED: return "GUBCHANGED";
        // case SCIP_EVENTTYPE_LBTIGHTENED: return "LBTIGHTENED";
        // case SCIP_EVENTTYPE_LBRELAXED: return "LBRELAXED";
        // case SCIP_EVENTTYPE_UBTIGHTENED: return "UBTIGHTENED";
        // case SCIP_EVENTTYPE_UBRELAXED: return "UBRELAXED";
        // case SCIP_EVENTTYPE_GHOLEADDED: return "GHOLEADDED";
        // case SCIP_EVENTTYPE_GHOLEREMOVED: return "GHOLEREMOVED";
        // case SCIP_EVENTTYPE_LHOLEADDED: return "LHOLEADDED";
        // case SCIP_EVENTTYPE_LHOLEREMOVED: return "LHOLEREMOVED";
        // case SCIP_EVENTTYPE_IMPLADDED: return "IMPLADDED";
        // case SCIP_EVENTTYPE_TYPECHANGED: return "TYPECHANGED";
        // case SCIP_EVENTTYPE_NODEFOCUSED: return "NODEFOCUSED";
        // case SCIP_EVENTTYPE_NODEFEASIBLE: return "NODEFEASIBLE";
        // case SCIP_EVENTTYPE_NODEINFEASIBLE: return "NODEINFEASIBLE";
        // case SCIP_EVENTTYPE_NODEBRANCHED: return "NODEBRANCHED";
        // case SCIP_EVENTTYPE_NODEDELETE: return "NODEDELETE";
        // case SCIP_EVENTTYPE_FIRSTLPSOLVED: return "FIRSTLPSOLVED";
        // case SCIP_EVENTTYPE_LPSOLVED: return "LPSOLVED";
        // case SCIP_EVENTTYPE_POORSOLFOUND: return "POORSOLFOUND";
        // case SCIP_EVENTTYPE_ROWADDEDSEPA: return "ROWADDEDSEPA";
        // case SCIP_EVENTTYPE_ROWDELETEDSEPA: return "ROWDELETEDSEPA";
        // case SCIP_EVENTTYPE_ROWADDEDLP: return "ROWADDEDLP";
        // case SCIP_EVENTTYPE_ROWDELETEDLP: return "ROWDELETEDLP";
        // case SCIP_EVENTTYPE_ROWCOEFCHANGED: return "ROWCOEFCHANGED";
        // case SCIP_EVENTTYPE_ROWCONSTCHANGED: return "ROWCONSTCHANGED";
        // case SCIP_EVENTTYPE_ROWSIDECHANGED: return "ROWSIDECHANGED";
        // case SCIP_EVENTTYPE_SYNC: return "SYNC";
        // case SCIP_EVENTTYPE_GBDCHANGED: return "GBDCHANGED";
        // case SCIP_EVENTTYPE_LBCHANGED: return "LBCHANGED";
        // case SCIP_EVENTTYPE_UBCHANGED: return "UBCHANGED";
        // case SCIP_EVENTTYPE_BOUNDTIGHTENED: return "BOUNDTIGHTENED";
        // case SCIP_EVENTTYPE_BOUNDRELAXED: return "BOUNDRELAXED";
        // case SCIP_EVENTTYPE_BOUNDCHANGED: return "BOUNDCHANGED";
        // case SCIP_EVENTTYPE_GHOLECHANGED: return "GHOLECHANGED";
        // case SCIP_EVENTTYPE_LHOLECHANGED: return "LHOLECHANGED";
        // case SCIP_EVENTTYPE_HOLECHANGED: return "HOLECHANGED";
        // case SCIP_EVENTTYPE_DOMCHANGED: return "DOMCHANGED";
        // case SCIP_EVENTTYPE_VARCHANGED: return "VARCHANGED";
        // case SCIP_EVENTTYPE_VAREVENT: return "VAREVENT";
        // case SCIP_EVENTTYPE_NODESOLVED: return "NODESOLVED";
        // case SCIP_EVENTTYPE_NODEEVENT: return "NODEEVENT";
        // case SCIP_EVENTTYPE_LPEVENT: return "LPEVENT";
        // case SCIP_EVENTTYPE_SOLFOUND: return "SOLFOUND";
        // case SCIP_EVENTTYPE_ROWCHANGED: return "ROWCHANGED";
        // case SCIP_EVENTTYPE_ROWEVENT: return "ROWEVENT";
        // Add other cases here
        default: return "UNKNOWN";
    }
}

/** C++ wrapper object for event handlers */
class EventhdlrNewSol : public scip::ObjEventhdlr {
   private:
    SolverBackend* _backend;

   public:
    EventhdlrNewSol(SCIP* scip, SolverBackend* backend)
        : ObjEventhdlr(scip, "ilpy", "event handler for ilpy"), _backend(backend) {}
    virtual ~EventhdlrNewSol() {}

    /** initialization method of event handler (called after problem was transformed) */
    virtual SCIP_DECL_EVENTINIT(scip_init) {
        // clang-format off
        SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_PRESOLVEROUND,    eventhdlr, NULL, NULL));  /**< a presolving round has been finished */
        SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_BESTSOLFOUND,     eventhdlr, NULL, NULL));  /**< a new best primal feasible solution was found */

        // // These are likely to happen in most MIP runs, but don't necessarily provide useful information
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_FIRSTLPSOLVED,    eventhdlr, NULL, NULL));  /**< the node's initial LP was solved */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_POORSOLFOUND,     eventhdlr, NULL, NULL));  /**< a good enough primal feasible (but not new best) solution was found */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEDELETE,       eventhdlr, NULL, NULL));  /**< a node is about to be deleted from the tree */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEFOCUSED,      eventhdlr, NULL, NULL));  /**< a node has been focused and is now the focus node */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWDELETEDSEPA,   eventhdlr, NULL, NULL));  /**< a row has been removed from SCIP's separation storage */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWDELETEDLP,     eventhdlr, NULL, NULL));  /**< a row has been removed from the LP */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEINFEASIBLE,   eventhdlr, NULL, NULL));  /**< the focus node has been proven to be infeasible or was bounded */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWADDEDSEPA,     eventhdlr, NULL, NULL));  /**< a row has been added to SCIP's separation storage */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWADDEDLP,       eventhdlr, NULL, NULL));  /**< a row has been added to the LP */
        
        // // Not sure if we need these
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_DISABLED,         eventhdlr, NULL, NULL));  /**< the event was disabled and has no effect any longer */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VARADDED,         eventhdlr, NULL, NULL));  /**< a variable has been added to the transformed problem */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VARDELETED,       eventhdlr, NULL, NULL));  /**< a variable will be deleted from the transformed problem */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VARFIXED,         eventhdlr, NULL, NULL));  /**< a variable has been fixed, aggregated, or multi-aggregated */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VARUNLOCKED,      eventhdlr, NULL, NULL));  /**< the number of rounding locks of a variable was reduced to zero or one */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_OBJCHANGED,       eventhdlr, NULL, NULL));  /**< the objective value of a variable has been changed */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GLBCHANGED,       eventhdlr, NULL, NULL));  /**< the global lower bound of a variable has been changed */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GUBCHANGED,       eventhdlr, NULL, NULL));  /**< the global upper bound of a variable has been changed */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LBTIGHTENED,      eventhdlr, NULL, NULL));  /**< the local lower bound of a variable has been increased */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LBRELAXED,        eventhdlr, NULL, NULL));  /**< the local lower bound of a variable has been decreased */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_UBTIGHTENED,      eventhdlr, NULL, NULL));  /**< the local upper bound of a variable has been decreased */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_UBRELAXED,        eventhdlr, NULL, NULL));  /**< the local upper bound of a variable has been increased */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GHOLEADDED,       eventhdlr, NULL, NULL));  /**< a global hole has been added to the hole list of a variable's domain */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GHOLEREMOVED,     eventhdlr, NULL, NULL));  /**< a global hole has been removed from the hole list of a variable's domain */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LHOLEADDED,       eventhdlr, NULL, NULL));  /**< a local hole has been added to the hole list of a variable's domain */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LHOLEREMOVED,     eventhdlr, NULL, NULL));  /**< a local hole has been removed from the hole list of a variable's domain */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_IMPLADDED,        eventhdlr, NULL, NULL));  /**< the variable's implication list, variable bound or clique information was extended */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_TYPECHANGED,      eventhdlr, NULL, NULL));  /**< the type of a variable has changed */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEFEASIBLE,     eventhdlr, NULL, NULL));  /**< the LP/pseudo solution of the node was feasible */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEBRANCHED,     eventhdlr, NULL, NULL));  /**< the focus node has been solved by branching */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LPSOLVED,         eventhdlr, NULL, NULL));  /**< the node's LP was completely solved with cut & price */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWCOEFCHANGED,   eventhdlr, NULL, NULL));  /**< a coefficient of a row has been changed (row specific event) */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWCONSTCHANGED,  eventhdlr, NULL, NULL));  /**< the constant of a row has been changed (row specific event) */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWSIDECHANGED,   eventhdlr, NULL, NULL));  /**< a side of a row has been changed (row specific event) */
        // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_SYNC,             eventhdlr, NULL, NULL));  /**< synchronization event */
        // clang-format on

        return SCIP_OKAY;
    }

    virtual SCIP_DECL_EVENTEXIT(scip_exit) { return SCIP_OKAY; }

    virtual SCIP_DECL_EVENTEXEC(scip_exec) {
        if (!_backend->hasEventCallback()) {
            return SCIP_OKAY;  // don't bother collecting the data
        }

        // Create a map to store the event data
        std::map<std::string, std::variant<std::string, double, int, long long>> map;

        // all events will have these fields
        SCIP_EVENTTYPE eventtype = SCIPeventGetType(event);
        map["event_type"] = getEventTypeName(eventtype);
        map["backend"] = "scip";

        if (eventtype == SCIP_EVENTTYPE_PRESOLVEROUND) {
            map["nativeconss"] = SCIPgetNConss(scip);
            map["nbinvars"] = SCIPgetNBinVars(scip);
            map["nintvars"] = SCIPgetNIntVars(scip);
            map["nimplvars"] = SCIPgetNImplVars(scip);
            map["nenabledconss"] = SCIPgetNEnabledConss(scip);
            map["upperbound"] = SCIPgetUpperbound(scip);
            map["nactiveconss"] = SCIPgetNActiveConss(scip);
            map["nenabledconss"] = SCIPgetNEnabledConss(scip);
            map["nactiveconss"] = SCIPgetNActiveConss(scip);
            map["cutoffbound"] = SCIPgetCutoffbound(scip);
            map["nfixedvars"] = static_cast<int>(SCIPgetNFixedVars(scip));

        } else if (eventtype == SCIP_EVENTTYPE_BESTSOLFOUND) {
            map["avgdualbound"] = SCIPgetAvgDualbound(scip);
            map["avglowerbound"] = SCIPgetAvgLowerbound(scip);
            map["dualbound"] = SCIPgetDualbound(scip);
            map["lowerbound"] = SCIPgetLowerbound(scip);
            map["dualboundroot"] = SCIPgetDualboundRoot(scip);
            map["lowerboundroot"] = SCIPgetLowerboundRoot(scip);
            map["gap"] = SCIPgetGap(scip);
            map["nsolsfound"] = SCIPgetNSolsFound(scip);
            map["nlimsolsfound"] = SCIPgetNLimSolsFound(scip);
            map["nbestsolsfound"] = SCIPgetNBestSolsFound(scip);
            map["primalbound"] = SCIPgetPrimalbound(scip);
            map["nactiveconss"] = SCIPgetNActiveConss(scip);
            map["nenabledconss"] = SCIPgetNEnabledConss(scip);
            map["nactiveconss"] = SCIPgetNActiveConss(scip);
        }

        // map["deterministictime"] = SCIPgetDeterministicTime(scip);

        // map["nruns"] = SCIPgetNRuns(scip);
        // map["nreoptruns"] = SCIPgetNReoptRuns(scip);
        // map["nnodes"] = SCIPgetNNodes(scip);
        // map["ntotalnodes"] = SCIPgetNTotalNodes(scip);
        // map["nfeasibleleaves"] = SCIPgetNFeasibleLeaves(scip);
        // map["ninfeasibleleaves"] = SCIPgetNInfeasibleLeaves(scip);
        // map["nobjlimleaves"] = SCIPgetNObjlimLeaves(scip);
        // map["nrootboundchgs"] = SCIPgetNRootboundChgs(scip);
        // map["nrootboundchgsrun"] = SCIPgetNRootboundChgsRun(scip);
        // map["ndelayedcutoffs"] = SCIPgetNDelayedCutoffs(scip);
        // map["nlps"] = SCIPgetNLPs(scip);
        // map["nlpiterations"] = SCIPgetNLPIterations(scip);
        // map["nnzs"] = SCIPgetNNZs(scip);
        // map["nrootlpiterations"] = SCIPgetNRootLPIterations(scip);
        // map["nrootfirstlpiterations"] = SCIPgetNRootFirstLPIterations(scip);
        // map["nprimallps"] = SCIPgetNPrimalLPs(scip);
        // map["nprimallpiterations"] = SCIPgetNPrimalLPIterations(scip);
        // map["nduallps"] = SCIPgetNDualLPs(scip);
        // map["nduallpiterations"] = SCIPgetNDualLPIterations(scip);
        // map["nbarrierlps"] = SCIPgetNBarrierLPs(scip);
        // map["nbarrierlpiterations"] = SCIPgetNBarrierLPIterations(scip);
        // map["nresolvelps"] = SCIPgetNResolveLPs(scip);
        // map["nresolvelpiterations"] = SCIPgetNResolveLPIterations(scip);
        // map["nprimalresolvelps"] = SCIPgetNPrimalResolveLPs(scip);
        // map["nprimalresolvelpiterations"] = SCIPgetNPrimalResolveLPIterations(scip);
        // map["ndualresolvelps"] = SCIPgetNDualResolveLPs(scip);
        // map["ndualresolvelpiterations"] = SCIPgetNDualResolveLPIterations(scip);
        // map["nnodelps"] = SCIPgetNNodeLPs(scip);
        // map["nnodezeroiterationlps"] = SCIPgetNNodeZeroIterationLPs(scip);
        // map["nnodelpiterations"] = SCIPgetNNodeLPIterations(scip);
        // map["nnodeinitlps"] = SCIPgetNNodeInitLPs(scip);
        // map["nnodeinitlpiterations"] = SCIPgetNNodeInitLPIterations(scip);
        // map["ndivinglps"] = SCIPgetNDivingLPs(scip);
        // map["ndivinglpiterations"] = SCIPgetNDivingLPIterations(scip);
        // map["nstrongbranchs"] = SCIPgetNStrongbranchs(scip);
        // map["nstrongbranchlpiterations"] = SCIPgetNStrongbranchLPIterations(scip);
        // map["nrootstrongbranchs"] = SCIPgetNRootStrongbranchs(scip);
        // map["nrootstrongbranchlpiterations"] = SCIPgetNRootStrongbranchLPIterations(scip);
        // map["npricerounds"] = SCIPgetNPriceRounds(scip);
        // map["npricevars"] = SCIPgetNPricevars(scip);
        // map["npricevarsfound"] = SCIPgetNPricevarsFound(scip);
        // map["npricevarsapplied"] = SCIPgetNPricevarsApplied(scip);
        // map["nseparounds"] = SCIPgetNSepaRounds(scip);
        // map["ncutsfound"] = SCIPgetNCutsFound(scip);
        // map["ncutsfoundround"] = SCIPgetNCutsFoundRound(scip);
        // map["ncutsapplied"] = SCIPgetNCutsApplied(scip);
        // map["nconflictconssfound"] = SCIPgetNConflictConssFound(scip);
        // map["nconflictconssfoundnode"] = SCIPgetNConflictConssFoundNode(scip);
        // map["nconflictconssapplied"] = SCIPgetNConflictConssApplied(scip);
        // map["nconflictdualproofsapplied"] = SCIPgetNConflictDualproofsApplied(scip);
        // map["maxdepth"] = SCIPgetMaxDepth(scip);
        // map["maxtotaldepth"] = SCIPgetMaxTotalDepth(scip);
        // map["nbacktracks"] = SCIPgetNBacktracks(scip);
        // map["firstlpdualboundroot"] = SCIPgetFirstLPDualboundRoot(scip);
        // map["firstlplowerboundroot"] = SCIPgetFirstLPLowerboundRoot(scip);
        // map["firstprimalbound"] = SCIPgetFirstPrimalBound(scip);
        // map["transgap"] = SCIPgetTransGap(scip);
        // map["avgpseudocostscore"] = SCIPgetAvgPseudocostScore(scip);
        // map["avgpseudocostscorecurrentrun"] = SCIPgetAvgPseudocostScoreCurrentRun(scip);
        // map["avgconflictscore"] = SCIPgetAvgConflictScore(scip);
        // map["avgconflictscorecurrentrun"] = SCIPgetAvgConflictScoreCurrentRun(scip);
        // map["avgconflictlengthscore"] = SCIPgetAvgConflictlengthScore(scip);
        // map["avgconflictlengthscorecurrentrun"] = SCIPgetAvgConflictlengthScoreCurrentRun(scip);
        // map["avginferencescore"] = SCIPgetAvgInferenceScore(scip);
        // map["avginferencescorecurrentrun"] = SCIPgetAvgInferenceScoreCurrentRun(scip);
        // map["avgcutoffscore"] = SCIPgetAvgCutoffScore(scip);
        // map["avgcutoffscorecurrentrun"] = SCIPgetAvgCutoffScoreCurrentRun(scip);
        // map["nimplications"] = SCIPgetNImplications(scip);

        _backend->emitEventData(map);
        return SCIP_OKAY;
    }
};
