# Expense System
The Expense System is an application based on the <b>Ikyo</b> framework.


# History
| Version | Date       | Author | Description    |
| ------- | ---------- | ------ | -------------- |
| 1.000   | 2025-05-12 | ikyo   | Initial release |

# Installation
1. Copy the application into the Ikyo ``django_backend`` folder.
2. Do the migrations:
    ```shell
    python manage.py makemigrations es
    python manage.py migrate es
    ```
3. Run the ikyo application.
4. Sign in to the Ikyo system via a web browser, then set the access rights. The top menu for the Expense System is labeled ``Expense System``.