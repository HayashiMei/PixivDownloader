import requests, re, os, zipfile, time, random, html
from bs4 import BeautifulSoup
from config import read_config

s = requests.Session()

account = read_config.account
password = read_config.password

class Pixiv:
    def __init__(self, save_path, artistId):
        self.baseUrl = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        self.LoginUrl = 'https://accounts.pixiv.net/api/login?lang=zh'
        self.firstPageUrl = 'https://www.pixiv.net/member_illust.php?id=' + artistId
        self.loginHeader = {
            'origin':
            'https://accounts.pixiv.net',
            'user-agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
            'referer':
            'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'content-type':
            'application/x-www-form-urlencoded',
            'connection':
            'keep-alive'
        }
        self.return_to = 'http://www.pixiv.net/'
        self.pixiv_id = account,
        self.password = password
        self.postKey = []
        self.save_path = save_path

    # 模拟登陆并返回登陆后跳转的第一个页面
    def login(self):
        loginHtml = s.get(self.baseUrl).text
        self.postKey = self.parser(loginHtml).find(
            'input', attrs={'name': 'post_key'})['value']

        loginData = {
            'pixiv_id': self.pixiv_id,
            'password': self.password,
            'post_key': self.postKey,
            'ref': 'wwwtop_accounts_index',
            'return_to': self.return_to
        }
        s.post(self.LoginUrl, data=loginData, headers=self.loginHeader)
        firstPageHtml = s.get(self.firstPageUrl)
        return firstPageHtml.text

    def getImgDetailPage(self, pageHtml):
        pattern = re.compile(
            '<li class="image-item.*?<a href="(.*?)".*?class="work  _work.*?</a>',
            re.S)
        imgPageUrls = re.findall(pattern, pageHtml)
        return imgPageUrls

    # 通过url获取页面
    def getPageWithUrl(self, url):
        header = {
            'accept-language':
            'zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,en-US;q=0.5',
            'user-agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        }
        return s.get(url, headers=header).text

    # 下载单张图片
    def getImg(self, pageUrls):
        for pageUrl in pageUrls:
            wholePageUrl = 'http://www.pixiv.net' + str(pageUrl)
            pageHtml = self.getPageWithUrl(wholePageUrl)

            bs = self.parser(pageHtml)
            result = bs.find(attrs={'class': '_illust_modal'})

            #如果这个页面只有一张图片，那就返回那张图片的url和名字，如果是多张图片 那就找不到返回none
            if (result):
                img = result.find('img')
                imgTitle = self.validateTitle(img['alt'])
                imgSourceUrl = img['data-src']
                self.info(u'这个地址只有1张图片，地址：' + html.unescape(wholePageUrl))
                self.info(u'正在获取图片......')
                self.info(u'文件名 : ' + imgTitle)
                self.info(u'源地址：' + imgSourceUrl)
                self.getBigImg(imgSourceUrl, wholePageUrl, imgTitle,
                               self.save_path)
                self.info(
                    u'######################################################')
            elif bs.find(attrs={'class': 'player toggle'}):
                urlPattern = re.compile(
                    '<meta property="og:image" content="https://i.pximg.net/c/150x150/img-master/img/(.*?)_master1200.jpg">',
                    re.S)
                urlResult = re.findall(urlPattern, pageHtml)
                nameResult = bs.find(
                    'section', attrs={
                        'class': 'work-info'
                    }).find(
                        'h1', attrs={
                            'class': 'title'
                        }).text
                self.getCanvasImg(urlResult[0], wholePageUrl, nameResult)
            else:
                self.getMultipleImg(wholePageUrl)

    #下载指定url的图片
    def getBigImg(self, sourceUrl, referer, name, path):
        header = {
            'Referer':
            referer,
            'user-agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        }
        urlArr = sourceUrl.split('.')
        suffix = '.' + urlArr[len(urlArr) - 1]
        imgExist = os.path.exists(path + '/' + name + suffix)
        if not imgExist:
            img = s.get(sourceUrl, headers=header)
            with open(name + suffix, 'wb') as f:
                f.write(img.content)
            self.nap()
        else:
            self.info('图片已存在，跳过！')

    # 下载多张图片
    def getMultipleImg(self, wholePageUrl):
        imgAlmostSourceUrl = str(wholePageUrl).replace('medium', 'manga')
        pageHtml = self.getPageWithUrl(imgAlmostSourceUrl)
        bs = self.parser(pageHtml)
        totalNum = bs.find('span', attrs={'class': 'total'}).text
        if (totalNum):
            self.info(u'这个地址含有' + html.unescape(totalNum) + u'张图片，转换后的地址：' +
                      str(imgAlmostSourceUrl))

            urls = bs.find_all(
                attrs={'class': 'full-size-container _ui-tooltip'})
            imgTitle = self.validateTitle(bs.find('title').text)

            # 将图片存到单独的文件夹中
            self.mkdir(self.save_path, imgTitle)
            for index, item in enumerate(urls):
                fullImageHtml = self.getPageWithUrl(
                    'https://www.pixiv.net' + item['href'])
                fullImageResult = self.parser(fullImageHtml).find('img')['src']
                fileName = str(index).zfill(6)

                self.info(u'正在获取第' + str(index + 1) + u'张图片......')
                self.info(u'文件名: ' + fileName)
                self.info(u'源地址：' + fullImageResult)

                self.getBigImg(fullImageResult, wholePageUrl, fileName,
                               self.save_path + '/' + imgTitle)

            # 返回到上一级目录
            os.chdir(self.save_path)

        self.info(u'这个地址的图片下完啦!')
        self.info('######################################################')

    def download(self, memberIllustHtml):
        imgPageUrls = self.getImgDetailPage(memberIllustHtml)
        self.getImg(imgPageUrls)

        btnNext = self.parser(memberIllustHtml).find(attrs={'rel': 'next'})
        if btnNext:
            self.info(u'前往下一页...')
            self.info('######################################################')
            nextHtml = self.getPageWithUrl(
                'https://www.pixiv.net/member_illust.php' + btnNext['href'])
            self.download(nextHtml)
        else:
            self.info(u'全都下完啦！')

    # 下载动图压缩包
    def getCanvasImg(self, sourceUrl, wholePageUrl, name):
        name = self.validateTitle(name)
        header = {
            'Referer':
            wholePageUrl,
            'user-agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
        }
        isExists = os.path.exists(os.path.join(self.save_path, name))
        if not isExists:
            img = s.get(
                'https://i.pximg.net/img-zip-ugoira/img/' + sourceUrl +
                '_ugoira1920x1080.zip',
                headers=header)
            with open(name + '.zip', 'wb') as f:
                f.write(img.content)
            self.unZip(name)
            self.nap()

    # 解压为同名文件夹并删除压缩文件
    def unZip(self, name):
        zip = zipfile.ZipFile(name + '.zip')
        zip.extractall(name)
        os.remove(name + '.zip')

    def nap(self):
        time.sleep(random.randint(3, 5))

    # 将'/ \ : * ? " < > |'等非法字符替换为下划线，并反转义html转义字符
    def validateTitle(self, title):
        title = title.strip()
        rstr = r"[\/\\\:\*\?\"\<\>\|]"
        new_title = html.unescape(re.sub(rstr, "_", title))
        return new_title

    # 创建并切换目录
    def mkdir(self, path, dir):
        self.info(u'新建文件夹')
        self.info(u'文件夹名 : ' + dir)
        isExists = os.path.exists(os.path.join(path, dir))
        if not isExists:
            self.info(u'建好啦！')
            os.makedirs(os.path.join(path, dir))
        else:
            self.info(u'文件夹已存在，跳过！')
        os.chdir(path + '/' + dir)
        self.info('######################################################')

    def info(self, str):
        print(str)

    def parser(self, html):
        return BeautifulSoup(html, 'html.parser')

    def start(self):
        self.info('######################################################')
        os.chdir(self.save_path)
        firstPageHtml = self.login()
        # self.mkdir(self.root_path, 'artist_name')
        self.info(u'开始下载...')
        self.info('######################################################')
        self.download(firstPageHtml)