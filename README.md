![Yelp Love](yelplove-medium.png)

# Yelp Love

Yelp Love lets you show others your appreciation for something they've done.
Did they make you laugh in your darkest hour? Did they save your ass? Did they
help fix that bug? Send them love!

## Features

* Send love to one or more recipients (publicly or privately)
* Email notifications when users receive love
* Viewing the most recent 20 loves sent or received by any user
* Leaderboard with the top 20 users who sent and received love
* [API](#api) that allows external applications to send and retrieve love data
* [Manual or automated synchronization](#import-employee-data) between Yelp Love and your employee data
* Admin section to manage aliases and API keys

## Installation

Yelp Love runs on [Google App Engine](https://appengine.google.com/).
In order to install Yelp Love you will need a Google account and the
[Google App Engine SDK for Python](https://cloud.google.com/appengine/downloads).
We recommend installing this via Homebrew if you don't already have it:
```
$ brew install google-app-engine
```

### Create a new project

Login to [Google Cloud Platform](https://console.cloud.google.com) and create a
new project and give it a project name. Optionally you
can specify a project id - a unique identifier for your project. If you don‘t
specify a project id Google will create a random one for you. This id can not be
changed once the project is created.

### Prepare for deployment

Before you can deploy the application for the first time and start sending love
you have to modify [app.yaml](app.yaml) and [worker.yaml](worker.yaml). Please
edit these files and replace the application placeholder with your project id.

Copy the [example config](config-example.py) file to config.py and change the
settings. Don't forget to specify your own SECRET_KEY.

### Initial deployment

Finally, run
```
$ make deploy
```
This will open a browser window for you to authenticate yourself with your
Google account and will upload your local application code to Google App Engine.

Once the deployment succeeds open your browser and navigate to your application
URL, normally [https://project_id.appspot.com](https://project_id.appspot.com).

## Import employee data

### CSV

Create a file employees.csv in the import directory, add all your employee data,
and deploy it. We‘ve put an example csv file in that directory so you can get an
idea of which fields Yelp Love requires for an employee.

Once the CSV file is deployed point your browser to
[https://project_id.appspot.com/employees/import](https://project_id.appspot.com/employees/import).
and follow the instructions.

### JSON via Amazon S3

Create a file employees.json, add all your employee data, and save it in an S3 bucket.
We‘ve put an example JSON file in the import directory so you can get an idea of which
fields Yelp Love requires for an employee.

The S3 bucket name must be configured in config.py.

In order to access the S3 bucket you have to save AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
using the [Secret](models/secret.py) model. Locally you can open up the
[interactive console](http://localhost:8000/console) and execute the following code:

```python
from models import Secret

Secret(id='AWS_ACCESS_KEY_ID', value='change-me').put()
Secret(id='AWS_SECRET_ACCESS_KEY', value='change-me').put()
```

In production you can either use the [Datastore UI](https://console.cloud.google.com/datastore/entities/)
or the [Remote API](https://cloud.google.com/appengine/docs/python/tools/remoteapi).

To kick off the final import you have to run:

```python
from logic import employee
employee.load_employees()
```

You can also setup a cronjob to keep employee data up to date.
Checkout [cron.yaml](cron.yaml) for further details.

## Development

### Prerequisites

Before you can run Yelp Love on your local machine please install the [Google App Engine SDK for Python](https://cloud.google.com/appengine/downloads). You can get it from Google directly or use
your favorite packet mananger.

### Running the application locally

* Check out the application code: <code>git clone git@github.com:Yelp/love.git</code>
* Follow the [Prepare for deployment](#prepare-for-deployment) section
* Run the app: <code>make run-dev</code> will start both [Yelp Love](http://localhost:8080) as well as the [Admin server](http://localhost:8000)
* Follow the [CSV import](#csv) section to locally import user data
* Make your changes

## Deployment

Once you've made your code changes and want to deploy them, you must bump the app version. If you don't,
your [deployment](#initial-deployment) will overwrite the active version of the
app on App Engine. The version number must be updated in 2 or possibly 3 places,
depending on the nature of your changes.

You will absolutely want to bump the version in [setup.py](setup.py) and
[app.yaml](app.yaml). These versions should always match e.g., 1.3.10 in
setup.py and 1-3-10 in app.yaml.

If you modified [worker.yaml](worker.yaml) then you will also need to bump the
version of worker.yaml. This version number is specific to the worker module and
is independent of the main app version.

When you bumped versions in the appropriate files you can deploy your changes by running
<code>make deploy</code>. If you have modified [dispatch.yaml](dispatch.yaml), you additionally
need to use the <code>make deploy_dispatch</code> command to update the routing entries.

Once your code has been uploaded to Google, you must activate the newly deployed version
in the [Developer Console](https://console.developers.google.com/). Then you're done!

If you've modified cron.yaml you have to run <code>appcfg.py update_cron <i>app-directory</i></code>
in order for your changes to take effect. For more information checkout [https://cloud.google.com/appengine/docs/python/config/cron](https://cloud.google.com/appengine/docs/python/config/cron).

## API

Yelp Love also ships with an API which will be available under [https://project_id.appspot.com/api](https://project_id.appspot.com/api).
All data of successful GET requests is sent as JSON.

### Authentication

Successful requests to the API require an API key. These can be created in the Admin section of the
application. Authenticating with an invalid API key will return <code>401 Unauthorized</code>.

### Endpoints

All names, e.g. sender or recipient in the following examples refer to employee usernames.

#### Retrieve love

```
GET /love?sender=foo&recipient=bar&limit=20
```

You must provide either a sender or a recipient. The limit parameter is optional - no limiting will
be applied if omitted.

##### Example

```
curl "https://project_id.appspot.com/api/love?sender=hammy&api_key=secret"
```
```javascript
[
  {
    "timestamp": "2017-02-10T18:10:08.552636",
    "message": "New Barking Release! <3",
    "sender": "hammy",
    "recipient": "darwin"
  }
]
```

#### Send love

```
POST /love
```

Sending love requires 3 parameters: sender, recipient, and message. The recipient parameter may contain
multiple comma-separated usernames.

##### Example

```
curl -X POST -F "sender=hammy" -F "recipient=john,jane" -F "message=YOLO" -F "api_key=secret"  https://project_id.appspot.com/api/love
```
```
Love sent to john, jane!
```

#### Autocomplete usernames

```
GET /autocomplete?term=ham
```

The autocomplete endpoint will return all employees which first_name, last_name, or username match the given term.

##### Example

```
curl "https://project_id.appspot.com/api/autocomplete?term=ha&api_key=secret"
```
```javascript
[
  {
    "label": "Hammy Yo (hammy)",
    "value": "hammy"
  },
  {
    "label": "Johnny Hamburger (jham)",
    "value": "jham"
  }
]
```

## License

Yelp Love is licensed under the [MIT license](LICENSE).

## Contributing

Everyone is encouraged to contribute to Yelp Love by forking the
[Github repository](http://github.com/Yelp/love) and making a pull request or
opening an issue.
