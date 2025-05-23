
"""
Odisha RERA Project Scraper - First 6 Projects
Scrapes project details from https://rera.odisha.gov.in/projects/project-list
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import sys
from urllib.parse import urljoin, urlparse

class OdishaRERAScraper:
    def __init__(self):
        self.base_url = "https://rera.odisha.gov.in"
        self.project_list_url = "https://rera.odisha.gov.in/projects/project-list"
        self.projects = []
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            # Comment out headless mode to see the browser (useful for debugging)
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Error setting up Selenium: {e}")
            return None
    
    def wait_for_content(self, driver, timeout=20):
        """Wait for project content to load"""
        try:
            # Wait for project cards or containers to load
            wait = WebDriverWait(driver, timeout)
            
            # Try different possible selectors for project containers
            selectors_to_try = [
                ".project-card",
                ".project-item",
                ".project-container",
                "[class*='project']",
                ".card",
                ".list-item",
                "div[contains(text(), 'RP/')]",
                "div[contains(text(), 'PS/')]"
            ]
            
            for selector in selectors_to_try:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✓ Content loaded with selector: {selector}")
                    return True
                except:
                    continue
            
            # If no specific selectors work, just wait for general content
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"⚠️ Timeout waiting for content: {e}")
            return False
    
    def extract_project_data(self, project_html):
        """Extract project data from HTML content"""
        project_data = {
            'project_name': '',
            'promoter_name': '',
            'address': '',
            'project_type': '',
            'started_from': '',
            'possession_by': '',
            'units_available': '',
            'rera_no': '',
            'contact_info': ''
        }
        
        try:
            soup = BeautifulSoup(project_html, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract RERA number (RP/XX/YYYY/XXXXX or PS/XX/YYYY/XXXXX)
            rera_match = re.search(r'(RP|PS)/\d+/\d{4}/\d+', text_content)
            if rera_match:
                project_data['rera_no'] = rera_match.group(0)
            
            # Extract project name (usually in bold or as heading)
            project_name_patterns = [
                r'([A-Z][A-Z\s\-&\.]+[A-Z])\s+by\s+',
                r'<strong>([^<]+)</strong>',
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
            ]
            
            for pattern in project_name_patterns:
                match = re.search(pattern, project_html, re.IGNORECASE)
                if match:
                    project_data['project_name'] = match.group(1).strip()
                    break
            
            # Extract promoter name (after "by")
            promoter_match = re.search(r'by\s+([A-Z][A-Z\s\-&\.\(\)]+?)(?:\s+Address|\s+Project Type|$)', text_content, re.IGNORECASE)
            if promoter_match:
                project_data['promoter_name'] = promoter_match.group(1).strip()
            
            # Extract address
            address_match = re.search(r'Address\s*:\s*(.*?)(?:Project Type|Started From|$)', text_content, re.IGNORECASE)

            if address_match:
                project_data['address'] = address_match.group(1).strip()
            
            # Extract project type
            type_match = re.search(r'Project Type\s*(Residential|Plotted Scheme|Commercial)', text_content, re.IGNORECASE)
            if type_match:
                project_data['project_type'] = type_match.group(1).strip()
            
            # Extract started from
            started_match = re.search(r'Started From\s*([A-Za-z]+,?\s*\d{4})', text_content, re.IGNORECASE)
            if started_match:
                project_data['started_from'] = started_match.group(1).strip()
            
            # Extract possession by
            possession_match = re.search(r'Possession by\s*([A-Za-z]+,?\s*\d{4})', text_content, re.IGNORECASE)
            if possession_match:
                project_data['possession_by'] = possession_match.group(1).strip()
            
            # Extract units available
            units_match = re.search(r'(\d+)\s*Units?\s*Available', text_content, re.IGNORECASE)
            if units_match:
                project_data['units_available'] = units_match.group(1)
            
            return project_data
            
        except Exception as e:
            print(f"❌ Error extracting project data: {e}")
            return project_data
    
    def scrape_projects_selenium(self, max_projects=6):
        """Scrape projects using Selenium"""
        driver = self.setup_selenium()
        if not driver:
            return []
        
        try:
            print(f"🌐 Loading page: {self.project_list_url}")
            driver.get(self.project_list_url)
            
            # Wait for content to load
            if not self.wait_for_content(driver):
                print("⚠️ Content may not have loaded properly")
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            
            # Save for debugging
            with open('debug_selenium_full_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("💾 Saved full page to debug_selenium_full_page.html")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try to find project containers using various strategies
            project_containers = []
            
            # Strategy 1: Look for elements containing RERA numbers
            rera_elements = soup.find_all(text=re.compile(r'(RP|PS)/\d+/\d{4}/\d+'))
            for element in rera_elements[:max_projects]:
                # Get the parent container
                container = element.parent
                while container and container.name not in ['div', 'article', 'section', 'li']:
                    container = container.parent
                if container:
                    project_containers.append(container)
            
            # Strategy 2: Look for common project container patterns
            if not project_containers:
                selectors = [
                    'div[class*="project"]',
                    'div[class*="card"]',
                    'li[class*="project"]',
                    'article',
                    '.project-item',
                    '.project-card'
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        project_containers = elements[:max_projects]
                        print(f"✓ Found {len(project_containers)} containers with selector: {selector}")
                        break
            
            # Strategy 3: Parse the entire content and extract projects manually
            if not project_containers:
                print("🔍 Using text-based extraction strategy")
                full_text = soup.get_text(separator='\n', strip=True)
                
                # Split by RERA numbers to identify projects
                rera_pattern = r'(RP|PS)/\d+/\d{4}/\d+'
                rera_matches = list(re.finditer(rera_pattern, full_text))
                
                for i, match in enumerate(rera_matches[:max_projects]):
                    if i < len(rera_matches) - 1:
                        # Extract text between current and next RERA number
                        start = max(0, match.start() - 500)  # Get some context before
                        end = rera_matches[i + 1].start()
                        project_text = full_text[start:end]
                    else:
                        # Last project
                        start = max(0, match.start() - 500)
                        project_text = full_text[start:start + 1000]
                    
                    # Create a pseudo-container with the text
                    pseudo_container = BeautifulSoup(f'<div>{project_text}</div>', 'html.parser')
                    project_containers.append(pseudo_container.div)
            
            print(f"📊 Found {len(project_containers)} project containers")
            
            # Extract data from each container
            projects_data = []
            for i, container in enumerate(project_containers[:max_projects], 1):
                print(f"🏗️ Processing project {i}/{min(max_projects, len(project_containers))}")
                
                container_html = str(container)
                project_data = self.extract_project_data(container_html)
                
                # Add some debug info
                project_data['raw_html'] = container_html[:500] + "..." if len(container_html) > 500 else container_html
                
                projects_data.append(project_data)
                
                # Print extracted data for verification
                print(f"  📋 Project: {project_data['project_name']}")
                print(f"  🏢 Promoter: {project_data['promoter_name']}")
                print(f"  📍 Address: {project_data['address']}")
                print(f"  🔢 RERA No: {project_data['rera_no']}")
                print("  " + "-" * 40)
            
            return projects_data
            
        except Exception as e:
            print(f"❌ Error during Selenium scraping: {e}")
            return []
        
        finally:
            driver.quit()
    
    def save_to_csv(self, projects_data, filename='odisha_rera_projects_first6.csv'):
        """Save projects data to CSV"""
        if not projects_data:
            print("❌ No data to save")
            return
        
        try:
            df = pd.DataFrame(projects_data)
            
            # Reorder columns for better readability
            column_order = [
                'project_name', 'promoter_name', 'address', 'project_type',
                'started_from', 'possession_by', 'units_available', 'rera_no',
                'contact_info'
            ]
            
            # Only include columns that exist
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"💾 Data saved to {filename}")
            
            # Print summary
            print(f"\n📊 SCRAPING SUMMARY:")
            print(f"Total projects scraped: {len(projects_data)}")
            print(f"Projects with RERA No: {len([p for p in projects_data if p['rera_no']])}")
            print(f"Projects with Project Name: {len([p for p in projects_data if p['project_name']])}")
            print(f"Projects with Promoter Name: {len([p for p in projects_data if p['promoter_name']])}")
            
            # Show sample data
            print(f"\n📋 SAMPLE DATA:")
            for i, project in enumerate(projects_data[:3], 1):
                print(f"Project {i}:")
                for key, value in project.items():
                    if key != 'raw_html' and value:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                print()
                
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
    
    def run(self, max_projects=6):
        """Main scraping function"""
        print("=" * 50)
        print("Odisha RERA Project Scraper - First 6 Projects")
        print("=" * 50)
        
        print(f"🎯 Target: First {max_projects} projects from {self.project_list_url}")
        
        # Use Selenium approach
        projects_data = self.scrape_projects_selenium(max_projects)
        
        if projects_data:
            self.save_to_csv(projects_data)
        else:
            print("❌ No project data was extracted")

def main():
    scraper = OdishaRERAScraper()
    scraper.run(max_projects=6)

if __name__ == "__main__":
    main()