# MIS Bot

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/SJCET_MIS_BOT)
[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-blue.svg)](https://t.me/joinchat/AAAAAEzdjHzLCzMiKpUw6w)

# Introduction
I created this bot as a means to avoid Defaulter's List, and I hope this bot can help others avoid it, too. The bot is hosted on Digital Ocean. 

## Flowchart
TO BE ADDED

## Features
  * **Bunk Calculator**
  
    Calculate rise/drop in your overall percentage.

    [![Bunk calculator formula](media/bunk_func.png)]()

    where 

          a = Total lectures attended

          b = Total lectures conducted on the day of bunk

          c = Total lectures conducted so far

          n = number of lectures to bunk
  * **Until80**

    Shows the number of lectures one must consecutively attend in order to get their Overall Attendance to 80%. It is the minimum percentage of overall lectures one must attend to avoid the defaulter's list.

    [![Until80 formula](media/until80_func.png)]()

    where 

          a = Total lectures attended

          c = Total lectures conducted so far

          x = number of lectures to attend
    **Note:** We calculate `x` from this equation. Value of `x` can be negative too, when your attendance is already over 80.
  * **Results**

    Fetch results of Class Tests. Uses scrapy-splash library.

## Setup
If you wish to run your own instance of the bot, follow the below steps. Note that it is recommended you use Linux to host this project as it's not completely compatible with Windows. I'm constantly working on making it platform agnostic so that it can be used on any OS.

 1. Clone/download the repository
 2. The project runs on Python3, so make sure you have it installed.

      Using a virtual environment to run the bot is the best practice, so create a virtual environment by
      `$ virtualenv venv` and activate the virtual env by running `source venv/bin/activate` before installing or executing the program.
 3. Install all the dependencies by running `$ pip install -r requirements.txt` inside the project directory.
 4. Add your bot `TOKEN` and `SPLASH_INSTANCE` IP address in your environment variables by using
     `$ nano /etc/environment`
     And paste
     
     ```
     TOKEN="your_bot_token"
     SPLASH_INSTANCE="your_splash_instance_ip_addr:8050"
     URL="server_ip_addr"
     ```
     Save your changes with `Ctrl-O`, and exit with `Ctrl-X`

     You can get the bot token from BotFather on telegram.
     Put the IP Address and port (8050 by default) of the Splash server into the creds file.
 5. Generate SSL certificates. Telegram servers communicate only via HTTPS, with long polling, the telegram servers take care of it, but since we're using webhooks, we need to take care of it. We'll be using a self-signed certificate.
     To create a self-signed SSL certificate using openssl, run the following command:

    `openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem`

    The openssl utility will ask you a few details. **Make sure you enter the correct FQDN!** If your server has a domain, enter the full domain name here (eg. sub.example.com). If your server only has an IP address, enter that instead. If you enter an invalid FQDN (Fully Qualified Domain Name), you won't receive any updates from Telegram but also won't see any errors!

    [Source](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#creating-a-self-signed-certificate-using-openssl)
 6. You must run a splash server (on a linux machine preferrably) to be able see the attendance and test reports, since it requires splash to generate the screenshot.
 7. To test run the bot, cd to the project dir and run `python telegram_bot.py`
 8. If everything works fine, you should create a systemd service (for a linux machine) so that it'll run on startup. To get an idea of how to set up a systemd service, [read this article](https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/) (it's same for all debian based distros)
    This is my project's systemd service:

    ```
    [Unit]
    Description=Aldel Bot
    After=network.target

    [Service]
    Type=idle
    WorkingDirectory=/home/Projects/MIS-Bot/mis-bot/
    ExecStart=/home/Projects/venv/bin/python telegram_bot.py
    EnvironmentFile=/etc/environment

    [Install]
    WantedBy=multi-user.target
    ```
    Save in `/lib/systemd/system/` as `bot.service`

    Enable: `sudo systemctl enable bot.service`

    Start: `sudo systemctl start bot`

    Restart: `sudo systemctl restart bot`
    
    Status: `sudo systemctl status bot`

# Roadmap
 * ~Attendance scraper~
 * ~Bunk/Until80 functions~
 * ~Allow registration~
 * ~Results scraper~
 * ~Store attendance data in a database~
 * Use scrapyd to deploy spiders as opposed to [the current solution](https://stackoverflow.com/a/43661172)
 * Create an API to execute spiders.
 * Create an Android application


# Contributors
 * [Arush Ahuja (arush15june)](https://github.com/arush15june)
 * [Vikas Yadav (v1k45)](https://github.com/v1k45)

# License
MIT License. Please see [License](LICENSE.md) file for more information.