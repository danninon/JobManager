import hashlib
import json
import random
import sys
from operator import itemgetter

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
import time
import re
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.wait import WebDriverWait


def setJobFiltersLookout(driver):
    # Experience level

    filterJobsByExperience(driver)
    # Time
    time.sleep(2)
    filterJobsByTime(driver)


def filterJobsByTime(driver):
    try:
        # Wait for the button to be clickable
        date_posted_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'searchFilter_timePostedRange'))
        )
        # Click the button
        date_posted_button.click()

        # Find and click the Past Week label
        past_week_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="timePostedRange-r604800"]'))
        )
        # Click the label
        past_week_label.click()

        # Click the date_posted_button again to apply the changes
        date_posted_button.click()

        # Wait for the job results to load after applying the changes
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
        )

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example
# filterJobsByTime(driver)


# Usage example
# filterTimeByWeb(driver)


def filterJobsByExperience(driver):
    try:
        # Find and click the Experience level filter button
        experience_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'searchFilter_experience'))
        )
        experience_button.click()

        # Find and click the Internship checkbox
        internship_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="experience-1"]'))
        )
        # Click the label
        internship_label.click()

        entry_level_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="experience-2"]'))
        )
        # Click the label
        entry_level_label.click()

        # Click the Experience level filter button again to apply the changes
        experience_button.click()

        # Wait for the job results to load after applying the changes
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
        )

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example
# filterJobsByExperience(driver)


# Usage example
# filterExperienceByWeb(driver)


# Initialize the browser
def extract_company_name(input_string):
    match = re.search(r'^(.*?) ·', input_string)
    return match.group(1) if match else None


# note: found a case
def extract_company_location(input_string):
    match = re.search(r'· (.*?),', input_string)
    return match.group(1) if match else None


def extract_time_posted(input_string):
    # Regular expression pattern to match time ago format
    pattern = re.compile(r'\b(\d+)\s+(minute|hour|day|week|month)s?\s+ago\b', re.IGNORECASE)

    # Search for the pattern in the input string
    match = pattern.search(input_string)

    # If a match is found, return the matched string
    if match:
        return match.group(0)
    else:
        return None


def extract_active_applicants(input_string):
    match = re.search(r'· (\d+) applicants$', input_string)
    return int(match.group(1)) if match else None


def page_is_fully_loaded(driver):
    return driver.execute_script("return document.readyState") == "complete"


def get_existing_hashes_from_file(filename):
    try:
        with open(filename, 'r') as file:
            jobs = json.load(file)
            return set(hashJob(job) for job in jobs)
    except FileNotFoundError:
        return set()


def loadJobsFromFile(filename):
    try:
        with open(filename, 'r') as file:
            jobs = json.load(file)
        return jobs
    except FileNotFoundError:
        return []


def saveNewJobsToFile(jobs, filename):
    try:
        existing_hashes = get_existing_hashes_from_file(filename)

        # Filter out jobs with existing hashes
        newJobs = [job for job in jobs if hashJob(job) not in existing_hashes]

        print(f"New Jobs Count: {len(newJobs)}")
        print(f"Existing Hashes: {existing_hashes}")
        print(f"New Hashes: {[hashJob(job) for job in newJobs]}")

        # Load existing jobs from the file
        existing_jobs = loadJobsFromFile(filename)

        # Combine existing jobs and new jobs
        allJobs = existing_jobs + newJobs

        # Save all jobs to the file
        save_jobs_to_file(allJobs, filename)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def save_jobs_to_file(jobs, filename):
    with open(filename, 'w') as file:
        json.dump(jobs, file, indent=2)


