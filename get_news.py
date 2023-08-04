import feedparser
import qrcode

def read_rss_feed(rss_url):
    feed = feedparser.parse(rss_url)
    rss_items = feed['items']
    news = []
    for item in rss_items:
        news.append(item['title'])
        news.append(item['link'])  
    return news

rss_url = "https://partner-feeds.beta.20min.ch/rss/20minuten"

news = read_rss_feed(rss_url)

qr = qrcode.QRCode(version=1, box_size=2, border=1)
qr.add_data(news[1])
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
qr_code_file = "newsqr.png"
img.save(qr_code_file)

print(news[0])