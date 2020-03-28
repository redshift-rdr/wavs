from modules.core.BaseModule import BaseModule
from bs4 import BeautifulSoup

from util_functions import success, info
from util_functions import http_get_request
from utils.InterceptingProxy import InterceptingProxy


class Crawler(BaseModule):
    info = {
        "name": "Site Crawler",
        "db_table_name": "files_discovered",
        "reportable": False,
        "desc": "Crawls through links to find new pages",
        "author": "@ryan_ritchie"
    }

    def __init__(self, main):
        BaseModule.__init__(self, main)

    def _parse_link(self, page, link):
        # remove blanks and param links
        if not link or link[0] == '?':
            return

        # ignore relative paths
        if '../' in link:
            return

        # references to same page
        if link in ['#', '.']:
            link = page

        if not any(x in link for x in ['http://', 'https://']):
            if '?' in link:
                # get page from href
                linked_page = link.split('?')[0]
            else:
                linked_page = link

            if linked_page in self.main.restrict_paths:
                return

            # check that the page actually exists first
            url = f'{self.main.get_host_url_base()}/{linked_page}'
            page_exists = http_get_request(url, self.main.cookies).status_code
            if page_exists in self.main.success_codes:
                return linked_page

    def _parse_links(self, page):
        # get the html
        url = f'{self.main.get_host_url_base()}/{page}'
        html = http_get_request(url, self.main.cookies).text

        # look for params to inject into
        soup = BeautifulSoup(html, 'html.parser')

        return_links = []

        # parse all hyperlinks
        for link in soup.find_all('a'):
            href = link.get('href')
            parsed_href = self._parse_link(page, href)

            if parsed_href:
                return_links.append(parsed_href)

        # parse all forms
        for form in soup.find_all('form'):
            action = form.get('action')
            parsed_action = self._parse_link(page, action)

            if parsed_action:
                return_links.append(parsed_action)

        return return_links

    def proxy_response_handle(self, resp, path):
        if resp.status_code in self.main.success_codes:
            if '?' in path:
                path = path.split('?')[0]

            # if '/' in path:
            #     path = path.replace('/', '')

            if path not in self.manual_found_pages:
                self.manual_found_pages.append(path)
                # success(f'Found new page: {path}', prepend='    ')

    def run_module(self):
        info('Crawling links...')

        # get found pages
        self.found_pages = self._get_previous_results('FileScanner')

        if self.main.options['manual_crawl']:
            self.manual_found_pages = self.found_pages
            proxy_port = self.main.options['proxy_port']

            # TODO: make config variable for port
            info(f'Proxy server started on http://127.0.0.1:{proxy_port}',
                 prepend='  ')
            info('Use browser to crawl target. CTRL+C to exit.',
                 prepend='  ')

            proxy = InterceptingProxy(self.main.host, proxy_port, self)
            proxy.start()

            self._save_scan_results(self.manual_found_pages)
        else:
            # loop through all pages found so far
            loop_pages = self.found_pages
            for page in loop_pages:
                for link in self._parse_links(page):
                    if link not in loop_pages:
                        success(f'Found page: {link}', prepend='  ')
                        loop_pages.append(link)

            self._save_scan_results(loop_pages, update_count=False)
