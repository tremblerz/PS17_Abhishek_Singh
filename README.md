# Facebook User Focused Analytics
## This project is a part of screening task. Its functional requirement is to build a Facebook scraper and perform visual analytics on the data.

### Backbone of this Project
This project has two major parts -
First is the main facebook crawler which visits accross the friends' profile and scrapes the friendship data such as mutual friends and friendship since.
The other one is the web application which runs this script as a shared task with Celery which is having rabbit-mq broker for AMQP. To render the data on web in realtime, chartit template of Django is used.

### Running this project
There are some software requirements to be considered in order to run this program.
1. django >= 1.9
2. rabbit-mq server
3. Mozilla Firefox with its geckodriver
4. Celery
5. Some python modules as listed -
	a) Scrapy
	b) Celery
	c) selenium
	d) re
	e) random
	f) chartit