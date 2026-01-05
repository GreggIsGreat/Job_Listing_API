import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_scrape():
    """Test the scraping logic directly"""
    url = "https://jobsbotswana.info/jobs/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        print(f"Fetching: {url}")
        response = await client.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)} characters")
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Check page title
        title = soup.find('title')
        print(f"Page title: {title.get_text() if title else 'Not found'}")
        
        # Find job articles
        articles = soup.find_all('article', class_='noo_job')
        print(f"\nFound {len(articles)} articles with class 'noo_job'")
        
        # Also try other selectors
        loadmore = soup.find_all('article', class_='loadmore-item')
        print(f"Found {len(loadmore)} articles with class 'loadmore-item'")
        
        all_articles = soup.find_all('article')
        print(f"Found {len(all_articles)} total articles")
        
        # Print first few jobs
        print("\n--- Jobs Found ---")
        for i, article in enumerate(articles[:5]):
            data_url = article.get('data-url', 'N/A')
            title_elem = article.find('h3', class_='loop-item-title')
            title = 'N/A'
            if title_elem:
                link = title_elem.find('a')
                if link:
                    title = link.get_text(strip=True)
            print(f"{i+1}. {title}")
            print(f"   URL: {data_url}")
        
        # Check pagination info
        count_div = soup.find('div', class_='noo-job-list-count')
        if count_div:
            print(f"\nPagination: {count_div.get_text(strip=True)}")
        
        return len(articles)

if __name__ == "__main__":
    count = asyncio.run(test_scrape())
    print(f"\n✅ Total jobs found: {count}")