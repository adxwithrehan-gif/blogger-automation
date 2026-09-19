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

print("=== STARTING DIAGNOSTIC RUN ===")

if not all([GEMINI_API_KEY, BLOG_ID, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    raise Exception("CRITICAL ERROR: One or more GitHub Secrets are missing!")

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
    print("Requesting new Access Token from Google...")
    response = requests.post(url, data=data)
    res_json = response.json()
    
    if "access_token" in res_json:
        print("SUCCESS: Access Token generated successfully!")
        return res_json.get("access_token")
    else:
        raise Exception(f"FAILED to generate Access Token: {res_json}")

def publish_to_blogger(title, content):
    """Blogger API v3 ke zariye post publish karta hai"""
    access_token = get_access_token()

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

    print(f"Publishing to Blogger -> Title: {title}")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"SUCCESSFULLY PUBLISHED: {title}")
        return True
    else:
        raise Exception(f"Blogger API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Test ke liye ek direct guaranteed trending headline
    test_title = "Global Technology Leaders Announce Major AI Breakthrough in 2026"
    
    print(f"Generating test article for: {test_title}")
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Write a professional news article in clean HTML format based on this headline: '{test_title}'."
    response = model.generate_content(prompt)
    article_html = response.text.replace("```html", "").replace("```", "")
    
    # Publish to Blogger
    publish_to_blogger(test_title, article_html)
    print("=== DIAGNOSTIC RUN COMPLETED ===")
