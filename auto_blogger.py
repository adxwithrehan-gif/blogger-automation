import os
import time
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- ENVIRONMENT VARIABLES ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

def get_blogger_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('blogger', 'v3', credentials=creds)

def fetch_latest_news(category):
    url = f"https://newsapi.org/v2/everything?q={category}&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "ok" and data.get("articles"):
            article = data["articles"][0]
            return article.get("title"), article.get("description"), article.get("url")
    except Exception as e:
        print(f"⚠️️ News API Error: {e}")
    return None, None, None

categories = ["Sports", "Law", "Government"]

service = get_blogger_service()
TOTAL_ARTICLES_TARGET = 10
published_count = 0

print(f"🚀 Starting Secure Auto Blogger: Target is {TOTAL_ARTICLES_TARGET} articles...")

while published_count < TOTAL_ARTICLES_TARGET:
    for category in categories:
        if published_count >= TOTAL_ARTICLES_TARGET:
            break
        
        try:
            title, description, source_url = fetch_latest_news(category)
            
            if not title:
                title = f"Latest Breaking Updates in {category} #{published_count + 1}"
                description = f"Explore the detailed analysis and core updates regarding {category}."

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            image_seed = abs(hash(title + str(published_count))) % 10000
            thumbnail_url = f"https://picsum.photos/seed/{image_seed}/800/450"
            
            featured_image_html = f'''
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
                <img src="{thumbnail_url}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px;" />
            </div>
            '''
            
            full_article_content = f"""
            {featured_image_html}
            <p><b>Published on:</b> {current_time}</p>
            
            <h2>Introduction to Latest {category} Trends</h2>
            <p>{description}</p>
            
            <h2>Key Highlights & In-Depth Analysis</h2>
            <p>The recent developments in the world of {category} have sparked widespread discussions among experts and enthusiasts.</p>
            
            <ul>
                <li><b>Primary Focus:</b> Comprehensive overview of the latest announcements.</li>
                <li><b>Sector Impact:</b> How this development shapes future directions.</li>
                <li><b>Expert Insights:</b> Key takeaways and evaluations on ongoing trends.</li>
            </ul>
            
            <h2>Conclusion & Future Outlook</h2>
            <p>Stay tuned to our platform for continuous coverage and breaking news.</p>
            """
            
            if source_url:
                full_article_content += f'<p><b>Source Reference:</b> <a href="{source_url}" target="_blank" rel="nofollow">Read original coverage here</a></p>'

            post_body = {
                'title': title,
                'content': full_article_content,
                'labels': [category, 'TrendingNews', 'AutoBlog']
            }

            request = service.posts().insert(blogId=BLOG_ID, body=post_body)
            request.execute()
            
            published_count += 1
            print(f"[{published_count}/{TOTAL_ARTICLES_TARGET}] ✅ Published [{category}]: {title}")
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error: {e} - Retrying in 10 seconds...")
            time.sleep(10)

print(f"\n🎉 Mubarak ho! Saare 10 articles successfully publish ho chuke hain!")
