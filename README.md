#  Fade of Fame: When Do TV Shows Overstay Their Welcome?

This project explores how audience sentiment toward TV shows changes over time, using user reviews from IMDb’s Top 250 TV Shows. The goal is to understand when and why shows start to decline in perceived quality.

## Summary

Using sentiment analysis and topic modeling on IMDb user reviews, this project identifies trends in viewer sentiment across seasons and episodes, revealing patterns such as:

- A general decline in sentiment after season 9.
- Genre-specific sentiment trajectories.
- Shifts in themes and audience engagement over time.

## Project Structure

- `scraper.py`: A Python web scraper built with Selenium to extract user reviews, ratings, genres, and episode information from IMDb.
- `imdb_reviews_analysis.ipynb`: A Jupyter Notebook containing the sentiment analysis, topic modeling, data visualization, and validation.
- `show_data.csv`: Folder containing the dataset (CSV format) used in the analysis.
- `README.md`: Current file.

## Methods

### Data Collection
- Scraped ~76,000 IMDb user reviews from Top 250 TV Shows.
- Limited to 20 reviews per episode to maintain consistency.
- Multithreaded scraping for efficiency.

### Sentiment Analysis
- Used TextBlob to compute polarity scores (-1 to +1).
- Aggregated sentiment at episode, season, and genre levels.
- Applied linear regression to detect trends in sentiment over time.

### Topic Modeling
- Applied TF-IDF and Latent Dirichlet Allocation (LDA) to episode descriptions and user reviews.
- Analyzed shifts in focus and themes before and after sentiment declines.

### Validation
- Manual review of sentiment classifications.
- Correlation analysis between sentiment scores and IMDb user ratings.
- Precision, recall, and F1-score metrics calculated.

## Key Findings

- **Decline in Sentiment**: Most TV shows show a drop in sentiment after their early seasons.
- **Genre Effects**: Genres like 'Boxing' and 'Adventure Epic' maintain high sentiment; genres like 'Dinosaur Adventure' and 'True Crime' show steep declines.
- **Narrative Shifts**: Topic modeling reveals thematic changes that may explain drops in viewer satisfaction.
