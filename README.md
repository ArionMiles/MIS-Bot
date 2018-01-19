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
If you wish to run your own instance of the bot, follow the below steps.

 1. Clone/download the repository
 2. The project runs on Python3, so make sure you have it installed.

      Using a virtual environment to run the bot is the best practice, so create a virtual environment by
      `$ virtualenv my_venv` and activate the virtual env by running `source my_venv/bin/activate` before installing or executing the program.
 3. Install all the dependencies by running `$ pip install -r requirements.txt` inside the project directory.
 4. Create a creds.ini file in the same dir with the following contents:

     ```
     [BOT]
     TOKEN = YOUR_BOT_TOKEN
     SPLASH_INSTANCE = http://SPLASH_INSTANCE_IP_ADDR:8050
     ```
     You can get the bot token from BotFather on telegram.
     Put the IP Address and port (8050 by default) of the Splash server into the creds file.
 5. You must run a splash server (on a linux machine preferrably) to be able to use the `/results` command, since it requires splash to generate the screenshot.
 5. To test run the bot, cd to the project dir and run `python telegram_bot.py`
 6. If everything works fine, you should create a systemd service (for a linux machine) so that it'll run on startup. To get an idea of how to set up a systemd service, [read this article](https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/) (it's same for all debian based distros)
    This is my project's systemd service:

    ```
    [Unit]
    Description=Aldel Bot
    After=network.target

    [Service]
    Type=idle
    WorkingDirectory=/home/Projects/MIS-Bot/mis-bot/
    ExecStart=/home/Projects/venv/bin/python telegram_bot.py

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