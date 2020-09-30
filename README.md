# MedQuizBot
 Quiz Bot for Indian Med School server at cyaniDE's request
 
 ## Running
 The bot doesn't allow you to run multiple quizzes simultaneously due to low memory on my host. You can always run your own instances of the bot to work around this, and maybe add support for multiple servers and quizzes in your own branch.
 
 ### Requirements to run:
  - Python >= 3.8.2 ([download here](https://www.python.org/downloads/))
  - PostgreSQL-12 server ([download here](https://www.postgresql.org/download/), or use a remote DB and configure)
 
 It is recommended to run your bot from a virtual environment. You can do this using `python3.8 -m venv venv`
 
 ### Steps to run
  - Install dependencies, i.e. `pip install -U -r requirements.txt`
  - create a `config.py` file in the root directory where the bot is with the following
  ```
  token = '' # your bot's token
  host = '' # your PostgreSQL server host ('localhost' or '127.0.0.1' if it's a local server)
  user = '' # your PostgreSQL username (or if you created a separate role or user for the bot, put that instead)
  password = '' # password for the user specified above
  database = '' # the database to connect to in your host
  ```
  - This code uses v1.5 of discord.py, which requires you to specify gateway intents. You must enable guild member and presence intents in the developer portal for the bot to function.
  - Run `bot.py` in your virtual environment using a process manager of your choice.
   