def extractJobDetails(jobUrl, driver):
    try:
        # Navigate to the job URL
        driver.get(jobUrl)

        # Wait for the company description element to be present
        time.sleep(2)

        companyDescriptionElement = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'job-details-jobs-unified-top-card__primary-description'
                                                             '-container'))
        )

        companyLocationPostedApplicants = companyDescriptionElement.text

        company_name = extract_company_name(companyLocationPostedApplicants)
        location = extract_company_location(companyLocationPostedApplicants)
        post_time = extract_time_posted(companyLocationPostedApplicants)
        applicants = extract_active_applicants(companyLocationPostedApplicants)

        # Wait for the job title element to be present
        jobTitleElement = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'job-details-jobs-unified-top-card__job-title'))
        )
        jobTitle = jobTitleElement.text

        # Click the "See more" button
        seeMoreButton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Click to see more description"]'))
        )
        seeMoreButton.click()

        # Wait for the job description text element to be present
        jobDescriptionElement = WebDriverWait(driver, 10).until(
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


def scrollDownUntilBottom(driver, element_class, offset=100, scroll_speed=1.0):
    try:
        # Find the container element that holds the list
        container_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, element_class))
        )

        # Get the initial scroll position
        initialScrollPosition = driver.execute_script("return arguments[0].scrollTop;", container_element)

        while True:
            # Scroll down by the specified offset
            driver.execute_script("arguments[0].scrollTop += arguments[1];", container_element, offset)

            # Wait for a short period to allow content to load
            time.sleep(scroll_speed)

            # Get the new scroll position
            newScrollPosition = driver.execute_script("return arguments[0].scrollTop;", container_element)

            # Check if the scroll position hasn't changed, indicating that we have reached the bottom
            if newScrollPosition == initialScrollPosition:
                break

            # Update the initial scroll position
            initialScrollPosition = newScrollPosition

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def readPage(driver, jobInformationHref):
    try:
        scrollDownUntilBottom(driver, element_class='jobs-search-results-list', offset=1000,
                              scroll_speed=random.uniform(0.3, 0.8))

        # job_title_elements = try_find_element(by=By.CLASS_NAME,
        #                                       value='ember-view.jobs-search-results__list-item.occludable-update.p0'
        #                                       '.relative.scaffold-layout__list-item', element=driver)
        # time.sleep(2)
        jobTitleElements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, 'ember-view.jobs-search-results__list-item.occludable-update.p0'
                                '.relative.scaffold-layout__list-item'))
        )
        # job_title_elements = driver.find_elements(By.CLASS_NAME,
        #                                           'ember-view.jobs-search-results__list-item.occludable-update.p0'
        #                                           '.relative.scaffold-layout__list-item')
        # time.sleep(2)
        for jobTitleElement in jobTitleElements:
            # Find the nested anchor element within the job title element
            anchorElement = WebDriverWait(jobTitleElement, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'a'))
            )
            # anchor_element = job_title_element.find_element(By.TAG_NAME, 'a')

            # anchor_element = job_title_element.find_element(By.TAG_NAME, 'a')

            jobHref = anchorElement.get_attribute('href')

            # Additional processing to handle specific structure
            if jobHref:
                jobInformationHref.append(jobHref)
        # Print the collected information
        # for job_info in jobInformation:
        #     print(f"Job Title: {job_info['text']}")
        #     print(f"Job Href: {job_info['href']}")
        #     print()
    except Exception as e:
        print(f"An error occurred: {e}")


def login(driver):

    username_input = driver.find_element(By.ID, 'session_key')
    password_input = driver.find_element(By.ID, 'session_password')
    # Enter the username and password
    username_input.send_keys(username)
    password_input.send_keys(password)
    # Find and click the sign-in button
    sign_in_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]")
    sign_in_button.click()


# sometimes not filtering the name
# def setJobTitleLookout(driver, searchQuery):
#     try:
#         text_box_element = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-box__text-input'))
#         )
#         # text_box_element = try_find_element(by=By.CLASS_NAME, value='jobs-search-box__text-input', element=driver)
#         text_box_element.clear()
#         text_box_element.send_keys(searchQuery)  # make different searches later, but start with this one
#         time.sleep(2)
#         text_box_element.send_keys(Keys.ENTER)
#         time.sleep(2)
#     except Exception as e:
#         print(f"An error occurred: {e}")

def setJobTitleLookout(driver, searchQuery):
    try:
        text_box_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-box__text-input'))
        )
        text_box_element.clear()
        text_box_element.send_keys(searchQuery)

        # Wait for a short period to ensure the text is entered before pressing Enter
        WebDriverWait(driver, 2).until(
            lambda driver: text_box_element.get_attribute('value') == searchQuery
        )

        text_box_element.send_keys(Keys.ENTER)

        # Wait for the job results to load after pressing Enter
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-results-list'))
        )

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example
# setJobTitleLookout(driver, 'software engineer')


def try_find_element(by, value, element, max_wait=10, poll_frequency=1):
    try:
        # First attemp of waiting for the element to be present
        time.sleep(1)
        if waitForElementDriver(by, max_wait, value):
            return element.find_element(by, value)
        # Second attempt of waiting for the element to be found

        if waitForElementLoop(by=by, value=value, element=element, max_wait=max_wait, poll_frequency=poll_frequency):
            return element.find_element(by, value)
    except Exception as e:
        time.sleep(2)
        return element.find_element(by, value)


