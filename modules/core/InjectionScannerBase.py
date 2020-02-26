import re
import requests

from datetime import datetime
from functools import partial
from multiprocessing import Pool

from util_functions import success, warning, info
from util_functions import http_get_request, http_post_request

# TODO: make sure that modules that depend on previous results handle the lack
#       of those results graciously

class InjectionScannerBase:
    """ this is a base class used to provide common functionality to all
        injection scanner modules. should be inherited.
    """

    # should not be imported directly, only inherited
    # __wavs_mod__ = True

    info = {}

    def _create_db_table(self):
        """ used to create database table needed to store results for this
            module. should be overwritten to meet this modules storage needs
        """
        # override this
        pass


    def _load_scan_results(self):
        """ loads in results from previous scans, should be overwritten to load
            in specific results needed for this module
        """
        # load directories from database, results are a list of tuples
        inject_params = self.main.db.load_scan_results(self.main.id,
                                                       'method, action, parameter',
                                                       'parameters_discovered')
        return inject_params

    def _save_scan_results(self, results):
        # override this
        pass

    def _construct_get_url(self, page, params):
        url = f'{self.main.get_host_url_base()}/{page}?'

        # http://localhost:80/index.php?username=test&password=test&submit=submit

        for param in params:
            url += f'{param}=test&'

        # remove the last &
        url = url[:-1]

        return url

    def _construct_post_params(self, params):
        param_dict = {}
        for p in params:
            param_dict[p] = 'test'

        return param_dict

    def _check_page_content(self, param, page, page_text):
        assert(hasattr(self, "re_search_strings"))

        search_strings = self.re_search_strings

        if any([re.search(s, page_text) for s in search_strings]):
            if not (page, param) in self.injectable_params:
                if self.main.options['verbose']:
                    success(f'Vulnerable parameter: {page}/{param}', prepend='  ')
                self.injectable_params.append((page, param))

            return True

        return False


    def _run_thread(self, param):
        method = param[0]
        page = param[1]

        self.injectable_params = []
        inject_params = param[2].split(', ')

        assert(hasattr(self, "attack_strings"))
        attack_strings = self.attack_strings

        if method == 'GET':
            url = self._construct_get_url(page, inject_params)

            for p in inject_params:
                for injection in attack_strings:
                    final_url = url.replace(f'{p}=test', f'{p}={injection}')

                    resp = http_get_request(final_url, self.main.cookies)
                    self._check_page_content(p, page, resp.text)

        elif method == 'POST':
            # construct the url to make the request to
            url = f'{self.main.get_host_url_base()}/{page}'

            for p in inject_params:
                params = self._construct_post_params(inject_params)

                for injection in attack_strings:
                    params[p] = injection

                    resp = http_post_request(url, params, self.main.cookies)
                    if self._check_page_content(p, page, resp.text):
                        break

        return self.injectable_params


    def run_module(self):
        """
            need to set self.attack_strings and self.re_search_strings
        """
        # override this

        pass