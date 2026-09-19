import os
import time
import requests
import feedparser
import google.generativeai as genai

# Environment Variables se Secrets uthayega
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")

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
    return response.json().get("access_token")

def fetch_global_news():
    """Google News RSS se duniya bhar ki top trending news items uthata hai"""
    rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    # Ek run mein top 10 high-quality articles fetch karega (isay aap adjust bhi kar sakte hain)
    return feed.entries[:10]

def generate_high_quality_article(title):
    """Gemini API se ek professional aur detailed SEO optimized article likhwata hai"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Write a comprehensive, highly engaging, professional, and high-quality news article based on this headline: '{title}'. 
    Ensure the article has:
    1. A catchy introduction paragraph.
    2. Detailed body paragraphs with insightful context using <h2> and <p> tags.
    3. A brief conclusion summary.
    Format the entire output in clean HTML code.
    """
    response = model.generate_content(prompt)
    return response.text

def publish_to_blogger(title, content):
    """Blogger API v3 ke zariye post publish karta hai"""
    access_token = get_access_token()
    if not access_token:
        print("Failed to get Access Token!")
        return False

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": content,
        "labels": ["World News", "Top Stories", "Global Trends"]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Successfully Published: {title}")
        return True
    else:
        print(f"Failed to publish: {response.text}")
        return False

if __name__ == "__main__":
    print("Fetching global top news...")
    entries = fetch_global_news()
    print(f"Found {len(entries)} news items to process.")
    
    for entry in entries:
        title = entry.title
        print(f"Processing: {title}")
        try:
            article_html = generate_high_quality_article(title)
            publish_to_blogger(title, article_html)
            # API limits aur server safety ke liye 3 seconds ka gap
            time.sleep(3)
        except Exception as e:
            print(f"Error processing article: {e}")
