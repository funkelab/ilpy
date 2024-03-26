#ifdef NO_PYTHON
typedef void PyObject;
#else
#include <Python.h>
#endif

#include <stdexcept>

#include "objscip/objscip.h"

// TODO: narrow these down to the ones we actually need
const char* getEventTypeName(SCIP_EVENTTYPE eventtype) {
  switch (eventtype) {
    case SCIP_EVENTTYPE_DISABLED: return "SCIP_EVENTTYPE_DISABLED";
    case SCIP_EVENTTYPE_VARADDED: return "SCIP_EVENTTYPE_VARADDED";
    case SCIP_EVENTTYPE_VARDELETED: return "SCIP_EVENTTYPE_VARDELETED";
    case SCIP_EVENTTYPE_VARFIXED: return "SCIP_EVENTTYPE_VARFIXED";
    case SCIP_EVENTTYPE_VARUNLOCKED: return "SCIP_EVENTTYPE_VARUNLOCKED";
    case SCIP_EVENTTYPE_OBJCHANGED: return "SCIP_EVENTTYPE_OBJCHANGED";
    case SCIP_EVENTTYPE_GLBCHANGED: return "SCIP_EVENTTYPE_GLBCHANGED";
    case SCIP_EVENTTYPE_GUBCHANGED: return "SCIP_EVENTTYPE_GUBCHANGED";
    case SCIP_EVENTTYPE_LBTIGHTENED: return "SCIP_EVENTTYPE_LBTIGHTENED";
    case SCIP_EVENTTYPE_LBRELAXED: return "SCIP_EVENTTYPE_LBRELAXED";
    case SCIP_EVENTTYPE_UBTIGHTENED: return "SCIP_EVENTTYPE_UBTIGHTENED";
    case SCIP_EVENTTYPE_UBRELAXED: return "SCIP_EVENTTYPE_UBRELAXED";
    case SCIP_EVENTTYPE_GHOLEADDED: return "SCIP_EVENTTYPE_GHOLEADDED";
    case SCIP_EVENTTYPE_GHOLEREMOVED: return "SCIP_EVENTTYPE_GHOLEREMOVED";
    case SCIP_EVENTTYPE_LHOLEADDED: return "SCIP_EVENTTYPE_LHOLEADDED";
    case SCIP_EVENTTYPE_LHOLEREMOVED: return "SCIP_EVENTTYPE_LHOLEREMOVED";
    case SCIP_EVENTTYPE_IMPLADDED: return "SCIP_EVENTTYPE_IMPLADDED";
    case SCIP_EVENTTYPE_TYPECHANGED: return "SCIP_EVENTTYPE_TYPECHANGED";
    case SCIP_EVENTTYPE_PRESOLVEROUND: return "SCIP_EVENTTYPE_PRESOLVEROUND";
    case SCIP_EVENTTYPE_NODEFOCUSED: return "SCIP_EVENTTYPE_NODEFOCUSED";
    case SCIP_EVENTTYPE_NODEFEASIBLE: return "SCIP_EVENTTYPE_NODEFEASIBLE";
    case SCIP_EVENTTYPE_NODEINFEASIBLE: return "SCIP_EVENTTYPE_NODEINFEASIBLE";
    case SCIP_EVENTTYPE_NODEBRANCHED: return "SCIP_EVENTTYPE_NODEBRANCHED";
    case SCIP_EVENTTYPE_NODEDELETE: return "SCIP_EVENTTYPE_NODEDELETE";
    case SCIP_EVENTTYPE_FIRSTLPSOLVED: return "SCIP_EVENTTYPE_FIRSTLPSOLVED";
    case SCIP_EVENTTYPE_LPSOLVED: return "SCIP_EVENTTYPE_LPSOLVED";
    case SCIP_EVENTTYPE_POORSOLFOUND: return "SCIP_EVENTTYPE_POORSOLFOUND";
    case SCIP_EVENTTYPE_BESTSOLFOUND: return "SCIP_EVENTTYPE_BESTSOLFOUND";
    case SCIP_EVENTTYPE_ROWADDEDSEPA: return "SCIP_EVENTTYPE_ROWADDEDSEPA";
    case SCIP_EVENTTYPE_ROWDELETEDSEPA: return "SCIP_EVENTTYPE_ROWDELETEDSEPA";
    case SCIP_EVENTTYPE_ROWADDEDLP: return "SCIP_EVENTTYPE_ROWADDEDLP";
    case SCIP_EVENTTYPE_ROWDELETEDLP: return "SCIP_EVENTTYPE_ROWDELETEDLP";
    case SCIP_EVENTTYPE_ROWCOEFCHANGED: return "SCIP_EVENTTYPE_ROWCOEFCHANGED";
    case SCIP_EVENTTYPE_ROWCONSTCHANGED: return "SCIP_EVENTTYPE_ROWCONSTCHANGED";
    case SCIP_EVENTTYPE_ROWSIDECHANGED: return "SCIP_EVENTTYPE_ROWSIDECHANGED";
    case SCIP_EVENTTYPE_SYNC: return "SCIP_EVENTTYPE_SYNC";
    case SCIP_EVENTTYPE_GBDCHANGED: return "SCIP_EVENTTYPE_GBDCHANGED";
    case SCIP_EVENTTYPE_LBCHANGED: return "SCIP_EVENTTYPE_LBCHANGED";
    case SCIP_EVENTTYPE_UBCHANGED: return "SCIP_EVENTTYPE_UBCHANGED";
    case SCIP_EVENTTYPE_BOUNDTIGHTENED: return "SCIP_EVENTTYPE_BOUNDTIGHTENED";
    case SCIP_EVENTTYPE_BOUNDRELAXED: return "SCIP_EVENTTYPE_BOUNDRELAXED";
    case SCIP_EVENTTYPE_BOUNDCHANGED: return "SCIP_EVENTTYPE_BOUNDCHANGED";
    case SCIP_EVENTTYPE_GHOLECHANGED: return "SCIP_EVENTTYPE_GHOLECHANGED";
    case SCIP_EVENTTYPE_LHOLECHANGED: return "SCIP_EVENTTYPE_LHOLECHANGED";
    case SCIP_EVENTTYPE_HOLECHANGED: return "SCIP_EVENTTYPE_HOLECHANGED";
    case SCIP_EVENTTYPE_DOMCHANGED: return "SCIP_EVENTTYPE_DOMCHANGED";
    case SCIP_EVENTTYPE_VARCHANGED: return "SCIP_EVENTTYPE_VARCHANGED";
    case SCIP_EVENTTYPE_VAREVENT: return "SCIP_EVENTTYPE_VAREVENT";
    case SCIP_EVENTTYPE_NODESOLVED: return "SCIP_EVENTTYPE_NODESOLVED";
    case SCIP_EVENTTYPE_NODEEVENT: return "SCIP_EVENTTYPE_NODEEVENT";
    case SCIP_EVENTTYPE_LPEVENT: return "SCIP_EVENTTYPE_LPEVENT";
    case SCIP_EVENTTYPE_SOLFOUND: return "SCIP_EVENTTYPE_SOLFOUND";
    case SCIP_EVENTTYPE_ROWCHANGED: return "SCIP_EVENTTYPE_ROWCHANGED";
    case SCIP_EVENTTYPE_ROWEVENT: return "SCIP_EVENTTYPE_ROWEVENT";
    // Add other cases here
    default: return "SCIP_EVENTTYPE_UNKNOWN";
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
    SCIP_CALL(SCIPcatchEvent(scip, SCIP_EVENTTYPE_ROWEVENT, eventhdlr, NULL, NULL));
    return SCIP_OKAY;
  }

  virtual SCIP_DECL_EVENTEXIT(scip_exit) {
    return SCIP_OKAY;
  }

  virtual SCIP_DECL_EVENTEXEC(scip_exec) {
    std::string eventTypeName = getEventTypeName(SCIPeventGetType(event));

    PyObject* callback = _backend->getEventCallback();
    if (callback != nullptr) {
      if (PyCallable_Check(callback)) {
        PyObject* pyEventTypeName = PyUnicode_FromString(eventTypeName.c_str());
        PyObject* payload = PyDict_New();
        PyDict_SetItemString(payload, "event_type", pyEventTypeName);
        PyObject* result = PyObject_CallFunctionObjArgs(callback, payload, nullptr);
        if (result == nullptr) {
          PyErr_Print();
        }
        Py_XDECREF(result);
        Py_DECREF(payload);
        Py_DECREF(pyEventTypeName);
      } else {
        throw std::runtime_error("Callback is not callable");
      }
    }

    return SCIP_OKAY;
  }
};
