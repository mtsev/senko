# Senko
Discord bot to emulate IRC clients' (also Skype and Slack's) keyword notification feature. 
Senko will DM you the server messages which contain your keywords or phrases along with the context and jumplink.
Phrases should be enclosed in quotation marks to distinguish them from multiple words.

**To add Senko to your server, [follow this link](https://discord.com/api/oauth2/authorize?client_id=578444573031006219&permissions=68608&scope=bot).**

<img src="images/example.png" alt="example of senko's keyword highlighting" width="500"/>

Keyword commands:
* `!kw add <keywords>...` to add keywords or phrases to be notified for
* `!kw rem <keywords>...` to remove keywords or phrases
* `!kw list` to see the list of all keywords and phrases
* `!kw clear` to remove all keywords and phrases

Other stuff:
* Dice rolls using [Random.org](https://www.random.org/) (falls back on random.py)
```
!roll [<max> [<min> [<num>]]]
    max   upper bound of range    [default: 6]
    min   lower bound of range    [default: 1]
    num   number of rolls         [default: 1]
```
* Welcomes you back with `おかえりなのじゃ！` :3
