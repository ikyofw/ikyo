APP_CODE = 'ES'
APP_NAME = 'Expense System'


SETTLE_BY_PRIOR_BALANCE_YES = "Y"
SETTLE_BY_PRIOR_BALANCE_YES_DISPLAY = "Yes"
SETTLE_BY_PRIOR_BALANCE_NO = "N"
SETTLE_BY_PRIOR_BALANCE_NO_DISPLAY = "No"


def getSettleByPriorBalanceDisplayValue(type) -> str:
    if type == SETTLE_BY_PRIOR_BALANCE_YES or type:
        return SETTLE_BY_PRIOR_BALANCE_YES_DISPLAY
    elif type == SETTLE_BY_PRIOR_BALANCE_NO or not type:
        return SETTLE_BY_PRIOR_BALANCE_NO_DISPLAY
    return type

# MSG01 = "Please select an image(PNG/JPG/JPEG) or a PDF to upload."


MENU_ES004 = "ES004"
MENU_ES005 = "ES005"
MENU_ES006 = "ES006"
MENU_PO001 = "PO001"
