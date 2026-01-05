import re
import logging
from typing import Optional, List, Tuple
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from app.scrapers.base import BaseScraper
from app.models.job import (
    JobListing, JobListingsResponse, PaginationInfo,
    JobCategory, JobLocation, JobType
)

logger = logging.getLogger(__name__)


class JobsBotswanaScraper(BaseScraper):
    """
    Scraper for jobsbotswana.info
    """
    
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
    
    def _build_listing_url(
        self, 
        page: int = 1, 
        category: Optional[str] = None, 
        location: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> str:
        """Build the URL for job listings based on filters."""
        base = self.base_url
        
        # Build base URL based on filters
        if category and not location and not job_type:
            # Single category filter
            if page == 1:
                url = f"{base}/job-category/{category}/"
            else:
                url = f"{base}/job-category/{category}/page/{page}/"
        elif location and not category and not job_type:
            # Single location filter
            if page == 1:
                url = f"{base}/job-location/{location}/"
            else:
                url = f"{base}/job-location/{location}/page/{page}/"
        elif job_type and not category and not location:
            # Single job type filter
            if page == 1:
                url = f"{base}/job-type/{job_type}/"
            else:
                url = f"{base}/job-type/{job_type}/page/{page}/"
        else:
            # No filters or multiple filters - use main jobs page
            if page == 1:
                url = f"{base}/jobs/"
            else:
                url = f"{base}/jobs/page/{page}/"
            
            # Add query parameters for multiple filters
            params = []
            if category:
                params.append(f"category={category}")
            if location:
                params.append(f"location={location}")
            if job_type:
                params.append(f"type={job_type}")
            if params:
                url += "?" + "&".join(params)
        
        logger.info(f"Built URL: {url}")
        return url
    
    def _extract_job_id(self, article: Tag) -> Optional[str]:
        """Extract job ID from article classes"""
        classes = article.get('class', [])
        for cls in classes:
            match = re.match(r'post-(\d+)', str(cls))
            if match:
                return match.group(1)
        return None
    
    def _extract_company(self, article: Tag) -> Optional[str]:
        """Extract company name from article classes or title"""
        # Try from classes first
        classes = article.get('class', [])
        for cls in classes:
            cls_str = str(cls)
            if cls_str.startswith('job_company-'):
                company_slug = cls_str.replace('job_company-', '').replace('-job-vacancies', '')
                return ' '.join(word.capitalize() for word in company_slug.split('-'))
        
        # Try from title
        title_elem = article.find('h3', class_='loop-item-title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            for separator in [' – ', ' - ', ' — ', '–', '-']:
                if separator in title_text:
                    parts = title_text.split(separator)
                    if len(parts) > 1:
                        return parts[-1].strip()
        
        return None
    
    def _extract_title(self, article: Tag) -> Optional[str]:
        """Extract job title"""
        # Try h3 with class
        title_elem = article.find('h3', class_='loop-item-title')
        if title_elem:
            link = title_elem.find('a')
            if link:
                return link.get_text(strip=True)
            return title_elem.get_text(strip=True)
        
        # Try any h3
        title_elem = article.find('h3')
        if title_elem:
            link = title_elem.find('a')
            if link:
                return link.get_text(strip=True)
            return title_elem.get_text(strip=True)
        
        # Try data-title attribute
        data_title = article.get('data-title')
        if data_title:
            return data_title
        
        return None
    
    def _extract_url(self, article: Tag) -> Optional[str]:
        """Extract job URL"""
        # Try data-url attribute first (most reliable)
        url = article.get('data-url')
        if url:
            return url
        
        # Try title link
        title_elem = article.find('h3', class_='loop-item-title')
        if title_elem:
            link = title_elem.find('a')
            if link and link.get('href'):
                return link.get('href')
        
        # Try any h3 link
        title_elem = article.find('h3')
        if title_elem:
            link = title_elem.find('a')
            if link and link.get('href'):
                return link.get('href')
        
        # Try job-details-link
        details_link = article.find('a', class_='job-details-link')
        if details_link and details_link.get('href'):
            return details_link.get('href')
        
        # Try View more button
        view_more = article.find('a', class_='btn-primary')
        if view_more and view_more.get('href'):
            return view_more.get('href')
        
        return None
    
    def _extract_job_type(self, article: Tag) -> Optional[str]:
        """Extract job type (Full Time, Contract, etc.)"""
        # Try span with job-type class
        job_type_elem = article.find('span', class_='job-type')
        if job_type_elem:
            # Look for nested span
            span = job_type_elem.find('span')
            if span:
                return span.get_text(strip=True)
            # Look for link with span
            link = job_type_elem.find('a')
            if link:
                span = link.find('span')
                if span:
                    return span.get_text(strip=True)
                return link.get_text(strip=True)
            return job_type_elem.get_text(strip=True)
        
        # Try from article classes
        classes = article.get('class', [])
        for cls in classes:
            cls_str = str(cls)
            if cls_str.startswith('job_type-'):
                type_slug = cls_str.replace('job_type-', '')
                return ' '.join(word.capitalize() for word in type_slug.split('-'))
        
        return None
    
    def _extract_location(self, article: Tag) -> Optional[str]:
        """Extract job location"""
        # Try span with job-location class
        location_elem = article.find('span', class_='job-location')
        if location_elem:
            # Look for em tag
            em = location_elem.find('em')
            if em:
                return em.get_text(strip=True)
            # Look for link
            link = location_elem.find('a')
            if link:
                em = link.find('em')
                if em:
                    return em.get_text(strip=True)
                return link.get_text(strip=True)
            return location_elem.get_text(strip=True)
        
        # Try from article classes
        classes = article.get('class', [])
        for cls in classes:
            cls_str = str(cls)
            if cls_str.startswith('job_location-'):
                location_slug = cls_str.replace('job_location-', '')
                return location_slug.capitalize()
        
        return None
    
    def _extract_closing_date(self, article: Tag) -> Optional[str]:
        """Extract application closing date"""
        # Try job-date__closing span
        date_elem = article.find('span', class_='job-date__closing')
        if date_elem:
            return date_elem.get_text(strip=True)
        
        # Try job-date span
        date_span = article.find('span', class_='job-date')
        if date_span:
            closing = date_span.find('span', class_='job-date__closing')
            if closing:
                return closing.get_text(strip=True)
        
        return None
    
    def _extract_posted_date(self, article: Tag) -> Optional[str]:
        """Extract the datetime when job was posted"""
        time_elem = article.find('time', class_='entry-date')
        if time_elem:
            return time_elem.get('datetime')
        
        time_elem = article.find('time')
        if time_elem:
            return time_elem.get('datetime')
        
        return None
    
    def _extract_category(self, article: Tag) -> Optional[str]:
        """Extract job category"""
        # Try span with job-category class
        category_elem = article.find('span', class_='job-category')
        if category_elem:
            links = category_elem.find_all('a')
            if links:
                categories = [link.get_text(strip=True) for link in links]
                return ' - '.join(categories)
            return category_elem.get_text(strip=True)
        
        # Try from article classes
        classes = article.get('class', [])
        categories = []
        for cls in classes:
            cls_str = str(cls)
            if cls_str.startswith('job_category-'):
                category_slug = cls_str.replace('job_category-', '')
                categories.append(' '.join(word.capitalize() for word in category_slug.split('-')))
        
        if categories:
            return ' - '.join(categories)
        
        return None
    
    def _extract_posted_ago(self, article: Tag) -> Optional[str]:
        """Extract human-readable time since posting"""
        posted_elem = article.find('span', class_='job-date-ago')
        if posted_elem:
            return posted_elem.get_text(strip=True)
        return None
    
    def _is_job_closed(self, article: Tag) -> bool:
        """Check if job posting is closed"""
        classes = article.get('class', [])
        return 'closed-job' in [str(c) for c in classes]
    
    def _parse_job_article(self, article: Tag) -> Optional[JobListing]:
        """Parse a single job article element"""
        try:
            title = self._extract_title(article)
            url = self._extract_url(article)
            
            if not title:
                logger.debug(f"Skipping article: no title found")
                return None
            
            if not url:
                logger.debug(f"Skipping article '{title}': no URL found")
                return None
            
            job = JobListing(
                id=self._extract_job_id(article),
                title=title,
                url=url,
                company=self._extract_company(article),
                job_type=self._extract_job_type(article),
                location=self._extract_location(article),
                closing_date=self._extract_closing_date(article),
                posted_date=self._extract_posted_date(article),
                category=self._extract_category(article),
                posted_ago=self._extract_posted_ago(article),
                is_closed=self._is_job_closed(article),
                source=self.source_name
            )
            
            logger.debug(f"Parsed job: {title}")
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job article: {str(e)}", exc_info=True)
            return None
    
    def _parse_pagination(self, soup: BeautifulSoup, current_page: int) -> PaginationInfo:
        """Parse pagination information from the page"""
        total_jobs = 0
        total_pages = 1
        jobs_per_page = 15
        
        # Try to find job count text
        count_elem = soup.find('div', class_='noo-job-list-count')
        if count_elem:
            text = count_elem.get_text()
            logger.debug(f"Job count text: {text}")
            
            # Match "of X jobs"
            match = re.search(r'of\s+(\d+)\s+jobs?', text, re.IGNORECASE)
            if match:
                total_jobs = int(match.group(1))
                logger.debug(f"Found total jobs: {total_jobs}")
            
            # Match "Showing X-Y"
            range_match = re.search(r'Showing\s+(\d+)[–\-](\d+)', text)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                jobs_per_page = end - start + 1
                logger.debug(f"Jobs per page: {jobs_per_page}")
        
        # Parse pagination links
        pagination_elem = soup.find('div', class_='pagination')
        if pagination_elem:
            page_numbers = pagination_elem.find_all(['a', 'span'], class_='page-numbers')
            for elem in page_numbers:
                text = elem.get_text(strip=True)
                if text.isdigit():
                    page_num = int(text)
                    total_pages = max(total_pages, page_num)
            logger.debug(f"Found total pages from pagination: {total_pages}")
        
        # Calculate total pages from job count
        if total_jobs > 0 and jobs_per_page > 0:
            calculated_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
            total_pages = max(total_pages, calculated_pages)
        
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
    
    async def scrape_listings(
        self, 
        page: int = 1, 
        category: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> JobListingsResponse:
        """Scrape job listings from jobsbotswana.info"""
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
            soup = await self.fetch_page(url)
            if soup is None:
                raise Exception("Failed to fetch page - soup is None")
        except Exception as e:
            logger.error(f"Failed to fetch page: {str(e)}")
            return JobListingsResponse(
                success=False,
                message=f"Failed to fetch page: {str(e)}",
                data=[],
                pagination=PaginationInfo(
                    current_page=page,
                    total_pages=0,
                    total_jobs=0,
                    jobs_per_page=0,
                    has_next=False,
                    has_previous=False
                ),
                filters_applied=filters_applied,
                source=self.source_name
            )
        
        # Debug: Log page title to verify we got the right page
        page_title = soup.find('title')
        if page_title:
            logger.info(f"Page title: {page_title.get_text()}")
        
        # Find all job articles using multiple strategies
        articles = []
        
        # Strategy 1: Find articles with class 'noo_job'
        articles = soup.find_all('article', class_='noo_job')
        logger.info(f"Strategy 1 (article.noo_job): Found {len(articles)} articles")
        
        # Strategy 2: If no articles found, try finding by class 'loadmore-item'
        if not articles:
            articles = soup.find_all('article', class_='loadmore-item')
            logger.info(f"Strategy 2 (article.loadmore-item): Found {len(articles)} articles")
        
        # Strategy 3: Try finding all articles within the jobs container
        if not articles:
            jobs_container = soup.find('div', class_='posts-loop-content')
            if jobs_container:
                articles = jobs_container.find_all('article')
                logger.info(f"Strategy 3 (posts-loop-content > article): Found {len(articles)} articles")
        
        # Strategy 4: Try finding articles within noo-job-list-row
        if not articles:
            jobs_container = soup.find('div', class_='noo-job-list-row')
            if jobs_container:
                articles = jobs_container.find_all('article')
                logger.info(f"Strategy 4 (noo-job-list-row > article): Found {len(articles)} articles")
        
        # Strategy 5: Find all articles on the page
        if not articles:
            articles = soup.find_all('article')
            logger.info(f"Strategy 5 (all articles): Found {len(articles)} articles")
        
        # Debug: Log HTML snippet if no articles found
        if not articles:
            logger.warning("No articles found! Logging page structure...")
            # Find any div that might contain jobs
            job_divs = soup.find_all('div', class_=lambda x: x and 'job' in x.lower() if x else False)
            for div in job_divs[:5]:
                logger.debug(f"Found div with class: {div.get('class')}")
        
        # Parse each article
        jobs = []
        for i, article in enumerate(articles):
            logger.debug(f"Processing article {i+1}/{len(articles)}")
            job = self._parse_job_article(article)
            if job:
                jobs.append(job)
            else:
                # Debug: Log why article was skipped
                article_classes = article.get('class', [])
                logger.debug(f"Article {i+1} skipped. Classes: {article_classes}")
        
        logger.info(f"Successfully parsed {len(jobs)} jobs out of {len(articles)} articles")
        
        # Parse pagination
        pagination = self._parse_pagination(soup, page)
        
        return JobListingsResponse(
            success=True,
            message=f"Successfully fetched {len(jobs)} jobs",
            data=jobs,
            pagination=pagination,
            filters_applied=filters_applied,
            source=self.source_name
        )
    
    async def scrape_job_detail(self, job_url: str) -> Optional[JobListing]:
        """Scrape detailed information for a single job"""
        logger.info(f"Scraping job details from: {job_url}")
        
        try:
            soup = await self.fetch_page(job_url)
            if soup is None:
                return None
        except Exception as e:
            logger.error(f"Failed to fetch job detail: {str(e)}")
            return None
        
        try:
            # Extract title
            title_elem = soup.find('h1', class_='entry-title')
            if not title_elem:
                title_elem = soup.find('h1')
            
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                logger.warning("No title found for job")
                return None
            
            # Extract metadata
            job_type = None
            location = None
            closing_date = None
            company = None
            
            # Look for job meta section
            meta_section = soup.find('ul', class_='job-meta')
            if not meta_section:
                meta_section = soup.find('div', class_='job-meta')
            
            if meta_section:
                # Job type
                type_elem = meta_section.find('span', class_='job-type')
                if type_elem:
                    job_type = type_elem.get_text(strip=True)
                
                # Location
                loc_elem = meta_section.find('span', class_='job-location')
                if loc_elem:
                    location = loc_elem.get_text(strip=True).replace('Location:', '').strip()
            
            # Closing date
            date_elem = soup.find('span', class_='job-date__closing')
            if date_elem:
                closing_date = date_elem.get_text(strip=True)
            
            # Description
            description = None
            content_elem = soup.find('div', class_='entry-content')
            if not content_elem:
                content_elem = soup.find('div', class_='job-content')
            
            if content_elem:
                paragraphs = content_elem.find_all('p')[:5]
                description = ' '.join([p.get_text(strip=True) for p in paragraphs])
                if len(description) > 1000:
                    description = description[:1000] + '...'
            
            # Company from title
            for separator in [' – ', ' - ', ' — ', '–', '-']:
                if separator in title:
                    parts = title.split(separator)
                    if len(parts) > 1:
                        company = parts[-1].strip()
                        break
            
            # Check if closed
            is_closed = soup.find('div', class_='job-closed') is not None
            
            return JobListing(
                title=title,
                url=job_url,
                company=company,
                job_type=job_type,
                location=location,
                closing_date=closing_date,
                description=description,
                is_closed=is_closed,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing job detail: {str(e)}", exc_info=True)
            return None
    
    async def scrape_categories(self) -> List[JobCategory]:
        """Scrape job categories from the website sidebar"""
        logger.info("Scraping job categories from sidebar")
        
        try:
            soup = await self.fetch_page(f"{self.base_url}/jobs/")
            if soup is None:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch categories: {str(e)}")
            return []
        
        categories = []
        
        # Find category widget
        category_widget = soup.find('div', class_='noo-job-category-widget')
        if not category_widget:
            # Try alternative selectors
            category_widget = soup.find('div', id=lambda x: x and 'category' in x.lower() if x else False)
        
        if category_widget:
            cat_list = category_widget.find('ul', class_='job-categories')
            if not cat_list:
                cat_list = category_widget.find('ul')
            
            if cat_list:
                for li in cat_list.find_all('li', class_='cat-item'):
                    link = li.find('a')
                    if link:
                        href = link.get('href', '')
                        name = link.get_text(strip=True)
                        
                        # Extract slug from URL
                        slug_match = re.search(r'/job-category/([^/]+)/?', href)
                        slug = slug_match.group(1) if slug_match else name.lower().replace(' ', '-')
                        
                        # Extract count
                        count = 0
                        li_text = li.get_text()
                        count_match = re.search(r'\((\d+)\)', li_text)
                        if count_match:
                            count = int(count_match.group(1))
                        
                        categories.append(JobCategory(
                            slug=slug,
                            name=name,
                            count=count,
                            url=href
                        ))
        
        logger.info(f"Found {len(categories)} categories")
        return categories
    
    async def scrape_locations(self) -> List[JobLocation]:
        """Scrape job locations from the website sidebar"""
        logger.info("Scraping job locations from sidebar")
        
        try:
            soup = await self.fetch_page(f"{self.base_url}/jobs/")
            if soup is None:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch locations: {str(e)}")
            return []
        
        locations = []
        
        # Find location widget
        location_widget = soup.find('div', class_='noo-job-location-widget')
        if not location_widget:
            location_widget = soup.find('div', id=lambda x: x and 'location' in x.lower() if x else False)
        
        if location_widget:
            loc_list = location_widget.find('ul')
            if loc_list:
                for li in loc_list.find_all('li', class_='cat-item'):
                    link = li.find('a')
                    if link:
                        href = link.get('href', '')
                        name = link.get_text(strip=True)
                        description = link.get('title')
                        
                        # Extract slug from URL
                        slug_match = re.search(r'/job-location/([^/]+)/?', href)
                        slug = slug_match.group(1) if slug_match else name.lower().replace(' ', '-')
                        
                        # Extract count
                        count = 0
                        li_text = li.get_text()
                        count_match = re.search(r'\((\d+)\)', li_text)
                        if count_match:
                            count = int(count_match.group(1))
                        
                        locations.append(JobLocation(
                            slug=slug,
                            name=name,
                            count=count,
                            description=description,
                            url=href
                        ))
        
        # Sort by count descending
        locations.sort(key=lambda x: x.count, reverse=True)
        
        logger.info(f"Found {len(locations)} locations")
        return locations
    
    async def get_job_types(self) -> List[JobType]:
        """Get available job types"""
        return [
            JobType(slug="full-time", name="Full Time", count=0),
            JobType(slug="contract", name="Contract", count=0),
            JobType(slug="part-time", name="Part Time", count=0),
            JobType(slug="temporary", name="Temporary", count=0),
            JobType(slug="internship", name="Internship", count=0),
        ]
    
    async def debug_page(self, url: str = None) -> dict:
        """Debug method to inspect page structure"""
        if url is None:
            url = f"{self.base_url}/jobs/"
        
        try:
            soup = await self.fetch_page(url)
            if soup is None:
                return {"error": "Failed to fetch page"}
            
            # Get page info
            title = soup.find('title')
            
            # Count various elements
            all_articles = soup.find_all('article')
            noo_job_articles = soup.find_all('article', class_='noo_job')
            loadmore_articles = soup.find_all('article', class_='loadmore-item')
            
            # Find containers
            posts_loop = soup.find('div', class_='posts-loop-content')
            job_list_row = soup.find('div', class_='noo-job-list-row')
            
            return {
                "url": url,
                "page_title": title.get_text() if title else None,
                "all_articles_count": len(all_articles),
                "noo_job_articles_count": len(noo_job_articles),
                "loadmore_articles_count": len(loadmore_articles),
                "has_posts_loop_content": posts_loop is not None,
                "has_noo_job_list_row": job_list_row is not None,
                "first_article_classes": all_articles[0].get('class') if all_articles else None,
                "first_article_data_url": all_articles[0].get('data-url') if all_articles else None,
            }
        except Exception as e:
            return {"error": str(e)}


# Create and register the scraper instance
jobs_botswana_scraper = JobsBotswanaScraper()

# Register with the registry
from app.scrapers.registry import scraper_registry
scraper_registry.register(jobs_botswana_scraper)