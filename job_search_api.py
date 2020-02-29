"""
    @script-author: amandeepsinghkhanna
    @python-version: Python 3.7.6
    @script-description: A python API to connect to various job portals, 
    return jobs and then perform text-mining on the descriptions.
"""

# importing the required PYPI modules:
import os  # for interfacing with the opertaing system
import requests  # for making requests to the API
import datetime  # for capturing timestamps
import pandas as pd  # for interfacing with pandas DataFrame objects
from bs4 import BeautifulSoup  # for web scraping

# setting global variables:
timestamp = datetime.datetime.now()

class search_jobs(object):
    def __init__(
        self,
        job_positions,
        cities,
        radius=100,
        job_type="fulltime",
        pages=20,
        base_url="https://www.indeed.co.in/jobs?q=",
    ):
        self.job_positions = job_positions
        self.cities = cities
        self.radius = radius
        self.job_type = job_type
        self.pages = pages * 10
        self.base_url = base_url

    @staticmethod
    def create_job_url(base_url, job_position, city, radius, job_type, page):
        if page == 0:
            page = ""
        else:
            page = str(page)
            page = "&start=" + page

        job_url = (
            base_url
            + job_position
            + "&l="
            + city
            + "&radius="
            + str(radius)
            + "&jt="
            + job_type
            + "&fromage=last"
            + page
        )

        return job_url

    @staticmethod
    def make_request(job_url):
        req_obj = requests.get(job_url)
        if req_obj.status_code == 200:
            if req_obj != None:
                return req_obj.text
            else:
                return None
        else:
            return None

    @staticmethod
    def soup_webpage(req_page):
        soup_obj = BeautifulSoup(req_page, "html.parser")
        return soup_obj

    @staticmethod
    def job_divs(soup_obj):
        job_divs = soup_obj.find_all("div", class_="jobsearch-SerpJobCard")
        if len(job_divs) == 0:
            job_divs = None
        return job_divs

    @staticmethod
    def extract_job_title(job_div):
        job_title = job_div.find("a").get("title")
        return job_title

    @staticmethod
    def extract_job_url(job_div):
        job_url = job_div.find("a")
        if job_url != None:
            job_url = job_url.get("href")
            return job_url
        else:
            return None

    @staticmethod
    def extract_job_salary(job_div):
        job_salary = job_div.find("span", class_="salaryText")
        return job_salary

    def extract_job_summary(self, job_url):
        req_page = self.make_request(job_url)
        if req_page == None:
            return None
        soup_obj = self.soup_webpage(req_page)
        if soup_obj == None:
            return None
        summary_obj = soup_obj.find("div", id="jobDescriptionText")
        if summary_obj == None:
            return None
        return summary_obj.text

    @staticmethod
    def extract_post_date(job_div):
        date = job_div.find("span", class_="date")
        return date

    @staticmethod
    def validate_fields(job_title, job_url, job_summary):
        if (job_title == None) and (job_url == None) and (job_summary == None):
            return False
        else:
            return True

    def extract_job_info(self, job_divs):
        scraped_info_df = pd.DataFrame()
        for job_div in job_divs:
            job_title = self.extract_job_title(job_div)
            if job_title != None:
                job_title = job_title.strip()
            job_url = self.extract_job_url(job_div)
            if job_url != None:
                job_url = job_url.strip()
                job_url = "https://www.indeed.co.in" + job_url
                job_summary = self.extract_job_summary(job_url)
            job_salary = self.extract_job_salary(job_div)
            if job_salary == None:
                job_salary = "Not Mentioned"
            posting_date = self.extract_post_date(job_div)
            if posting_date != None:
                posting_date = posting_date.text
                posting_date = posting_date.strip()
            validation_check = self.validate_fields(
                job_title=job_title, job_url=job_url, job_summary=job_summary
            )
            if validation_check == True:
                scraped_info = pd.DataFrame(
                    {
                        "JOB TITLE": [job_title],
                        "JOB URL": [job_url],
                        "JOB SUMMARY": [job_summary],
                        "JOB SALARY": [job_salary],
                        "POSTING DATE": [posting_date],
                    }
                )
                scraped_info_df = scraped_info_df.append(
                    scraped_info, ignore_index=True
                )
        if scraped_info_df.shape[0] > 1:
            return scraped_info_df
        else:
            return None

    def scrape_webpage(self, job_url):
        req_page = self.make_request(job_url)
        if req_page == None:
            return None
        soup_obj = self.soup_webpage(req_page)
        if soup_obj == None:
            return None
        job_divs = self.job_divs(soup_obj)
        if job_divs == None:
            return None
        scraped_info = self.extract_job_info(job_divs)
        if scraped_info is None:
            return None
        # print("{} - scrape_webpage".format(scraped_info))
        return scraped_info

    def scrape_data(self):
        error_urls = []
        scraped_info_df = pd.DataFrame()
        for city in self.cities:
            for job_position in self.job_positions:
                for page in range(0, self.pages, 10):
                    job_url = self.create_job_url(
                        base_url=self.base_url,
                        job_position=job_position,
                        city=city,
                        radius=self.radius,
                        job_type=self.job_type,
                        page=page,
                    )
                    # print(job_url)
                    scraped_info = self.scrape_webpage(job_url)
                    if scraped_info is None:
                        error_urls.append(job_url)
                    # print(scraped_info)
                    scraped_info_df = scraped_info_df.append(
                        scraped_info, ignore_index=True
                    )
        if len(error_urls) > 0:
            print("Error occuredd in scraping the following urls:")
            print(error_urls)
        else:
            print("Scraped all the website inforamtion successfully!")
        scraped_info_df = scraped_info_df.reset_index(drop=True)
        return scraped_info_df
