

import asyncio
import os
import random
import pyautogui

from selenium_driverless import webdriver
from selenium_driverless.types.by import By

from redbox import EmailBox
from redbox.query import UNSEEN, SUBJECT

from bs4 import BeautifulSoup


async def random_sleep(min_seconds=2, max_seconds=5):
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


class Stocktwits:

    def __init__(self, _id, name, 
                 start_page='https://stocktwits.com', 
                 proxy_type=None, proxy_address=None, 
                 username=None, password=None, fullname=None,
                 avatar=None, bio=None,
                 update_status_in_db=None):

        self.id = _id
        self.name = name
        self.start_page = start_page
        self.proxy_type = proxy_type
        self.proxy_address = proxy_address
        
        self.username = username
        self.password = password
        self.fullname = fullname
        self.bio = bio
        self.avatar = avatar
        
        self.update_status_in_db = update_status_in_db
        
        self.driver = None

        self.tickers_required = ['BURU', 'CRKN', 'MDAI', 'HMBL']
        self.tickers_optional = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        
    async def initialize(self):

        options = webdriver.ChromeOptions()
        
        extension_dir = "extensions"
        adguard_extension_path = os.path.join(extension_dir, 'AdGuard-AdBlocker-Chrome-Web-Store')
        adguard_extension_path = os.path.abspath(adguard_extension_path)
        if os.path.isdir(adguard_extension_path):
            options.add_argument(f"--load-extension={adguard_extension_path}")        

        driver = await webdriver.Chrome(options=options)

        await driver.maximize_window()
        
        await asyncio.sleep(2)
        
        await self.switch_to_original_tab(driver)
                
        use_proxy = bool(int(os.getenv('USE_PROXY', '0')))
        if use_proxy and (self.proxy_type and self.proxy_address):
            await driver.set_single_proxy(f'{self.proxy_type}://{self.proxy_address}')
            await driver.get('https://ipv4.icanhazip.com', wait_load=True, timeout=120)
            await random_sleep()
            
            # todo: verify proxy connection

        self.driver = driver

    async def switch_to_original_tab(self, driver):

        # Switch to the new tab (get the handles of all open tabs)
        all_tabs = await driver.window_handles
        print('tabs:', len(all_tabs))        
        
        original_tab = None
        other_tabs = []
        for tab in all_tabs:
            print(tab.id, tab.url)
            if 'about:blank' in tab.url:
                original_tab = tab
            else:
                other_tabs.append(tab)
        
        for tab in other_tabs:
            print('switch to tab:', tab.url)
            await driver.switch_to.window(tab)
            await random_sleep()
            print('closing tab:', tab.url)
            try:
                await driver.close()
            except Exception:
                pass

        # Switch back to the original tab
        await driver.switch_to.window(original_tab)
        print("Switched back to the original tab.", original_tab.id)        
        
    async def close(self):
        await self.driver.quit()

    async def login(self, login_url):

        username = self.username.split('@')[0]
        password = self.password

        await self.driver.get(login_url, wait_load=False)
        await asyncio.sleep(10)  # Allow time for the redirect
        print("StockTwits login page opened successfully.")

        # Enter the username
        username_field = await self.driver.find_element("xpath", "//input[@data-testid='log-in-username']", timeout=60)
        if not username_field:
            raise Exception("Username field not found.")
        
        await username_field.click()
        await username_field.send_keys(username)
        print("Username entered.")
        await random_sleep()

        # Wait for the password field to appear
        password_field = await self.driver.find_element("css selector", "[data-testid='log-in-password']", timeout=60)
        if not password_field:
            raise Exception("Password field not found.")

        await password_field.click()
        await password_field.send_keys(password)
        print("Password entered.")
        await random_sleep()

        # Click the login button
        login_button = await self.driver.find_element("xpath", "//button[@type='submit']", timeout=60)
        if not login_button:
            raise Exception("Login button not found.")

        await self.driver.execute_script("arguments[0].click();", login_button, timeout=10)
        print("Login button clicked.")
        await random_sleep()      
 

        # Wait and check the current URL
        await asyncio.sleep(20)  # Allow time for the redirect
        current_url = await self.driver.current_url  # Use await to get the URL value
        if not current_url:
            raise Exception("Failed to load URL after login.")
 
        print(f"Current URL after login: {current_url}")  # Debug log
        if "signin" in current_url:
            raise Exception("Login failed.")
        print("Login successful")

        if self.update_status_in_db:
            message = f"User '{username}' successfully logged in and was redirected to {current_url}."
            print(message)
            self.update_status_in_db(self.id, 'log_event', {
                'activity': 'Logged In', #  todo list of activity
                'page_url': current_url,
                'message': message[:200]   # max length 200
            }) 

    async def upload_avatar_via_dialog(self):

        avatar_file = self.avatar
        avatar_path = os.path.abspath(avatar_file)

        print(f"Uploading avatar from: {avatar_path}")

        # Wait for file dialog to appear
        await asyncio.sleep(10)

        # Type the file path
        pyautogui.write(avatar_path)
        await random_sleep()

        # Press Enter to confirm
        pyautogui.press("enter")
        print("Avatar uploaded successfully via dialog.")

    async def update_profile(self):

        profile_element = await self.driver.find_element("xpath", "//span[contains(@class, 'MenuItem_label__') and contains(text(), 'Profile')]", timeout=30)
        if not profile_element:
            raise Exception("Profile button not found. Exiting.")

        await self.driver.execute_script("arguments[0].click();", profile_element, timeout=10)
        print("Profile button clicked.")
        await random_sleep()

        edit_profile_element = await self.driver.find_element("xpath", "//a[text()='Edit Profile']", timeout=30)
        if not edit_profile_element:
            raise Exception("Edit profile button not found. Exiting.")

        await self.driver.execute_script("arguments[0].click();", edit_profile_element, timeout=10)
        print("Edit profile button clicked.")
        await random_sleep()

        add_profile_photo_element = await self.driver.find_element("xpath", "//button[span[text()='Add Photo']]", timeout=30)
        if not add_profile_photo_element:
            raise Exception("Add profile photo button not found. Exiting.")
 
        await self.driver.execute_script("arguments[0].click();", add_profile_photo_element, timeout=10)
        print("Add profile photo button clicked.")
        await random_sleep()

        # Call the function to handle file dialog for avatar upload
        await self.upload_avatar_via_dialog()
        await random_sleep()

       # Bio
        bio_element = await self.driver.find_element("xpath", "//label[text()='Tell the Stocktwits community a little about yourself']", timeout=30)
        if not bio_element:
            raise Exception("Bio field not found")

        profile_bio = self.bio
        # Send the generated bio to the input field
        await bio_element.send_keys(profile_bio)
        print(f"Bio entered: {profile_bio}")
        await random_sleep()

        # Asset traded most frequently
        equities_checkbox_element = await self.driver.find_element("xpath", "//label[span[text()='Equities']]", timeout=30)

        if not equities_checkbox_element:
              raise Exception("Equity checkbox element not found.")

        # Scroll to the element to make it visible
        await self.driver.execute_script(
              "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", equities_checkbox_element, timeout=10)
        await random_sleep()  # Let the scroll animation complete

          # Click the element
        await self.driver.execute_script("arguments[0].click();", equities_checkbox_element, timeout=10)
        print("Equity Checkbox Selected")
        await random_sleep()

        # Approach to Trading
        trading_checkbox_elements = await self.driver.find_elements("xpath", "//div[@role='group']//label[contains(@class, 'MultiCheckboxInput_optionContainer__SvKV3')]", timeout=30)
        if not trading_checkbox_elements:
            raise Exception("Approach to Trading checkboxes found.")
        
        # Randomly select one checkbox
        random_checkbox = random.choice(trading_checkbox_elements)
        # Scroll to the element using its bounding rectangle
        await self.driver.execute_script(
             """
            const element = arguments[0];
            const rect = element.getBoundingClientRect();
            const scrollOffset = rect.top + window.scrollY - (window.innerHeight / 2);
            window.scrollTo({ top: scrollOffset, behavior: 'smooth' });
            """, random_checkbox, timeout=10
        )
        await random_sleep()  # Let the scroll complete

        # Click the randomly selected checkbox
        await self.driver.execute_script("arguments[0].click();", random_checkbox, timeout=10)
        # Get the checkbox text by awaiting the text attribute
        checkbox_text = await random_checkbox.text

        # Print the text of the clicked checkbox
        print(f"Clicked on checkbox with text: {checkbox_text}")
        await random_sleep() 

        # Primary Holding Period
        holding_period_checkbox_elements = await self.driver.find_elements("xpath", "//div[@role='group']//label[contains(@class, 'MultiCheckboxInput_optionContainer__SvKV3')]", timeout=30)
        
        if not holding_period_checkbox_elements:
            raise Exception("Primary Holding Period checkboxes found.")
        
        # Randomly select one checkbox
        random_checkboxx = random.choice(holding_period_checkbox_elements)
        # Scroll to the element using its bounding rectangle
        await self.driver.execute_script(
             """
            const element = arguments[0];
            const rect = element.getBoundingClientRect();
            window.scrollBy(0, rect.top + window.scrollY - window.innerHeight / 2);
            """, random_checkboxx, timeout=10
        )
        await random_sleep()  # Let the scroll complete

        # Click the randomly selected checkbox
        await self.driver.execute_script("arguments[0].click();", random_checkboxx)
        # Get the checkbox text by awaiting the text attribute
        checkbox_text = await random_checkboxx.text

        # Print the text of the clicked checkbox
        print(f"Clicked on checkbox with text: {checkbox_text}")
        await random_sleep() 

        # Experience
        experience_checkbox_elements = await self.driver.find_elements("xpath", "//div[@role='group']//label[contains(@class, 'MultiCheckboxInput_optionContainer__SvKV3')]", timeout=30)
        if not experience_checkbox_elements:
            raise Exception("Primary Holding Period checkboxes found.")
        
        # Randomly select one checkbox
        random_checkboxxx = random.choice(experience_checkbox_elements)
        # Scroll to the element using its bounding rectangle
        await self.driver.execute_script(
             """
            const element = arguments[0];
            const rect = element.getBoundingClientRect();
            window.scrollBy(0, rect.top + window.scrollY - window.innerHeight / 2);
            """, random_checkboxxx, timeout=10
        )
        await random_sleep()  # Let the scroll complete

        # Click the randomly selected checkbox
        await self.driver.execute_script("arguments[0].click();", random_checkboxxx, timeout=10)
        # Get the checkbox text by awaiting the text attribute
        checkbox_text = await random_checkboxxx.text

        # Print the text of the clicked checkbox
        print(f"Clicked on checkbox with text: {checkbox_text}")
        await random_sleep() 

        # Click the save button
        save_button = await self.driver.find_element("xpath", "//button[contains(@class, 'Button_button__mg_cR') and contains(@class, 'Profile_saveBtn__ZDu3B') and text()='Save']", timeout=30)
        if not save_button:
            raise Exception("Save button not found.")

        await self.driver.execute_script("arguments[0].click();", save_button, timeout=10)
        print("Save button clicked.")
        await random_sleep()
        # Get the current URL of the page
        current_url = await self.driver.current_url
        print(f"Profile Updation completed on page: {current_url}")
        if self.update_status_in_db:
            # Generate the log message
            message = (
                f"User '{self.username.split('@')[0]}' updated their profile: "
                f"Bio set to '{self.bio}', "
                f"Selected 'Equities' as the asset traded most frequently, "
                f"Trading approach set to '{checkbox_text}', "
                f"Holding period set to '{checkbox_text}', "
                f"Experience set to '{checkbox_text}'."
            )
            print(message)

            self.update_status_in_db(self.id, 'log_event', {
                'activity': 'Profile Updated', # TODO: list of activity
                'page_url': '',
                'message': message[:200]  # max length 200
            })  

    async def human_like_mouse_move(driver,self, x_start, y_start, x_end, y_end):
        """Perform a human-like mouse movement from one point to another."""
        try:
            speed = random.uniform(0.1, 0.3)  # Slow down the movement for visibility
            num_steps = random.randint(15, 30)  # More steps for smoother movement
            x_step = (x_end - x_start) / num_steps
            y_step = (y_end - y_start) / num_steps

            print(f"Starting human-like mouse movement from ({x_start}, {y_start}) to ({x_end}, {y_end})")

            for i in range(num_steps):
                x_offset = random.uniform(-5, 5)
                y_offset = random.uniform(-5, 5)
                x = x_start + (x_step * i) + x_offset
                y = y_start + (y_step * i) + y_offset
                pyautogui.moveTo(x, y, duration=speed)

                # print(f"Moving to ({x}, {y})")

                if random.random() < 0.3:
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                await asyncio.sleep(random.uniform(0.01, 0.05))

            await random_sleep()
            # Get the current URL of the page
            current_url = await self.driver.current_url
            print(f"Mouse movement completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'Mouse Movement', # TODO: list of activity
                    'page_url': current_url,
                    'message': f"Human-like mouse movement performed on page: {current_url}." 
                }) 
        
        except Exception as e:
            print(f"Error during mouse movement: {e}")

    async def do_some_scroll(self, scroll_count=5, min_scroll_distance=300, max_scroll_distance=600):
        """Perform human-like scrolling."""
        try:
            for scroll in range(scroll_count):
                
                print(f"Scrolling... {scroll + 1} / {scroll_count}")
                
                scroll_distance = random.randint(min_scroll_distance, max_scroll_distance)
                await self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});", timeout=10)
                print(f"Scrolled down by {scroll_distance} pixels.")
                await random_sleep()

                # Randomly scroll up
                if random.random() < 0.5:
                    scroll_distance_up = random.randint(min_scroll_distance, max_scroll_distance)
                    await self.driver.execute_script(f"window.scrollBy(0, -{scroll_distance_up});", timeout=10)
                    print(f"Scrolled up by {scroll_distance_up} pixels.")
                    await random_sleep()
                # Get the current URL of the page
                current_url = await self.driver.current_url
                print(f"Scrolling activity completed on page: {current_url}")

                if self.update_status_in_db:
                    self.update_status_in_db(self.id, 'log_event', {
                        'activity': 'Page Scroll', # TODO: list of activity
                        'page_url': current_url,
                        'message': f"Human-like scrolling performed on page: {current_url}."  
                    }) 

        except Exception as e:
            print(f"Error during scrolling: {e}")

    async def like_post(self, random_post):
        try:
            like_button = await random_post.find_element(
                "xpath", ".//button[@aria-label='Like message']"
            )

            # Scroll the like button into view and click it
            await self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button, timeout=10)
            await random_sleep()  # Short delay before liking
            await like_button.click()
            print("Post liked successfully.")
            # Extract post link
            post_url_element = await random_post.find_element("xpath","//div[@class='flex flex-row justify-between items-center gap-x-2']/a[contains(@href, '/message/')]")
            post_url = await post_url_element.get_attribute("href")
            print(post_url)

            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'like_post', # TODO: list of activity
                    'page_url': post_url,
                    'message': f"User '{self.username.split('@')[0]}' liked the post at URL: {post_url}"[:200]   # max length 200
                })

        except Exception as e:
            print(f"Error liking post: {e}")

    async def generate_random_comment(_):
        comments = [
        "Great post! ✨",
        "Insightful thoughts, thanks for sharing!",
        "Really helpful analysis! 🚀",
        "Keep up the great work! 👍",
        "Very interesting perspective."
        ]
        return random.choice(comments)
    
    async def comment_on_post(self, random_post):
        try:
            comment_button = await random_post.find_element("xpath", ".//button[@aria-label='Reply']")
            # Scroll the comment button into view and click it
            await self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_button, timeout=10)
            await random_sleep()  # Short delay before commenting

            await comment_button.click()
            comment_input = await self.driver.find_element("xpath", "//div[@contenteditable='true']")
            comment = await self.generate_random_comment()
            await random_sleep()

            # Input comment
            await self.driver.execute_script("""
                arguments[0].innerText = arguments[1];
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
            """, comment_input, comment)
            await random_sleep()

            # post comment
            reply_button = await self.driver.find_element( "xpath", "//button[contains(., 'Reply')]")
            await self.driver.execute_script("arguments[0].click();", reply_button)

            print(f"Comment {comment} added successfully.")
            await random_sleep()
            # Extract post link
            post_url_element = await random_post.find_element("xpath","//div[@class='flex flex-row justify-between items-center gap-x-2']/a[contains(@href, '/message/')]")
            post_url = await post_url_element.get_attribute("href")
            print(post_url)

            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'comment_post', # TODO: list of activity
                    'page_url': post_url,
                    'message': f"User '{self.username.split('@')[0]}' comment on the post at URL: {post_url}"[:200]   # max length 200
                })

        except Exception as e:
            print(f"Error commenting on post: {e}")

    async def follow_user(self, random_post):
        try:
            link_a = await random_post.find_element("xpath", ".//span[starts-with(@class, 'StreamMessage_username')]/..", timeout=10)
            if not link_a:
                raise Exception("User link not found.")

            # Scroll the like button into view and click it
            await self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_a, timeout=10)
            await random_sleep()  # Short delay before liking

            await link_a.click()
            
            await asyncio.sleep(20) # Wait for the user page to be fully loaded

            # find follow button in user page header
            cond1 = "//div[contains(concat(' ', normalize-space(@class), ' '), ' UserPageHeader_actions')]"
            cond2 = "//button[contains(concat(' ', normalize-space(@class), ' '), ' FollowButton_button')]"
            follow_button = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=20)
            if not follow_button:
                raise Exception("follow button not found.")
            
            button_text = await follow_button.text
            button_text = button_text.strip()
            print(f"Follow button text: {button_text}")
            if button_text == 'Follow':
                await follow_button.click()
                print("follow user successfully.")

                # Get the current URL of the page
                current_url = await self.driver.current_url
                print(f"Follow user activity completed on page: {current_url}")

                 # Generate the message
                # Extract the username of the person performing the action
                followed_user_element = await  random_post.find_element("xpath", ".//span[starts-with(@class, 'StreamMessage_username')]")
                followed_user = await followed_user_element.text                
                message = f"User {self.username.split('@')[0]} has followed {followed_user} on StockTwits!"
                print(message)

                if self.update_status_in_db:
                    self.update_status_in_db(self.id, 'log_event', {
                        'activity': 'follow user', # TODO: list of activity
                        'page_url': current_url,
                        'message': message[:200]  # max length 200
                    })
            else:
                print('user is already followed.')
            
            await random_sleep()
            
            await self.like_comment_some_random_post(
                random.randint(2, 4),  # Number of scrolls
                random.randint(0, 3)  # Maximum likes per scroll
            )

        except Exception as e:
            print(f"Error following user on post: {e}")

    async def like_comment_some_random_post(self, scrolls=3, max_like_comments=2):
        """assuming there are posts on the page"""
        print('like_comment_some_random_post')

        like_comment_count = 0  # counter for likes/comments

        for scroll in range(scrolls):

            try:
                print(f"Scrolling... {scroll + 1} / {scrolls}")
                
                # Scroll the page
                await self.driver.execute_script("window.scrollBy(0, 3000);", timeout=10)
                await random_sleep()

                # Wait for posts to load dynamically
                # posts = await self.driver.find_elements("xpath", "//div[contains(@class, 'StreamMessageItem')]", timeout=60)
                posts = await self.driver.find_elements("xpath", "//div[contains(concat(' ', normalize-space(@class), ' '), ' StreamMessage_clickable__')]", timeout=10)
                print(f"Found {len(posts)} posts in the current scroll view.")

                if len(posts) > 0 and max_like_comments > 0:

                    # Randomly choose a post to like
                    random_post = random.choice(posts)
                    
                    like_or_comment = random.choice(['like', 'comment'])
                    if like_or_comment == 'like':
                        await self.like_post(random_post)
                    elif like_or_comment == 'comment':
                        await self.comment_on_post(random_post)

                    like_comment_count += 1
                    if like_comment_count >= max_like_comments:
                        break
            
                await random_sleep()

            except Exception as e:
                print(f"Error during scrolling: {e}")
                # Retry scrolling if there's an issue with loading new content
                await random_sleep()        

    async def follow_some_random_user(self):
        """Follow some random users on the page"""
        print('follow_some_random_user')
        
        try:
            
            await self.do_some_scroll(scroll_count=random.randint(2, 5))
            
            await random_sleep()

            posts = await self.driver.find_elements("xpath", "//div[contains(concat(' ', normalize-space(@class), ' '), ' StreamMessage_clickable')]", timeout=10)
            print(f"Found {len(posts)} posts in the current scroll view.")

            if len(posts) > 0:

                # Randomly choose a post to like
                random_post = random.choice(posts)
                await self.follow_user(random_post)
                        
            await random_sleep()

        except Exception as e:
            print(f"Error during follow: {e}")
        
    async def add_to_watchlist(self, ticker):
        
        print('add_to_watchlist', ticker)
 
        try:
            # find follow button in user page header
            cond1 = "//div[contains(concat(' ', normalize-space(@class), ' '), ' WatchButton_container')]"
            cond2 = "//button[contains(concat(' ', normalize-space(@class), ' '), ' WatchButton_button')]"
            watchlist_button = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)
            if not watchlist_button:
                raise Exception("watchlist button not found.")
            
            button_text = await watchlist_button.text
            button_text = button_text.strip()
            print(f"watchlist button text: {button_text}")
            
            # check button text to determine if it's already in watchlist
            # If not, click the button
            
            if button_text == 'Watch':
                await watchlist_button.click()                
                print('Ticker added to watchlist.', ticker)
                await random_sleep()
                # Get the current URL of the page
                current_url = await self.driver.current_url
                print(f"Added ticker to watchlist activity completed on page: {current_url}")
                if self.update_status_in_db:
                    self.update_status_in_db(self.id, 'log_event', {
                        'activity': 'Ticker added to watchlist', # TODO: list of activity
                        'page_url': current_url,
                        'message':f"User '{self.username.split('@')[0]}'  added {ticker} to watchlist"[:200]   # max length 200  # max length 200
                    })
            else:
                print('Ticker already in watchlist.', ticker)
                    
        except Exception as e:
            print(f"Error adding in watchlist: {e}")

    async def search_random_ticker_and_scroll(self):
        """Search for a random ticker, add it to watchlist if not already, and scroll through the search results."""
        try:
            search_bar = await self.driver.find_element("xpath", "//input[@name='desktopSearch' and @placeholder='Search stocks, crypto, and people']", timeout=60)
            if not search_bar:
                raise Exception("Search bar not found.")
                
            await search_bar.click()
            print("Search bar clicked.")
            await random_sleep()

            # Get the current URL of the page
            current_url = await self.driver.current_url
            print(f"Search random tickers activity completed on page: {current_url}")

            # Select a random ticker
            all_tickes = self.tickers_required + self.tickers_optional
            ticker_to_search = random.choice(all_tickes)
            print(f"Searching for ticker: {ticker_to_search}")
            await search_bar.send_keys(ticker_to_search)
            await random_sleep()
            

            # Click the first search result
            result_element = await self.driver.find_element("xpath", "//div[contains(@class, 'List_list__VdL2T')]//div[contains(@class, 'Item_item__CUnwa')]", timeout=20)
            if not result_element:
                raise Exception("No search results found.")
            
            await result_element.click()
            print(f"Clicked on search result for ticker: {ticker_to_search}")
            await random_sleep()
            current_urll = await self.driver.current_url
            print(f"Ticker search activity completed on page: {current_urll}")

            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'ticker search', # TODO: list of activity
                    'page_url': current_urll ,
                    'message':f"User '{self.username.split('@')[0]}'  search this ticker: {ticker_to_search}"[:200]   # max length 200  # max length 200
                })
            await asyncio.sleep(20) # Wait for ticker page to load

            # add to watchlist if not already
            await self.add_to_watchlist(ticker_to_search)

            await self.like_comment_some_random_post(
                random.randint(2, 4),  # Number of scrolls
                random.randint(0, 3)  # Maximum likes per scroll
            )
                        
            # Scroll on the resulting page
            await self.do_some_scroll(scroll_count=random.randint(2, 5))

            await self.driver.execute_script("window.scrollTo(0, 0);")
            print("Scrolled up on search results.")
            
            await self.follow_some_random_user()
            
            # go to home
            logo_element = await self.driver.find_element("id", "sidebar_logo_id", timeout=20)
            if not logo_element:
                raise Exception("No logo found.")
            
            await logo_element.click()
            await asyncio.sleep(20) # Wait for ticker page to load
            
        except Exception as e:
            print(f"Error during ticker search: {e}")

    async def switch_between_latest_popular_and_scroll(self):
        """Switch between "Latest" and "Popular" tabs, like some random post and scroll."""
        try:
            # choose between "Latest" and "Popular" tabs
            tabs = ['Latest', 'Popular']
            tab_name = random.choice(tabs)

            # Click on the "Latest" tab
            selected_tab = await self.driver.find_element("xpath", f"//div[contains(@class, 'flex flex-row justify-start items-center') and text()='{tab_name}']", timeout=60)
            if not selected_tab:
                raise Exception(f"{tab_name} tab not found.")

            await selected_tab.click()
            print(f"clicked on {tab_name} tab.")
            await random_sleep()
            current_url = await self.driver.current_url
            print(f"{tab_name} tab clicking activity completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': f'open {tab_name} tab', # TODO: list of activity
                    'page_url': current_url,
                    'message':f"User '{self.username.split('@')[0]}'  clicked on {tab_name} tab and opened url is {current_url}"[:200]   # max length 200  # max length 200
                })
                        
            if tab_name == 'Latest':
                # choose between "Following", "Watchlist" and "Trending" tabs
                sub_tabs = ['Following', 'Watchlist', 'Trending']
                sub_tab_name = random.choice(sub_tabs)
            
                sub_selected_tab = await self.driver.find_element("xpath", f"//div[contains(@class, 'flex flex-row justify-start items-center') and text()='{sub_tab_name}']", timeout=60)
                if sub_selected_tab:
                    await sub_selected_tab.click()
                    print(f"open {sub_tab_name} sub tab.")            
                    await random_sleep()
                    current_url = await self.driver.current_url
                    print(f"{sub_tab_name} sub tab clicking activity completed on page: {current_url}")
                    if self.update_status_in_db:
                        self.update_status_in_db(self.id, 'log_event', {
                            'activity': f'clicked on {sub_tab_name} sub tab', # TODO: list of activity
                            'page_url': current_url,
                            'message':f"User '{self.username.split('@')[0]}'  clicked on {sub_tab_name} tab and opened url is {current_url}"[:200]   # max length 200  # max length 200
                    })
                else:
                    print(f"{sub_tab_name} tab not found.")
            
            await self.do_some_scroll()

            await self.like_comment_some_random_post(
                random.randint(2, 4),  # Number of scrolls
                random.randint(0, 3)  # Maximum likes per scroll
            )
            
            await random_sleep()

            await self.follow_some_random_user()
                        
        except Exception as ex:
            print(f"Error switching between tabs: {ex}")


    async def switch_between_random_nav_links(self):
        """Function to simulate clicking on Random links (Trending + sublinks, News+ sublinks, Earnings) and scrolling."""

        try:
            
            # choose between random nav bar links
            nav_links = ['Trending', 'News', 'Earnings']
            nav_link = random.choice(nav_links)
            
            
            cond1 = "//ul[starts-with(@class, 'SiteNav_navbar')]"
            cond2 = f"//a[text()='{nav_link}']"
            selected_link = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)
            if not selected_link:
                raise Exception('Nav link {nav_link} not found')

            await selected_link.click()
            print("Clicked on nav link tab.", nav_link)
            await random_sleep()
            current_url = await self.driver.current_url
            print(f"Navigation bar item activity completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': f'open navigation bar link: {nav_link}', # TODO: list of activity
                    'page_url': current_url,
                    'message':f"User '{self.username.split('@')[0]}'  clicked on {nav_link} tab and opened url is {current_url}"[:200]   # max length 200  # max length 200
            })
            
            await asyncio.sleep(20) # wait for page to load

            await self.do_some_scroll(
                scroll_count=random.randint(2, 4)
            )

            await random_sleep()
            await self.driver.execute_script("window.scrollTo(0, 0);")
            print("Scrolled up to top.")
            
            if nav_link == 'Trending':
                await self.click_trending_tab_random_links()
            elif nav_link == 'News':
                await self.click_news_tab_random_links()

        except Exception as e:
          print(f"An error occurred while interacting with the Random nav links: {e}")

    # These are the functions for interacting with the subtabs under the "Trending" link.
    async def click_trending_tab_random_links(self):
        try:
            # choose between random nav bar links
            trending_nav_links = ['Most Active', 'Watchers', 'Top Gainers', 'Top Losers']
            trending_nav_link = random.choice(trending_nav_links)
            print(trending_nav_link)

            cond1 = "//div[contains(@class, 'MarketsNavigation_pills__ym8u3')]"
            cond2 = f"//a[.//div[text()='{trending_nav_link}']]"
            selected_trending_link = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)
            if not selected_trending_link:
                raise Exception('Nav link {nav_link} not found')
            await selected_trending_link.click()
            print("Clicked on nav link tab.", trending_nav_link)
            await random_sleep()
            current_url = await self.driver.current_url
            print(f"Navigation bar sub item activity completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': f'open navigation bar sub link: {trending_nav_link}', # TODO: list of activity
                    'page_url': current_url,
                    'message':f"User '{self.username.split('@')[0]}'  clicked on {trending_nav_link} tab and opened url is {current_url}"[:200]   # max length 200  # max length 200
            })

            await asyncio.sleep(20) # wait for page to load

            await self.do_some_scroll(
                scroll_count=random.randint(2, 4)
            )

            await random_sleep()
            await self.driver.execute_script("window.scrollTo(0, 0);")
            print("Scrolled up to top.")

        except Exception as e:
            print(f"An error occurred while interacting with the Trending tab: {e}")

    # These are the functions for interacting with the subtabs under the "News" link.
    async def click_news_tab_random_links(self):
        try:

            # choose between random nav bar links
            news_nav_links = ['Watchlist', 'Trending', 'Stocks', 'Crypto', 'Press Releases']
            news_nav_link = random.choice(news_nav_links)
            print(news_nav_link)

            cond1 = "//ul[contains(@class, 'react-tabs__tab-list')]"
            cond2 = f"//li[.//div[text()='{news_nav_link}']]"
            selected_news_link = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)
            if not selected_news_link:
                raise Exception('Nav link {nav_link} not found')

            await selected_news_link.click()
            print("Clicked on nav link tab.", news_nav_link)
            await random_sleep()
            current_url = await self.driver.current_url
            print(f"Navigation bar sub item activity completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': f'open navigation bar sub link: {news_nav_link}', # TODO: list of activity
                    'page_url': current_url,
                    'message':f"User '{self.username.split('@')[0]}'  clicked on {news_nav_link} tab and opened url is {current_url}"[:200]   # max length 200  # max length 200
            })

            await asyncio.sleep(20) # wait for page to load

            await self.do_some_scroll(
                scroll_count=random.randint(2, 4)
            )

            await random_sleep()
            await self.driver.execute_script("window.scrollTo(0, 0);")
            print("Scrolled up to top.")

            await self.click_random_stocktwits_news_article()
            await random_sleep()

        except Exception as e:
            print(f"An error occurred while interacting with the News tab: {e}")

    # Function to find the div and click on random Stocktwits news article in News tab; News > watchlist
    async def click_random_stocktwits_news_article(self):
        try:
            cond1 = "//div[contains(@class, 'react-tabs__tab-panel--selected')]"
            cond2 = f"//div[@role='news feed']"
            parent_div = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)
            if not parent_div:
                raise Exception('stocktwits news list not found')

            child_divs = await parent_div.find_elements("xpath", ".//div[starts-with(@class, 'NewsBucket_itemVertical')]")# Find all child div elements inside the parent div that match the specified class
            if not child_divs:
                raise Exception('stocktwits news not found')

            total_divs = len(child_divs) # Count the total number of divs found
            print(f"Total matching divs found: {total_divs}")
            total_links = 0 # Initialize counters for all spans and links
            all_links = [] 
            for div in child_divs:
                cond4 = "//div[starts-with(@class, 'NewsItem_title')]"
                links = await div.find_elements("xpath", f"{cond4}")

                total_links += len(links)  # Increment the total link count
                all_links.extend(links)

            print(f"Total matching links found: {total_links}")

            if len(all_links) > 0: # If any links were found, randomly select one and click it
                random_link = random.choice(all_links)  # Choose a random link from the list
                await random_link.click()  # Click on the selected link
                print("Clicked on a Stocktwits news link.")
                await random_sleep()
                current_url = await self.driver.current_url
                print(f"Open stocktwits news from navigation bar items activity completed on page: {current_url}")
                if self.update_status_in_db:
                    self.update_status_in_db(self.id, 'log_event', {
                        'activity': 'open stocktwits news link', # TODO: list of activity
                        'page_url': current_url,
                        'message':f"User '{self.username.split('@')[0]}'  opened the stocktwsits news articles at the page {current_url}"[:200]   # max length 200  # max length 200
                })
                
                # Switch to the new tab (get the handles of all open tabs)
                all_tabs = await self.driver.window_handles
                print('tabs:', len(all_tabs))        
                
                original_tab = None
                other_tabs = []
                for tab in all_tabs:
                    print(tab.id, tab.url)
                    if 'https://stocktwits.com/news-articles' in tab.url:
                        original_tab = tab
                    else:
                        other_tabs.append(tab)
                
                for tab in other_tabs:
                    print('switch to tab:', tab.url)
                    await self.driver.switch_to.window(tab)
                    await random_sleep()
                    print('closing tab:', tab.url)
                    try:
                        await self.driver.close()
                    except Exception:
                        pass

                # Switch back to the original tab
                await self.driver.switch_to.window(original_tab)
                print("Switched back to the original tab.", original_tab.id)      
            else:
                print("No links found.")
            
        except Exception as e:
            print(f"Error occurred: {e}")


    async def click_notifications(self):
        """randome browse the notifications"""

        try:
            cond1 = "//nav[starts-with(@class, 'SidebarUserMenu_navItems')]"
            cond2 = f"//span[text()='Notifications']"
            notification_item = await self.driver.find_element("xpath", f"{cond1}{cond2}", timeout=10)

            if not notification_item:
                raise Exception('Notifiation nav item not found')

            await notification_item.click()
            print("Clicked on notification nav link")
            current_url = await self.driver.current_url
            print(f"open Notifications activity completed on page: {current_url}")
            if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'notifications', # TODO: list of activity
                    'page_url': current_url,
                    'message':f"User '{self.username.split('@')[0]}'  view all notifications at {current_url}"[:200]   # max length 200  # max length 200
            })

            await asyncio.sleep(30)  # wait for page to load

            # Find the div with the text "No Notifications"
            no_notifications_div = await self.driver.find_elements("xpath", "//div[text()='No Notifications']")

            if no_notifications_div:
                print("No Notifications found. No need to scroll.")

            else:
                print("Notifications found. Scrolling...")
                
                await self.do_some_scroll(
                    scroll_count=random.randint(2, 4)
                )

                await random_sleep()
                await self.driver.execute_script("window.scrollTo(0, 0);")
                print("Scrolled up to top.")
            
        except Exception as e:
            print(f"Error during click_notifications: {e}")

    async def start(self, wait_time=1800):

        while True:        
            await random_sleep(5, 300)  # random start wait
            await self.start_activity()

            wait_time = random.uniform(1800, 7200)
            print(self.username, 'wait', wait_time, 'seconds before starting next activity...  user:')
            await asyncio.sleep(wait_time)

    async def start_activity(self):
        print('starting activity for user', self.username)
        username = self.username

        await self.initialize()
        
        if self.update_status_in_db:
            await self.update_status_in_db(self.id, 'activity_started')

        try:
            await self.driver.get(self.start_page, wait_load=False)
            await asyncio.sleep(10)
            
            login_url = "https://stocktwits.com/signin"
            await self.login(login_url)
                        
            # perform other activity here
            await asyncio.sleep(10)
            
            browsing_events = [
                # 'search_random_ticker_and_scroll',
                'switch_between_latest_popular_and_scroll',
                # 'switch_between_random_nav_links',
                # 'click_notifications'
            ]
            
            for idx in range(random.randint(0, len(browsing_events) - 1)):
                event_name = browsing_events[idx]
                print('========> event_name', event_name)
                # event_name = 'switch_between_random_nav_links'
                func = getattr(self, event_name)
                await func()
            
            await self.search_random_ticker_and_scroll()  # with random like, comment and follow user
            
            await self.switch_between_latest_popular_and_scroll()  # with random like, comment and follow user

            await self.switch_between_random_nav_links()   # interacting with random links at the top right navbar

            await self.click_notifications()   # interacting with notifications

        except Exception as e:
            print(f"Error: start_activity: {username} {e}")
        
        finally:
            print("start_activity: closing driver...", username)
            await self.close()

            # update status in db also in app level
            if self.update_status_in_db:
                await self.update_status_in_db(self.id, 'activity_stopped')
        
    async def initiate_signup_process(self):

        username = self.username

        # await self.driver.get("https://stocktwits.com/", wait_load=True, timeout=120)
        # todo: click on create account button

        await self.driver.get("https://stocktwits.com/signup?next=/", wait_load=False)
        await asyncio.sleep(10)
        print("StockTwits website opened successfully.")
        await random_sleep()

        # Enter the email (username)
        email_field = await self.driver.find_element("xpath", "//input[@name='email']", timeout=60)
        if not email_field:
            raise Exception("Email field not found.")

        await email_field.click()
        await email_field.send_keys(username)
        print(f"StockTwits Username '{username}' entered.")
        await random_sleep()

        # Check if the signup button is enabled after entering the email
        signup_button = await self.driver.find_element("xpath", "//button[@type='submit' and contains(@class, 'Button_primary__PFIP8') and text()='Sign Up']", timeout=60)
        if not signup_button:
            raise Exception("Signup button not found.")

        # Check if the signup button is still disabled
        is_disabled = await self.driver.execute_script("return arguments[0].disabled;", signup_button, timeout=10)
        if is_disabled:
            # todo: handle this case (user already exists)
            # update status on db: marked blocked, etc.
            raise Exception("Signup button is disabled, user already exists.")
        
        # If the signup button is enabled, proceed to click it
        await self.driver.execute_script("arguments[0].click();", signup_button, timeout=10)
        print("Signup button clicked.")
        

        # Wait and check the current URL
        await self.driver.sleep(10)  # Allow time for the redirect
        current_url = await self.driver.current_url  # Use await to get the URL value

        if not current_url:
            raise Exception("Failed to load URL.") 
        
        if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'sign up initialize', # TODO: list of activity
                    'page_url': current_url,
                    'message': f"User '{self.username.split('@')[0]}' has successfully initialize the signed up process!"[:200]  # max length 200
            })

        await self.after_signup_process()

    async def after_signup_process(self):

        fullname = self.fullname
        username = self.username.split('@')[0]
        password = self.password

        if not fullname:
            raise Exception("Missing Full Name.")

        # Find the name field and enter the user's name
        name_field = await self.driver.find_element("xpath", "//input[@name='name']", timeout=60)
        if not name_field:
            raise Exception("Name field not found.")

        await name_field.click()
        await name_field.send_keys(fullname)
        print(f"StockTwits Name '{fullname}' entered.")
        await random_sleep()

        # Find the username field and enter the user's name
        username_field = await self.driver.find_element("xpath", "//input[@name='login']", timeout=60)
        if not username_field:
            raise Exception("Username field not found.")

        await username_field.click()
        await username_field.send_keys(username)
        print(f"Username '{username}' entered.")
        await random_sleep()

        # Find the password field and enter the user's name
        password_field = await self.driver.find_element("xpath", "//input[@name='password']", timeout=60)
        if not password_field:
            raise Exception("Password field not found.")

        await password_field.click()
        await password_field.send_keys(password)
        print(f"Password '{password}' entered.")
        await random_sleep()

        # Click the signup button
        submit_button = await self.driver.find_element("xpath", "//button[@type='submit' and text()='Sign Up']", timeout=60)
        if not submit_button:
            raise Exception("Submit button not found")

        await self.driver.execute_script("arguments[0].click();", submit_button, timeout=10)
        print("Submit button clicked.")
        await random_sleep()
        current_url = await self.driver.current_url  # Use await to get the URL value

        if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'sign up completed', # TODO: list of activity
                    'page_url': current_url,
                    'message': f"User '{self.username.split('@')[0]}' has successfully  signed up and created their StockTwits account!"[:200]  # max length 200
            })

        print("After signup process completed.")
        
        # Wait and check the current URL
        await self.driver.sleep(30)  # Allow time for the redirect
        current_url = await self.driver.current_url  # Use await to get the URL value

        if not current_url:
            raise Exception("Failed to load URL after submitting.")        
        
    async def after_submit_process(self):
        skip_button = await self.driver.find_element("xpath", "//span[contains(@class, 'WhoToFollow_skip__') and text()='Skip']", timeout=60)
        if not skip_button:
            raise Exception("Skip button not found")

        await self.driver.execute_script("arguments[0].click();", skip_button, timeout=10)
        print("Skip button clicked.")
        await random_sleep()

        # Wait and check the current URL
        await self.driver.sleep(30)  # Allow time for the redirect
        current_url = await self.driver.current_url  # Use await to get the URL value
        if not current_url:
            raise Exception("Failed to load URL after submitting.")
        
    async def read_email_and_extract_verify_url(self):

        email = self.username
        password = self.password
        # username = email.split('@')[0]
        domain = email.split('@')[1]

        box = EmailBox(
            host=f"mail.{domain}", port=993,
            username=email, password=password
        )

        inbox = box['INBOX']

        verify_url = None

        # for msg in inbox.search(UNSEEN & SUBJECT("Stocktwits")):
        for msg in inbox.search(SUBJECT("Stocktwits")):

            print(msg.subject)
            print(msg.from_)
            
            html_body = msg.html_body.replace('=\r\n', '').replace('=3D', '=')
                
            soup = BeautifulSoup(html_body, "html.parser")
            a_tags = soup.find_all('a')

            for a_tag in a_tags:
                if a_tag.text == 'Verify Your Email':
                    verify_url = a_tag.get('href').strip('"')
                    print(a_tag.text)
                    print(verify_url)
                    break
            
            if verify_url:
                break
                
        return verify_url

    async def signup(self):

        username = self.username
            
        await self.initialize()
        
        # initiate signup process
        try:
            await self.initiate_signup_process()
            if self.update_status_in_db:
                await self.update_status_in_db(self.id, 'account_created')
            
            await self.after_submit_process()
            
        except Exception as e:
            print(f"Error: signup: {username} {e}")
        
        finally:
            print("signup: closing driver...", username)
            await self.close()

    async def verify(self):

        username = self.username
                
        verify_url = await self.read_email_and_extract_verify_url()
        current_url = await self.driver.current_url  # Use await to get the URL value

        if self.update_status_in_db:
                self.update_status_in_db(self.id, 'log_event', {
                    'activity': 'user verified', # TODO: list of activity
                    'page_url': current_url,
                    'message': f"User '{self.username.split('@')[0]}' has successfully verified his StockTwits account and now able to log in!"[:200]  # max length 200
            })
        if not verify_url:
            print("Failed to find the verify URL.")
            return

        await self.initialize()
        
        try:
            
            await self.login(verify_url)
            # update in db: account status: account_verified after successful login
            if self.update_status_in_db:
                await self.update_status_in_db(self.id, 'account_verified')

            await self.update_profile()

        except Exception as e:
            print(f"Error: verify: {username} {e}")
        
        finally:
            print("verify: closing driver...", username)
            await self.close()

            
async def main(task_id, payload, task):
    print(task_id, 'stocktwits bot initiated!')

    # await random_sleep()

    # profile_id = payload['profile_id']
    # name = payload['name']
    # start_page = payload['start_page']
    # proxy_type = payload['proxy_type']
    # proxy_address = payload['proxy_address']

    # bot = Stocktwits(profile_id, name, start_page, proxy_type, proxy_address)
    # await bot.start()
    