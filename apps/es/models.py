from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, F, FloatField, Sum, Value, When
from django.db.models.functions import Coalesce, Round

from core.db.model import IDModel
from core.models import (Currency, Group, IdDateModel, Office, User, UserGroup,
                         UserOffice)

from .core import ESTools


class UserWorkOffice(IdDateModel):
    usr = models.OneToOneField(
        User, models.CASCADE, unique=True, verbose_name='User')
    office = models.ForeignKey(Office, models.CASCADE, verbose_name='Office')

    class Meta:
        verbose_name = 'User work office'


class UserRole(IdDateModel):
    ROLE_ADMIN = 'admin'
    ROLE_READ = 'read'
    ROLE_LIMIT = 'limit'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_READ, 'Read Only'),
        (ROLE_LIMIT, 'Limited Access'),
    ]

    usr = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='User')
    usr_grp = models.ForeignKey(Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='User group')
    office = models.ForeignKey(Office, blank=True, null=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_LIMIT)
    target_usr = models.ForeignKey(User, models.DO_NOTHING, null=True, blank=True, related_name='+', verbose_name='Target user')
    target_usr_grp = models.ForeignKey(Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Target user group')
    prj_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Project name')
    enable = models.BooleanField(default=True)
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Office admin'


class Accounting(IdDateModel):
    office = models.ForeignKey(Office, models.CASCADE)
    usr = models.ForeignKey(User, models.DO_NOTHING,
                            verbose_name='Finance Personnel')
    is_default = models.BooleanField(
        verbose_name='Is Default Finance Personnel')
    rmk = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Remarks')

    class Meta:
        unique_together = (('office_id', 'usr_id'), )
        verbose_name = 'Accounting'


class Payee(IdDateModel):
    office = models.ForeignKey(Office, models.CASCADE)
    payee = models.CharField(max_length=255, verbose_name='Payee')
    bank_info = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Bank Information')
    rmk = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Remarks')

    class Meta:
        unique_together = (('office_id', 'payee'),)
        verbose_name = 'Payee'


class PettyCashExpenseAdmin(IdDateModel):
    office = models.ForeignKey(Office, models.CASCADE)
    admin = models.ForeignKey(User, models.CASCADE,
                              verbose_name='Petty Cash Admin')
    admin_payee = models.ForeignKey(
        Payee, models.CASCADE, verbose_name="Administrator's payee ID")
    max_amt = models.FloatField(verbose_name='Petty Max Amount', validators=[
                                MinValueValidator(Decimal('0.01'))])
    enable = models.BooleanField(
        default=True, verbose_name='Enable')
    rmk = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Remarks')

    class Meta:
        unique_together = (('office_id', 'admin_id'), )


class Approver(IdDateModel):
    office = models.ForeignKey(Office, models.CASCADE)
    claimer = models.ForeignKey(
        User, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Claimer')
    claimer_grp = models.ForeignKey(
        Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Claimer group')
    approver = models.ForeignKey(
        User, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Approver')
    approver_grp = models.ForeignKey(
        Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Approver group')
    approver_assistant = models.ForeignKey(
        User, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Approver assistant')
    approver_assistant_grp = models.ForeignKey(
        Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='Approver assistant group')
    approver2 = models.ForeignKey(User, models.CASCADE, blank=True,
                                  null=True, verbose_name='The second approver', related_name='+')
    approver2_grp = models.ForeignKey(
        Group, models.CASCADE, blank=True, null=True, related_name='+', verbose_name='The second approver group')
    approver2_min_amount = models.FloatField(
        blank=True, null=True, verbose_name="The second approver's min approve amount")
    enable = models.BooleanField(
        default=True, verbose_name='Enable')
    rmk = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Remark')

    class Meta:
        verbose_name = 'Approver'


class PaymentMethod(IdDateModel):
    PETTY_CASH = "petty cash"
    PRIOR_BALANCE = "prior balance"
    E_CHEQUE = "e-cheque"
    BANK_TRANSFER = "bank transfer"
    TP_CHOICE = [(PETTY_CASH, PETTY_CASH), (PRIOR_BALANCE, PRIOR_BALANCE), (E_CHEQUE, E_CHEQUE), (BANK_TRANSFER, BANK_TRANSFER)]

    tp = models.CharField(unique=True, max_length=50, choices=TP_CHOICE, verbose_name='Type')
    dsc = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Remarks')

    class Meta:
        verbose_name = 'Expense Reimbursement Method'


class ExpenseCategory(IdDateModel):
    cat = models.CharField(unique=True, max_length=50, verbose_name='Category')
    dsc = models.CharField(max_length=255, blank=True,
                           null=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Expense Category'


class SupportingDocumentSetting(IdDateModel):
    REQUIRE = 'require'
    OPTIONAL = 'optional'
    DISABLE = 'disable'

    claimer = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Claimer')
    approver = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Approver')
    office = models.ForeignKey(Office, models.DO_NOTHING, blank=True, null=True, verbose_name='Office')
    enable = models.BooleanField(default=True, verbose_name='Enable')
    setting = models.CharField(max_length=10, choices=[
        (REQUIRE, 'Require'),
        (OPTIONAL, 'Optional'),
        (DISABLE, 'Disable')
    ])
    dsc = models.TextField(blank=True, null=True, verbose_name='Expense Description')

    class Meta:
        verbose_name = 'Supporting Document Setting'


class Sequence(IdDateModel):
    tp = models.CharField(max_length=30, verbose_name='Sequence type')
    office = models.ForeignKey(Office, models.CASCADE)
    seq = models.BigIntegerField(verbose_name='Sequence')

    class Meta:
        unique_together = (('tp', 'office_id'), )

    def __str__(self):
        return '%s,%s' % (self.tp, self.office.name if self.office else '')


class File(IdDateModel):
    tp = models.CharField(max_length=30, verbose_name='Type')
    office = models.ForeignKey(Office, models.DO_NOTHING)
    seq = models.BigIntegerField(verbose_name='Sequence')
    file_nm = models.CharField(max_length=20, verbose_name='File Name')
    file_tp = models.CharField(max_length=4, verbose_name='File Type')
    file_original_nm = models.CharField(
        max_length=255, verbose_name='File Original Type')
    file_size = models.BigIntegerField(verbose_name='File Size')
    file_path = models.CharField(max_length=255, verbose_name='File Path')
    is_empty_file = models.BooleanField(
        default=False, verbose_name='Is Empty File')
    sha256 = models.CharField(
        max_length=64, blank=True, null=True, verbose_name='SHA 256')
    old_file_id = models.IntegerField(blank=True, null=True, verbose_name='wci_file id')
    amount = None  # page amount

    class Meta:
        unique_together = (('file_nm', 'file_path'),
                           ('tp', 'office_id', 'seq'),)


class Po(IdDateModel):
    SAVED_STATUS = 'saved'
    SUBMITTED_STATUS = 'submitted'
    APPROVED_STATUS = 'approved'
    REJECTED_STATUS = 'rejected'
    DELETED_STATUS = 'deleted'
    STATUS_CHOICES = [(SUBMITTED_STATUS, SUBMITTED_STATUS), (SAVED_STATUS, SAVED_STATUS), (APPROVED_STATUS, APPROVED_STATUS),
                      (REJECTED_STATUS, REJECTED_STATUS), (DELETED_STATUS, DELETED_STATUS)]

    sn = models.CharField(max_length=20, unique=True, verbose_name='SN')
    office = models.ForeignKey(Office, models.CASCADE, verbose_name='Office')
    purchase_item = models.TextField(verbose_name='Purchase Item/Reason')
    recommendation = models.TextField(blank=True, null=True, verbose_name='Recommendation')
    assigned_approver = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Assigned Approver')
    submitter = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Submitter')
    submit_dt = models.DateTimeField(blank=True, null=True, verbose_name='Submit Date')
    approver = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Approver')
    approve_dt = models.DateTimeField(blank=True, null=True, verbose_name='Approve Date')
    rejecter = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Rejecter')
    reject_dt = models.DateTimeField(blank=True, null=True, verbose_name='Reject Date')
    deleter = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Deleter')
    delete_dt = models.DateTimeField(blank=True, null=True, verbose_name='Delete Date')
    rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Approve/Reject Remark')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True, verbose_name="Status")
    file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True, verbose_name='Sign PO File')
    file_rmk = models.CharField(max_length=255, blank=True, null=True, verbose_name='Sign PO File Remark')
    old_data_id = models.IntegerField(blank=True, null=True, verbose_name='wci_form_data id')
    operator = None
    operate_dt = None

    class Meta:
        verbose_name = 'PO'


class PoQuotation(IdDateModel):
    po = models.ForeignKey(Po, models.CASCADE, verbose_name='PO')
    vr = models.CharField(max_length=255, verbose_name='Vendor / Remark')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True, verbose_name='Quotation File')
    have_file = None

    class Meta:
        verbose_name = 'PO Quotation'

# TODO: rename to Activity


class Activity(IdDateModel):
    tp = models.CharField(max_length=3, verbose_name='Type')  # 1. expense, 2. cash advancement
    transaction_id = models.BigIntegerField(verbose_name='Transactions record ID')
    operate_dt = models.DateTimeField(blank=True, null=True, verbose_name='Operation date')
    operator = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='Operator')
    sts = models.CharField(max_length=20, verbose_name='Transactions status')
    dsc = models.TextField(max_length=255, blank=True, null=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Activities'


class Expense(IdDateModel):
    office = models.ForeignKey(Office, models.DO_NOTHING, verbose_name='Office')
    sn = models.CharField(unique=True, max_length=11, verbose_name='Expense SN')
    po = models.ForeignKey(Po, models.DO_NOTHING, blank=True, null=True, verbose_name='PO NO.')
    sts = models.CharField(max_length=20, verbose_name='Status')
    payee = models.ForeignKey(Payee, models.DO_NOTHING, db_column='payee_id', blank=True, null=True, verbose_name='Payee')
    submit_dt = models.DateTimeField(blank=True, null=True, verbose_name='Submit time')
    claimer = models.ForeignKey(User, models.DO_NOTHING, related_name='+', verbose_name='Claimer')
    claim_amt = models.FloatField(blank=True, null=True, verbose_name='Claim amount')
    pay_amt = models.FloatField(blank=True, null=True, verbose_name='Pay amount')
    # TODO: for old data
    fx_ccy = models.ForeignKey(Currency, models.DO_NOTHING, blank=True, null=True, verbose_name='FX CCY')
    fx_amt = models.FloatField(blank=True, null=True, verbose_name='FX amount')

    supporting_doc = models.ForeignKey(File, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Supporting Document')
    dsc = models.TextField(blank=True, null=True, verbose_name='Expense Description')

    approver = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='approver')

    use_prior_balance = models.BooleanField(default=False, verbose_name='Is settle by prior balance')
    is_petty_expense = models.BooleanField(default=False, verbose_name='Is a petty expense')

    approve_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Approve activity')
    approve2_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='2nd Approve activity')
    petty_expense_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Petty operation activity')
    last_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Last activity')

    payment_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Payment activity')
    payment_tp = models.ForeignKey(PaymentMethod, models.DO_NOTHING, blank=True, null=True, verbose_name='Payment type')
    payment_record_file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True, verbose_name='Payment record file')
    payment_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='Payment record No.')

    po_sn = None  # used for po
    action_rmk = None

    @property
    def expense_cat(self) -> str:
        """Used for ES005 search result table."""
        if self.fx_ccy is not None:
            return 'FXE'
        elif self.is_petty_expense is True:
            return 'PCE'
        return None


class ExpenseDetail(IdDateModel):
    hdr = models.ForeignKey(Expense, models.CASCADE, blank=True, null=True, verbose_name='Expense')
    seq = models.SmallIntegerField(verbose_name='Sequence')  # original is sn
    incur_dt = models.DateField(verbose_name='Incurrence date')
    dsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='Description')
    cat = models.ForeignKey(ExpenseCategory, models.DO_NOTHING, verbose_name='Category')
    ccy = models.ForeignKey(Currency, models.DO_NOTHING, blank=True, null=True, verbose_name='')
    amt = models.FloatField(verbose_name='Amount')
    ex_rate = models.FloatField(blank=True, null=True, verbose_name='Exchange rate')
    file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True, verbose_name='File')
    office = models.ForeignKey(Office, models.DO_NOTHING, blank=True, null=True, verbose_name='Office')
    claimer = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, verbose_name='Claimer')
    prj_nm = models.CharField(max_length=100, blank=True, null=True, verbose_name='Project name')

    is_current = None
    fx_local_amt = None
    fx_rate = None

    @property
    def ex_amt(self):
        if self.ex_rate is not None:
            return float(ESTools.round2(ESTools.mul(self.amt, self.ex_rate)))
        else:
            return self.amt

    class Meta:
        verbose_name = 'Expense detail'