def waitForElementDriver(by, max_wait, value):
    try:
        selector = (by, value)
        WebDriverWait(by, max_wait).until(
            EC.presence_of_element_located(selector)
        )
        return True
    except Exception as e:
        return False


def waitForElementLoop(max_wait, poll_frequency, by, value, element):
    try:
        end_time = time.time() + max_wait
        while time.time() < end_time:
            try:
                element.find_element(by, value)
                print(f"Element found: {by}='{value}'")
                return True
            except NoSuchElementException:
                print(f"Element not found, retrying in {poll_frequency} seconds...")
                time.sleep(poll_frequency)
        print(f"Element not found within the specified timeout ({max_wait} seconds).")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def goToPage(driver, PageNumber):
    try:
        # Wait for the parent element containing the page buttons to be present
        wait = WebDriverWait(driver, 10)
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


def ExtractHrefsData(driver, jobInformationHref, searchQueries, pagesToRead):
    try:
        if pagesToRead == 0:
            return
        for searchQuery in searchQueries:

            setJobTitleLookout(driver, searchQuery)
            pageNumber = 1
            time.sleep(2)
            while pagesToRead - pageNumber >= 0:
                readPage(driver, jobInformationHref)
                pageNumber += 1
                # Check if there is a next page
                if not goToPage(driver, pageNumber):
                    break  # Exit the loop if there is no next page
    except Exception as e:
        print(f"An error occurred: {e}")


# def ExtractJobsFromHref(driver, jobInformationHref, jobInformation):
#     for href in jobInformationHref:
#         # driver.get(href)
#         jobDetails = extractJobDetails(href, driver)
#         # Check if the job_details is not already in the list before adding it
#         if jobDetails not in jobInformation:
#             jobInformation.append(jobDetails)

def ExtractJobsFromHref(driver, jobInformationHref, jobInformation):
    try:
        # Load existing jobs from the file
        existingJobs = loadJobsFromFile('jobs.json')

        for href in jobInformationHref:
            # driver.get(href)
            jobDetails = extractJobDetails(href, driver)

            # Check if the job details are not already in the existing jobs based on hash
            if hashJob(jobDetails) not in (hashJob(existing_job) for existing_job in existingJobs):
                jobInformation.append(jobDetails)
            else:
                print(f"Job already exists: {jobDetails}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def sort_key(job):
    try:
        global counter
        company_name = job['company_name'] if 'company_name' in job else 'Not Found'
        location = job['location'] if 'location' in job and job['location'] is not None else 'Not Found'
        job_title = job['job_title'] if 'job_title' in job else 'Not Found'

        # Print statements for debugging
        print(f"Company Name: {company_name}, Location: {location}, Job Title: {job_title}")
        print(f"Counter: {counter}")
        counter += 1

        if None in (company_name, location, job_title):
            raise ValueError(f"Found None value in job: {job}")

        return company_name, location, job_title
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# Sort the jobs using the custom key function

counter = 1


def Main():
    try:
        driver = webdriver.Chrome()
        # Open the web page
        driver.get('https://www.linkedin.com/')
        # sign in

        try:
            # put my credentials in the login page
            # there has to be a break point here since they are sometimes asking for validation for not being a bot
            login(driver)

            # get a new relevant page now that were logged in

            driver.get('https://www.linkedin.com/jobs/search/')

            # set the job title lookout
            jobInformationHref = []

            # fullstack, backend, support developer, junior, graduate, software developer

            searchQueries = {'software engineer'}

            setJobFiltersLookout(driver)
            pagesToRead = sys.maxsize

            ExtractHrefsData(driver, jobInformationHref, searchQueries,
                             pagesToRead)

            jobInformation = loadJobsFromFile('jobs.json')

            ExtractJobsFromHref(driver, jobInformationHref, jobInformation)

            saveNewJobsToFile(jobInformation, 'jobs.json')

            sorted_jobs = sorted(jobInformation, key=sort_key)
            a = 1

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    except NoSuchElementException as e:
        print(f"Error: {e}")
        print("The <html> element was not found. Make sure the page is loaded correctly.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the browser window
        if driver is not None:
            driver.quit()


Main()
