from django.shortcuts import render
from .crawler import FbScraperSpider
from scrapy.crawler import CrawlerRunner
from django.http import HttpResponse
from .tasks import run_crawler
from celery.result import AsyncResult
import json
from chartit import DataPool, Chart
from .models import UserSelfData, UserFriends
from django.db.models import Count
from chartit import PivotDataPool, PivotChart
from datetime import date

# Create your views here.

def home(request):

    context = {}
    return render(request, 'index.html', context)

def crawl(request):

	if request.is_ajax():
		if 'id' in request.POST.keys() and 'password' in request.POST.keys():
			email = request.POST['id']
			password = request.POST['password']
		else:
			return HttpResponse('Id or Password not present')
	else:
		return HttpResponse('Ajax request not received')

	print("beginning crawler")
	job_id = run_crawler.delay(email, password)
	return HttpResponse(json.dumps({"job_id": job_id.id}), content_type='application/json')
	"""process = CrawlerRunner({
	    #'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})
	process.crawl(FbScraperSpider, email=email, password=password)
	#process.start()
	return HttpResponse('crawling started')"""

def get_progress(request):

	if request.is_ajax():
		if 'job' in request.POST.keys():
			job_id = request.POST['job']
			job = AsyncResult(job_id)
			result = job.result 
			state = job.state
			context = {
				'result': result,
				'state': state,
			}
			return HttpResponse(json.dumps(context), content_type='application/json')
	else:
		return HttpResponse('Ajax request not received')

def mutual_friends_chart_view(request):

	if 'id' in request.POST.keys():
		uname = request.POST['id']
		print(uname)
		friends_data = PivotDataPool(
						series =
						[
							{
							'options': {'source': UserFriends.objects.filter(UserName=uname), 'categories': ['FriendshipDate'],},
							'terms': {
										'num_friends': Count('FriendName'),
									 }
							}
						]
							)

		cht = PivotChart(
				datasource = friends_data,
				series_options =
					[
						{
					 	'options': {'type': 'column', 'stacking': 'False'},
					 	'terms': ['num_friends']
						}
					],
				chart_options =
					[
						{
						'title': {
							'text': 'Number of Mutual friends'
							},
						'xAxis': {
							'title': {
								'text': 'FriendshipDate'
								}
							}
						}
					]
				)
		return render(request, 'chart.html', {'friends_chart': cht})
	else:
		return HttpResponse('id Not found')