class DraftFile(IdDateModel):
    EXPENSE = 'expense'

    tp = models.CharField(max_length=30, verbose_name='Sequence type')
    claimer = models.ForeignKey(
        User, models.DO_NOTHING, verbose_name='Claimer')
    office = models.ForeignKey(
        Office, models.DO_NOTHING, verbose_name='Office')
    file = models.ForeignKey(File, models.DO_NOTHING, verbose_name='File')

    class Meta:
        verbose_name = 'Draft file'
        unique_together = (('tp', 'claimer_id', 'office_id', 'file_id'),)


class CashAdvancementManager(models.Manager):
    def get_queryset(self):
        from .core.status import Status

        #  sum(PriorBalance.balance_amt)，default 0.0
        prior_sum = Coalesce(Sum('priorbalance__balance_amt'), 0.0, output_field=FloatField())
        # calculate claim_amt - prior_balance_sum
        calculated = F('claim_amt') - prior_sum
        #  calculate when settled, othewise return None
        condition = When(sts=Status.SETTLED.value, then=Round(prior_sum, 2))
        balance_condition = When(sts=Status.SETTLED.value, then=Round(calculated, 2))

        return super().get_queryset().annotate(
            prior_balance_amt=Case(
                condition,
                default=Value(None),
                output_field=FloatField()
            ),
            balance_amt=Case(
                balance_condition,
                default=Value(None),
                output_field=FloatField()
            )
        )


