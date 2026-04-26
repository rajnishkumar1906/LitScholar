import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def extract_important_words(text, num_words=10):
    """
    Extract most important words from text using frequency and filtering
    """
    if not text:
        return []
    
    # Clean text
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize
    words = word_tokenize(text)
    
    # Remove stopwords and lemmatize
    words = [
        lemmatizer.lemmatize(word) 
        for word in words 
        if word not in stop_words and len(word) > 3
    ]
    
    # Count frequency
    word_freq = Counter(words)
    
    # Get top words
    top_words = [word for word, count in word_freq.most_common(num_words)]
    
    return top_words

def build_mini_context(book, num_keywords=5):
    """
    Build minimal context for LLM using keywords
    """
    # Extract keywords from description
    desc_keywords = extract_important_words(
        book.get('description', ''), 
        num_keywords
    )
    
    # Clean title and author
    title_words = extract_important_words(book.get('title', ''), 3)
    author_words = extract_important_words(book.get('author', ''), 2)
    
    # Combine all
    context_parts = [
        f"Title: {' '.join(title_words)}",
        f"Author: {' '.join(author_words)}",
        f"Genre: {book.get('genres', '')}",
        f"About: {' '.join(desc_keywords)}"
    ]
    
    return ' | '.join(context_parts)