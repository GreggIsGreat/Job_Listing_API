import re
import logging
from typing import Optional, List

from bs4 import BeautifulSoup, Tag

from app.scrapers.base import BaseScraper
from app.models.job import (
    JobListing, JobListingsResponse, PaginationInfo,
    JobCategory, JobLocation, JobType
)

logger = logging.getLogger(__name__)


class JobsBotswanaScraper(BaseScraper):
    
    @property
    def source_id(self) -> str:
        return "jobsbotswana"
    
    @property
    def source_name(self) -> str:
        return "Jobs Botswana"
    
    @property
    def base_url(self) -> str:
        return "https://jobsbotswana.info"
    
    @property
    def description(self) -> str:
        return "Leading job portal for employment opportunities in Botswana"
    
    def _build_listing_url(self, page: int = 1, category: Optional[str] = None,
                          location: Optional[str] = None, job_type: Optional[str] = None) -> str:
        base = self.base_url
        
        if category and not location and not job_type:
            return f"{base}/job-category/{category}/" if page == 1 else f"{base}/job-category/{category}/page/{page}/"
        
        if location and not category and not job_type:
            return f"{base}/job-location/{location}/" if page == 1 else f"{base}/job-location/{location}/page/{page}/"
        
        if job_type and not category and not location:
            return f"{base}/job-type/{job_type}/" if page == 1 else f"{base}/job-type/{job_type}/page/{page}/"
        
        url = f"{base}/jobs/" if page == 1 else f"{base}/jobs/page/{page}/"
        
        params = []
        if category:
            params.append(f"category={category}")
        if location:
            params.append(f"location={location}")
        if job_type:
            params.append(f"type={job_type}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def _parse_job_from_article(self, article: Tag) -> Optional[JobListing]:
        try:
            job_url = article.get('data-url', '')
            
            job_id = None
            classes = article.get('class', [])
            for cls in classes:
                if isinstance(cls, str) and cls.startswith('post-'):
                    match = re.match(r'post-(\d+)', cls)
                    if match:
                        job_id = match.group(1)
                        break
            
            title = None
            title_elem = article.find('h3', class_='loop-item-title')
            if title_elem:
                title_link = title_elem.find('a')
                if title_link:
                    title = title_link.get_text(strip=True)
                    if not job_url:
                        job_url = title_link.get('href', '')
            
            if not title or not job_url:
                return None
            
            company = None
            for sep in [' – ', ' - ', '–', '-']:
                if sep in title:
                    parts = title.split(sep)
                    if len(parts) > 1:
                        company = parts[-1].strip()
                        break
            
            if not company:
                for cls in classes:
                    if isinstance(cls, str) and cls.startswith('job_company-'):
                        slug = cls.replace('job_company-', '').replace('-job-vacancies', '')
                        company = ' '.join(word.capitalize() for word in slug.split('-'))
                        break
            
            job_type = None
            job_type_span = article.find('span', class_='job-type')
            if job_type_span:
                inner_span = job_type_span.find('span')
                if inner_span:
                    job_type = inner_span.get_text(strip=True)
            
            if not job_type:
                for cls in classes:
                    if isinstance(cls, str) and cls.startswith('job_type-'):
                        slug = cls.replace('job_type-', '')
                        job_type = ' '.join(word.capitalize() for word in slug.split('-'))
                        break
            
            location = None
            location_span = article.find('span', class_='job-location')
            if location_span:
                em = location_span.find('em')
                if em:
                    location = em.get_text(strip=True)
                else:
                    link = location_span.find('a')
                    if link:
                        location = link.get_text(strip=True)
            
            if not location:
                for cls in classes:
                    if isinstance(cls, str) and cls.startswith('job_location-'):
                        location = cls.replace('job_location-', '').capitalize()
                        break
            
            closing_date = None
            closing_span = article.find('span', class_='job-date__closing')
            if closing_span:
                closing_date = closing_span.get_text(strip=True)
            
            posted_date = None
            time_elem = article.find('time', class_='entry-date')
            if time_elem:
                posted_date = time_elem.get('datetime')
            
            category = None
            category_span = article.find('span', class_='job-category')
            if category_span:
                cat_links = category_span.find_all('a')
                if cat_links:
                    category = ' - '.join([a.get_text(strip=True) for a in cat_links])
            
            if not category:
                categories_list = []
                for cls in classes:
                    if isinstance(cls, str) and cls.startswith('job_category-'):
                        slug = cls.replace('job_category-', '')
                        categories_list.append(' '.join(word.capitalize() for word in slug.split('-')))
                if categories_list:
                    category = ' - '.join(categories_list)
            
            posted_ago = None
            posted_ago_span = article.find('span', class_='job-date-ago')
            if posted_ago_span:
                posted_ago = posted_ago_span.get_text(strip=True)
            
            is_closed = 'closed-job' in [str(c) for c in classes]
            
            return JobListing(
                id=job_id,
                title=title,
                url=job_url,
                company=company,
                job_type=job_type,
                location=location,
                closing_date=closing_date,
                posted_date=posted_date,
                category=category,
                posted_ago=posted_ago,
                is_closed=is_closed,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing job article: {e}")
            return None
    
    def _parse_pagination(self, soup: BeautifulSoup, current_page: int) -> PaginationInfo:
        total_jobs = 0
        total_pages = 1
        jobs_per_page = 15
        
        count_div = soup.find('div', class_='noo-job-list-count')
        if count_div:
            text = count_div.get_text()
            match = re.search(r'of\s+(\d+)\s+jobs?', text, re.IGNORECASE)
            if match:
                total_jobs = int(match.group(1))
            
            range_match = re.search(r'Showing\s+(\d+)[–\-](\d+)', text)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                jobs_per_page = end - start + 1
        
        pagination = soup.find('div', class_='pagination')
        if pagination:
            for elem in pagination.find_all(['a', 'span'], class_='page-numbers'):
                text = elem.get_text(strip=True)
                if text.isdigit():
                    total_pages = max(total_pages, int(text))
        
        if total_jobs > 0 and jobs_per_page > 0:
            calculated = (total_jobs + jobs_per_page - 1) // jobs_per_page
            total_pages = max(total_pages, calculated)
        
        has_next = current_page < total_pages
        has_previous = current_page > 1
        
        return PaginationInfo(
            current_page=current_page,
            total_pages=total_pages,
            total_jobs=total_jobs,
            jobs_per_page=jobs_per_page,
            has_next=has_next,
            has_previous=has_previous,
            next_page=current_page + 1 if has_next else None,
            previous_page=current_page - 1 if has_previous else None
        )
    
    def scrape_listings(self, page: int = 1, category: Optional[str] = None,
                       location: Optional[str] = None, job_type: Optional[str] = None,
                       keyword: Optional[str] = None) -> JobListingsResponse:
        
        url = self._build_listing_url(page, category, location, job_type)
        logger.info(f"Scraping jobs from: {url}")
        
        filters_applied = {}
        if category:
            filters_applied['category'] = category
        if location:
            filters_applied['location'] = location
        if job_type:
            filters_applied['job_type'] = job_type
        
        try:
            soup = self.fetch_page_sync(url)
            if soup is None:
                raise Exception("Failed to parse page")
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return JobListingsResponse(
                success=False,
                message=f"Failed to fetch page: {str(e)}",
                data=[],
                pagination=PaginationInfo(
                    current_page=page, total_pages=0, total_jobs=0,
                    jobs_per_page=0, has_next=False, has_previous=False
                ),
                filters_applied=filters_applied,
                source=self.source_name
            )
        
        articles = soup.find_all('article', class_='noo_job')
        logger.info(f"Found {len(articles)} job articles")
        
        jobs: List[JobListing] = []
        for article in articles:
            job = self._parse_job_from_article(article)
            if job:
                jobs.append(job)
        
        logger.info(f"Successfully parsed {len(jobs)} jobs")
        pagination = self._parse_pagination(soup, page)
        
        return JobListingsResponse(
            success=True,
            message=f"Successfully fetched {len(jobs)} jobs",
            data=jobs,
            pagination=pagination,
            filters_applied=filters_applied,
            source=self.source_name
        )
    
    def scrape_job_detail(self, job_url: str) -> Optional[JobListing]:
        logger.info(f"Fetching job details from: {job_url}")
        
        try:
            soup = self.fetch_page_sync(job_url)
            if soup is None:
                return None
        except Exception as e:
            logger.error(f"Failed to fetch job detail: {e}")
            return None
        
        try:
            title_elem = soup.find('h1', class_='entry-title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            company = None
            for sep in [' – ', ' - ', '–', '-']:
                if sep in title:
                    parts = title.split(sep)
                    if len(parts) > 1:
                        company = parts[-1].strip()
                        break
            
            description = None
            content = soup.find('div', class_='entry-content')
            if content:
                paragraphs = content.find_all('p')[:5]
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                description = ' '.join(texts)
                if len(description) > 1000:
                    description = description[:1000] + '...'
            
            closing_date = None
            closing_elem = soup.find('span', class_='job-date__closing')
            if closing_elem:
                closing_date = closing_elem.get_text(strip=True)
            
            return JobListing(
                title=title,
                url=job_url,
                company=company,
                description=description,
                closing_date=closing_date,
                source=self.source_name
            )
        except Exception as e:
            logger.error(f"Error parsing job detail: {e}")
            return None
    
    def scrape_categories(self) -> List[JobCategory]:
        try:
            soup = self.fetch_page_sync(f"{self.base_url}/jobs/")
            if soup is None:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch categories: {e}")
            return []
        
        categories = []
        widget = soup.find('div', class_='noo-job-category-widget')
        if widget:
            ul = widget.find('ul', class_='job-categories')
            if ul:
                for li in ul.find_all('li', class_='cat-item'):
                    link = li.find('a')
                    if link:
                        name = link.get_text(strip=True)
                        href = link.get('href', '')
                        slug_match = re.search(r'/job-category/([^/]+)/?', href)
                        slug = slug_match.group(1) if slug_match else name.lower().replace(' ', '-')
                        count = 0
                        count_match = re.search(r'\((\d+)\)', li.get_text())
                        if count_match:
                            count = int(count_match.group(1))
                        categories.append(JobCategory(slug=slug, name=name, count=count, url=href))
        
        return categories
    
    def scrape_locations(self) -> List[JobLocation]:
        try:
            soup = self.fetch_page_sync(f"{self.base_url}/jobs/")
            if soup is None:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch locations: {e}")
            return []
        
        locations = []
        widget = soup.find('div', class_='noo-job-location-widget')
        if widget:
            ul = widget.find('ul')
            if ul:
                for li in ul.find_all('li', class_='cat-item'):
                    link = li.find('a')
                    if link:
                        name = link.get_text(strip=True)
                        href = link.get('href', '')
                        description = link.get('title')
                        slug_match = re.search(r'/job-location/([^/]+)/?', href)
                        slug = slug_match.group(1) if slug_match else name.lower().replace(' ', '-')
                        count = 0
                        count_match = re.search(r'\((\d+)\)', li.get_text())
                        if count_match:
                            count = int(count_match.group(1))
                        locations.append(JobLocation(slug=slug, name=name, count=count, description=description, url=href))
        
        locations.sort(key=lambda x: x.count, reverse=True)
        return locations
    
    def get_job_types(self) -> List[JobType]:
        return [
            JobType(slug="full-time", name="Full Time", count=0),
            JobType(slug="contract", name="Contract", count=0),
            JobType(slug="part-time", name="Part Time", count=0),
        ]


jobs_botswana_scraper = JobsBotswanaScraper()