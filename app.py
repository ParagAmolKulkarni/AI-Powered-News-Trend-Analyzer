from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import feedparser
from textblob import TextBlob

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define models
class Headline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    topic = db.Column(db.String(50), nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)

# Topic classification keywords
TOPIC_KEYWORDS = {
    "Politics": [
        "election", "vote", "voting", "trump", "biden", "parliament", "minister", "government", 
        "senate", "congress", "president", "democracy", "republican", "democrat", "cabinet", "campaign"
    ],
    "Technology": [
        "ai", "artificial intelligence", "tech", "startup", "google", "meta", "apple", "microsoft",
        "software", "hardware", "computer", "robot", "gadget", "coding", "programming", "cyber", 
        "cloud", "algorithm", "blockchain", "5g", "machine learning", "deep learning"
    ],
    "Health": [
        "covid", "corona", "hospital", "vaccine", "vaccination", "health", "medical", "doctor", 
        "disease", "virus", "pandemic", "epidemic", "nurse", "mental health", "therapy", "surgery",
        "diabetes", "cancer", "WHO", "nutrition", "fitness", "exercise"
    ],
    "Business": [
        "market", "stock", "economy", "economic", "business", "company", "industry", "startup", 
        "investment", "ipo", "shares", "revenue", "profit", "loss", "merger", "acquisition", 
        "funding", "finance", "inflation", "trade", "commerce"
    ],
    "Entertainment": [
        "movie", "film", "celebrity", "actor", "actress", "director", "music", "album", "tv", 
        "show", "series", "drama", "hollywood", "bollywood", "netflix", "trailer", "release", "oscar", 
        "award", "box office"
    ],
    "Sports": [
        "football", "soccer", "cricket", "sports", "olympics", "game", "match", "tournament", "player", 
        "athlete", "score", "goal", "league", "fifa", "nba", "tennis", "badminton", "medal", "world cup"
    ],
    "Science": [
        "nasa", "space", "astronomy", "mars", "rocket", "quantum", "physics", "chemistry", "biology", 
        "experiment", "scientist", "research", "theory", "dna", "genetics", "planet", "telescope"
    ],
    "Crime": [
        "murder", "crime", "attack", "shooting", "robbery", "police", "arrest", "assault", "theft", 
        "fraud", "investigation", "court", "trial", "criminal", "homicide", "scam", "cybercrime"
    ],
    "Education": [
        "school", "college", "university", "student", "education", "exam", "degree", "course", 
        "online class", "scholarship", "teacher", "learning", "tutor", "syllabus", "academic"
    ],
    "Environment": [
        "climate", "climate change", "global warming", "pollution", "wildlife", "nature", "forest", 
        "deforestation", "greenhouse", "carbon", "sustainability", "recycle", "earth", "solar", 
        "biodiversity", "eco"
    ]
}


# RSS feeds (reliable ones)
RSS_FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/etf-report.xml",
    "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
    "Wired": "https://www.wired.com/feed/rss",
    "Hacker News": "https://hnrss.org/frontpage",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Google News": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "Financial Times": "https://www.ft.com/?format=rss",
    "India Today": "https://www.indiatoday.in/rss/home",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "Business Insider": "https://www.businessinsider.in/rss.cms",
    "LiveMint": "https://www.livemint.com/rss/news",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/1221656.cms"
}


# Helper functions
def classify_topic(title):
    title_lower = title.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in title_lower for keyword in keywords):
            return topic
    return "Other"

def analyze_sentiment(title):
    analysis = TextBlob(title)
    if analysis.sentiment.polarity > 0.1:
        return "Positive"
    elif analysis.sentiment.polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def parse_rss_date(entry):
    """Robust RSS date parser"""
    # Try structured date fields first
    date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
    for field in date_fields:
        if hasattr(entry, field):
            try:
                return datetime(*getattr(entry, field)[:6])
            except (TypeError, ValueError):
                pass
    
    # Try string date fields
    string_fields = ['published', 'updated', 'created']
    date_formats = [
        '%a, %d %b %Y %H:%M:%S %z',  # RFC 822 format
        '%a, %d %b %Y %H:%M:%S %Z',  # With timezone name
        '%Y-%m-%dT%H:%M:%SZ',         # ISO 8601 UTC
        '%Y-%m-%dT%H:%M:%S%z',        # ISO 8601 with offset
        '%Y-%m-%d'                    # Date only
    ]
    
    for field in string_fields:
        if hasattr(entry, field):
            date_str = getattr(entry, field)
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except (ValueError, TypeError):
                    pass
    
    # Fallback to current time
    return datetime.utcnow()

# Scraper function
def scrape_headlines():
    headlines = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:  # Get first 15 entries per feed
            date = parse_rss_date(entry)
            headlines.append({
                "title": entry.title,
                "source": source,
                "date": date,
                "link": entry.link
            })
    return headlines

# CLI command to scrape headlines
@app.cli.command("scrape")
def scrape_command():
    headlines = scrape_headlines()
    for h in headlines:
        # Skip duplicates
        existing = Headline.query.filter_by(title=h["title"]).first()
        if existing:
            continue
            
        new_headline = Headline(
            title=h["title"],
            source=h["source"],
            date=h["date"],
            topic=classify_topic(h["title"]),
            sentiment=analyze_sentiment(h["title"])
        )
        db.session.add(new_headline)
    db.session.commit()
    print(f"Added {len(headlines)} headlines")

# API Endpoints
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/headlines')
def get_headlines():
    headlines = Headline.query.order_by(Headline.date.desc()).limit(30).all()
    return jsonify([{
        "title": h.title,
        "source": h.source,
        "date": h.date.isoformat(),
        "topic": h.topic,
        "sentiment": h.sentiment
    } for h in headlines])

@app.route('/api/stats')
def get_stats():
    # Get last week's data
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Topic counts
    topic_counts = db.session.query(
        Headline.topic,
        db.func.count(Headline.id)
    ).filter(Headline.date >= one_week_ago) \
     .group_by(Headline.topic) \
     .all()
    
    topics_dict = {t[0]: t[1] for t in topic_counts}
    
    # Sentiment counts
    sentiment_counts = db.session.query(
        Headline.sentiment,
        db.func.count(Headline.id)
    ).filter(Headline.date >= one_week_ago) \
     .group_by(Headline.sentiment) \
     .all()
    
    sentiment_dict = {s[0]: s[1] for s in sentiment_counts}
    
    # Get top trending news (most mentioned topics with latest headline)
    trending = []
    for topic, count in topic_counts:
        if topic == "Other":
            continue
            
        # Get latest headline for this topic
        latest = Headline.query.filter_by(topic=topic) \
                       .order_by(Headline.date.desc()) \
                       .first()
        
        if latest:
            trending.append({
                "topic": topic,
                "title": latest.title,
                "source": latest.source,
                "sentiment": latest.sentiment,
                "count": count
            })
    
    # Sort by count and get top 5
    trending_sorted = sorted(trending, key=lambda x: x["count"], reverse=True)[:5]
    
    return jsonify({
        "topics": topics_dict,
        "sentiment": sentiment_dict,
        "top_trending": trending_sorted
    })

if __name__ == "__main__":
    app.run(debug=True)