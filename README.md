# MIS Bot

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/SJCET_MIS_BOT)
[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-blue.svg)](https://t.me/joinchat/AAAAAEzdjHzLCzMiKpUw6w)

# Introduction
I created this bot as a means to avoid Defaulter's List, and I hope this bot can help others avoid it, too. The bot currently lives on my raspberry pi, but I intend to shift it to a cloud service, like Heroku or Azure very soon. 

## Flowchart
## Features
  * **Bunk Calculator**
  
    Calculate rise/drop in your overall percentage.

    [![Bunk calculator formula](http://www.sciweavers.org/upload/Tex2Img_1511028597/eqn.png)]()

    where 

          a = Total lectures attended

          b = Total lectures conducted on the day of bunk

          c = Total lectures conducted so far

          n = number of lectures to bunk
  * **Until80**

    Shows the number of lectures one must consecutively attend in order to get their Overall Attendance to 80%. It is the minimum percentage of overall lectures one must attend to avoid the defaulter's list.

    [![Until80 formula](http://www.sciweavers.org/upload/Tex2Img_1511029267/eqn.png)]()

    where 

          a = Total lectures attended

          c = Total lectures conducted so far

          x = number of lectures to attend
    **Note:** We calculate `x` from this equation. Value of `x` can be negative too, when your attendance is already over 80.
  * **Results**

    Fetch results of Class Tests. Uses scrapy-splash library.

## Usage

# Contributors
 * [Arush Ahuja (arush15june)](https://github.com/arush15june)
 * [Vikas Yadav (v1k45)](https://github.com/v1k45)