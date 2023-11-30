# ikyo
Python ikyo.  

Notes:  
   1. Python 3.10 or above.
   2. Django 4.x.
   3. React
   4. django-rest-framework (https://www.django-rest-framework.org)
   5. Database: sqlite3


# History
| Version | Date | Author | Description |
| ------- | ---- | ------ | ----------- |
| 1       | 2023-11-20 | ikyo | Init |
|  |  | |  |


# Folder structure
1. **django_backend**  
   Python django backend folder.
2. **react**  
   React frontend folder.
3. **apps**  
   Demo apps folder.
4. README.md  
   Readme file.


# Python and Django Environment Setup

To set up your Python environment, follow these steps:

1. **Install Python 3.10.x**  
   Download and install Python 3.10.x from the official [Python website](https://www.python.org/downloads/).

2. **Create a Virtual Environment**  
   Open a terminal in the project directory and first run the following command to enter the backend folder:   
   ``cd django_backend``  
   Then run the following command to create a virtual environment:   
   ``python -m venv .venv``
3. **Activate virtual environment**  
   On Windows, use:  
   ``.\.venv\Scripts\activate``
4. **Install python modules**  
   Ensure you have a requirements.txt file in your project directory. Install the required modules using the following command:  
   ``pip install -r requirements.txt``
5. **Start the Django Development Server**   
   Start the development server using the following command:   
   ``python manage.py runserver``

## Python modules
| #  | Name                    | Version         | Description         |
| -- | ----------------------- | --------------- | ------------------- |
| 1  | django                  | 4.x             |                     |
| 2  | django-cors-headers     |                 |                     |
| 3  | djangorestframework     |                 |                     |
| 4  | markdown                |                 | Markdown support for the browsable API. |
| 5  | django-filte            |                 | Filtering support   |
| 6  | json5                   |                 | Convert no standard json string to json object. |
| 7  | pandas                  |                 | Process spreadsheet. |
| 8  | openpyxl                |                 | Process spreadsheet. |
| 9 | pycryptodome            |                 | Used for login page. |
|  |  | |

# Setting Up and Integrating React with Django

Follow these steps to set up and run your React application:

1. **Navigate to the React Directory**  
   Open a terminal and change to the React project directory:  
   ``cd react``
2. **Build the React App** 
   Compile and build your React application:  
   ``npm run build`` 
3. **Ensure the Django Templates Directory Exists**
   Create the necessary directory structure in your Django project (if it doesn't already exist):  
    ``mkdir -p ../django_backend/templates/react`` 
3. **Move the Build Folder**  
   Move the build folder to the Django templates directory:    
   ``move build ../django_backend/templates/react``  
   This step integrates the built React app with your Django project.
4. **View the App in the Browser**  
   After moving the build folder, you can view the app in the browser at http://localhost:8000.

For more information, please reference to *react/README.md* file.

## React packages
Please reference to *package.json* file.
| #  | Name                    | Version         | Description         |
| -- | ----------------------- | --------------- | ------------------- |
|  |  | |


# Debug django and react (Visual Studio Code)
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
When debug the react app, plesae start the react server first:  
```shell
cd pyi-react
npm start
```

# License  
   N/A

# Reference
1. Django  
   https://www.djangoproject.com

2. Django REST framework    
   https://www.django-rest-framework.org

3. React  
   https://react.dev

