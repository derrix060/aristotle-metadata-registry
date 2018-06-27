# Aristotle Development Docker environment

This docker configuration is designed to make development of the Aristotle Metadata Registry
easy and makes it easier to review the system. This docker *should not* be used as the base of
a production instance of Aristotle.

* Step 1: Clone the Aristotle Metadata repository
* Step 2: From this directory run `docker-compose up`
* Step 3: Done!

This will create a docker image, will all components of the registry installed as editable
python modules, ready to run as a web service.
This web service will be run on port 8080 and accept all hosts (`ALLOWED_HOSTS = ['*']`),
and serves static files from app directories thorugh Django - both not recommended for
production.

Running this will create 'docker/data' directory in the repository that will not be checked
in or tracked for changes.

## Testing the server

* Step 1: From this directory run `docker-compose up`
* Step 2: Prepare static files and database: `docker-compose exec web make prepare_server`
* Step 3: Browse to your localhost (or server address)
* Step 4: If running with debug off, restart the server to refresh whitenoise - `docker-compose restart web`

## Running tests in this environment

* Step 1: From this directory run `docker-compose up`
* Step 2: `docker-compose exec web command_to_run`

  For example to run all Aristotle tests, run:

        docker-compose exec web django-admin test aristotle_mdr.tests --settings=aristotle_mdr.tests.settings.settings

  Or to run a single class of tests, run:

        docker-compose exec web django-admin test aristotle_mdr.tests.main.test_html_pages.AnonymousUserViewingThePages --settings=aristotle_mdr.tests.settings.settings

* Step 3 (optional): It is possible to execute bash in the docker container using:
  
        docker-compose exec web bash

    From this bash console the tests can also be run, and the test commands can be
    shorter by setting the correct `DJANGO_SETTINGS_MODULE`, either by exporting the
    correct environment variable:
    
        export DJANGO_SETTINGS_MODULE=aristotle_mdr.tests.settings.settings
        django-admin test aristotle_mdr.tests
    
    or prefixing ahead of the command:
  
        DJANGO_SETTINGS_MODULE=aristotle_mdr.tests.settings.settings django-admin test aristotle_mdr.tests
  

Note: We encourage the use of `docker-compose exec web` over `docker run` as we anticipate
adding extra services (workers, advanced caches, etc...) around Aristotle that will make 
docker-compose easier for testing around.
