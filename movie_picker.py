import asyncio
import concurrent.futures
import random
import sys
import webbrowser

import bs4
import pyttsx3
import requests

IMDB_URL = 'https://www.imdb.com/'
TOP_FILMS = IMDB_URL + 'chart/top'
TOP_SHOWS = IMDB_URL + 'chart/toptv'
TOP_FILMS_BY_GENRE = IMDB_URL + 'search/title?genres={genres}&' \
                                'sort=user_rating,desc&' \
                                'title_type=feature&' \
                                'num_votes=25000,&' \
                                'page={page}&' \
                                'ref_=adv_nxt'


class MoviePicker:
    """
    Implements methods of randomly picking top rated movie with/without(+tv-shows) genre
    (in async/sync way) from IMDB site
    """

    def pick_random_film_or_show(self, type):
        print('Do you feel lucky today? :)')
        print('Loading...')
        if type == 'movie':
            requested_url = TOP_FILMS
        else:
            requested_url = TOP_SHOWS
        top_chart = requests.get(requested_url)
        top_chart.raise_for_status()
        elements = bs4.BeautifulSoup(top_chart.text, 'lxml').select('.titleColumn a')
        print('Choosing from {} results...'.format(len(elements)))
        random_element = random.choice(elements)
        webbrowser.open(IMDB_URL + random_element.get('href'))
        self.say_text(random_element.text)

    async def pick_random_film_by_genre(self, genre):
        print("Loading...")
        pages = self.get_page_quantity(genre)

        result = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=pages) as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(
                    executor,
                    requests.get,
                    TOP_FILMS_BY_GENRE.format(genres=genre, page=str(page)))
                for page in range(pages)
            ]
            for top_films_by_genre in await asyncio.gather(*futures):
                top_films_by_genre.raise_for_status()
                films_per_page = bs4.BeautifulSoup(top_films_by_genre.text, 'lxml').select('.lister-item-header a')
                if not films_per_page:
                    break
                result.append(films_per_page)
            random_film = random.choice(random.choice(result))
            webbrowser.open(IMDB_URL + random_film.get('href'))
            self.say_text(random_film.text)

    @staticmethod
    def get_page_quantity(genre):
        # get the number of result's pages
        req = requests.get(TOP_FILMS_BY_GENRE.format(genres=genre, page=1))
        req.raise_for_status()
        try:
            pages_number = bs4.BeautifulSoup(req.text, 'lxml').select('.desc')[0]
            # have to remove redundant spaces
            formatted_res = ' '.join(pages_number.text.split())
            number = formatted_res.split()[4]
            if ',' in number:
                number = number.replace(',', '')
            print('Choosing from {} results...'.format(str(number)))
            # as each page has 50 movies
            return round(int(number) / 50)
        except IndexError:
            print('There is no results found.')

    @staticmethod
    def say_text(film_name):
        engine = pyttsx3.init()
        engine.say("Looks like you're going to watch {} today.".format(film_name))
        engine.runAndWait()


if __name__ == '__main__':
    try:
        if sys.argv[1] == 'random' and (sys.argv[2] == 'movie' or 'tv-show'):
            MoviePicker().pick_random_film_or_show(sys.argv[2])
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(MoviePicker().pick_random_film_by_genre(sys.argv[1]))
    except IndexError:
        print('You need to specify an argument!')
