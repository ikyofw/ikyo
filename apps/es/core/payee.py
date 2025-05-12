"""Payee management
"""
from core.log.logger import logger
from ..models import Office, Payee


def vaildiate_payee(office: Office, payee: Payee) -> bool:
    """
    Validates if the provided payee is associated with the given office.

    This method checks that:
      1. Both the `office` and `payee` objects are not `None`.
      2. The `payee` object has a valid `office` attribute that is not `None`.
      3. The `id` of the provided `office` matches the `id` of the `payee`'s associated office.

    Args:
        office (Office): The office to validate against.
        payee (Payee): The payee whose office association is to be validated.

    Returns:
        bool: True if the payee is associated with the office, otherwise False.

    Example:
        office = Office(id=1)
        payee = Payee(office=Office(id=1))
        is_valid = validate_payee(office, payee)
        # is_valid will be True
    """
    return office is not None and payee is not None and payee.office is not None and office.id == payee.office.id


# def getLastPayeeID(claimerID: int, office: str = None) -> int:
#     """Get claimer's last payee ID

#     Args:
#         claimerID (int): Claimer's ID.
#         office (str, optional): The office which claimer want to submit to.

#     Returns:
#         Payee's ID if found, None otherwise.

#     """
#     if claimerID is None:
#         return None
#     # 1. get payee from rejected expense
#     sql = "SELECT payee_id FROM wci_es_hdr_reject WHERE claimer_id=%s" % claimerID
#     if isNotNullBlank(office):
#         sql += " AND exists(select 1 from wci_es_payee p where p.id=wci_es_hdr_reject.payee_id and p.office=%s)" % dbUtils.toSqlField(office)
#     with connection.cursor() as cursor:
#         cursor.execute(sql)
#         rs = dbUtils.dictfetchall(cursor)
#         if not dbUtils.isEmpty(rs):
#             payeeID = rs[0]['payee_id']
#             if payeeID is not None:
#                 return payeeID
#     # 2. get payee from normal expense
#     sql = "SELECT payee_id FROM wci_es_hdr WHERE claimer_id=%s" % claimerID
#     if isNotNullBlank(office):
#         sql += " AND exists(select 1 from wci_es_payee p where p.id=wci_es_hdr.payee_id and p.office=%s)" % dbUtils.toSqlField(office)
#     with connection.cursor() as cursor:
#         cursor.execute(sql)
#         rs = dbUtils.dictfetchall(cursor)
#         if not dbUtils.isEmpty(rs):
#             payeeID = rs[0]['payee_id']
#             if payeeID is not None:
#                 return payeeID
#     return None