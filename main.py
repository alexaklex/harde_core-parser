import requests
from bs4 import BeautifulSoup
import csv
import re
import config

class AvitoParser:

    count = 0

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)',
            'Accept-Language': 'ru' ,
        }
        #Создаем начальный заголовок
        self.get_title_csv()

    def get_html(self, url, useragent=None, proxy=None):
        r = self.session.get(url, headers=useragent, proxies=proxy)
        # r = self.session.get(url)
        # print(r.text)
        return r.text

    #получаем данные из страницы
    def soup_function(self, url, tag=None):
        useragent = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)'}
        proxy = {'http': 'http://140.238.15.65:3128'}
        block = self.get_html(url, useragent, proxy)
        soup = BeautifulSoup(block, 'lxml')
        container = soup.select(tag)
        return container

    #Удаляем дубли ссылок карточек, которые подтягиваются из доп. атрибута img
    def del_dubl(self, cartchki):
        x = []
        [x.append(item.get('href')) for item in cartchki]

        r = [x[0]]
        i = 1
        j = 0
        while i < len(x):
            if r[j] != x[i]:
                r.append(x[i])
                j += 1
            i += 1

        return r

    #Вытаскиваеи данные из карточки товара(Title, price и прочее)
    #Проходим по полученным ссылкам на карточку и вытаскиваем значение
    def product_info(self, cartchki, category, podcategory):

        #Удаляем дубли
        cartchki = self.del_dubl(cartchki)

        for item in cartchki:
            print(self.count)
            block = self.soup_function(item, 'div.product.type-product.status-publish')[0]

            if block:
                    try:
                        title = block.select('h1.product_title.entry-title')[0].string.strip()
                        print(title)
                    except:
                        title = ''

                    try:

                        #Если в карточке в дескрипшоне есть список
                        if block.select('div ul'):
                            data = []
                            descr_size = block.select('div.woocommerce-product-details__short-description p')[0].string.strip()
                            ul = block.select('li')

                            if descr_size == 'Размеры шпильки:' or descr_size == 'Размеры:':
                                # data.append(descr_size)
                                lenght_full = block.select('li')[0].string.strip()
                                lenght = re.findall(r'\d+', lenght_full)[0]
                                width_full = block.select('li')[1].string.strip()
                                width = re.findall(r'\d+', width_full)[0]
                                descr_main = ''

                            elif len(ul) < 2 or len(ul) > 2:
                                for r in range(len(ul)):
                                    u = ul[r].text.strip()
                                    data.append(u)
                                # С помощью джойн мы взяли массив и превратили его в строку, после каждого элемента идет перенос каретки
                                descr_main = '\n'.join(data)

                            else:
                                print("в дескрипшине ничего")

                            descr = block.select('div.woocommerce-product-details__short-description p')[1].text.strip()
                            # print(descr_main)
                        else:
                            descr_main = ''
                            lenght = ''
                            width = ''
                            descr = block.select('div.woocommerce-product-details__short-description p')[0].string.strip()
                            print(descr)
                    except:
                         descr = ''
                         print("jopa")


                    try:
                        featured_image = block.select('img.attachment-shop_single')[0].get('src')
                        print(featured_image)
                    except:
                        featured_image = ''
                    try:
                        gallery = []
                        img_gallery_massiv = block.select('div.woocommerce-product-gallery__image')

                        if len(img_gallery_massiv) > 1:
                            for i in img_gallery_massiv:
                                if img_gallery_massiv[0] == i:
                                    continue
                                p_gallery = i.get('data-thumb')
                                gallery.append(p_gallery)
                                product_gallery = '|'.join(gallery)
                                print(product_gallery)
                        else:
                            product_gallery = ''
                    except:
                        product_gallery = ''
                    try:
                        if block.select('span.woocommerce-Price-amount.amount')[0].string.strip():
                            price_text = block.select('span.woocommerce-Price-amount.amount')[0].string.strip()
                            price = re.findall(r'\d+', price_text)[0]
                            print(price)
                        elif block.select('div.wl-price-complect__price span')[0].string.strip():
                            price = block.select('div.wl-price-complect__price span')[0].string.strip()
                            print(price)

                    except:
                        price = ''

                    self.count = self.count + 1
                    print("_______________________")
                    #Делаем проверку если у нас есть подкатегории
                    if podcategory != '':
                        cat = category + '>' + podcategory
                    else:
                        cat = category

                    data_csv = {
                        'category': cat,
                        'sku': self.count,
                        'post_title': title,
                        'post_content': descr,
                        'regular_price': price,
                        'post_status': 'publish',
                        # 'post_content2': descr_main,
                        'lenght': lenght,
                        'width': width,
                        'featured_image': featured_image,
                        'product_gallery': product_gallery,
                    }
                    self.write_csv(data_csv)

    def total_page(self, nav):
        return  nav[0].select('a.page-numbers')[-2].string.strip()

    #Начало пути
    #Итерация по полученным ссылкам с главной страницы
    def link_iteration(self, container):
        # for item in container:
        #     link = self.parse_block(item)
            # return
        for i in range(1,2):
            link = self.parse_block(container[i])


    def parse_block(self, item):
        #Вытаскиваем заголовок главной категории
        try:
            title_block= item.select_one('h2.woocommerce-loop-category__title')
            title_category = title_block.string.strip()
        except:
            title_category = ''


        #Вытаскиваем ссылку
        url_block = item.select_one('a')

        if url_block:
            #Вытаскиваем атрибут href
            href = url_block.get('href')
            if href:
                url = href
                # print(url)
                #делаем переход в подкатегорию
                # block = self.get_html(url)
                #Ссылки на подкатегории
                cartchki_link = self.soup_function(url, 'li.product.type-product.status-publish a')

                # Если сразу появляются карточки товаров из основной категории
                if cartchki_link:
                    title_podcat = 'нет'
                    self.product_info(cartchki_link, title_category, title_podcat)

                #Если у нас есть подкатегории
                else:
                    podcategory = self.soup_function(url, 'li.product-category.product a')
                    # для теста, вы таскиваем определенную подкатегорию
                    #_________________________________________________________________________________________
                    lenght = len(podcategory)

                    for i in range(lenght):
                        p = podcategory[i]
                        link_podcat = p.get('href')
                        try:
                            self.title_podcat = p.select('h2.woocommerce-loop-category__title')[0].string.strip()
                            print(self.title_podcat)
                        except:
                            self.title_podcat = ''
                    #____________________________________________________________________________________________

                    # [print(x) for x in podcategory]

                    #Основная
                    # for p in podcategory:
                    #     link_podcat = p.get('href')
                    #     try:
                    #         self.title_podcat = p.select('h2.woocommerce-loop-category__title')[0].string.strip()
                    #         print(self.title_podcat)
                    #     except:
                    #         self.title_podcat = ''

                        # Проверяем если в подкатегории навигация
                        navigation = self.soup_function(link_podcat, 'nav.woocommerce-pagination')
                        if navigation:
                            # Получаем количество страниц подкатегории
                            total_page = self.total_page(navigation)
                            print(total_page)
                            # count = 0
                            for i in range(int(total_page)):
                                print(i, "Страница")
                                #Получаем ссылки карточек из подкатегории
                                cartchki_link = self.soup_function(link_podcat +'page/' + str(i), 'li.product.type-product.status-publish a')

                                if cartchki_link:
                                    self.product_info(cartchki_link, title_category, self.title_podcat)
                                # count = count + 1
                        else:
                            #Если навигации нет
                            cartchki_link = self.soup_function(link_podcat, 'li.product.type-product.status-publish a')
                            if cartchki_link:
                                self.product_info(cartchki_link, title_category, self.title_podcat)
            else:
                url = None

    #Записывает данные в файл csv
    def write_csv(self, data):
        with open('alex.csv', 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow((
                data['category'],
                data['sku'],
                data['post_title'],
                data['post_content'],
                data['lenght'],
                data['width'],
                data['regular_price'],
                data['post_status'],
                data['featured_image'],
                data['product_gallery']
            ))

    # Функция начального создание title
    def get_title_csv(self):
            data = {
                    'category': 'category',
                    'podcategory': 'podcategory',
                    'sku': 'sku',
                    'post_title': 'post_title',
                    'post_content': 'post_content',
                    'lenght': 'lenght',
                    'width': 'width',
                    'regular_price': 'regular_price',
                    'post_status': 'post_status',
                    'featured_image': 'featured_image',
                    'product_gallery': 'product_gallery',

                    }

            with open('alex.csv', 'a', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    (
                    data['category'],
                    data['sku'],
                    data['post_title'],
                    data['post_content'],
                    data['lenght'],
                    data['width'],
                    data['regular_price'],
                    data['post_status'],
                    data['featured_image'],
                    data['product_gallery'])
                )

    def get_blocks(self):
        #Название сайта который парсим, подключаем с помощь вспомогательного файла конфиг
        url = config.site
        container = self.soup_function(url, 'li.product-category.product')
        self.link_iteration(container)


def main():
    p = AvitoParser()
    p.get_blocks()


if __name__ == '__main__':
    main()