import re

from flask import Flask, jsonify

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

app = Flask(__name__)


@app.route('/')
def home():  # put application's code here

	# Set up the Chrome driver with Selenium
	options = Options()
	options.headless = True
	driver_path = './chromedriver'
	driver = webdriver.Chrome(driver_path, options=options)

	# Define the URL of the page to scrape
	url = 'https://e-auksion.uz/lots?group=27&category=103&index=1&lt=0&at=0&order=0'
	# Set initial page number
	page_number = 1

	data = []
	while True:
		url_with_page = f'{url}&page={page_number}'
		# Load the page with Selenium
		driver.get(url_with_page)
		# Get the page source after the JavaScript has loaded
		html_content = driver.page_source
		# Parse the HTML content using BeautifulSoup
		soup = BeautifulSoup(html_content, 'html.parser')
		advertisements = soup.find_all("div", {"class": "col-md-12"})

		if not advertisements:
			break

		for advertisement in advertisements:
			try:
				lot_number = advertisement.find("span", {"class": "ea-lot-number"}).text.strip()
				lot_name = advertisement.find("p", {"class": "lot-name"}).text.strip()
				start_price = advertisement.find_all("p", {"class": "lot-value text-line-1"})[0].text.strip()
				start_price = re.sub(r"[^\d\.]+", "", start_price)
				deposit_amount = advertisement.find_all("p", {"class": "lot-value text-line-1"})[1].text.strip()
				deposit_amount = re.sub(r"[^\d\.]+", "", deposit_amount)
				auction_date = advertisement.find_all("p", {"class": "lot-value text-line-1"})[2].text.strip()
				bid_submission_deadline = advertisement.find_all("p", {"class": "lot-value text-line-1"})[
					3].text.strip()
				address = advertisement.find("p", {"class": "lot-value text-line-2"}).text.strip()

				data.append({
					"lot_number": lot_number,
					"lot_name": lot_name,
					"start_price": str("{:,.2f}".format(float(start_price))),
					"deposit_amount": str("{:,.2f}".format(float(deposit_amount))),
					"auction_date": auction_date,
					"bid_submission_deadline": bid_submission_deadline,
					"address": address
				})
			except Exception:
				pass
		page_number += 1

	driver.quit()
	return jsonify(data)


if __name__ == '__main__':
	app.run()
