from lxml import etree
import requests
from urllib.parse import quote
import re
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import time
import pyperclip

BASE_URL = "https://movies7.to"
SITEMAP_URL = BASE_URL + "/sitemap.xml"
SEARCH_URL = BASE_URL + "/search?keyword="
MAX_LISTING = 5
START_VALUE = DEFAULT_CHOICE = 1
MAX_WAIT_TIME = 10
M3U8_POLLING_FREQ = 1
DRIVER_SCOPES = ['.*\.m3u8']
PLAYBUTTON_ID = "play"
ELEMENT_PRESENCE = By.CLASS_NAME, "bl-servers"


def sitemap(search):
	keywords = search.split()
	content = etree.fromstring(requests.get(SITEMAP_URL).content)
	sitemap = list(map(lambda x: x.getchildren()[0].text, content))
	movies = [x for x in sitemap if "/movie/" in x]
	print(f"{len(movies)} movies in sitemap.")
	return [movie for movie in movies if all(x in movie for x in keywords)]


def builtin(search):
	results = requests.get(SEARCH_URL + quote(search)).content
	raw_matches = list(dict.fromkeys(re.findall(r"\"/movie/.*?\"", results.decode("utf-8"))))[:MAX_LISTING]
	matches = list(map(lambda x: BASE_URL + x[1:-1], raw_matches))
	pretty_matches = list(map(lambda x: re.findall(r"Watch.*? \(\d{4}\)", requests.get(x).content.decode("utf-8"))[0][len("Watch "):], matches))
	print(pretty_matches)
	return pretty_matches, matches


def main(search):
	pretty_matches, matches = builtin(search)
	for i, movie in reversed(list(enumerate(pretty_matches))):
		option = i + START_VALUE
		print(f"{option}: {movie}")
	choice = int(input(f"Which movie? ({START_VALUE}-{MAX_LISTING}) [{DEFAULT_CHOICE}]>") or DEFAULT_CHOICE)
	link = matches[choice - START_VALUE]
	name = pretty_matches[choice - START_VALUE]
	driver = webdriver.Firefox()
	driver.scopes = DRIVER_SCOPES
	driver.get(link)
	try:
		WebDriverWait(driver, MAX_WAIT_TIME).until(ec.presence_of_element_located(ELEMENT_PRESENCE))
		playbutton = driver.find_element_by_id(PLAYBUTTON_ID)
		playbutton.click()
		m3u8 = None
		while not m3u8:
			time.sleep(M3U8_POLLING_FREQ)
			for request in driver.requests:
				if request.response:
					m3u8 = request.url
					ref = request.headers['Referer']
					ydl = f"youtube-dl -f best {m3u8} --add-header 'Referer: {ref}' -o '{name}.%(ext)s'"
	finally:
		driver.close()
	print(ydl)
	pyperclip.copy(ydl)
	print("Download command copied!")


if __name__ == '__main__':
	search = input("Search for a movie >")
	main(search)
