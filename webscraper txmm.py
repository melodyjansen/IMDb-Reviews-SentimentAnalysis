from selenium import webdriver 
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup as BS
import time
import pandas as pd

# Selenium setup function to create a new driver for each thread
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    service = Service("C:/Users/mjmel/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
    return webdriver.Chrome(service=service, options=options)

class IMDBScraper:
    def __init__(self):
        self.base_url = 'https://www.imdb.com/chart/toptv/'
        self.tv_shows = []

    def fetch_top_shows(self):
        driver = create_driver()
        driver.get(self.base_url)
        time.sleep(1)
        doc = BS(driver.page_source, 'html.parser')
        show_entries = doc.select('li.ipc-metadata-list-summary-item')
        
        # Set a limit of 125 shows
        start_idx = 5 # if we want to start at show x
        stop_idx = 10 # if we want to stop at show x
        for idx, show in enumerate(show_entries):
        #    if idx < start_idx:
        #        continue
        #    if idx > stop_idx: 
        #        continue
            
            title_tag = show.select_one('h3.ipc-title__text')
            link_tag = show.select_one('a.ipc-title-link-wrapper')
            if title_tag and link_tag:
                title = title_tag.text.strip()
                url = 'https://www.imdb.com' + link_tag['href']
                self.tv_shows.append(TVShow(title, url, idx))
                
        driver.quit()

    def scrape_show_data(self):
        with ThreadPoolExecutor(max_workers=3 ) as executor:
            executor.map(lambda show: show.fetch_show_details(), self.tv_shows)

    def create_dataframe(self):
        print("Working on the dataframe now...")
        data = []
        for show in self.tv_shows:
            for episode in show.episodes:
                for review in episode.user_reviews:
                    data.append({
                        "TV Show": show.title,
                        "Avg Show Rating": show.avg_rating,
                        "Genres": ', '.join(show.genres),
                        "Season": episode.season,
                        "Episode": episode.episode_number,
                        "Nth Episode": episode.nth_episode,
                        "Episode Title": episode.title,
                        "Avg Episode Rating": episode.avg_rating,
                        "Episode Description": episode.description,
                        "User Rating": review.user_rating,
                        "User Review": review.text
                    })
        # Ensure DataFrame is created with appropriate columns even if empty
        return pd.DataFrame(data, columns=[
            "TV Show", "Avg Show Rating", "Genres", "Season", "Episode", "Nth Episode",
            "Episode Title", "Avg Episode Rating", "Episode Description",
            "User Rating", "User Review"
        ])

class TVShow:
    def __init__(self, title, url, index):
        self.title = title
        self.url = url
        self.avg_rating = None
        self.genres = []
        self.episodes = []
        self.episode_count = 0  
        self.index = index

    def fetch_show_details(self):
        driver = create_driver()
        driver.get(self.url)
        time.sleep(1)
        doc = BS(driver.page_source, 'html.parser')
        
        # Get IMDb ID for review URL
        imdb_id = self.url.split('/')[4]
        
        # Get average rating
        rating_tag = doc.select_one('div[data-testid="hero-rating-bar__aggregate-rating__score"]')
        if rating_tag:
            self.avg_rating = rating_tag.text.strip()
        
        # Get genres
        genre_tags = doc.select('div.ipc-chip-list__scroller a.ipc-chip')
        if genre_tags:
            self.genres = [genre_tag.text.strip() for genre_tag in genre_tags]

        print(f"show:{self.title}")
        self.fetch_seasons_and_episodes(driver, imdb_id)
        print(f"{self.index}/250")
        driver.quit()

    def fetch_seasons_and_episodes(self, driver, imdb_id):
        driver.get(self.url)
        time.sleep(1)
        doc = BS(driver.page_source, 'html.parser')
        episode_link_tag = doc.select_one('a[href*="episodes?"]')
        if episode_link_tag:
            episodes_url = 'https://www.imdb.com' + episode_link_tag['href']
            self.fetch_episodes(driver, episodes_url, imdb_id)

    def fetch_episodes(self, driver, episodes_url, imdb_id):
        driver.get(episodes_url)
        time.sleep(1)
        doc = BS(driver.page_source, 'html.parser')
        
        # Process each season link
        season_links = doc.select('a[data-testid="tab-season-entry"]')
        for season_link in season_links:
            season_url = 'https://www.imdb.com' + season_link['href']
            season_number = season_link.text.strip()
            self.fetch_episodes_for_season(driver, season_url, season_number, imdb_id)

    def load_all_episodes(self, driver):
        while True:
            try:
                # Locate the "All" button using XPath and navigate up the DOM tree to find the clickable button element
                all_button = driver.find_element(By.XPATH, "//span[contains(@class, 'ipc-see-more__text')]")
                span_parent_element = all_button.find_element(By.XPATH, "..")
                button_parent_element = span_parent_element.find_element(By.XPATH, "..")

                # Execute JavaScript click on the button's parent element
                driver.execute_script("arguments[0].click();", button_parent_element)
                time.sleep(1)  # Small wait to let content load after each click
                
            except NoSuchElementException:
                break  # Exit the loop if "All" button is no longer found


    def fetch_episodes_for_season(self, driver, season_url, season_number, imdb_id):
        driver.get(season_url)
        time.sleep(1)
        
        #print(f"Fetching episodes for season {season_number}")
        self.load_all_episodes(driver)
        
        doc = BS(driver.page_source, 'html.parser')
        episode_tags = doc.select('article.episode-item-wrapper')
        for episode_tag in episode_tags:
            title_tag = episode_tag.select_one('a.ipc-title-link-wrapper')
            description_tag = episode_tag.select_one('div.ipc-html-content-inner-div')
            rating_container = episode_tag.select_one('div[data-testid="ratingGroup--container"] span[aria-label]')
            avg_rating = rating_container['aria-label'].split(":")[-1].strip() if rating_container else None
            episode_number = title_tag.text.split('E')[-1].strip()
            title = title_tag.text.strip()
            description = description_tag.text.strip() if description_tag else ""
            episode_url = 'https://www.imdb.com' + title_tag['href'] 

            # Increment the cumulative episode count
            self.episode_count += 1
            nth_episode = self.episode_count

            episode = Episode(season_number, episode_number, title, avg_rating, description, episode_url,driver, nth_episode, self.title)
            episode.fetch_user_reviews()
            self.episodes.append(episode)

class Episode:
    def __init__(self, season, episode_number, title, avg_rating, description, url, driver, nth_episode, show):
        self.season = season
        self.episode_number = episode_number
        self.title = title
        self.avg_rating = avg_rating
        self.description = description
        self.url = url
        self.user_reviews = []
        self.driver = driver
        self.nth_episode = nth_episode 
        self.show = show

    def load_all_reviews(self):

        max_clicks = 3
        clicks = 0

        while clicks < max_clicks:
            try:
                # Locate the "All" button using XPath and navigate up the DOM tree to find the clickable button element
                all_button = self.driver.find_element(By.XPATH, "//span[contains(@class, 'ipc-see-more__text')]")
                span_parent_element = all_button.find_element(By.XPATH, "..")
                button_parent_element = span_parent_element.find_element(By.XPATH, "..")
                
                # Execute JavaScript click on the button's parent element
                self.driver.execute_script("arguments[0].click();", button_parent_element)
                time.sleep(1)  # Small wait to let content load after each click
                
            except NoSuchElementException:
                break  # Exit the loop if "All" button is no longer found

    def check_for_spoilers(self):
        while True:
            try:
                # Locate the "All" button using XPath and navigate up the DOM tree to find the clickable button element
                spoiler_button = self.driver.find_element(By.CLASS_NAME, "review-spoiler-button")
                # Execute JavaScript click on the button's parent element
                self.driver.execute_script("arguments[0].click();", spoiler_button)
                time.sleep(1)  # Small wait to let content load after each click
                
            except NoSuchElementException:
                break  # Exit the loop if "All" button is no longer found


    def fetch_user_reviews(self):
        print(f"    Attempting to fetch user reviews for {self.show} (Season {self.season}, Episode {self.episode_number})")
        # Navigate to the episode page
        self.driver.get(self.url)
        time.sleep(1)
        
        # Find the user reviews link on the episode page
        doc = BS(self.driver.page_source, 'html.parser')
        review_link_tag = doc.select_one("div.ipc-title__wrapper:has(h3:contains('User reviews')) a") #["href"]

        # Check for "Be the first to review" 
        if "Be the first to review" in review_link_tag.text:
            # print(f"    No user reviews yet for episode {self.episode_number}.")
            return  # Skip fetching reviews but continue to the next episode

        review_link = review_link_tag["href"]
        full_review_link = f"https://www.imdb.com{review_link}"
        self.driver.get(full_review_link)
        time.sleep(1)

        self.load_all_reviews()
        self.check_for_spoilers()

        # After loading all reviews, retrieve them
        doc = BS(self.driver.page_source, 'html.parser')  
        review_tags = doc.select('article.user-review-item')
        for idx, review_tag in enumerate(review_tags):
            if idx >= 20:  # Stop after processing 100 reviews
                continue
            user_rating_tag = review_tag.select_one('span.ipc-rating-star--rating')
            review_text_tag = review_tag.select_one('div.ipc-html-content-inner-div')
            user_rating = int(user_rating_tag.text) if user_rating_tag else None
            review_text = review_text_tag.text.strip() if review_text_tag else ""
            self.user_reviews.append(UserReview(user_rating, review_text))
        

class UserReview:
    def __init__(self, user_rating, text):
        self.user_rating = user_rating
        self.text = text

# Run the scraper and compile data into a DataFrame
scraper = IMDBScraper()
scraper.fetch_top_shows()
scraper.scrape_show_data()
df = scraper.create_dataframe()

# Print sample of dataframe
print(df.head())


# Save the DataFrame to a CSV file
df.to_csv('show_data.csv', index=False)  # index=False prevents adding a row number column
print("Data saved")