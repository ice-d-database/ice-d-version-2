## Dev Dependencies

- Docker & Docker Compose
- Python 3
- Pipenv
- Pyenv

## Developer Setup

Start by setting up virtual environment:

1. Go into django-app folder (`cd django-app`)
2. Type `cp .env.example .env` to create a copy of the environment example file (or use a filemanager and rename).
3. Run `pipenv --python 3.9.6` to setup the virtual environment.
   - If you don't have Pyenv installed you'll hit an error when doing this saying it can't find python. Pyenv allows multiple
     verions of Python to be installed on a single machine, and this is used to download/install the version specified (3.9.6).
     You can however install Python 3.9.6 (it may work with other versions, but it's not recommended) and use `pipenv --python {path_to_python_3.9.6}`
     without needing to install Pyenv.
4. Run `pipenv shell` to activate the virtual environment.
5. Run `pipenv install` to install requirements.txt dependencies.
6. Go back up to the parent directory where `docker-compose.yml` lives. Run `docker-compose up --build`. This may fail
   (need to look further into this), simply `ctrl+c` to quit and re-run using `docker-compose up`
7. Open a new terminal window and go into `django-app` folder again and type `pipenv shell` to activate the virtual environment.
8. Run `pipenv run iced/manage.py migrate` to run migrations.
9. You should now be abe to access app at http://localhost:8000.

## Setting up a Super User

A Super User is the administering account for the Django admin tool. This can be generated using the following steps:

1. Ensure the docker-compose file is up and running.
2. Go into the `django-app` directory.
3. Run `pipenv run iced/manage.py createsuperuser`.
4. Fill out information required (username, email, password etc.).

You should now be able to go to http://localhost:8000/admin and sign in using the credentials provided to the command.

## Testing

All subclasses of unittest.TestCase in any file whose name starts with test

1. Run `docker exec -w /var/www/iced berkeley-ice-d_application_1 python manage.py test base`

## Code Quality

We have implemented a number of django management commands to run these processes.
**Styling**

Styling is accomplished via Black and isort. Black formats, isort handles import sorting alphabetically/hierarchically.

- Run `pipenv run iced/manage.py style` to see a report showing what would be changed.
- Run `pipenv run iced/manage.py style --write` to run fixes automatically.

**Linting**

Linting is accomplished via Flake8 and MyPy. Flake8 is for general code consistency, and MyPy handles the static typing checks.

- Run `pipenv run iced/manage.py lint` to view results of both.

**Security**

Security check is accomplished via Bandit. This checks the source code for common vulnerabilities.

- Run `pipenv run iced/manage.py security` to view the security report.

## Configure Google Cloud

1. Create and configure a new Google API project
2. Register the app by filling out the OAuth Consent Screen.
3. Create a new **oAuth Client ID** under Credentials.
   - Select **Web application** for the **Application type**.
   - Add http://127.0.0.1:8000 under Authorized JavaScript origins.
   - Add http://127.0.0.1:8000/accounts/google/login/callback/ under Authorized redirect URIs.

## Configure DJango admin to integrate with Google oAuth

1. Log into Django Admin console
2. Under Sites, add 127.0.0.1:8000 as both **Domain name** and **Display name**.
3. Under Social Applications , click Add and fill in the details as follows:
   1. Provider: Google
   2. Name: OAuth App
   3. Client ID: `<client id>`
   4. Secret Key: `<secret key>`
   5. Sites: 127.0.0.1:8000

## Add email to Test users

1. Open the Google Cloud Platform oAuth Consent Screen
2. Scroll down to the Test users list
3. Add your email to the test users list

## Setup User/Group Permissions

- User Permissions:

1. Open the User Permission panel
2. Select the User and the allowed Application
   - User will now be restricted to only view those Applications and the associated Application components

- Group Permissions:

1. Create a group in the Groups panel
2. Add a user to the group in the User panel
3. Open the Group Permission panel
4. Add a new Group Permission and select both the group and the application allowed for that group
   - Users in the group will now be restricted to only view those Applications and the associated Application components

### Note: Both User Permissions and Group Permissions will be applied equally and exist at the same level

Watch the following for initial setup instructions:
https://www.loom.com/share/6753cf63fa7a4b2fa04329487485661e

## Cronjobs

- With the [django-crontab](https://pypi.org/project/django-crontab/) library we are able to schedule tasks to run at specific times. 
- These are configured in `django-app/iced/iced/settings.py` in the CRONJOBS array. You can use this [tool](https://crontab.guru/) to help you with your cron notation. For example `('1 0 * * *', 'django.core.management.call_command', ['calculate_ages_v3'])` runs `pipenv manage.py calculate_ages_v3` everynight at 12:01 am (or 00:01). 
- Once these jobs are scheduled in the file, you need to activate them. 
   - If existing tasks exist, run `pipenv run python iced/manage.py crontab remove` to remove 
   - And this will add them: `pipenv run python iced/manage.py crontab add`
   - You can check your work with `crontab -l` to view the current crontab schedule.
   