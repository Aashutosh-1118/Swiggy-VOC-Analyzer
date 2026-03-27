from google_play_scraper import Sort, reviews
import pandas as pd

def scrape_swiggy_reviews(count=1000):
    print(f"🚀 Fetching the latest {count} reviews for Swiggy...")
    app_id = 'in.swiggy.android'

    result, _ = reviews(
        app_id,
        lang='en',
        country='in',
        sort=Sort.NEWEST,
        count=count,
        filter_score_with=1 # Focusing on 1-star reviews for root cause analysis
    )

    df = pd.DataFrame(result)
    # Keeping userName and content for the dashboard
    df = df[['reviewId', 'userName', 'content', 'score', 'at']]

    filename = "swiggy_negative_reviews.csv"
    df.to_csv(filename, index=False)

    print(f"✅ Success! Saved {len(df)} reviews to {filename}")

if __name__ == "__main__":
    scrape_swiggy_reviews(1000)