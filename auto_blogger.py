import os
import pickle
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.generativeai as genai

# --- CONFIGURATIONS (Fetched from GitHub Secrets securely) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOG_ID = os.environ.get("BLOG_ID")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Blogger API Scope
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_blogger_service():
    """
    GitHub Actions ke liye token handling environment variables ya pickled credentials se.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # GitHub Actions ke liye JSON credentials env se load kiye ja sakte hain
            token_json = os.environ.get("TOKEN_PICKLE_BASE64")
            if token_json:
                import base64
                with open('token.pickle', 'wb') as token:
                    token.write(base64.b64decode(token_json))
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
    
    return build('blogger', 'v3', credentials=creds)

# Categories focused on daily trending news / hot topics
categories = ["World News", "Technology Trends", "Crypto Updates", "Viral Stories"]

service = get_blogger_service()

TOTAL_ARTICLES_TARGET = 10
published_count = 0

print(f"🚀 Starting Automated Daily Trending News Posting: Target is {TOTAL_ARTICLES_TARGET} articles...")

while published_count < TOTAL_ARTICLES_TARGET:
    for category in categories:
        if published_count >= TOTAL_ARTICLES_TARGET:
            break
        
        success = False
        while not success:
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                prompt = f"""
                Timestamp: {current_time} (Post Number {published_count + 1})
                Write a fresh, highly engaging, SEO-optimized trending news blog post based on recent happenings in the category: '{category}'. 
                Make sure the content is unique, structured, and informative.
                Return the response strictly in this exact format:
                TITLE: [Catchy and Viral News Blog Post Title]
                CONTENT: [Detailed HTML formatted blog post content with h2 headings, paragraphs, and bullet points]
                """
                
                response = model.generate_content(prompt)
                text = response.text
                
                # Parse Title and Content
                if "TITLE:" in text and "CONTENT:" in text:
                    parts = text.split("CONTENT:")
                    title = parts[0].replace("TITLE:", "").strip()
                    content = parts[1].strip()
                else:
                    title = f"Latest {category} Update #{published_count + 1}"
                    content = text

                # Automatic Thumbnail Generation
                image_seed = abs(hash(title + str(published_count))) % 10000
                thumbnail_url = f"https://picsum.photos/seed/{image_seed}/800/450"
                
                featured_image_html = f'''
                <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
                    <img src="{thumbnail_url}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                </div>
                '''
                
                final_content = featured_image_html + content

                # Prepare Post Data for Blogger
                post_body = {
                    'title': title,
                    'content': final_content,
                    'labels': [category, 'TrendingNews', 'AutoBlog']
                }

                # Publish Directly to Blogger
                request = service.posts().insert(blogId=BLOG_ID, body=post_body)
                request.execute()
                
                published_count += 1
                print(f"[{published_count}/{TOTAL_ARTICLES_TARGET}] ✅ Published [{category}]: {title}")
                
                # 1 se 2 minute ka gap (120 seconds) har post ke darmiyan
                print("⏳ Waiting for 90 seconds before the next post...")
                time.sleep(90)
                success = True
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"⚠️ Quota limit hit (429). Waiting for 60 seconds...")
                    time.sleep(60)
                else:
                    print(f"❌ Error: {e} - Retrying in 15 seconds...")
                    time.sleep(15)

print(f"\n🎉 Mubarak ho! Aaj ke saare {TOTAL_ARTICLES_TARGET} trending articles successfully publish ho chuke hain!")
