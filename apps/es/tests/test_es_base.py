from django.test import TestCase
from core.models import UserOffice, Currency, Menu
from ..models import User, Office, Approver


class ESTestCase(TestCase):
    def setUp(self):
        self.currency_usd = Currency.objects.create(id=1, seq=1.0, code="USD", name="US Dollar", dsc="United States Dollar")
        self.currency_eur = Currency.objects.create(id=2, seq=2.0, code="EUR", name="Euro", dsc="European Euro")

        self.admin_user = User.objects.create(id=1, usr_nm="admin", psw="admin123", active=True)
        self.regular_user1 = User.objects.create(id=2, usr_nm="johndoe", psw="password1", active=True)
        self.regular_user2 = User.objects.create(id=3, usr_nm="david", psw="password2", active=True)
        self.regular_user3 = User.objects.create(id=4, usr_nm="dexiang", psw="password3", active=True)
        
        self.menu1 = Menu.objects.create(
            version_no=0,
            menu_nm="ES001A",
            menu_caption="ES001A - Payment Method",
            screen_nm="ES001A",
            enable=True,
            is_free_access=True
        )
        self.menu2 = Menu.objects.create(
            version_no=0,
            menu_nm="ES001B",
            menu_caption="ES001B - Payee",
            screen_nm="ES001B",
            enable=True,
            is_free_access=True
        )
        self.menu3 = Menu.objects.create(
            version_no=0,
            menu_nm="ES001C",
            menu_caption="ES001C - Finance",
            screen_nm="ES001C",
            enable=True,
            is_free_access=True
        )
        self.menu4 = Menu.objects.create(
            version_no=0,
            menu_nm="ES001D",
            menu_caption="ES001D - Approver",
            screen_nm="ES001D",
            enable=True,
            is_free_access=True
        )
        self.menu5 = Menu.objects.create(
            version_no=0,
            menu_nm="ES001E",
            menu_caption="ES001E - Petty Expense",
            screen_nm="ES001E",
            enable=True,
            is_free_access=True
        )
        self.menu6 = Menu.objects.create(
            version_no=0,
            menu_nm="ES002",
            menu_caption="ES002 - Select Office",
            screen_nm="ES002",
            enable=True,
            is_free_access=True
        )
        self.menu7 = Menu.objects.create(
            version_no=0,
            menu_nm="ES003",
            menu_caption="ES003 - Approver",
            screen_nm="ES003",
            enable=True,
            is_free_access=True
        )
        self.menu8 = Menu.objects.create(
            version_no=0,
            menu_nm="ES004",
            menu_caption="ES004 - New Expense",
            screen_nm="ES004",
            enable=True,
            is_free_access=True
        )
        self.menu8 = Menu.objects.create(
            version_no=0,
            menu_nm="ES005",
            menu_caption="ES005 - Expense Enquiry",
            screen_nm="ES005",
            enable=True,
            is_free_access=True
        )
        self.menu8 = Menu.objects.create(
            version_no=0,
            menu_nm="ES006",
            menu_caption="ES006 - Cash Advancement",
            screen_nm="ES006",
            enable=True,
            is_free_access=True
        )


        self.office_a = Office.objects.create(
            name="Office A",
            code="001",
            addr="123 Main St",
            city="City A",
            st="State A",
            country="Country A",
            postal_code="10001",
            phone_num="123-456-7890",
            email="officeA@example.com",
            ccy=self.currency_usd,
            dsc="Main office for region A"
        )
        self.office_b = Office.objects.create(
            name="Office B",
            code="002",
            addr="456 Elm St",
            city="City B",
            st=None,
            country="Country B",
            postal_code=None,
            phone_num=None,
            email="officeB@example.com",
            ccy=self.currency_usd,
            dsc="Backup office for region B"
        )
        self.office_c = Office.objects.create(
            name="Office C",
            code="003",
            addr="789 Oak St",
            city="City C",
            st="State C",
            country="Country C",
            postal_code="30003",
            phone_num="987-654-3210",
            email=None,
            ccy=self.currency_eur,
            dsc="European branch office"
        )
        self.office_d = Office.objects.create(
            name="Office D",
            code="004",
            addr="101 Pine St",
            city="City D",
            st="State D",
            country="Country D",
            postal_code="40004",
            phone_num="555-555-5555",
            email="officeD@example.com",
            ccy=self.currency_eur,
            dsc="Additional office for testing"
        )

        UserOffice.objects.create(usr=self.regular_user1, office=self.office_a, is_default=True, seq=1.0, dsc="Primary office for johndoe")
        UserOffice.objects.create(usr=self.regular_user1, office=self.office_b, is_default=False, seq=2.0, dsc="Secondary office for johndoe")
        
        UserOffice.objects.create(usr=self.regular_user2, office=self.office_a, is_default=True, seq=1.0, dsc="Primary office for david")
        UserOffice.objects.create(usr=self.regular_user2, office=self.office_b, is_default=False, seq=2.0, dsc="Secondary office for david")

        UserOffice.objects.create(usr=self.admin_user, office=self.office_a, is_default=True, seq=1.0, dsc="Admin access to office A")
        UserOffice.objects.create(usr=self.admin_user, office=self.office_c, is_default=False, seq=1.0, dsc="Admin access to office C")
        UserOffice.objects.create(usr=self.admin_user, office=self.office_d, is_default=False, seq=3.0, dsc="Additional admin access to office D")
        
        Approver.objects.create(id=1, approver=self.admin_user, office=self.office_a, rmk="Primary approver for admin")
        Approver.objects.create(id=2, approver=self.admin_user, office=self.office_b, rmk="Primary approver for admin")
