import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse

def fetch_page(url):
    """
    Fetch the HTML content of a given URL using a GET request.
    
    Args:
        url (str): The URL of the page to fetch.
    
    Returns:
        BeautifulSoup: Parsed HTML content of the page.
    
    Raises:
        Exception: If the page cannot be fetched (e.g., network error or invalid URL).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        raise Exception(f"Failed to fetch page: {url}")

def extract_movies(soup):
    """
    Extract movie details (year, title, URL) from a parsed watchlist page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content of the page.
    
    Returns:
        list: List of dictionaries containing movie details.
    """
    movies = []
    for poster in soup.find_all('div', class_='film-poster'):
        img = poster.find('img')
        if img and 'alt' in img.attrs:
            alt_text = img['alt']
            if alt_text.startswith("Poster for "):
                title = alt_text[len("Poster for "):].strip()
            else:
                title = alt_text.strip()
        else:
            title = ''
        link = poster.get('data-target-link', '')
        if link:
            url = 'https://letterboxd.com' + link
            # Extract year from slug
            slug = link.strip('/').split('/')[-1]
            slug_parts = slug.split('-')
            if slug_parts and slug_parts[-1].isdigit() and len(slug_parts[-1]) == 4:
                year = slug_parts[-1]
            else:
                year = ''
        else:
            url = ''
            year = ''
        movies.append({'year': year, 'title': title, 'url': url})
    return movies

def get_total_pages(soup):
    """
    Determine the total number of pages in the watchlist from pagination links.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content of the first page.
    
    Returns:
        int: Total number of pages (defaults to 1 if no pagination is found).
    """
    pagination = soup.find('div', class_='pagination')
    if pagination:
        page_links = pagination.find_all('a')
        page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]
        return max(page_numbers) if page_numbers else 1
    return 1

def main():
    """
    Main function to export a Letterboxd watchlist (including filtered views) to a CSV file.
    - Takes a full watchlist URL as input.
    - Fetches all pages of the watchlist.
    - Extracts movie details (year, title, URL).
    - Saves them to a CSV file with a filename based on the username and filters.
    """
    watchlist_url = input("Enter Letterboxd watchlist URL: ").strip()
    if not watchlist_url:
        print("No URL provided.")
        return
    
    # Validate and parse the URL
    parsed_url = urlparse(watchlist_url)
    if parsed_url.netloc != 'letterboxd.com':
        print("Invalid URL: not a letterboxd.com URL")
        return
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) < 2 or path_parts[1] != 'watchlist':
        print("Invalid watchlist URL: does not contain '/watchlist/'")
        return
    
    # Extract username and filter parts for the filename
    username = path_parts[0]
    filter_parts = path_parts[2:]
    filter_str = '_'.join(filter_parts) if filter_parts else ''
    if not watchlist_url.endswith('/'):
        watchlist_url += '/'
    output_file = f"{username}_watchlist_{filter_str}.csv" if filter_str else f"{username}_watchlist.csv"

    try:
        # Fetch and parse the first page
        first_page = fetch_page(watchlist_url)
        total_pages = get_total_pages(first_page)
        all_movies = []
        
        # Iterate through all pages
        for page in range(1, total_pages + 1):
            if page > 1:
                page_url = f"{watchlist_url}page/{page}/"
                soup = fetch_page(page_url)
            else:
                soup = first_page
            movies = extract_movies(soup)
            all_movies.extend(movies)
            print(f"Fetched page {page}/{total_pages}")
        
        # Export to CSV with specified order: year, title, url
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['year', 'title', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for movie in all_movies:
                writer.writerow(movie)
        
        print(f"Exported {len(all_movies)} movies to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
