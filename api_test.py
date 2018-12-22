import requests
import os
def main():
    api_request = requests.get("https://www.goodreads.com/book/review_counts.json",
                               params={'key': os.getenv('GOODREADS_DEV_KEY'), 'isbns': '0380795272', 'format': 'json'})
    if api_request.status_code != 200:
        raise Exception("ERROR: API request unsuccessful")
    goodreads_data = api_request.json()
    print(goodreads_data['books'])


if __name__ == "__main__":
    main()