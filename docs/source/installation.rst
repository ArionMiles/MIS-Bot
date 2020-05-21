Installation
============

.. _pre-reqs:

Pre-requisites
--------------

Telegram
^^^^^^^^
You need a Telegram Bot Token, which you can get by messaging `Botfather
<https://t.me/botfather>`_ on Telegram. You can get your bot token by asking BotFather anytime, but for now, save your bot token somewhere because we will require it in the next step.

Since you're gonna run the bot, you are the administrator of the bot.
You require your telegram chat ID to use admin commands like ``/push``, ``/revert``, etc. 
To get your chat ID, message `FalconGate
<https://telegram.me/FalconGate_Bot>`_ with the command ``/get_my_id`` and save the 9-digit number that comes back, 
we will require this in the next step.


Docker
^^^^^^

Linux
~~~~~

`Learn how to install docker here.
<https://docs.docker.com/install/linux/docker-ce/ubuntu/>`_

`Learn how to install docker-compose here.
<https://docs.docker.com/compose/install/>`_

Windows
~~~~~~~

On Windows 10 Home, I found using Docker-Toolbox to be less than ideal since the VM docker-toolbox uses doesn't expose the container's ports to the host machine, which wouldn't let my bot's container talk to the Splash container (you'll know what it is in next step).

So I chose to run docker inside a Ubuntu VM which I run through Vagrant.
If you're on Windows 10 Pro or Enterprise, just using Docker Desktop will work out fine.
`Download it here.
<https://hub.docker.com/editions/community/docker-ce-desktop-windows>`_

However, if you're on Windows 10 Home edition, follow below steps.

`Download & install Vagrant from here.
<https://www.vagrantup.com/downloads.html>`_

After installation is done run this command in the folder where you'll be downloading or cloning this repository (e.g. ``Documents``):
.. code-block::
vagrant init kwilczynski/ubuntu-16.04-docker
vagrant up

A new ``Vagrantfile`` will be created inside the directory where you run the above command (``Documents`` in our case). 
Open it and add this line before the last line (which says ``end``)
.. code-block::
config.vm.synced_folder "MIS-Bot/", "/srv/MIS-Bot"

This will sync the cloned/downloaded project folder with the ubuntu virtual machine.

Now you can run this command to get inside your Ubuntu VM with docker installed:
.. code-block::
vagrant ssh

When you're done doing docker stuff, you can type ``exit`` to come out of the Ubuntu VM and then run ``vagrant halt`` to shutdown the VM.

Development Setup
-----------------

Cloning the repository
^^^^^^^^^^^^^^^^^^^^^^
Clone the repository by running (in ``Documents`` or some other directory, whichever you created the vagrant VM in the previous step):

.. code-block::
git clone https://github.com/ArionMiles/MIS-Bot/

Open the project directory in terminal with

.. code-block::
cd MIS-Bot/

Run the below command to create folders which will be required by our bot:

.. code-block::
   mkdir -p files/captcha/

Setting environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rename ``example.env`` to ``.env``:

``mv example.env .env``

Edit ``.env`` and enter your ``Bot Token``, your ``Chat ID`` (See :ref:`pre-reqs`), and if you are gonna run it with webhooks,
you'll need to enter your server address as ``URL`` (without HTTP:// or trailing /, like this: ``X.X.X.X``).

Enter ``SPLASH_INSTANCE`` as ``http://splash:8050``

Running with Long Polling
^^^^^^^^^^^^^^^^^^^^^^^^^

If you're testing this locally, change DEBUG value to ``True`` in 
`this file
<https://github.com/ArionMiles/MIS-Bot/blob/master/mis-bot/telegram_bot.py#L147>`_ 
which allows you to use long-polling instead of webhooks and makes development easier.

Running with Webhooks
^^^^^^^^^^^^^^^^^^^^^

If you're gonna deploy this on a remote server, and are expecting lots of users, it's better to use webhooks rather than long-polling.

You need SSL certificates in order to use webhooks. Telegram servers communicate only via HTTPS, with long polling,
the telegram servers take care of it, but since we're using webhooks, we need to take care of it. 
We'll be using a self-signed certificate. To create a self-signed SSL certificate using openssl, run the following command:

``openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem``

The openssl utility will ask you a few details. Make sure you enter the correct FQDN! If your server has a domain,
enter the full domain name here (eg. sub.example.com). If your server only has an IP address, enter that instead.
If you enter an invalid FQDN (Fully Qualified Domain Name), you won't receive any updates from Telegram but also won't see any errors!

-`Source
<https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#creating-a-self-signed-certificate-using-openssl>`_

Move the ``private.key`` and ``cert.pem`` generated to the ``files/`` directory so that they're picked up by ``telegram_bot.py``:
.. code-block::
mv private.key cert.pem files/

Running the docker container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the first run, docker will build an image for our container, it can take significant amount of time depending on your 
internet connection, so wait while docker downloads the python, splash images and installs all the dependencies.

Start the container by running this from the root directory of the project:
.. code-block::
docker-compose up

and after everything is installed, the bot should be up.

Cool! Now you've got the bot running, start experimenting, create new features, the possibilities are endless!

ON GCP: Switch to your project, go to Compute Instance > VPC Network > Firewall Rules
and change "default-http" rule's Protocol/ports value from "tcp:80" to all to allow tg webhook to work 