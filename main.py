import asyncio
from playwright.async_api import async_playwright
import csv

async def scrape_page(page):
    """Scrape the current page and return the collected data."""
    results = []

    # Find all links within the table
    links = await page.query_selector_all("table#table81 a")
    urls = [{"text": await link.inner_text(), "url": await link.get_attribute('href')} for link in links]

    for link in urls:
        try:
            if link["url"] and link["text"]:
                print(f"Visiting: {link['text']} - {link['url']}")
                await page.goto(link["url"])
                
                try:
                    await page.wait_for_selector("body", timeout=30000)

                    description = await page.evaluate('''() => {
                        const paragraphs = document.querySelectorAll('p.MsoNormal');
                        for (const p of paragraphs) {
                            if (p.textContent.includes('Description:')) {
                                return p.textContent.trim();
                            }
                        }
                        return '';
                    }''')

                    if not description:
                        description = "Description not found."

                    homepage_url = None
                    try:
                        homepage_element = await page.query_selector("a:has-text('http')")
                        if homepage_element:
                            homepage_url = await homepage_element.get_attribute('href')
                    except Exception as e:
                        print(f"Error finding homepage URL: {e}")

                    results.append({
                        'text': link["text"], 
                        'url': link["url"], 
                        'description': description, 
                        'homepage_url': homepage_url
                    })
                    print(f"Scraped: {link['text']} - {link['url']} - {description} - {homepage_url}")
                except Exception as e:
                    print(f"Error extracting content for {link['url']}: {e}")
        except Exception as e:
            print(f"Error visiting link: {e}")

    return results

async def has_next_page(page):
    """Check if the 'Next' button exists and is enabled."""
    next_button = await page.query_selector('a#nextButton')  # Change the selector as per actual site
    if next_button:
        is_disabled = await next_button.get_attribute('aria-disabled')
        return is_disabled != 'true'
    return False

async def go_to_next_page(page):
    """Click the 'Next' button to go to the next page."""
    await page.click('a#nextButton')  # Change the selector as per actual site
    await page.wait_for_load_state('networkidle')

async def scrape_website(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"Attempting to access {url}")
        await page.goto(url)
        
        all_results = []
        
        # Continue to scrape while there are more pages
        while True:
            print("Scraping page...")
            page_results = await scrape_page(page)
            all_results.extend(page_results)
            
            if not await has_next_page(page):
                break
            await go_to_next_page(page)
            print("Moved to next page.")

        await browser.close()
        return all_results

async def main():
    base_url = "https://www.adrevu.com/index.php?id=2"
    scraped_data = await scrape_website(base_url)

    with open('scraped_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['text', 'url', 'description', 'homepage_url'])
        writer.writeheader()
        writer.writerows(scraped_data)

    print("Scraping completed. Data saved to scraped_data.csv")

if __name__ == "__main__":
    asyncio.run(main())
