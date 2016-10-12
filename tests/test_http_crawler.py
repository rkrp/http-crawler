from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
from multiprocessing import Process

import http_crawler


serving = False


def serve():
    global serving

    if serving:
        return

    serving = True

    class HTTPHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('/')
            if path[-2] == 'redirect-old-path':
                path[-2] = 'redirect-new-path'
                newpath = '/'.join(path)
                self.send_response(301)
                self.send_header('Location', newpath)
                self.send_header('content-type', 'text/html')
                self.end_headers()
            else:
                return super(HTTPHandler, self).do_GET()

    def _serve(dir, port):
        base_dir = os.path.join('tests', dir)
        os.chdir(base_dir)
        server = HTTPServer(('', port), HTTPHandler)
        server.serve_forever()

    Process(target=_serve, args=('site', 8000), daemon=True).start()
    Process(target=_serve, args=('external-site', 8001), daemon=True).start()
    Process(target=_serve, args=('redirect-site', 8002), daemon=True).start()


def test_crawl():
    serve()

    rsps = list(http_crawler.crawl('http://localhost:8000/'))

    assert len(rsps) == 13

    urls = [rsp.url for rsp in rsps]

    assert len(urls) == len(set(urls))
    assert set(urls) == {
        'http://localhost:8000/',
        'http://localhost:8000/pages/page-1/',
        'http://localhost:8000/pages/page-2/',
        'http://localhost:8000/pages/page-3/',
        'http://localhost:8000/assets/styles.css',
        'http://localhost:8000/assets/styles-2.css',
        'http://localhost:8000/assets/image.jpg',
        'http://localhost:8000/assets/script.js',
        'http://localhost:8000/assets/tile-1.jpg',
        'http://localhost:8000/assets/tile-2.jpg',
        'http://localhost:8000/assets/somefont.eot',
        'http://localhost:8000/assets/somefont.ttf',
        'http://localhost:8001/pages/page-1/',
    }


def test_crawl_follow_external_links_false():
    serve()

    rsps = list(http_crawler.crawl('http://localhost:8000/',
                follow_external_links=False))

    assert len(rsps) == 12

    urls = [rsp.url for rsp in rsps]

    assert len(urls) == len(set(urls))
    assert set(urls) == {
        'http://localhost:8000/',
        'http://localhost:8000/pages/page-1/',
        'http://localhost:8000/pages/page-2/',
        'http://localhost:8000/pages/page-3/',
        'http://localhost:8000/assets/styles.css',
        'http://localhost:8000/assets/styles-2.css',
        'http://localhost:8000/assets/image.jpg',
        'http://localhost:8000/assets/script.js',
        'http://localhost:8000/assets/tile-1.jpg',
        'http://localhost:8000/assets/tile-2.jpg',
        'http://localhost:8000/assets/somefont.eot',
        'http://localhost:8000/assets/somefont.ttf',
    }


def test_extract_urls_from_html():
    with open(os.path.join('tests', 'site', 'index.html')) as f:
        content = f.read()

    urls = http_crawler.extract_urls_from_html(content)

    assert len(urls) == 8
    assert set(urls) == {
        '/',
        'http://localhost:8000/pages/page-1',
        'http://localhost:8001/pages/page-1',
        '/pages/page-2',
        'pages/page-3',
        '/assets/styles.css',
        '/assets/image.jpg',
        '/assets/script.js',
    }


def test_extract_urls_from_css():
    with open(os.path.join('tests', 'site', 'assets', 'styles.css')) as f:
        content = f.read()

    urls = http_crawler.extract_urls_from_css(content)

    assert len(urls) == 5
    assert set(urls) == {
        '/assets/styles-2.css',
        '/assets/tile-1.jpg',
        '/assets/somefont.eot',
        '/assets/somefont.ttf',
    }


def test_with_redirect():
    serve()

    rsps = list(http_crawler.crawl('http://localhost:8002/'))
    actual_urls = set([resp.url for resp in rsps])
    expected_urls = set([
        'http://localhost:8002/',
        'http://localhost:8002/redirect-new-path/page-2.html',
        'http://localhost:8002/redirect-new-path/page-1.html'
    ])

    assert actual_urls == expected_urls


def test_without_redirect():
    serve()

    rsps = list(http_crawler.crawl('http://localhost:8002/',
                                   follow_redirects=False))
    actual_urls = set([resp.url for resp in rsps])
    expected_urls = set([
        'http://localhost:8002/',
    ])

    assert actual_urls == expected_urls
