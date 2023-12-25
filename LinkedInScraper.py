import random
import sys
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
import time
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import json
import hashlib


class LinkedInScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()  # You can change the webdriver as needed
        self.jobsCollection = []
        self.ioFilePath = "jobs.json"
        self.pagesToRead = 0 # sys.maxsize
        self.searchQueries = {'software engineer'}

    def setJobFiltersLookout(self):
        self.filterJobsByExperience()
        time.sleep(2)
        self.filterJobsByTime()

    def filterJobsByTime(self):
        try:
            # Wait for the button to be clickable
            date_posted_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'searchFilter_timePostedRange'))
            )
            # Click the button
            date_posted_button.click()

            # Find and click the Past Week label
            past_week_label = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="timePostedRange-r604800"]'))
            )
            # Click the label
            past_week_label.click()

            # Click the date_posted_button again to apply the changes
            date_posted_button.click()

            # Wait for the job results to load after applying the changes
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
            )
        except Exception as e:
            print(f"An error occurred: {e}")

    def filterJobsByExperience(self):
        try:
            # Find and click the Experience level filter button
            experience_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'searchFilter_experience'))
            )
            experience_button.click()

            # Find and click the Internship checkbox
            internship_label = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="experience-1"]'))
            )
            # Click the label
            internship_label.click()

            entry_level_label = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="experience-2"]'))
            )
            # Click the label
            entry_level_label.click()

            # Click the Experience level filter button again to apply the changes
            experience_button.click()

            # Wait for the job results to load after applying the changes
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
            )
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def extractCompanyName(input_string):
        match = re.search(r'^(.*?) ·', input_string)
        return match.group(1) if match else None

    @staticmethod
    def extractCompanyLocation(input_string):
        match = re.search(r'· (.*?),', input_string)
        return match.group(1) if match else None

    @staticmethod
    def extractTimePosted(input_string):
        # Regular expression pattern to match time ago format
        pattern = re.compile(r'\b(\d+)\s+(minute|hour|day|week|month)s?\s+ago\b', re.IGNORECASE)

        # Search for the pattern in the input string
        match = pattern.search(input_string)

        # If a match is found, return the matched string
        if match:
            return match.group(0)
        else:
            return None

    @staticmethod
    def extractActiveApplicants(input_string):
        match = re.search(r'· (\d+) applicants$', input_string)
        return int(match.group(1)) if match else None

    def isPageFullyLoaded(self):
        return self.driver.execute_script("return document.readyState") == "complete"

    def getExistingHashesFromFile(self):
        try:
            with open(self.ioFilePath, 'r') as file:
                jobs = json.load(file)
                return set(self.hashJob(job) for job in jobs)
        except FileNotFoundError:
            return set()

    def loadJobsFromFile(self):
        try:
            with open(self.ioFilePath, 'r') as file:
                jobs = json.load(file)
            return jobs
        except FileNotFoundError:
            return []

    def saveNewJobsToFile(self):
        try:



            # Filter out jobs with existing hashes

            # counts the number of existing hashes (in the file, before saving)
            existingHashes = self.getExistingHashesFromFile()
            # basically counts the number of jobs that are not in the existing hashes
            newJobs = [job for job in self.jobsCollection if self.hashJob(job) not in existingHashes]

            print(f"New Jobs Count: {len(newJobs)}")
            print(f"Existing Hashes: {existingHashes}")
            print(f"New Hashes: {[self.hashJob(job) for job in newJobs]}")

            # Load existing jobs from the file
            # existing_jobs = self.loadJobsFromFile(self.ioFilePath)

            # Combine existing jobs and new jobs
            # allJobs = existing_jobs + newJobs

            # Save all jobs to the file
            self.saveJobsToFile()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def saveJobsToFile(self):
        with open(self.ioFilePath, 'w') as file:
            json.dump(self.jobsCollection, file, indent=2)

    def extractJobDetails(self, jobUrl):
        try:
            # Navigate to the job URL
            self.driver.get(jobUrl)

            # Wait for the company description element to be present
            time.sleep(2)

            companyDescriptionElement = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'job-details-jobs-unified-top-card__primary-description'
                                    '-container'))
            )

            companyLocationPostedApplicants = companyDescriptionElement.text

            company_name = self.extractCompanyName(companyLocationPostedApplicants)
            location = self.extractCompanyLocation(companyLocationPostedApplicants)
            post_time = self.extractTimePosted(companyLocationPostedApplicants)
            applicants = self.extractActiveApplicants(companyLocationPostedApplicants)

            # Wait for the job title element to be present
            jobTitleElement = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'job-details-jobs-unified-top-card__job-title'))
            )
            jobTitle = jobTitleElement.text

            # Click the "See more" button
            seeMoreButton = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Click to see more description"]'))
            )
            seeMoreButton.click()

            # Wait for the job description text element to be present
            jobDescriptionElement = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-description-content__text'))
            )
            jobDescriptionText = jobDescriptionElement.text

            # Add the current timestamp as 'discovered_time'
            discoveredTime = time.strftime("%Y-%m-%d %H:%M:%S")

            return {
                'company_name': company_name,
                'location': location,
                'post_time': post_time,
                'applicants': applicants,
                'job_title': jobTitle,
                'job_url': jobUrl,
                'job_description_text': jobDescriptionText,
                'discovered_time': discoveredTime
            }
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def hashJob(job):
        try:
            # Create a new dictionary including only 'company_name', 'job_title', and 'location'
            hashableJob = {key: job[key] for key in ('company_name', 'job_title', 'location')}

            # Convert the hashable job dictionary to a string representation
            jobStr = str(hashableJob)

            # Use hashlib to create a hash of the string representation
            hashObject = hashlib.md5(jobStr.encode())

            # Return the hexadecimal representation of the hash
            return hashObject.hexdigest()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def scrollDownUntilBottom(self, element_class, offset=100, scroll_speed=1.0):
        try:
            # Find the container element that holds the list
            container_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, element_class))
            )

            # Get the initial scroll position
            initialScrollPosition = self.driver.execute_script("return arguments[0].scrollTop;", container_element)

            while True:
                # Scroll down by the specified offset
                self.driver.execute_script("arguments[0].scrollTop += arguments[1];", container_element, offset)

                # Wait for a short period to allow content to load
                time.sleep(scroll_speed)

                # Get the new scroll position
                newScrollPosition = self.driver.execute_script("return arguments[0].scrollTop;", container_element)

                # Check if the scroll position hasn't changed, indicating that we have reached the bottom
                if newScrollPosition == initialScrollPosition:
                    break

                # Update the initial scroll position
                initialScrollPosition = newScrollPosition

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def readPage(self, jobInformationHref):
        try:
            self.scrollDownUntilBottom(element_class='jobs-search-results-list', offset=1000,
                                       scroll_speed=random.uniform(0.3, 0.8))

            jobTitleElements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, 'ember-view.jobs-search-results__list-item.occludable-update.p0'
                                    '.relative.scaffold-layout__list-item'))
            )

            for jobTitleElement in jobTitleElements:
                # Find the nested anchor element within the job title element
                anchorElement = WebDriverWait(jobTitleElement, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'a'))
                )

                jobHref = anchorElement.get_attribute('href')

                # Additional processing to handle specific structure
                if jobHref:
                    jobInformationHref.append(jobHref)
        except Exception as e:
            print(f"An error occurred: {e}")

    # todo: username and password should be in a file and not in the code itself
    # todo: could replace find_element with using WebDriverWait
    def login(self):
        try:
          
            username_input = self.driver.find_element(By.ID, 'session_key')
            password_input = self.driver.find_element(By.ID, 'session_password')
            # Enter the username and password
            username_input.send_keys(username)
            password_input.send_keys(password)
            # Find and click the sign-in button
            sign_in_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]")
            sign_in_button.click()
        except Exception as e:
            print(f"An error occurred: {e}")

    def setJobTitleLookout(self, searchQuery):
        try:
            text_box_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-box__text-input'))
            )
            text_box_element.clear()
            text_box_element.send_keys(searchQuery)

            # Wait for a short period to ensure the text is entered before pressing Enter
            WebDriverWait(self.driver, 2).until(
                lambda driver: text_box_element.get_attribute('value') == searchQuery
            )

            text_box_element.send_keys(Keys.ENTER)

            # Wait for the job results to load after pressing Enter
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
            )

        except Exception as e:
            print(f"An error occurred: {e}")

    def goToPage(self, PageNumber):
        try:
            # Wait for the parent element containing the page buttons to be present
            wait = WebDriverWait(self.driver, 10)
            pagination_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'artdeco-pagination__pages--number')))

            # Find the button corresponding to the input page number
            pageButtonXpath = f"//button[@aria-label='Page {PageNumber}']"
            pageButton = wait.until(EC.element_to_be_clickable((By.XPATH, pageButtonXpath)))

            # Click the page button
            pageButton.click()

            print(f"Clicked the button for Page {PageNumber}")
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    # todo, move searchQueries and pagesToRead to the constructor
    def ExtractHrefsData(self, jobInformationHref):
        try:
            if self.pagesToRead == 0:
                return
            for searchQuery in self.searchQueries:

                self.setJobTitleLookout(searchQuery)
                pageNumber = 1
                time.sleep(2)
                while self.pagesToRead - pageNumber >= 0:
                    self.readPage(jobInformationHref)
                    pageNumber += 1
                    # Check if there is a next page
                    if not self.goToPage(pageNumber):
                        break  # Exit the loop if there is no next page
        except Exception as e:
            print(f"An error occurred: {e}")

    def ExtractJobsFromHref(self, jobInformationHref):
        try:
            # Load existing jobs from the file
            self.jobsCollection = self.loadJobsFromFile()

            for href in jobInformationHref:
                # driver.get(href)
                jobDetails = self.extractJobDetails(href)

                # Check if the job details are not already in the existing jobs based on hash
                if self.hashJob(jobDetails) not in (self.hashJob(existing_job) for existing_job in self.jobsCollection):
                    self.jobsCollection.append(jobDetails)
                else:
                    print(f"Job already exists: {jobDetails}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")



    # Sort the jobs using the custom key function

    @staticmethod
    def sortKey(job):
        try:

            company_name = job['company_name'] if 'company_name' in job else 'Not Found'
            location = job['location'] if 'location' in job and job['location'] is not None else 'Not Found'
            job_title = job['job_title'] if 'job_title' in job else 'Not Found'

            # Print statements for debugging
            print(f"Company Name: {company_name}, Location: {location}, Job Title: {job_title}")

            if None in (company_name, location, job_title):
                raise ValueError(f"Found None value in job: {job}")

            return company_name, location, job_title
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    # todo: change to public and the rest to private name conventions
    def LinkedInScrape(self):

        try:
            self.driver.get('https://www.linkedin.com/')
            # put my credentials in the login page
            # there has to be a break point here since they are sometimes asking for validation for not being a bot
            self.login()

            # get a new relevant page now that were logged in

            self.driver.get('https://www.linkedin.com/jobs/search/')

            # set the job title lookout
            jobInformationHref = []

            # fullstack, backend, support developer, junior, graduate, software developer

            self.setJobFiltersLookout()

            self.ExtractHrefsData(jobInformationHref)

            self.ExtractJobsFromHref(jobInformationHref)

            self.saveNewJobsToFile()

            breakpoint = "breakpoint"
            return self.jobsCollection

            # return self.jobsCollection
            #
            # sorted_jobs = sorted(self.jobsCollection, key=self.sortKey)
            # a = 1

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        finally:
            # Close the browser window
            if self.driver is not None:
                self.driver.quit()

    # def extract_job_details(self, job_url):
    #     return self._extract_job_details(job_url)
    #
    # def scrape_linkedin(self, filename):
    #     # Implement your main scraping logic here using the private methods
    #     pass

# Example Usage:
# scraper = LinkedInScraper()
# scraper.set_job_filters_lookout()
# job_details = scraper.extract_job_details("https://example.com/job-url")
# scraper.scrape_linkedin("output_file.json")