class CashAdvancement(IdDateModel):  # WciEsCash
    office = models.ForeignKey(Office, models.DO_NOTHING, verbose_name='Office')
    sn = models.CharField(unique=True, max_length=11, verbose_name='Expense SN')
    po = models.ForeignKey(Po, models.DO_NOTHING, blank=True, null=True, verbose_name='PO NO.')
    sts = models.CharField(max_length=20, verbose_name='Status')
    ccy = models.ForeignKey(Currency, models.DO_NOTHING, verbose_name='CCY')
    dsc = models.CharField(max_length=255, verbose_name='Description')
    claimer = models.ForeignKey(User, models.DO_NOTHING, related_name='+', verbose_name='Claimer')
    claim_amt = models.FloatField(verbose_name='Claim amount')
    claim_dt = models.DateTimeField(verbose_name='Submit date')
    pay_amt = models.FloatField(blank=True, null=True, verbose_name='Pay amount')
    payee = models.ForeignKey(Payee, models.DO_NOTHING, verbose_name='Payee')

    approver = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='+', verbose_name='approver')

    approve_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Approve activity')
    approve2_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='2nd Approve activity')
    last_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Last activity')

    payment_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Payment activity')
    payment_tp = models.ForeignKey(PaymentMethod, models.DO_NOTHING, blank=True, null=True, verbose_name='Payment type')
    payment_record_file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True, verbose_name='Payment record file')
    payment_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='Payment record No.')

    po_sn = None  # used for po
    action_rmk = None  # used in the screen. E.g. cancel reason

    objects = CashAdvancementManager()  # replace the original objects

    class Meta:
        verbose_name = 'Cash advancement'


