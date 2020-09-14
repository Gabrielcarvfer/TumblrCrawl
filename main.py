from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import pickle
import re
import requests

EMAIL = 'your_email'
PASSWORD = 'your_password'
media_folder = "media"


class TumblrSelenium:
    def __init__(self, email, password):
        self.email = email
        self.password = password

        self.browser = webdriver.Firefox()
        self.browser.set_window_position(-3000, 0)  # hide window

        # Load login page
        self.browser.get('https://www.tumblr.com/login')

        # Fill email and click button to continue
        email_field = self.browser.find_element_by_id('signup_determine_email')
        email_field.send_keys(self.email + Keys.RETURN)
        self.browser.implicitly_wait(20)

        # Click button to use password
        use_password_button = self.browser.find_elements_by_class_name('forgot_password_link')
        time.sleep(10)
        use_password_button[0].location_once_scrolled_into_view
        use_password_button[0].click()

        # Fill password field and click button to continue
        self.browser.implicitly_wait(10)
        password_field = self.browser.find_element_by_id('signup_password')
        password_field.send_keys(self.password + Keys.RETURN)

        # Look for 2nd-factor authentication field
        self.browser.implicitly_wait(10)
        tfa_response_field = self.browser.find_element_by_id('tfa_response_field')

        # Request command line 2nd-factor authentication
        print("Type 2nd-factor code:")
        code = input()
        tfa_response_field.send_keys(code + Keys.RETURN)

        # Tumblr is logged in

    def __del__(self):
        # Close browser
        self.browser.quit()


def scroll(driver, timeout):
    scroll_pause_time = timeout

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height


def download_image(url, session):
    try:
        response = session.get(url, timeout=20)
        if response.status_code == 200:
            return response.content
        else:
            print('Error:' + str(response.status_code))
            return None
    except requests.exceptions.ConnectionError as error:
        print('Connection error：' + str(error))
        return None


if __name__ == "__main__":
    contents = None

    tumblr = TumblrSelenium(email=EMAIL, password=PASSWORD)
    request_cookies_browser = tumblr.browser.get_cookies()
    requests.adapters.DEFAULT_RETRIES = 5

    if os.path.exists("htmldump"):
        with open("htmldump", "rb") as file:
            contents = pickle.load(file)
    else:
        scroll(tumblr.browser, 10)
        contents = tumblr.browser.page_source
        with open("htmldump", "wb") as file:
            pickle.dump(contents, file)
    del tumblr

    s = requests.Session()
    c = [s.cookies.set(c['name'], c['value']) for c in request_cookies_browser]

    # Try to use session cookies from the browser on requests
    # response = s.get('')

    # Regex to match media files
    media_links_regex = re.compile('.([^\ \">]*.(\.jpg|\.gif|\.gifv|\.mp4|\.png))')
    media_links = media_links_regex.findall(contents)

    # Use set to remove duplicates
    media_links = set([media_link[0].replace('\\u002F', '/') for media_link in media_links])

    # Check if media folder exists
    if not os.path.exists(media_folder):
        os.mkdir(media_folder)

    # Check if image exists
    for media_link in media_links:
        # Some links are missing http
        if media_link[0] != 'h':
            media_link = "http://" + media_link
        filename = media_link.split('/')[-1]
        filepath = media_folder + os.sep + filename
        if not os.path.exists(filepath):
            # Download missing media
            image_contents = download_image(media_link, s)
            if image_contents:
                with open(filepath, "wb") as file:
                    file.write(image_contents)

