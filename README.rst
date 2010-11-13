Armstrong ESI
=============
Django application for handling `edge side include (ESI)`_

.. warning::
   This document is speculative until this warning is removed.  Don't expect
   the awesomeness described within as long as this is here.

Hows and Whys
-------------

ESI allows you to specify sections of the site that require different caching
strategies and can be sent to a smart caching layer for rendering.

For example, if you want to send a page that is identical for every user except
for a welcome message, you would render that message like::

    <html>
      <body>
        <esi:include "/esi/welcome-message.html" />
        ... the rest of the page ...
      </body>
    </html>

A smart proxy such as `Varnish`_ and the middleware included with
``armstrong.esi`` can cache this page, then render it dropping in the dynamic
portions without having to talk to the app server again.

Use this package to specify sections of your templates that can be rendered via
ESI.  You call the ``{% esi %}`` template tag and give it the name of a
registered view and it will replace itself with the appropriate
``<esi:include>`` tag.  For example, the above example becomes::

    {% load esi %}
    <html>
      <body>
        {% esi welcome_message %}
        ... the rest of the page ...
      </body>
    </html>

This replaces our ``{% esi %}`` tag with a ``<esi:include>`` tag pointing to
the URL for that view.


Loading without ESI
"""""""""""""""""""

The template tag reads the ``DEBUG`` settings value [#]_ and if set to ``True``
renders the view with the current request rather than including the
``<esi:include>`` tag.

You can change this default behavior to through several settings:

``TT_ESI_FORCE``
    Setting to ``True`` means that a ``<esi::include>`` tag will always be
    generated.  (Default: ``False``)
``TT_ESI_NEVER``
    Setting to ``True`` means that a ``<esi:include>`` tag will never be
    generated.  The ``TT_ESI_FORCE`` setting always takes precedence.  Any time
    it is set, this value has no meaning.  (Default: ``True``)

Installation
------------
Recommending installation is through `pip`_::

    prompt> pip install -e git://github.com/texastribune/tt.templatetags.esi#egg=tt.templatetags.esi

Once installed, you must add the app to your ``INSTALLED_APPS`` inside your
settings::

    'tt.templatetags.esi',

You must also enable the custom middleware if you want to use the internal ESI
caching.  To do this, add the following line to your ``MIDDLEWARE_CLASSES``::

    'armstrong.esi.middleware.ESIHandlerMiddleware',


Internal Middleware
-------------------

Edge-Side Includes are great for increasing the cachability of your pages, but
they traditionally require additional overhead to get running.
``armstrong.esi`` includes a middleware that can handle the caching for you so
you don't have to setup and maintain any additional server hardware.

.. todo:: add information explaining what is happening


Contributing
------------
Contributions are welcomed and encouraged.  Please follow these instructions
for making a contribution:

* Fork this repository
* Create a topic branch.  Be descriptive with its name.
* Make some great addition, fix a bug, or clean it up
* Submit a Pull Request

You can also report bugs via `Issue Tracker`_.


.. _edge side include (ESI): http://en.wikipedia.org/wiki/Edge_Side_Includes
.. _Wikipedia article: http://en.wikipedia.org/wiki/Edge_Side_Includes 
.. _pip: http://pip.openplans.org
.. _Varnish: http://www.varnish-cache.org/
.. _Issue Tracker: https://github.com/texastribune/tt.templatetags.esi/issues

.. rubric:: Footnotes
.. [#] http://docs.djangoproject.com/en/1.2/ref/settings/#debug
