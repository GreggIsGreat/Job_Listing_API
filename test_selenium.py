from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def test_selenium():
    print("Setting up Chrome options...")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    print("Installing ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    
    print("Creating driver...")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "https://jobsbotswana.info/jobs/"
        print(f"Fetching: {url}")
        
        driver.get(url)
        
        # Wait for job articles to load
        print("Waiting for articles to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.noo_job"))
        )
        
        # Get page source
        html = driver.page_source
        print(f"Page loaded, content length: {len(html)}")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find title
        title = soup.find('title')
        print(f"Page title: {title.get_text() if title else 'N/A'}")
        
        # Find articles
        articles = soup.find_all('article', class_='noo_job')
        print(f"\n✅ Found {len(articles)} job articles!")
        
        # Print first 5 jobs
        print("\n--- First 5 Jobs ---")
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
        
        # Find pagination info
        count_div = soup.find('div', class_='noo-job-list-count')
        if count_div:
            print(f"\nPagination: {count_div.get_text(strip=True)}")
            
    finally:
        print("\nClosing driver...")
        driver.quit()
        print("Done!")

if __name__ == "__main__":
    test_selenium()