#!/usr/bin/env python3

import requests
from pyquery import PyQuery as pq
import sys
import shutil
from os.path import basename

chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36';

req_hdrs = {
    'User-Agent': chrome_ua,
    'Referer': 'http://www.waybig.com/blog/'
}


proxies = { 'http': 'http://localhost:7070' }

def main():

    url=sys.argv[1]
    print("PostUrl: \n", url)

    page = requests.get(url, req_hdrs, proxies=proxies)
    content = page.content
    # with open('/tmp/men.html') as f:
    #     content = f.read()

    doc = pq(content)

    title = doc('.entry-title').text()

    coverimg = doc('.entry-content img:first').attr('src')

    print("Title: \n", title)
    #print("Coverimg Url:\n", coverimg)
    # print(" ---download coverimg")
    imgresp = requests.get(coverimg, req_hdrs , proxies=proxies, stream=True)
    text = upload(coverimg, imgresp.raw)

    print("BB Code:\n", text)

def upload(url, file_obj):
    # print(" ---post coverimg")
    imgbamresp = requests.post('http://www.imagebam.com/sys/upload/save',
        {
            'content_type': '1',
            'thumb_size':'350',
            'thumb_aspect_ratio':'resize',
            'thumb_file_type': 'jpg',
            'gallery_options': '0',
            'gallery_title':'',
            'gallery_description':'',
            'gallery_existing':'',
        },
    headers = {
        'User-Agent': chrome_ua,
        'Referer': 'http://www.imagebam.com/basic-upload',
        'Cookie': 'IBsession=621396e45175fcf796ab80543eb92a09;' 
    },
        proxies=proxies,
        files = [
            ('file[]', (basename(url), file_obj)),
        ]);

    # print(imgbamresp.content)
    # import pdb; pdb.set_trace()
    doc = pq(imgbamresp.content)
    text = doc('table textarea:first').text()

    return text

if __name__ == '__main__':
    main()
