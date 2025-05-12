from core.core.exception import IkValidateException
from ..models import User, Office, SupportingDocumentSetting
def get_upload_supporting_document_setting(claimer_rc: User, office_rc: Office, approver_rc: User) -> str:
    """
    Retrieves the upload supporting document setting based on the provided claimer, office, and approver.

    Parameters:
    claimer_rc (User): The user who is claiming the document.
    office_rc (Office): The office associated with the document.
    approver_rc (User): The user who is approving the document.

    Returns:
    str: The setting for the supporting document.
    """
    if claimer_rc is None:
        raise IkValidateException('Parameter [claimer_rc] is required')
    if office_rc is None:
        raise IkValidateException('Parameter [office_rc] is required')
    if approver_rc is None:
        raise IkValidateException('Parameter [approver_rc] is required')
    # Define priority matching list (from strict matching to loose matching)
    conditions = [
        {"claimer": claimer_rc,     "office": office_rc,     "approver": approver_rc},
        {"claimer": claimer_rc,     "office": None,          "approver": approver_rc},
        {"claimer": claimer_rc,     "office": office_rc,     "approver": None},
        {"claimer": claimer_rc,     "office": None,          "approver": None},
        {"claimer": None,           "office": None,          "approver": approver_rc},
        {"claimer": None,           "office": office_rc,     "approver": None},
        {"claimer": None,           "office": None,          "approver": None},
    ]
    for cond in conditions:
        filters = {"enable": True}
        for key, value in cond.items():
            if value is None:
                filters[f"{key}__isnull"] = True
            else:
                filters[key] = value
        rc = SupportingDocumentSetting.objects.filter(**filters).filter(enable=True).first()
        if rc:
            return rc.setting
    return SupportingDocumentSetting.OPTIONAL