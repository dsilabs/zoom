
import requests

url = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'
response = requests.get(url)
channels = response.json()['channels']
stable_channel = channels['Stable']
downloads = stable_channel['downloads']
chromedriver_downloads = downloads['chromedriver']
linux64_downloads = [d for d in chromedriver_downloads if d['platform'] == 'linux64']
chromedriver_url = linux64_downloads[0]['url']

print(chromedriver_url)
