# Analytics as a Service

Suricate is a very simple Analytics as a Service originally designed to
analyze data streams coming from [DTrace](http://www.dtrace.org). Based
on that models could be created and finally actions taken based on the
models and new incoming data via AMQP.

With this first release this has become more a general purpose tool. The
AMQP and DTrace part are stripped out for now.

# Usage

The following steps guide to the usage of the service.

## Step 1 - get the data

Create a simple file json file:

    {
      "server1": [10, 20, 30, 10, 20, 30, 50, 10],
      "server2": [5, 6, 3, 2, 1, 3, 10, 20],
      "server3": [80, 80, 80, 80, 90, 85, 80, 80]
    }

Open the browser navigate to http://localhost:8080 and click 'Data Sources'.
 Select the file an upload it.

*Note*: Support for AMQP data streams will be added soon.

## Step 2 - analyse it

Navigate to the 'Analytics' part. Enter a new name (Optionally you can also
write some python code local and upload it) and hit 'New'. Select the newly
created notebook. From here on it is just some Python coding.

To list the objects and then retrieve the just created one add:

    list_objects()
    tmp = get_object('<id>')

Now we can plot it:

    pyplot.bar(range(0,8, tmp['server1'])
    plot()

Now we will do sth very simple! You can add
[scikit-learn](http://scikit-learn.org/stable/) or
[pandas](http://pandas.pydata.org/) to the preload scripts to directly use
those.

    import numpy
    tmp2 = numpy.asarray(tmp['server1'])
    mean = tmp2.mean()

Now we will store that value:

    create_object({'mean_server1': mean})

Note the edit and remove capabilities of the notebooks as well.

## Step 3 - do sth with it

Just like the analytics part the processing is done in Python. Lets load the
model we just learned:

    mean = get_object('<id_of_mean_obj>')['mean_server1']

Let's use the streaming data sources to get latest usage percentage from
**server1**:

*Note*: This is still work in progress

Compare them and run an action when needed:

    if new_val > mean:
        run_ssh_command(server1, 'shutdown -k now')

We can now update the object from step one too. And therefore learn a new
mean afterwards when we trigger the analytics notebook again. So we get a
continuously updating process.

The scripts for the analytics and or processing part can be triggered
externally via an API (by a cron job?). The clean split of learning
(analytics) and acting (processing) makes the idea of when to trigger what.

# Running it

Currently only a [MongoDB](http://www.mongodb.org) is needed.

## For Development & local

For local environments just run:

    $ ./runme

## In Production

Suricate is a simple [WSGI](http://www.wsgi.org) app which can be run with
multiple servers. It can also be easily deployed on
[OpenShift](http://www.openshift.org) or similar.

By adding Oauth2 support through a WSGI middleware such as [wsgi-oauth2]
(http://styleshare.github.io/wsgi-oauth2/) users can be authenticated. Just
make sure that at some point in your middleware a username needs to be set.
Suricate expects this attribute to be called 'X_UID'. So for example:

    environ['HTTP_X_UID'] = '123'

To get the app do the following:

    from web import wsgi_app
    app = wsgi_app.application

Please note that the usage of TLS is highly recommend!

## Configuration

The configuration file supports some simple configuration settings:

* Mongo
    * The *host* for the MongoDB Server.
    * The *port* for the MongoDB Server.
* Suricate
    * The *preload_ext* script which will be loaded for each notebook and
    which will be exported when the notebook is downloaded.
    * The *preload_int* script which will be loaded for each notebook to
    offer some convenience routines.

# Security considerations

Run at own risk & please be aware that the users of the service get a full
Python interpreter at their hands.
