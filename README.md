StockTwits Automation
This repository contains an automation bot for interacting with StockTwits using Selenium and Python. The bot automates a variety of actions like logging in, signing up, liking posts, following users, adding tickers to the watchlist, interacting with posts, and more.

Features
1. Login Automation
The bot automates the login process by filling out the username and password fields and submitting the form.
2. Sign-up Automation
Handles the creation of new accounts, including checking if the username is already taken.
3. Liking Posts
Scans StockTwits' feed, randomly selects posts, and likes them.
4. Following Users
Follows users after clicking on their username in the posts and navigating to their profile.
5. Ticker Interaction
The bot can interact with specific stock tickers, like following a particular stock and engaging with posts related to those tickers.
6. Watchlist Management
The bot can add tickers to a watchlist, allowing users to monitor specific stocks in the future.
7. Commenting on Posts
In addition to liking posts, the bot can comment on posts with predefined messages or custom inputs.
8. Scrolling & Dynamic Interaction
Automatically scrolls through StockTwits pages, loading and interacting with new posts dynamically.
Installation
To run this automation bot, you'll need Python and several dependencies. Below are the steps for setting up the environment:

Prerequisites
Python 3.8 or higher
Selenium
selenium-driverless package
An active StockTwits account
Install Dependencies
Clone the repository:

bash
Copy code
git clone git@github.com:Areeba018/stocktwits_automation_all.git
cd stocktwits_automation_all
Install the required Python libraries:

bash
Copy code
pip install -r requirements.txt
Configuration
Replace the placeholder values of username and password in the script with your StockTwits login credentials.
If you wish to update the database with activity logs, configure the update_status_in_db function to interact with your database.
Activities Performed by the Bot
Login
The bot logs in by entering the username and password into the respective fields and clicking the "Login" button.

Activity Logged: "User logged in successfully"
Sign-up
The bot handles the signup process, where it inputs an email (used as the username) and clicks the "Sign Up" button. If the signup button is disabled (username already taken), the bot raises an error.

Activity Logged: "User signed up successfully"
Error Handling: If the user already exists, an error is raised and the bot stops.
Liking Posts
The bot scans posts on StockTwits and likes random posts. It dynamically waits for new posts to load, randomly selects one, and clicks the like button.

Activity Logged: "Post liked successfully"
Message: Logs the post that was liked and the post link.
Following Users
The bot follows users by navigating to their profile after clicking their username in a post. It clicks the "Follow" button if available.

Activity Logged: "User followed successfully"
Message: Logs which user was followed and their profile URL.
Ticker Interaction
The bot can engage with posts related to specific stock tickers. It can like posts, comment, or follow users who post about a particular stock.

Activity Logged: "Interacted with ticker post: $XYZ"
Message: Logs the ticker and the action taken (like, comment, follow).
Watchlist Management
The bot can add stock tickers to the watchlist, allowing users to track specific stocks. It interacts with posts related to these tickers and adds them to a list for later tracking.

Activity Logged: "Ticker $XYZ added to watchlist"
Message: Logs when a ticker is added to the watchlist, helping the bot keep track of stocks for future interactions.
Commenting on Posts
The bot can comment on posts with either predefined comments or custom user input. This feature is useful for engaging with the StockTwits community or initiating discussions on specific posts.

Activity Logged: "Comment added to post successfully"
Message: Logs the comment posted along with the post it was attached to.
Page Scrolling and Dynamic Interaction
The bot automatically scrolls through the StockTwits feed, loading new posts as it goes. It interacts with these posts by liking, commenting, or following users.

Activity Logged: "Scrolled and interacted with posts"
Message: Logs the actions taken after scrolling.
Example Usage
Run the Bot
To run the bot, execute the following command:

bash
Copy code
python stocktwits.py
This will start the bot, and it will perform various activities based on the functions defined in the script.

Notes
Ensure that the selenium-driverless package is installed and properly working.
Modify the random sleep times to avoid detection by StockTwits.
The bot logs all activities to a database, so ensure your database connection is configured properly.
Use the watchlist and ticker interaction functionalities to focus on specific stocks or topics.



