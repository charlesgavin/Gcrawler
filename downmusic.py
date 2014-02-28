#coding=utf-8

import urllib,urllib2,re,os,json,gevent,traceback	#json是数据交换语言。
from BeautifulSoup import BeautifulSoup		#HTML
from gevent import monkey

monkey.patch_all()

rootUrl='http://music.baidu.com'
artistId=14626917 #想批量下载并归类你喜欢的歌手的所有专辑？那就把这里替换成该歌手在百度音乐的Id吧，例如：http://music.baidu.com/artist/2825
pagesize=10
savePath='/home/hongye/文档' #改成你想存储的文件夹
listDir='_____downlist\\'
handleCount=0
BAIDUVERIFY=''

def crawlList():
	artistUrl=rootUrl+'/artist/'+str(artistId)
	homeHtml=request(artistUrl)	#请求目标服务器，生成一个类
	soup=BeautifulSoup(homeHtml)	 # html为html源代码字符串，type(html) == str
	
	try:
		pagecount=len(soup.findAll("div",{"class":"page-inner"})[1].findAll(text=re.compile(r'\d+')))	#以当前节点为起点，搜索整个子数，后返回；re中，\d表示数字0-9，findALL()用于找出字符串中的数字，而split('\d+')用于去掉字符串中的数字
	except:
		print traceback.print_exc()
		print homeHtml
		return
	jobs=[]
	listPath=savePath+listDir
	if not os.path.exists(listPath):
		os.mkdir(listPath)
	for i in range(pagecount):	#0～～pagecount-1.
		jobs.append(gevent.spawn(crawlPage,i))
	gevent.joinall(jobs)
		
def request(url):
	global BAIDUVERIFY
	req=urllib2.Request(url)
	if BAIDUVERIFY!='':
		req.add_header('Cookie','BAIDUVERIFY='+BAIDUVERIFY+';')
	resp=urllib2.urlopen(req)
	html= resp.read()
	verify=getBaiduVerify(html)
	if verify!='': 
		print u'成功提取验证码并重新发起请求'
		BAIDUVERIFY=verify 
		return request(url)
	return html
	
def getBaiduVerify(html):
	vcode=re.search(r'name=\"vcode\" value=\"(.*?)\"' , html, re.I)
	id=re.search(r'name=\"id\" value=\"(.*?)\"' , html, re.I)
	di=re.search(r'name=\"di\" value=\"(.*?)\"' , html, re.I)
	if vcode and id and di:
		return vcode.group(1)+':'+id.group(1)+':'+di.group(1)
	return ''

def crawlPage(page):
	start=page*pagesize
	albumListUrl='http://music.baidu.com/data/user/getalbums?start=%d&ting_uid=%d&order=time' % (start,artistId)
	print albumListUrl
	albumListHtml=json.loads(request(albumListUrl))["data"]["html"]
	albumListSoup=BeautifulSoup(albumListHtml)
	covers=albumListSoup.findAll('a',{'class':'cover'})
	pagePath=savePath+listDir+str(page)+'\\'
	if not os.path.exists(pagePath):
		os.mkdir(pagePath)
	for cover in covers:
		try:
			crawlAlbum(pagePath,rootUrl+cover['href'],cover['title'])
		except:
			print traceback.print_exc()

def crawlAlbum(pagePath,albumUrl,title):
	print albumUrl,title
	albumHtml=request(albumUrl)
	albumSoup=BeautifulSoup(albumHtml)
	musicWraps=albumSoup.findAll('span',{'class':'song-title '})
	title=re.subn(r'\\|\/|:|\*|\?|\"|\<|\>|\|','',title)[0]
	path=savePath+title+'\\'
	albumListPath=pagePath+title+'.txt'
	albumFile=open(albumListPath,'w')
	for wrap in musicWraps:
		link=wrap.find('a')
		try:
			musicPage=rootUrl+link['href']
			albumFile.write('%s\t%s\t%s\n' % (musicPage,link['title'],path)) #真实下载地址会过期，这里保存下载页面
		except:
			print traceback.print_exc()	#获取异常相关的数据都是通过sys.exc_info()函数得到的
	albumFile.close()

def crawlDownloadUrl(musicPage):
	downPage=musicPage+'/download'
	downHtml=request(downPage)
	downUrl=re.search('http://[^ ]*xcode.[a-z0-9]*' , downHtml, re.M).group()
	return downUrl

def downList():
	listPath=savePath+listDir
	jobs=[]
	for pageDir in os.listdir(listPath):
		jobs.append(gevent.spawn(downPage,listPath+pageDir))
	gevent.joinall(jobs)

def downPage(pagePath):
	for filename in os.listdir(pagePath):
		filePath=pagePath+'\\'+filename
		albumFile=open(filePath,'r')
		try:
			for args in albumFile.readlines():
				arrArgs=args.split('\t')
				downMusic(arrArgs[0],arrArgs[1],arrArgs[2].replace('\n',''))
		except:
			print traceback.print_exc()
		finally:
			albumFile.close()


def downMusic(musicPage,title,path):
	global handleCount
	if not os.path.exists(path):
		os.mkdir(path)
	handleCount+=1
	print handleCount,musicPage,title,path
	filename=path+re.subn(r'\\|\/|:|\*|\?|\"|\<|\>|\|','',title)[0]+'.mp3'
	if os.path.isfile(filename):
		return
	downUrl=crawlDownloadUrl(musicPage)
	try:
		urllib.urlretrieve(downUrl,filename)
	except:
		print traceback.print_exc()
		os.remove(filename)

if __name__=='__main__':
	print u'命令：\n\tlist\t生成下载清单\n\tdown\t开始下载\n\texit\t退出'
	cmd=raw_input('>>>')
	while cmd!='exit':
		if cmd=='list':
			crawlList()
			print u'已生成下载清单'
		elif cmd=='down':
			downList()
			print u'下载完成'
		else:
			print 'unknow cmd'
		cmd=raw_input('>>>')
