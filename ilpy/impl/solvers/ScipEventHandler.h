#include <Python.h>

#include <stdexcept>

#include "objscip/objscip.h"

// TODO: narrow these down to the ones we actually need
const char* getEventTypeName(SCIP_EVENTTYPE eventtype) {
  switch (eventtype) {
    case SCIP_EVENTTYPE_DISABLED: return "DISABLED";
    case SCIP_EVENTTYPE_VARADDED: return "VARADDED";
    case SCIP_EVENTTYPE_VARDELETED: return "VARDELETED";
    case SCIP_EVENTTYPE_VARFIXED: return "VARFIXED";
    case SCIP_EVENTTYPE_VARUNLOCKED: return "VARUNLOCKED";
    case SCIP_EVENTTYPE_OBJCHANGED: return "OBJCHANGED";
    case SCIP_EVENTTYPE_GLBCHANGED: return "GLBCHANGED";
    case SCIP_EVENTTYPE_GUBCHANGED: return "GUBCHANGED";
    case SCIP_EVENTTYPE_LBTIGHTENED: return "LBTIGHTENED";
    case SCIP_EVENTTYPE_LBRELAXED: return "LBRELAXED";
    case SCIP_EVENTTYPE_UBTIGHTENED: return "UBTIGHTENED";
    case SCIP_EVENTTYPE_UBRELAXED: return "UBRELAXED";
    case SCIP_EVENTTYPE_GHOLEADDED: return "GHOLEADDED";
    case SCIP_EVENTTYPE_GHOLEREMOVED: return "GHOLEREMOVED";
    case SCIP_EVENTTYPE_LHOLEADDED: return "LHOLEADDED";
    case SCIP_EVENTTYPE_LHOLEREMOVED: return "LHOLEREMOVED";
    case SCIP_EVENTTYPE_IMPLADDED: return "IMPLADDED";
    case SCIP_EVENTTYPE_TYPECHANGED: return "TYPECHANGED";
    case SCIP_EVENTTYPE_PRESOLVEROUND: return "PRESOLVEROUND";
    case SCIP_EVENTTYPE_NODEFOCUSED: return "NODEFOCUSED";
    case SCIP_EVENTTYPE_NODEFEASIBLE: return "NODEFEASIBLE";
    case SCIP_EVENTTYPE_NODEINFEASIBLE: return "NODEINFEASIBLE";
    case SCIP_EVENTTYPE_NODEBRANCHED: return "NODEBRANCHED";
    case SCIP_EVENTTYPE_NODEDELETE: return "NODEDELETE";
    case SCIP_EVENTTYPE_FIRSTLPSOLVED: return "FIRSTLPSOLVED";
    case SCIP_EVENTTYPE_LPSOLVED: return "LPSOLVED";
    case SCIP_EVENTTYPE_POORSOLFOUND: return "POORSOLFOUND";
    case SCIP_EVENTTYPE_BESTSOLFOUND: return "BESTSOLFOUND";
    case SCIP_EVENTTYPE_ROWADDEDSEPA: return "ROWADDEDSEPA";
    case SCIP_EVENTTYPE_ROWDELETEDSEPA: return "ROWDELETEDSEPA";
    case SCIP_EVENTTYPE_ROWADDEDLP: return "ROWADDEDLP";
    case SCIP_EVENTTYPE_ROWDELETEDLP: return "ROWDELETEDLP";
    case SCIP_EVENTTYPE_ROWCOEFCHANGED: return "ROWCOEFCHANGED";
    case SCIP_EVENTTYPE_ROWCONSTCHANGED: return "ROWCONSTCHANGED";
    case SCIP_EVENTTYPE_ROWSIDECHANGED: return "ROWSIDECHANGED";
    case SCIP_EVENTTYPE_SYNC: return "SYNC";
    case SCIP_EVENTTYPE_GBDCHANGED: return "GBDCHANGED";
    case SCIP_EVENTTYPE_LBCHANGED: return "LBCHANGED";
    case SCIP_EVENTTYPE_UBCHANGED: return "UBCHANGED";
    case SCIP_EVENTTYPE_BOUNDTIGHTENED: return "BOUNDTIGHTENED";
    case SCIP_EVENTTYPE_BOUNDRELAXED: return "BOUNDRELAXED";
    case SCIP_EVENTTYPE_BOUNDCHANGED: return "BOUNDCHANGED";
    case SCIP_EVENTTYPE_GHOLECHANGED: return "GHOLECHANGED";
    case SCIP_EVENTTYPE_LHOLECHANGED: return "LHOLECHANGED";
    case SCIP_EVENTTYPE_HOLECHANGED: return "HOLECHANGED";
    case SCIP_EVENTTYPE_DOMCHANGED: return "DOMCHANGED";
    case SCIP_EVENTTYPE_VARCHANGED: return "VARCHANGED";
    case SCIP_EVENTTYPE_VAREVENT: return "VAREVENT";
    case SCIP_EVENTTYPE_NODESOLVED: return "NODESOLVED";
    case SCIP_EVENTTYPE_NODEEVENT: return "NODEEVENT";
    case SCIP_EVENTTYPE_LPEVENT: return "LPEVENT";
    case SCIP_EVENTTYPE_SOLFOUND: return "SOLFOUND";
    case SCIP_EVENTTYPE_ROWCHANGED: return "ROWCHANGED";
    case SCIP_EVENTTYPE_ROWEVENT: return "ROWEVENT";
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
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_PRESOLVEROUND, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEDELETE, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GBDCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LBCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_UBCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_BOUNDTIGHTENED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_BOUNDRELAXED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_BOUNDCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_GHOLECHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LHOLECHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_HOLECHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_DOMCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VARCHANGED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_VAREVENT, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODESOLVED, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_NODEEVENT, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_LPEVENT, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_SOLEVENT, eventhdlr, NULL, NULL));
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWCHANGED, eventhdlr, NULL, NULL));
    // this is VERY verbose
    // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWEVENT, eventhdlr, NULL, NULL));

    // This is also verbose, but if you want to be notified at least every gap change, this is one way
    // SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWADDEDLP, eventhdlr, NULL, NULL));

    return SCIP_OKAY;
  }

  virtual SCIP_DECL_EVENTEXIT(scip_exit) { return SCIP_OKAY; }

  virtual SCIP_DECL_EVENTEXEC(scip_exec) {
      if (!_backend->hasEventCallback()) {
        return SCIP_OKAY; // don't bother collecting the data
    }

    _backend->emitEventData({
      {"backend", "scip"},
      {"event_type", getEventTypeName(SCIPeventGetType(event))},
      {"gap", SCIPgetGap(scip)},
      {"dualbound", SCIPgetDualbound(scip)},
      {"primalbound", SCIPgetPrimalbound(scip)}
    });

    return SCIP_OKAY;
  }
};
