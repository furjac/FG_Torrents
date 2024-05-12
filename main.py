import requests
import logging
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time
import warnings
import winreg
import zipfile
import socketserver
import random
import string
import http.server
import threading
import requests
from extractor import extract
import webbrowser

import chromedriver_autoinstaller
import pyfiglet
import qbittorrentapi
from colorama import init, Fore, Style
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

init(autoreset=True)

warnings.filterwarnings("ignore")

BLOCKED_FILE = "block-inspect.js"


class Handler(http.server.SimpleHTTPRequestHandler):
    pass


class Movies:
    def __init__(self):
        self.check_version()
        self.clear()
        self.use_proxy = False
        self.proxy_config = None
        chromedriver_autoinstaller.install()
        self.conn_info = dict(
            host="localhost",
            port=8080,
            username="admin",
            password="administrator",
        )
        self.url = "https://thepiratebay.party/"
        self.saerch_box = '//*[@id="inp"]/input'
        self.title_list = "./td[2]/a"
        self.magnet = "a[title='Get this torrent']"
        self.numbers = "//td[@colspan='9']"
        self.next = "[alt='Next']"
        self.title = "//*[@id='searchResult']/tbody/tr"
        self.uploaders = "./td[8]/a"
        logging.getLogger("selenium").setLevel(logging.WARNING)
        self.qbt_client = qbittorrentapi.Client(**self.conn_info)
        self.movie = None
        self.picked = None
        self.link = []
        self.search = None
        self.picture = []
        self.urls = []
        self.uled = []
        self.season = []
        self.ep_link = None
        self.alert = None
        self.port = None
        self.options = webdriver.ChromeOptions()
        self.clear()
        self.logo()
        proxy_choice = input("Do you want to use a proxy? (y/n): ").lower()
        if proxy_choice == 'y':
            self.use_proxy = True
            self.proxy_config = self.read_proxy_config("proxy.txt")
            PROXY_HOST = self.proxy_config["PROXY_HOST"]
            PROXY_PORT = self.proxy_config["PROXY_PORT"]
            PROXY_USER = self.proxy_config["PROXY_USER"]
            PROXY_PASS = self.proxy_config["PROXY_PASS"]

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (
                PROXY_HOST,
                PROXY_PORT,
                PROXY_USER,
                PROXY_PASS,
            )
            pluginfile = "proxy_auth_plugin.zip"

            with zipfile.ZipFile(pluginfile, "w") as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
                self.options.add_extension(pluginfile)
        elif proxy_choice == 'n':
            self.use_proxy = False
            pass
        else:
            print("Invalid input. Defaulting to not using proxy.")

        ua = UserAgent()
        user_agent = ua.random
        self.options.add_argument("--headless=new")
        self.options.add_argument(f"user-agent={user_agent}")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-renderer-backgrounding")
        self.options.add_argument("--disable-background-timer-throttling")
        self.options.add_argument("--disable-backgrounding-occluded-windows")
        self.options.add_argument("--disable-client-side-phishing-detection")
        self.options.add_argument("--disable-crash-reporter")
        self.options.add_argument("--disable-oopr-debug-crash-dump")
        self.options.add_argument("--no-crash-upload")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-low-res-tiling")
        self.options.add_argument("--log-level=3")
        self.options.add_argument("--silent")
        self.options.add_extension("chrome.crx")
        self.options.add_experimental_option(
            "excludeSwitches", ["enable-logging"])
        self.options.add_argument("--log-level=3")
        self.options.add_experimental_option("detach", True)
        self.options.add_experimental_option("useAutomationExtension", False)
        self.options.add_argument(
            "--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=self.options)
        self.movie_name = None
        self.types = []
        self.years = []
        self.video = None
        self.driver.execute_cdp_cmd("Page.enable", {})
        self.driver.execute_cdp_cmd("Network.enable", {})
        blocked_urls = [
            "https://cdn.jsdelivr.net/npm/disable-devtool",
            "https://www.2embed.cc/js/block-inspect.js"
        ]

        self.driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": blocked_urls})
        
    def check_version(self):
        current_version = 'FG Torrents 8.0'
        response = requests.get("https://api.github.com/repos/furjac/FG_Torrents/releases/latest")
        latest_version = response.json()["name"]

        if latest_version != current_version:
            print('You are using an old version.')
            print('The latest version is', latest_version)
            print('Download latest version for extra experience\nThanks')
        else:
            print('You are using the latest version.. ')

    def open_site(self):
        self.clear()
        print(Fore.LIGHTBLUE_EX + "Using server 1" + Fore.LIGHTBLUE_EX)
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//*[@id="{self.search}"]'))
        ).click()

    def read_proxy_config(self, filename):
        self.proxy_config = {}
        with open(filename, "r") as file:
            for line in file:
                if "=" in line:
                    key, value = line.strip().split("=")
                    self.proxy_config[key.strip()] = value.strip().strip("'")
        return self.proxy_config

    @staticmethod
    def clear():
        system_name = platform.system()
        if system_name == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    @staticmethod
    def logo():
        print(
            Fore.GREEN
            + pyfiglet.figlet_format(
                "FG_Torrents", font="ansi_shadow", justify="center", width=100
            )
            + Style.RESET_ALL
        )

    def find_and_list(self):
        self.clear()
        self.logo()
        print(
            Fore.GREEN
            + "Let me cook plz wait this may take some time... 🥵"
            + Fore.GREEN
        )
        search = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.saerch_box))
        )
        search.send_keys(self.movie_name)
        search.send_keys(Keys.ENTER)
        while True:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, self.numbers))
                )
            except:
                break

            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            titles = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, self.title))
            )

            for result in titles:
                try:
                    title_element = result.find_element(
                        By.XPATH, self.title_list)
                    title = title_element.text

                    url = title_element.get_attribute("href")

                    uled_by_element = result.find_element(
                        By.XPATH, self.uploaders)
                    uled_by = uled_by_element.text

                    self.picture.append(title)
                    self.urls.append(url)
                    self.uled.append(uled_by)
                except:
                    ...

            try:
                next_page_link = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, self.next))
                )
            except:
                break

            if next_page_link:
                next_page_link.click()
            else:
                break

        titles_list = self.picture
        urls_list = self.urls
        uled_list = self.uled
        unique_titles, unique_urls, unique_uled = (
            self.remove_duplicates_and_corresponding(
                titles_list, urls_list, uled_list)
        )
        self.picture = unique_titles
        self.urls = unique_urls
        self.uled = unique_uled

    def remove_duplicates_and_corresponding(self, list1, list2, list3):
        seen = set()
        unique_list1 = []
        unique_list2 = []
        unique_list3 = []
        for item1, item2, item3 in zip(list1, list2, list3):
            if item1 not in seen:
                seen.add(item1)
                unique_list1.append(item1)
                unique_list2.append(item2)
                unique_list3.append(item3)
        return unique_list1, unique_list2, unique_list3

    def check_and_arrange_list(self):
        self.clear()
        self.logo()

        if not self.picture:
            print(f"The {self.search} does not exist or not found.")
            print("Please try a different server.")

        for i, movie in enumerate(self.picture):
            uled_by_value = self.uled[i]

            print(
                Fore.CYAN +
                f"\n{i}. {movie} - Uploaded By: {uled_by_value}" + Fore.CYAN
            )

        print(Fore.RED + "\ne - Exit application" + Fore.RED)

    def server2(self):
        ...

    def take_user_input(self):
        user_input = input(
            "Enter the numbers of the torrents you want to download (separated by spaces), or 'e' to exit: ").strip().lower()

        if user_input == "e":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
            subprocess.run("taskkill /f /im chromedriver.exe", shell=True)
            raise SystemExit
        else:
            try:
                selected_numbers = [int(num) for num in user_input.split()]
                selected_links = []

                for r in selected_numbers:
                    if 0 <= r < len(self.urls):
                        selected_links.append(self.urls[r])
                    else:
                        print(f"Invalid input {r}. Skipping.")

                if not selected_links:
                    print("No valid selections. Please enter valid numbers.")
                    return None

                print("\nPlease be patient. Your downloads will begin in a few seconds.")

                for selected_link in selected_links:
                    self.driver.get(selected_link)
                    magnet_link = (
                        WebDriverWait(self.driver, 10)
                        .until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, self.magnet))
                        )
                        .get_attribute("href")
                    )

                    self.link.append(magnet_link)

                self.driver.quit()
                self.download_selected()
            except ValueError:
                print("Invalid input. Please enter valid numbers separated by spaces.")
                return None

    def download_selected(self):
        try:
            self.qbt_client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            ...
        response = self.qbt_client.torrents_add(urls=self.link)

        if response != "Ok.":
            raise Exception("Failed to add torrent.")

        torrents = list(self.qbt_client.torrents_info())
        progress_percentage = torrents[0].progress * 100
        print(
            f"Downloading: [{Fore.GREEN}{' ' * int(progress_percentage)}>{Style.RESET_ALL}{' ' * (100 - int(progress_percentage))}]"
            f"{progress_percentage:.2f}%",
            end="",
            flush=True,
        )

        while True:
            torrents = list(self.qbt_client.torrents_info())
            progress_percentage = torrents[0].progress * 100

            os.system("cls" if os.name == "nt" else "clear")

            print(
                f"Downloading: [{'#' * int(progress_percentage)}>{' ' * (100 - int(progress_percentage))}] {progress_percentage:.2f}%\n",
                end="",
                flush=True,
            )

            if torrents[0].progress >= 1.0:
                break

            time.sleep(1)

        self.qbt_client.torrents.pause(torrents[0].hash)
        self.qbt_client.auth_log_out()

    def exit_application(self, signal, frame):
        print(
            Fore.CYAN
            + "\nExiting application. Thanks for using the software! 😘"
            + Style.RESET_ALL
        )
        try:
            self.qbt_client.auth_log_out()
            os.system("taskkill /f /im chrome.exe")
            os.system("taskkill /f /im chromedriver.exe")
        except:
            ...
        sys.exit()

    def setup_signal_handling(self):
        signal.signal(signal.SIGINT, self.exit_application)

    @staticmethod
    def check_chrome_installed():
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"
            )
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    @staticmethod
    def is_qbittorrent_installed():
        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, "qbittorrent.exe")
            if os.path.isfile(exe_path):
                return True

        known_paths = [
            r"C:\Program Files\qBittorrent\qbittorrent.exe",
            r"C:\Program Files (x86)\qBittorrent\qbittorrent.exe",
        ]
        for path in known_paths:
            if os.path.isfile(path):
                return True

        for root, dirs, files in os.walk("C:\\"):
            if "qbittorrent.exe" in files:
                subprocess.Popen(
                    ["qbittorrent.exe"], shell=True, stdout=subprocess.PIPE
                )
                return True

        return False

    def anime(self):
        self.driver.get("aniwatchtv.to")

    def search_category(self):
        self.clear()
        self.logo()
        print(
            Fore.YELLOW
            + "Please use this responsibly im not be responsible for any illegal thing u do"
        )
        print(Fore.YELLOW + "\n1. Audios 🎵" + Style.RESET_ALL)
        print(Fore.YELLOW + "\n2. Movies/Videos 🎥" + Style.RESET_ALL)
        print(Fore.YELLOW + "\n3. Softwares" + Style.RESET_ALL)
        print(Fore.YELLOW + "\n4. Games 🎮" + Style.RESET_ALL)
        print(Fore.YELLOW + "\n5. Porn 🔞" + Style.RESET_ALL)
        print(Fore.YELLOW + "\n6. Other" + Style.RESET_ALL)
        category = input(
            Fore.YELLOW + "\n\nWhat you wanna download > " + Style.RESET_ALL
        )
        if category == "1":
            self.search = "audio"
        elif category == "2":
            self.search = "video"
        elif category == "3":
            self.search = "apps"
        elif category == "4":
            self.search = "games"
        elif category == "5":
            self.search = "porn"
        elif category == "6":
            self.search = "other"

    def current_page(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "card-body")))
        except Exception:
            print(
                Fore.RED
                + "\nPlease enter the movie name correctly.\n"
                + Style.RESET_ALL
            )
            input('press enter to continue...')
            self.driver.quit()
            sys.exit()
        movie_elements = self.driver.find_elements(By.CLASS_NAME, "card-body")
        url_element = self.driver.find_elements(
            By.XPATH, "//a[@class='card card-movie']")
        for url in url_element:
            url = url.get_attribute("href") if url_element else "N/A"
            self.urls.append(url)

        for movie_element in movie_elements:
            title_element = movie_element.find_element(By.CLASS_NAME, "title")
            title = title_element.get_attribute("title")
            self.picture.append(title)

            year_element = movie_element.find_elements(By.XPATH,
                                                       ".//ul[@class='list-inline list-separator fs-xs text-muted mb-1']/li[@class='list-inline-item'][2]")
            year = year_element[0].text if year_element else "N/A"
            self.years.append(year)

            type_elements = movie_element.find_elements(
                By.CSS_SELECTOR, "li.list-inline-item")
            movie_type = type_elements[0].text.strip(
            ) if type_elements else "N/A"
            self.types.append(movie_type)

    def checked_list(self):
        self.clear()
        self.logo()

        if not self.picture:
            print(f"{self.movie_name} does not exist or not found.")
            print("Please try a different server.")

        for i, movie in enumerate(self.picture):
            type = self.types[i]
            year = self.years[i]

            print(
                Fore.CYAN +
                f"\n{i}. {movie} - is: {type} - released on: {year}" + Fore.CYAN
            )

        print(Fore.RED + "\ne - Exit application" + Fore.RED)

        self.picked = input("\nEnter which one you watch > ")

    def user_input(self):
        self.clear()
        self.logo()
        if self.picked == "e":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
            subprocess.run("taskkill /f /im chromedriver.exe", shell=True)
            raise SystemExit
        else:
            try:
                r = int(self.picked)
                if 0 <= r < len(self.urls):
                    selected_link = self.urls[r]
                    self.driver.get(selected_link)
                    if self.types[r] == 'Movie':
                        print('you selected a Movie')
                        self.extract_video()
                    elif self.types[r] == 'Series':
                        self.series()
                else:
                    print("Invalid input. Please enter a valid number.")
                    return None
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return None

    def series(self):
        self.clear()
        self.logo()
        season_accordion_items = self.driver.find_elements(
            By.CLASS_NAME, "accordion-item")

        for index, item in enumerate(season_accordion_items, start=1):
            season_name = item.find_element(
                By.CLASS_NAME, "accordion-header").text
            self.season.append(season_name)
            print(f"{index} {Fore.YELLOW}{season_name}{Style.RESET_ALL}")

        selected_season_index = int(
            input("Enter the number corresponding to the season you want to explore: "))

        if 1 <= selected_season_index <= len(self.season):
            selected_season_name = self.season[selected_season_index - 1]

            selected_season_header = season_accordion_items[selected_season_index - 1].find_element(
                By.CLASS_NAME, "accordion-header")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "accordion-header")))
            ActionChains(self.driver).move_to_element(
                selected_season_header).click(selected_season_header).perform()
            time.sleep(1)

            selected_season_episodes = season_accordion_items[selected_season_index - 1].find_elements(
                By.CLASS_NAME, "card-episode")
            print(
                f"\nEpisodes for {Fore.GREEN}{selected_season_name}{Style.RESET_ALL}:")
            for index, episode in enumerate(selected_season_episodes, start=1):
                episode_number = episode.find_element(
                    By.CLASS_NAME, "episode").text
                episode_title = episode.find_element(
                    By.CLASS_NAME, "name").text
                print(
                    f"{index} {episode_number} {Fore.CYAN}{episode_title}{Style.RESET_ALL}")

            selected_episode_number = int(
                input("\nEnter the number corresponding to the episode you want to explore: "))

            if 1 <= selected_episode_number <= len(selected_season_episodes):
                self.ep_link = selected_season_episodes[selected_episode_number - 1].find_element(
                    By.CLASS_NAME, "episode").get_attribute("href")
                self.driver.get(self.ep_link)
            else:
                print("Invalid episode number selected.")
        else:
            print("Invalid season number selected.")

    def watch_online(self):
        self.clear()
        self.logo()
        self.driver.get('https://uflix.to/')
        print(Fore.GREEN + 'Using The best server to get the movies' + Fore.GREEN)
        search = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="search"]'))
        )

        search.send_keys(self.movie_name)
        search.send_keys(Keys.ENTER)
        self.current_page()

        pagination_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "ul.pagination.pagination-spaced li.page-item")

        total_pages = len(pagination_elements)

        for page_number in range(2, total_pages + 1):
            current_url = self.driver.current_url
            next_url = f'{current_url}&page={page_number}'

            self.driver.get(next_url)

            self.current_page()

    def execute_module(self, extractor):
        extractor(self.new_url, self.use_proxy)

    def extract_video(self):
        self.clear()
        self.logo()

    def extract_embed_video(self):
        self.clear()
        self.logo()
        ifr = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 've-iframe')))
        self.new_url = ifr.get_attribute('src')
        time.sleep(1)
        thread = threading.Thread(target=self.execute_module, args=(extract,))
        thread.start()
        thread.join()
        self.clear()
        self.logo()
        print(Fore.LIGHTGREEN_EX +
              'Done extracting source plz wait a few seconds \nsorry for delay')
        with open('frames.html', 'r', encoding='utf-8') as file:
            html_content = file.read()

        start_index = html_content.find('https://streamsrcs.2embed.cc/vsrc')

        if start_index != -1:
            end_index = html_content.find("'", start_index)
            if end_index != -1:
                url = html_content[start_index:end_index]
        time.sleep(1)
        self.driver.get(url)
        textarea_element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "embed-content"))
        )
        self.frame = textarea_element.text
        os.remove('frames.html')
        host = threading.Thread(target=self.host)
        host.start()
        self.driver.quit()

    def host(self):
        self.html_filename = os.path.join(
            tempfile.gettempdir(), self.generate_random_string() + ".html")
        css = """
            <style>
                html, body {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            </style>
            """

        with open(self.html_filename, "w+", encoding="utf-8") as html_file:
            html_file.write(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script disable-devtool-auto src='https://cdn.jsdelivr.net/npm/disable-devtool'></script>
            <script block-inspect src='https://www.2embed.cc/js/block-inspect.js'></script>
            <title>{self.movie_name}</title>
            {css}
        </head>
        <body>
            {self.frame}
        </body>
        </html>
        """)
        self.port = 8844
        os.chdir(tempfile.gettempdir())
        httpd = socketserver.TCPServer(("", self.port), Handler)
        httpd.serve_forever()

    def aniwatch(self):
        self.html_filename = os.path.join(
            tempfile.gettempdir(), self.generate_random_string() + ".html")
        movie = self.movie_name.lower()
        movie = movie.replace(' ', '-')
        css = """
            <style>
                html, body {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            </style>
            """
        if self.sub_dub == 's':
            with open(self.html_filename, "w+", encoding="utf-8") as html_file:
                html_file.write(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script disable-devtool-auto src='https://cdn.jsdelivr.net/npm/disable-devtool'></script>
                <script block-inspect src='https://www.2embed.cc/js/block-inspect.js'></script>
                <title>{self.movie_name}</title>
                {css}
            </head>
            <body>
                <iframe src="https://2anime.xyz/embed/{movie}-episode-{self.ep_no}" width="100%" height="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>
            </body>
            </html>
            """)
        elif self.sub_dub == 'd':
            with open(self.html_filename, "w+", encoding="utf-8") as html_file:
                html_file.write(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script disable-devtool-auto src='https://cdn.jsdelivr.net/npm/disable-devtool'></script>
                <script block-inspect src='https://www.2embed.cc/js/block-inspect.js'></script>
                <title>{self.movie_name}</title>
                {css}
            </head>
            <body>
                <iframe src="https://2anime.xyz/embed/{movie}-dub-episode-{self.ep_no}" width="100%" height="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>
                <p>If loading takes too long plz try sub dont use dub</p>
            </body>
            </html>
            """)
        else:
            print('sorry invalid sub dub selection')
            input('Press enter to continue...')
            raise SystemExit
        self.port = 8844
        os.chdir(tempfile.gettempdir())
        httpd = socketserver.TCPServer(("", self.port), Handler)
        thread = threading.Thread(target=self.shorten_video_link(),)
        thread.start()
        httpd.serve_forever()

    def generate_random_string(self, length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def shorten_video_link(self):
        response = requests.get(
            f'http://ouo.io/api/uSRW4WFH?s=http://localhost:{self.port}/{os.path.basename(self.html_filename)}')
        if response.status_code == 200:
            self.shortened_link = response.text
        print(self.shortened_link)
        self.play()

    def play(self):
        webbrowser.open(self.shortened_link)

    def hindi(self):
        self.clear()
        self.logo()
        print('searching all the internet plz wait it may take time')
        self.driver.get(f'https://desicinemas.tv/?s={self.movie_name}')
    
    def get_hindi_list(self):
        ...

    def tamilyogi(self):
        self.clear()
        self.logo()
        print('searching all the tamilrockers database...')
        self.driver.get(f'https://tamilyogi.red/?s={self.movie_name}')

    def get_list(self):
        try:
            posts = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.postcontent a')))

            for post in posts:
                self.picture.append(post.get_attribute('title'))
                self.urls.append(post.get_attribute('href'))
        except:
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all anchor tags within the div with id "post-results"
            movie_links = soup.select('#post-results a')

            for link in movie_links:
                self.picture.append(link.find('h2').text.strip())
                self.urls.append(link['href'])

    def list_tamil(self):
        self.clear()
        self.logo()

        if not self.picture:
            print(f"The {self.movie_name} does not exist or not found.")
            print("Please try a different server.")

        for i, movie in enumerate(self.picture):
            print(
                Fore.CYAN +
                f"\n{i}. {movie}" + Fore.CYAN
            )

        print(Fore.RED + "\ne - Exit application" + Fore.RED)
        self.picked = input('\n\nPlz enter what u want to watch > ')

    def user_selected(self):
        self.clear()
        self.logo()
        if self.picked == "e":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
            subprocess.run("taskkill /f /im chromedriver.exe", shell=True)
            raise SystemExit
        else:
            try:
                r = int(self.picked)
                if 0 <= r < len(self.urls):
                    selected_link = self.urls[r]
                    self.driver.get(selected_link)
                else:
                    print("Invalid input. Please enter a valid number.")
                    return None
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return None

    def extract_html(self):
        self.clear()
        self.logo()
        print('Plz wait this may take some time')
        WebDriverWait(self.driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, 'iframe')))

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@onclick, 'window.top.location.href')]"))
        )

        onclick_attribute = element.get_attribute("onclick")

        href = onclick_attribute.split("'")[1]
        try:
            self.driver.get(href)
            WebDriverWait(self.driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, 'myIframe')))
            time.sleep(30)

            self.src = self.driver.execute_script(
                "return document.documentElement.outerHTML;")
            script_tags = [
                "<script disable-devtool-auto src='https://cdn.jsdelivr.net/npm/disable-devtool'></script>",
                "<script block-inspect src='https://www.2embed.cc/js/block-inspect.js'></script>"
            ]
            self.src = self.inject_scripts(self.src, script_tags)
            host = threading.Thread(target=self.tamil_host)
            host.start()
            self.driver.quit()
        except:
            print('sorry the movie is not available or has been deleted :(')
            input('press enter to continue...')
            self.driver.quit()
            raise SystemExit

    def inject_scripts(self, html_content, script_tags):
        # Find the position to inject the script tags (before </body> tag)
        index = html_content.rfind('</body>')
        if index != -1:
            # Insert the script tags before </body> tag
            for script_tag in script_tags[::-1]:  # Reverse to maintain order
                html_content = html_content[:index] + \
                    script_tag + html_content[index:]
            return html_content
        else:
            # If </body> tag not found, simply append the script tags at the end
            return html_content + ''.join(script_tags)

    def tamil_host(self):
        self.html_filename = os.path.join(
            tempfile.gettempdir(), self.generate_random_string() + ".html")

        with open(self.html_filename, "w+", encoding="utf-8") as html_file:
            html_file.write(self.src)
        self.port = 8844
        os.chdir(tempfile.gettempdir())
        httpd = socketserver.TCPServer(("", self.port), Handler)
        httpd.serve_forever()

    def server_selection_menu(self):
        self.clear()
        self.logo()
        print(Fore.YELLOW + "Torrent download servers:" + Style.RESET_ALL)
        print(
            Fore.YELLOW
            + "1. Server 1(almost anything using torrents)"
            + Style.RESET_ALL
        )
        print(Fore.YELLOW + "2. Anime server(download animes)" + Style.RESET_ALL)

        print(Fore.RED + '\n\nWatch online servers:(movies only)' + Style.RESET_ALL)
        print(Fore.CYAN + '\n3. Watch online(all language movies available no dubs)' + Style.RESET_ALL)
        print(Fore.CYAN + '\n4. Hindi movies (only movies but all dubs are available)' + Style.RESET_ALL)
        print(Fore.CYAN + '\n5. Tamil movies/series (dubbed)' + Style.RESET_ALL)
        print(Fore.CYAN + '\n6. anime (sub-dub)' + Style.RESET_ALL)
        print(Fore.CYAN + "More adding soon" + Style.RESET_ALL)
        server_choice = input(
            Fore.YELLOW + "\nEnter your choice: " + Style.RESET_ALL
        )
        if server_choice == "1":
            self.search_category()
            self.clear()
            self.logo()
            self.movie_name = input(
                Fore.YELLOW
                + f"Enter name of {movie_instance.search} > "
                + Style.RESET_ALL
            )
            self.open_site()
            self.find_and_list()
            self.check_and_arrange_list()
            self.take_user_input()
            self.download_selected()
            print(
                Fore.GREEN
                + "\nDownload complete. Thanks for using my software! 😘"
                + Style.RESET_ALL
            )
            os.system("pause")
        elif server_choice == "2":
            print(Fore.LIGHTGREEN_EX + "Coming soon" + Style.RESET_ALL)
            os.system("taskkill /f /im chrome.exe")
            os.system("taskkill /f /im chromedriver.exe")
            input("Press Enter to continue...")
            self.driver.quit()
            raise SystemExit
        elif server_choice == '3':
            self.clear()
            self.logo()
            self.movie_name = input(
                Fore.YELLOW
                + "Enter name of movie/series > "
                + Style.RESET_ALL
            )
            self.watch_online()
            self.checked_list()
            self.user_input()
            self.extract_embed_video()
            time.sleep(5)
            self.shorten_video_link()
        elif server_choice == '4':
            self.clear()
            self.logo()
            print(Fore.RED + 'Make sure use vpn or enable proxy from the software')
            self.movie_name = input(
                Fore.YELLOW
                + "Enter name of movie > "
                + Style.RESET_ALL
            )
            self.hindi()
            self.get_hindi_list()
            self.list_hindi()
            self.user_selected_hindi()
            self.extract_html_hindi()
            self.shorten_video_link()
        elif server_choice == '5':
            self.clear()
            self.logo()
            self.movie_name = input(
                Fore.YELLOW
                + "Enter name of movie/series > "
                + Style.RESET_ALL
            )
            self.tamilyogi()
            self.get_list()
            self.list_tamil()
            self.user_selected()
            self.extract_html()
            self.shorten_video_link()
        elif server_choice == '6':
            self.clear()
            self.logo()
            self.driver.quit()
            self.sub_dub = input(
                Fore.YELLOW
                + "how you want to watch Sub or dub (s/d)> "
                + Style.RESET_ALL
            )
            self.movie_name = input(
                Fore.YELLOW
                + "Enter name of the anime (plz dont make spelling mistake) > "
                + Style.RESET_ALL
            )
            self.ep_no = input(
                Fore.YELLOW
                + "Episode number > "
                + Style.RESET_ALL
            )
            self.aniwatch()
        else:
            print(
                Fore.RED + "Invalid choice. Please enter 1, 2, 3, 4, 5" + Style.RESET_ALL)


if __name__ == "__main__":
    if platform.system() == "Windows":
        if not Movies.check_chrome_installed():
            print("Please install Chrome to run the code.")
            input("Press Enter to continue")
            sys.exit()
        if not Movies.is_qbittorrent_installed():
            print("Please install qBittorrent to run the code.")
            input("Press Enter to continue")
            sys.exit()
    else:
        print('make sure u have installed chrome and qbittorrent plz')
    movie_instance = Movies()
    movie_instance.setup_signal_handling()
    movie_instance.server_selection_menu()
