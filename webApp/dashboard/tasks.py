from celery import shared_task,current_task
from .crawler import FbScraperSpider, ELEMENT_TIMEOUT, PAGE_LOAD_DELAY
from time import sleep
from scrapy.http import TextResponse
import random

NUM_FRIENDS = 50

@shared_task
def run_crawler(email, password):
	current_task.update_state(state='PROGRESS', meta={'process_percent': 5})

	crawler_object = FbScraperSpider(email, password)
	
	crawler_object.driver.get("https://facebook.com/login.php")

	crawler_object.fill_login_form()
	current_task.update_state(state='PROGRESS', meta={'process_percent': 10})
	"""
	Navigating through links just after the Login can trigger alert to Facebook for
	a possible bot and hence can trigger human validation mechanisms such as CAPTCHA hence
	time delay of three seconds has been put here
	"""
	sleep(3)

	crawler_object.visit_profile()
	current_task.update_state(state='PROGRESS', meta={'process_percent': 15})

	sleep(PAGE_LOAD_DELAY)

	xpath = '//div[@class="clearfix"]//a[contains(@href, "followers")]/text()'
	crawler_object.wait_until_loads(xpath, ELEMENT_TIMEOUT)
	response = TextResponse(url=crawler_object.driver.current_url, body=crawler_object.driver.page_source, encoding='utf-8')
	user_data = crawler_object.extract_user_data(response=response)
	current_task.update_state(state='PROGRESS', meta={'process_percent': 20, 'udata': user_data})

	profile_urls = crawler_object.traverse_friend_list()
	current_task.update_state(state='PROGRESS', meta={'process_percent': 25, 'udata': user_data})
	
	sample_profile_urls = profile_urls
	random.shuffle(sample_profile_urls)
	current_task.update_state(state='PROGRESS', meta={'process_percent': 30, 'udata': user_data})

	final_data = crawler_object.gather_friends_data(sample_profile_urls[0:NUM_FRIENDS])
	current_task.update_state(state='PROGRESS', meta={'process_percent': 20, 'udata': user_data})

	print(final_data)

	crawler_object.driver.quit()