# Background
The main objective of this framework is to minimize the development effort for typical web-based applications that do not require fancy user interfaces. Only one standard UI style is provided. This framework was originally developed in 2002 using Java and JavaScript. In 2022, we migrated the framework to React and Django, resulting in the new version, 2.0. In December 2023, we open-sourced the framework.
# Features
1. Web screens can be defined online.
2. Upon saving a screen definition, although not in a WYSIWYG manner, the layout can be previewed.
3.	Screen definition involves high-level objects such as dialogues, enquiry fields, simple fields, tabular fields, button bars, etc., which we refer to as 'field groups'.
4.	These screen definition screens are also created using the framework itself.
5.	An option is also available to define a screen using an Excel spreadsheet.
6.	Once defined, the backend can submit the screen definition to the React frontend, which will then render the screen accordingly.
7.	React development is generally not required unless there is a need for a new type of field group.
8.	The tabular field group is a powerful feature of the framework. It allows data input and display in a tabular format, with a UI similar to a spreadsheet. This includes navigation in the table using cursor keys or the mouse, and supports copy and paste functions.
9.	Menu management, user management, and permission management are already integrated into the framework.
10.	We have provided three sample applications: a timesheet, task management, and expense tracking.

# Notes
1. Python 3.10 or above.
2. Django 4.x.
3. React.
4. Django Rest Framework ([Official Website](https://www.django-rest-framework.org)).
5. Database: Postgresql.

# History
| Version | Date       | Author | Description    |
| ------- | ---------- | ------ | -------------- |
| 2.000   | 2023-12-08 | ikyo   | Initial release |

# Folder Structure
1. **django_backend**: Python Django backend folder.
2. **react**: React frontend folder.
3. **apps**: Demo apps folder.
4. README.md: Readme file.

# Python and Django Environment Setup

To set up your Python environment, follow these steps:

1. **Install Python 3.10.x**: Download and install Python 3.10.x from the official [Python website](https://www.python.org/downloads/).  
2. **Create a Virtual Environment**: Open a terminal in the project directory and first navigate to the backend folder:  
   ``cd django_backend``  
   Then create a virtual environment:    
   ``python -m venv .venv``
3. **Activate the Virtual Environment**: On Windows, use:
   ``.\.venv\Scripts\activate``
   Linux:  
   ``source ./.venv/bin/activate``
4. **Install Python Modules**: Ensure you have a `requirements.txt` file in your project directory. Install the required modules using the following command:
   ``pip install -r requirements.txt``
5. **Initialize database**:  
   ``python manage.py makemigrations sessions core``  
   ``python manage.py migrate``
6. **Start the Django Development Server**: Start the development server using the following command:  
   ``python manage.py runserver``

## Python Modules
| #  | Name                | Version | Description                                           |
| -- | ------------------- | ------- | ----------------------------------------------------- |
| 1  | django              | 4.x     |                                                       |
| 2  | django-cors-headers |         |                                                       |
| 3  | djangorestframework |         |                                                       |
| 4  | markdown            |         | Markdown support for the browsable API.               |
| 5  | django-filte        |         | Filtering support                                     |
| 6  | json5               |         | Convert non-standard JSON strings to JSON objects.    |
| 7  | pandas              |         | Process spreadsheets.                                 |
| 8  | openpyxl            |         | Process spreadsheets.                                 |
| 9  | pycryptodome        |         | Used for the login page.                              |

# Setting Up and Integrating React with Django

Follow these steps to set up and run your React application:

1. **Navigate to the React Directory**  
   Open a terminal and change to the React project directory:  
   ``cd react``
2. **Installing Dependencies**  
   Install all dependencies required for the project:  
   ``npm install --force``
3. **Build the React App** 
   Compile and build your React application:  
   ``npm run build`` 
4. **Ensure the Django Templates Directory Exists**
   Create the necessary directory structure in your Django project (if it doesn't already exist):  
    ``mkdir -p ../django_backend/templates/react`` 
5. **Move the Build Folder**  
   Move the build folder to the Django templates directory:    
   ``move build ../django_backend/templates/react``  
   This step integrates the built React app with your Django project.
6. **View the App in the Browser**  
   After moving the build folder, you can view the app in the browser at http://localhost:8000.

For more information, please reference to *react/README.md* file.


# Debug django and react in Visual Studio Code
Please reference to *.vscode/launch.json* file.  
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [

        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}\\manage.py",
            "args": [
                "runserver",
                "0.0.0.0:8000"
            ],
            "django": true,
            "justMyCode": true
        },
        {
            "type": "pwa-msedge",
            "request": "launch",
            "name": "React",
            "url": "http://localhost:3000",
            "webRoot": "${workspaceFolder}"
        }
    ]
}
```

Start the react server:  
```shell
cd pyi-react
npm start
``` 

# License
MIT

# Reference
1. Django  
   https://www.djangoproject.com

2. Django REST framework    
   https://www.django-rest-framework.org

3. React  
   https://react.dev

4. React Spreadsheet (0.6.2)  
   https://iddan.github.io/react-spreadsheet
