armstrong.esi
=============
Django application for handling `edge side include (ESI)`_

.. _edge side include (ESI): http://en.wikipedia.org/wiki/Edge_Side_Includes

Usage
-----
ESI allows you to specify sections of the site that require different caching
strategies and can be sent to a smart caching layer for rendering.

For example, if you want to send a page that is identical for every user except
for a welcome message, you could render that message like::

    <html>
      <body>
        <esi:include "/esi/welcome-message" />
        ... the rest of the page ...
      </body>
    </html>

A smart proxy such as `Varnish`_ and the middleware included with
``armstrong.esi`` can cache this page, and send a request for /esi/welcome-message
for personalization. The next user hitting the page would get the cached version and
your application server would only need to render /esi/welcome-message

armstrong.esi provides a template tag for rendering the correct urls with the same
syntax as django's url tag. For example, the above example becomes::

    {% load esi %}
    <html>
      <body>
        {% esi welcome_message %}
        ... the rest of the page ...
      </body>
    </html>

This replaces our ``{% esi %}`` tag with a ``<esi:include>`` tag pointing to
the URL for that view.


.. _Varnish: http://www.varnish-cache.org/

Using with Varnish
""""""""""""""""""

`Varnish`_ integrates fairly easily with armstrong.esi. The EsiHeaderMiddleware
sets the 'X-ESI' header to 'true' if the page request has esi tags on it.  To
enable esi processing in varnish for pages that need it, add the following to
your vcl_fetch method::

    if (beresp.http.X-ESI) {
        set beresp.do_esi = true;
    }


Loading without ESI
"""""""""""""""""""

The template tag reads the ``DEBUG`` settings value and if set to ``True``
renders the view with the current request rather than including the
``<esi:include>`` tag. This makes it easy to see fully rendered pages in development.


Installation & Configuration
----------------------------
You can install the latest release of ``armstrong.esi`` using `pip`_:

::

    pip install armstrong.apps.articles

Make sure to add ``armstrong.esi`` to your ``INSTALLED_APPS``.  You can 
add this however you like.  This works as a copy-and-paste solution:

::

    INSTALLED_APPS += ["armstrong.esi"]

You must also enable the armstrong.esi middleware. To do this, add the following 
line to your ``MIDDLEWARE_CLASSES``::

    'armstrong.esi.middleware.EsiHeaderMiddleware'

If you want to use the ``{% esi %}`` template tag mentioned above please also
add the ``esi`` context processor to your ``TEMPLATE_CONTEXT_PROCESSORS``
setting::

    'armstrong.esi.context_processors.esi'

.. _pip: http://www.pip-installer.org/

Contributing
------------

* Create something awesome -- make the code better, add some functionality,
  whatever (this is the hardest part).
* `Fork it`_
* Create a topic branch to house your changes
* Get all of your commits in the new topic branch
* Submit a `pull request`_

.. _pull request: http://help.github.com/pull-requests/
.. _Fork it: http://help.github.com/forking/


State of Project
----------------
Armstrong is an open-source news platform that is freely available to any
organization.  It is the result of a collaboration between the `Texas Tribune`_
and `Bay Citizen`_, and a grant from the `John S. and James L. Knight
Foundation`_.  The first release is scheduled for June, 2011.

To follow development, be sure to join the `Google Group`_.

``armstrong.apps.articles`` is part of the `Armstrong`_ project.  You're
probably looking for that.

.. _Texas Tribune: http://www.texastribune.org/
.. _Bay Citizen: http://www.baycitizen.org/
.. _John S. and James L. Knight Foundation: http://www.knightfoundation.org/
.. _Google Group: http://groups.google.com/group/armstrongcms
.. _Armstrong: http://www.armstrongcms.org/


License
-------
Copyright 2011-2012 Bay Citizen and Texas Tribune

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
