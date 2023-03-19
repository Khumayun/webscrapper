import re

from flask import Flask, jsonify

from selenium import webdriver
from bs4 import BeautifulSoup
import notion_client
import os
import requests

app = Flask(__name__)


def create_item(notion, lot_name, address, auction_date, bid_submission_deadline, deposit_amount, lot_number,
				start_price):
	database_parent = {
		"database_id": "b1793240-b93d-4ca2-9917-8f7ce090452f"
	}
	notion.pages.create(
		parent=database_parent,
		properties={
			"lot_name": {
				"title": [
					{
						"text": {
							"content": lot_name
						}
					}
				]
			},
			"address": {
				"rich_text": [
					{
						"text": {
							"content": address,
						},
					},
				]
			},
			"auction_date": {
				"rich_text": [
					{
						"text": {
							"content": auction_date,
						},
					},
				]
			},
			"bid_submission_deadline": {
				"rich_text": [
					{
						"text": {
							"content": bid_submission_deadline,
						},
					},
				]
			},
			"deposit_amount": {
				"rich_text": [
					{
						"text": {
							"content": deposit_amount,
						},
					},
				]
			},
			"lot_number": {
				"rich_text": [
					{
						"text": {
							"content": lot_number,
						},
					},
				]
			},
			"start_price": {
				"rich_text": [
					{
						"text": {
							"content": start_price,
						},
					},
				]
			},
		}
	)


@app.route('/')
def home():  # put application's code here

	# Set up the Chrome driver with Selenium
	options = webdriver.ChromeOptions()
	options.add_argument("--no-sandbox")
	options.add_argument("--headless")
	options.add_argument("--disable-gpu")
	options.add_argument('--disable-dev-shm-usage')
	driver = webdriver.Chrome(options=options)

	# Define the URL of the page to scrape
	url = 'https://e-auksion.uz/lots?group=27&category=103&index=1&lt=0&at=0&order=0'
	# Set initial page number
	page_number = 1

	lots = []
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

				lots.append({
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

	EAUCTION_LOTS = [x['lot_number'] for x in lots]
	EAUCTION_LOTS = set(EAUCTION_LOTS)

	##################################### NOTION adding ###################################################
	notion = notion_client.Client(auth="secret_845Edx3zL7IXRwP5JLeIjUQvyq4porSPgz7HJ7uTw6M")

	# Retrieve all the pages in the database
	results = notion.databases.query(
		**{
			"database_id": "b1793240b93d4ca299178f7ce090452f",
		}
	)
	EXISTING_LOTS = list()
	# Loop through the pages and retrieve their properties
	for page in results["results"]:
		# Get the page ID and retrieve the page object
		page_id = page["id"]
		page_obj = notion.pages.retrieve(page_id)

		# Get the properties of the page object
		#     page_props = page_obj.properties

		# Print the properties of the page object
		try:
			EXISTING_LOTS.append(page_obj['properties']['lot_number']['rich_text'][0]['text']['content'])
		except Exception:
			pass

	# if something is not in notion add
	diff = EAUCTION_LOTS.difference(set(EXISTING_LOTS))
	if diff:
		for lot_number in diff:
			for lot in lots:
				if lot['lot_number'] == lot_number:
					create_item(
						notion, lot['lot_name'], lot['address'], lot['auction_date'],
						lot['bid_submission_deadline'], lot['deposit_amount'],
						lot['lot_number'], lot['start_price']
					)
					the_message = f"""Добавлен новый лот {lot_number}
					Сумма депозита: {lot['deposit_amount']}
					Дата аукциона: {lot['auction_date']}
					Стартовая цена: {lot['start_price']}
					Адрес: {lot['address']}"""
					requests.get(f"https://api.telegram.org/bot6021384441:AAFaN9t0dERFDHsTws_hYdeYbKVOS2xFEBw/sendMessage?chat_id=-1001906972100&text={the_message}")

	return jsonify({"success": "True"})


if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
