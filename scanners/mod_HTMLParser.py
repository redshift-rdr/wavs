from multiprocessing import Pool
from bs4 import BeautifulSoup

from datetime import datetime
from utils import success, warning, info
from utils import http_get_request

class HTMLParser:
    __wavs_mod__ = True

    info = {
        "name": "HTML Parser",
        "desc": "Takes a webpage and parses the HTML to find params to inject",
        "author": "@ryan_ritchie"
    }

    def __init__(self, main, options=None):
        self.main = main

        self.options = {
            # the number of threads the directory scanner should use
            "numberOfThreads": 8,
            "verbosity": 1
        }

    def _extract_link_params(self, link):
        assert('?' in link)

        action, params = link.split('?')

        stored_params = []
        for param in params.split('&'):
            stored_params.append(param.split('=')[0])

        final_params = [{'method': 'GET', 'action': action, 'param': p} for p in stored_params]

        return final_params

    def _extract_links(self, html):
        """ extract anchor links out of html data

            :param html:        a beautiful soup html object
            :return (list):     a list of links found in the html
        """
        links = []

        # loop through all the anchor tags
        for link in html.find_all('a'):
            # we only want links with parameters in
            if not '?' in link.get('href'):
                continue

            # we assume if it is an absolute path it is external and ignore it
            if any(x in link.get('href') for x in ['http://', 'https://']):
                continue

            # extract the parameters from the link
            links.extend(self._extract_link_params(link.get('href')))

        return links

    def _extract_form_params(self, form, field):
        ''' from an html form, build param data

            :param form:        a beautiful soup form object
            :param field:       a beautiful soup field object
            :return (dict):     a dictionary with param data
        '''

        action = form.get('action')
        method = form.get('method')

        if not action:
            return None

        if any(x in action for x in ['http://', 'https://']):
            return None

        return {'method': method, 'action': action, 'param': field.get('name')}

    def _extract_forms(self, html):
        """ extract params from html forms

            :param html:        a beautiful soup html object
            :return (list):     a list of params found in the html
        """

        form_params = []
        for form in html.find_all('form'):
            for field in form:
                if field.name == 'input' and field.get('type') != 'submit':
                    form_params.append(self._extract_form_params(form, field))

        return form_params

    def _run_thread(self, webpage):
        """ runs in a thread. parses a webpage's html for form and links, then
            extracts parameters to inject attacks into

            :param webpage:         a beautiful soup html parser object
            :return (list):         a list of dictionaries containing params
        """
        # get the html
        url = f'http://{self.main.host}:{self.main.port}/{webpage}'
        html = http_get_request(url).text

        # look for params to inject into
        soup = BeautifulSoup(html, 'html.parser')

        params = []
        params.extend(self._extract_links(soup))
        params.extend(self._extract_forms(soup))

        return params

    def run_module(self):
        """ the entrypoint into the module.

            takes any found webpages and uses threads to extract params from
            the html.
        """
        start_time = datetime.now()
        info('Starting param parsing at {}'.format(datetime.strftime(start_time,
                                                    '%d/%b/%Y %H:%M:%S')))

        # get the list of found pages
        found_pages = self.main.scan_results['files_found']

        # if there are no found pages, theres no need to run this module
        if not found_pages:
            return

        # pass the found pages to threads
        pool = Pool(self.options['numberOfThreads'])
        found_params = pool.map(self._run_thread, found_pages)

        # close the threads
        thread_pool.close()
        thread_pool.join()

        # clean up the results from the threads
        final = []
        found_params = [final.extend(p) for p in found_params if p]

        if self.options['verbosity']:
            for param in final:
                success(f'Found injectable param: {param["action"]}/{param["param"]}')

        self.main.scan_results['params_found'] = final

        end_time = datetime.now()
        info('Param parsing completed. Elapsed: {}'.format(end_time - start_time))