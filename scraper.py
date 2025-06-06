import feedparser
from datetime import datetime

RSS_FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "Associated Press": "http://feeds.ap.org/apnews/topnews",
    "The Guardian": "https://www.theguardian.com/international/rss"
}
def scrape_headlines():
    headlines = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            headlines.append({
                "title": entry.title,
                "source": source,
                "date": datetime(*entry.published_parsed[:6]),
                "link": entry.link
            })
    return headlines
TOPIC_KEYWORDS = {
    "Politics": ["election", "trump", "parliament", "minister"],
    "Tech": ["ai", "tech", "google", "meta", "apple"],
    "Health": ["covid", "hospital", "vaccine", "disease"],
    "Sports": ["football", "olympics", "tournament", "match"]
}

def classify_topic(title):
    title_lower = title.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in title_lower for keyword in keywords):
            return topic
    return "Other"
from textblob import TextBlob

def analyze_sentiment(title):
    analysis = TextBlob(title)
    if analysis.sentiment.polarity > 0.1:
        return "Positive"
    elif analysis.sentiment.polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"