class ForeignExchange(IdDateModel):  # WciEsCashFx
    ca = models.ForeignKey(CashAdvancement, models.CASCADE)
    submit_dt = models.DateTimeField(verbose_name='Submit time')
    amt = models.FloatField()
    fx_ccy = models.ForeignKey(Currency, models.CASCADE, verbose_name='Fx CCY')
    fx_amt = models.FloatField()
    fx_rate = models.FloatField()
    fx_receipt_file = models.ForeignKey(File, models.CASCADE)
    dsc = models.CharField(max_length=255)
    sts = models.CharField(max_length=20)

    approver = models.ForeignKey(User, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Approver')

    approve_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Approve activity')
    approve2_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='2nd Approve activity')
    last_activity = models.ForeignKey(Activity, models.DO_NOTHING, related_name='+', blank=True, null=True, verbose_name='Last activity')

    class Meta:
        verbose_name = 'Foreign Exchange'


class PriorBalance(IdDateModel):
    ca = models.ForeignKey(CashAdvancement, models.DO_NOTHING, verbose_name="Cash Advancement", related_name='priorbalance')
    expense = models.ForeignKey(Expense, models.DO_NOTHING, verbose_name="Expense")
    balance_amt = models.FloatField()
    fx = models.ForeignKey(ForeignExchange, models.DO_NOTHING, blank=True, null=True)
    fx_balance_amt = models.FloatField(blank=True, null=True)

    is_petty_expense = None

    @property
    def claim_amt(self) -> str:
        return self.fx_balance_amt if self.fx_balance_amt is not None else self.balance_amt

    class Meta:
        unique_together = (('ca', 'expense', 'fx'), )
        verbose_name = 'Expense Prior Balance'


class AvailablePriorBalance(IDModel):
    """No database model"""
    ca = models.ForeignKey(CashAdvancement, models.DO_NOTHING, verbose_name="Cash Advancement")
    ccy = models.ForeignKey(Currency, models.DO_NOTHING, verbose_name='CCY')
    fx = models.ForeignKey(ForeignExchange, models.DO_NOTHING, blank=True, null=True)
    total_amt = models.FloatField(verbose_name="Total amount")
    balance_amt = models.FloatField(verbose_name="Balance amount")
    deduction_amt = models.FloatField(null=True, blank=True, verbose_name="Deduction amount")

    class Meta:
        managed = False


class UserExpensePermission(models.Model):
    usr_id = models.BigIntegerField()
    expense_id = models.BigIntegerField()
    acl = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = "es_v_user_expense"


class UserCashAdvancementPermission(models.Model):
    usr_id = models.BigIntegerField()
    ca_id = models.BigIntegerField()
    acl = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = "es_v_user_cash_advancement"
