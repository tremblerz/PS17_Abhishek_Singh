# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import FormRequest, TextResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import common
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from time import sleep
from datetime import date, datetime
from scrapy.crawler import CrawlerRunner
import random
import re
from .models import UserFriends, UserSelfData

PAGE_LOAD_DELAY = 5
ELEMENT_TIMEOUT = 120

class FbScraperSpider():

    email = ""
    password = ""
    current_user_id = ""

    def __init__(self, email, password):
        """Initializes web-driver using selenium library.
           Gets the command line arguments which will be User's credentials for Facebook.
        
        Args:
            *args: Contains various options or arguments given.
            **kwargs: Takes user specified arguments in the form of "dictionary"
        """
        self.email = email
        self.password = password
        self.driver = webdriver.Firefox()

    def fill_login_form(self):
        """
        fill_login_form() performs Login by typing the email/phone-number of the user
        and password in their respective fields. Once the credentials are inserted a
        click on the login button is made. There are few assertions made in this function
        such as -
        1. The current webdriver is already on the login page of Facebook.
        2. Email field has id in its one of the tag with id's value as "email"
        3. Password field has id in its one of the tag with id's value as "pass"
        4. Login button has an id associated with value "loginbutton"
        """
        email_field = self.driver.find_element_by_id("email")
        password_field = self.driver.find_element_by_id("pass")
        login_button = self.driver.find_element_by_id("loginbutton")
        # Submits the form and click on Login
        email_field.send_keys(self.email)
        password_field.send_keys(self.password)
        login_button.click()

    def visit_profile(self):
        """Visits the profile of user after he/she logs in successfully
        
        Returns:
            Nothing
        """
        sleep(PAGE_LOAD_DELAY)
        xpath = '//div[@data-click="profile_icon"]'
        profile_button = self.wait_until_loads(xpath, ELEMENT_TIMEOUT)
        profile_button.click()

    def extract_user_data(self, response):
        """
        Returns:
            user_info(Dictionary): Contains Name, Number of Friends, Number of Followers, Joining Date
        
        Args:
            response (String): HTML Enocding of the profile page of User
        """
        user_info = {}
        
        user_id = response.xpath('//div[@class="_1k67 _4q39"]//a[@title="Profile"]/@href').extract_first()
        print(user_id)
        ob = re.match(r'.*\.com/(profile.php/\?id=)?(.*)$', user_id)
        print(ob)
        user_id = ob.group(2)
        self.current_user_id = user_id

        name = response.xpath('//span[@id="fb-timeline-cover-name"]/text()').extract_first()
        
        num_friends = int(response.xpath('//a[@data-tab-key="friends"]/span/text()').extract_first())
        
        num_followers = response.xpath('//div[@class="clearfix"]//a[contains(@href, "followers")]/text()').extract_first()
        num_followers = num_followers.split(' ')
        num_followers = int(num_followers[0])
        
        join_date = response.xpath('//div/div[@class="_50f3"]/text()').extract()
        join_date = join_date[9]
        join_date = join_date.split(' ')
        join_date = join_date[2:]

        user_info['name'] = name
        user_info['num_friends'] = num_friends
        user_info['num_followers'] = num_followers
        user_info['join_date'] = join_date
        user_info['id'] = user_id

        print(user_info)
        return user_info

    def scroll_down(self):        
        """Scrolls down on a webpage offering Infinite scrolling based on logic of difference
        created in height
        
        Returns:
            Nothing. Makes change in the member of current object. self.page_source
        """
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
            self.driver.execute_script("return document.body.scrollHeight")
            response = TextResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
            print(response.xpath('//img[contains(@class, "async_saving")]'))
            if response.xpath('//h3[@class="uiHeaderTitle"][text() [contains(., "More About")]]'):
                break


    def traverse_friend_list(self):
        """Grabs the URL of link pointing to friends' list, goes to the grabbed URL and 
        Traverses over the list of friends and grabs the profile URL of friends visible on
        the list.
        
        Returns:
            friends_list(List): A List containing URLs of all friends of a given user
        """
        response = TextResponse(url=self.driver.current_url , body=self.driver.page_source, encoding='utf-8')
        friends_list_link = response.xpath('//div[@class="fsm fwn fcg"]/a[contains(@href, "friends")]/@href').extract_first()

        print(friends_list_link)

        self.driver.get(friends_list_link)

        self.scroll_down()

        response = TextResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
        friends_list = response.xpath('//div[@class="_6a _6b"]/div[contains(@class,"fsl fwb fcb" )]/a/@href').extract()
        print(friends_list)
        return friends_list

    def gather_friends_data(self, friends_list):
        """Data collection of user's friends by visiting their profile
        
        Returns:
            TYPE: Description
        """
        final_data = []
        print(friends_list)
        deactivated_accounts = 0

        for profile_link in friends_list:
            if profile_link == '#':
                deactivated_accounts += 1
            else:
                username = re.match(r'^.*.com/(profile.php\?id=)?(.*).fref.*', profile_link)
                username = username.group(2)

                if not self.scraped_already(username):
                    data = self.extract_friend_data(profile_link, username)
                    result = self.get_formatted_dictionary(data)
                    result['id'] = username
                    self.fill_database(result)
                    final_data.append(result)

        return final_data

    def scraped_already(self, username):
        available = UserFriends.objects.all().filter(UserName=self.current_user_id, FriendName=username)
        return len(available) > 0

    def extract_friend_data(self, profile_link, username):
        """Visits Friends' profile and collects the appropriate data
        
        Args:
            profile_link (String): profile_url of Friend
        
        Returns:
            result(List): Data about 
        """
        main_window = self.driver.current_window_handle
        self.driver.execute_script("window.open(\"" + profile_link + "\",'_blank');")
        self.driver.switch_to_window(self.driver.window_handles[-1])
        #Go to friends' profile and scrape the data
        self.load_friendship(username)

        xpath = '//div[@class="_42ef"]/div/div[@class="_50f3"]/a[contains(@href, "friendship")]/text()'
        while True:
            try:
                friendship_since = self.wait_until_loads(xpath, ELEMENT_TIMEOUT)
                break
            except:
                pass

        response = TextResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
        result = self.scrape_friendship_data(response=response)
        #Close the tab after scraping friends' data and set the window location to earlier one
        self.driver.close()
        self.driver.switch_to_window(main_window)

        return result

    def load_friendship(self, username):
        """Performs just two basic things
        1. Clicks on the more button of a person's profile.
        2. Clicks on see friendship button
        
        Returns:
            Nothing, changes source of the webpage
        """
        """
        xpath = '//div[contains(@class, "_6a _6b uiPopover")]'
        while True:
            try:
                more_button = self.wait_until_loads(xpath, ELEMENT_TIMEOUT)
                more_button.click()
                break
            except:
                pass


        xpath = '//ul[@class="_54nf"]/li[contains(@data-store, "see_friendship")]'
        while  True:
            try:
                see_friendship_button = self.wait_until_loads(xpath, 1)
                break
            except:
                more_button.click()

        see_friendship_button.click()"""
        self.driver.get('https://www.facebook.com/friendship/' + self.current_user_id + "/" + username + "/")
        sleep(PAGE_LOAD_DELAY)

    def scrape_friendship_data(self, response):
        """
        
        Args:
            response (String): HTML response of page after getting the see friendship page
        
        Returns:
            friendship_data(List): Contains strings having Month and Year of friendship and Mutual friends
        """

        friendship_since = response.xpath('//div[@class="_42ef"]/div/div[@class="_50f3"]/a[contains(@href, "friendship")]/text()')
        print(friendship_since)
        friendship_since = friendship_since.extract()
        friendship_since = friendship_since[0].split(' ')

        if not friendship_since[-1].isdigit():
            friendship_since.append(str(date.today().year))

        friendship_since = friendship_since[-2:]

        mutual_friends = response.xpath('//li[contains(@data-store,"mutual_friends")]/div[@class="clearfix"]/div[@class="_42ef"]/div/div[@class="_50f3"]/text()')
        print(mutual_friends)
        mutual_friends = mutual_friends.extract()
        try:
            mutual_friends = mutual_friends[0].split(' ')
        except Exception as e:
            mutual_friends = ['0']
            #raise e
        mutual_friends = mutual_friends[:1]

        return friendship_since + mutual_friends

    def get_formatted_dictionary(self, data):
        """Returns the data by putting it into a dictionary with appropriate key-value pair
        
        Args:
            data (List): List of Strings containing data about friends
        
        Returns:
            result(Dictionary): Formatted version of data in form of Dictionary
        """
        result = {}

        month = data[0]
        year = data[1]
        obj = datetime.strptime(month + " " + year, "%B %Y")
        result['date'] = obj

        mutual_friends = int(data[2])
        result['mutual_friends'] = mutual_friends

        return result

    def fill_database(self, user_data):
        """Puts the data scraped for all friends in database for analytics and visualization
        at front end
        
        Returns:
            TYPE: Description
        
        Args:
            user_data (Dictionary): A key value pair containing data
        """
        mf = user_data['mutual_friends']
        d = user_data['date']
        fid = user_data['id']
        uid = self.current_user_id
        object_handler = UserFriends(MutualFriends = mf, FriendshipDate = d, FriendName = fid, UserName = uid)
        object_handler.save()

    def wait_until_loads(self, xpath, timeout):
        try:
            webelement = WebDriverWait(self.driver, timeout).until(
                expected_conditions.presence_of_element_located((By.XPATH, xpath))
            )
            return webelement
        except:
            return None