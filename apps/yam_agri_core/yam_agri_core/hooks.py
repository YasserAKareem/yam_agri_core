# hooks for yam_agri_core
doc_events = {
    "Lot": {
        "validate": "yam_agri_core.doctype.lot.lot.Lot.validate",
    },
    "Certificate": {
        "validate": "yam_agri_core.doctype.certificate.certificate.Certificate.validate",
    },
    "QCTest": {
        "validate": "yam_agri_core.doctype.qc_test.qc_test.QCTest.validate",
    },
    "Nonconformance": {
        "validate": "yam_agri_core.doctype.nonconformance.nonconformance.Nonconformance.validate",
    },
}
