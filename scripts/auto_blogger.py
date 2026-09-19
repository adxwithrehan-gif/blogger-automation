import os
import time
import requests
import feedparser
import google.generativeai as genai

# Environment Variables se Secrets uthayega
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")

print("--- Checking Environment Secrets ---")
if not all([GEMINI_API_KEY, BLOG_ID, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    print("ERROR: Essential Blogger or Gemini secrets are missing!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

def get_access_token():
    """OAuth2 refresh token se fresh access token generate karta hai"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data)
    res_json = response.json()
    if "access_token" in res_json:
        print("Successfully generated fresh Blogger Access Token.")
        return res_json.get("access_token")
    else:
        print(f"Failed to refresh access token: {res_json}")
        return None

def fetch_global_news():
    """News API aur RSS Feeds dono se top trending headlines uthata hai"""
    headlines = []
    
    # 1. News API se fetch karein (Agar API Key mojood ho)
    if NEWS_API_KEY:
        try:
            print("Fetching top headlines from News API...")
            news_api_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
            response = requests.get(news_api_url, timeout=15)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                print(f"Found {len(articles)} articles from News API.")
                for art in articles:
                    if art.get("title") and art.get("title") != "[Removed]":
                        headlines.append(art.get("title"))
        except Exception as e:
            print(f"Error fetching from News API: {e}")

    # 2. Backup ke taur par RSS Feeds se bhi fetch karein
    rss_urls = [
        "https://rss.cnn.com/rss/edition_world.rss",
        "http://feeds.bbci.co.uk/news/world/rss.xml"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    
    for url in rss_urls:
        try:
            print(f"Fetching from RSS: {url}")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:5]:
                    if hasattr(entry, 'title'):
                        headlines.append(entry.title)
        except Exception as e:
            print(f"Error fetching RSS {url}: {e}")

    # Agar phir bhi kuch na mile toh fallback topics
    if not headlines:
        print("Using fallback global trending topics.")
        headlines = [
            "Global Markets React to Latest Economic Policy Changes in 2026",
            "Major Breakthrough in Artificial Intelligence Technology Announced Today"
        ]
        
    # Unique headlines rakhein aur top 5 select karein per run
    unique_headlines = list(dict.fromkeys(headlines))
    print(f"Total unique headlines to process: {len(unique_headlines)}")
    return unique_headlines[:5]

def generate_high_quality_article(title):
    """Gemini API se ek professional aur detailed SEO optimized article likhwata hai"""
    try:
        print(f"Generating article via Gemini for: {title}")
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Write a comprehensive, highly engaging, professional, and high-quality SEO-optimized news article based on this headline: '{title}'. 
        Ensure the article has:
        1. A catchy introduction paragraph.
        2. Detailed body paragraphs with insightful context using <h2> and <p> tags.
        3. A brief conclusion summary.
        Format the entire output in clean HTML code. Do not include markdown code block ticks like ```html in the output, just raw HTML.
        """
        response = model.generate_content(prompt)
        article_text = response.text.replace("```html", "").replace("```", "")
        print("Article generated successfully.")
        return article_text
    except Exception as e:
        print(f"Gemini API Error for title '{title}': {e}")
        return None

def publish_to_blogger(title, content):
    """Blogger API v3 ke zariye post publish karta hai"""
    access_token = get_access_token()
    if not access_token:
        print("Publishing skipped because access token is missing.")
        return False

    url = f"[https://www.googleapis.com/blogger/v3/blogs/](https://www.googleapis.com/blogger/v3/blogs/){BLOG_ID}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": content,
        "labels": ["World News", "Top Stories", "Global Trends", "MSN News", "Google News"]
    }

    print(f"Sending post to Blogger: {title}")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Successfully Published on Blogger: {title}")
        return True
    else:
        print(f"Failed to publish '{title}'. Status: {response.status_code}, Response: {response.text}")
        return False

if __name__ == "__main__":
    print("Starting Global News Automation Script with News API...")
    headlines = fetch_global_news()
    
    if not headlines:
        print("No headlines found to process.")
    else:
        for title in headlines:
            print(f"\nProcessing headline: {title}")
            article_html = generate_high_quality_article(title)
            if article_html:
                success = publish_to_blogger(title, article_html)
                if success:
                    print("Waiting 5 seconds before next post...")
                    time.sleep(5)
            else:
                print("Skipping due to generation failure.")
