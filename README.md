# Odisha RERA Project Scraper

A Python-based web scraper that extracts real estate project data from the [Odisha RERA portal](https://rera.odisha.gov.in/projects/project-list) using Selenium and BeautifulSoup. Currently, it fetches data for the **first 6 projects** listed on the website.

## 📦 Features

- Extracts:
  - Project Name
  - Promoter Name
  - Address
  - Project Type
  - Start Date
  - Possession Date
  - Units Available
  - RERA Number
- Saves data to CSV (`odisha_rera_projects_first6.csv`)
- Headless browser scraping using Selenium
- HTML backup for debugging

## 🛠️ Tech Stack

- Python 3.7+
- Selenium
- BeautifulSoup4
- pandas
- ChromeDriver (via `webdriver-manager`)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/odisha-rera-scraper.git
cd odisha-rera-scraper
# odisha_rera_scraper
