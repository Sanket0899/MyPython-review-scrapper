from flask import Flask,render_template,jsonify,request
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app=Flask(__name__)

@app.route('/',methods=['Get','POST'])
def index():
    if request.method=='POST':
        searchstring=request.form['content'].replace(" ","")
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['mycrawlerDB']
            reviews=db[searchstring].find({})
            if db[searchstring].count_documents({})>0:
                return render_template('results.html',reviews=reviews)
            else:
                flipkart_url='https://www.flipkart.com/search?q='+searchstring #Preparing the URL
                Uclient=uReq(flipkart_url) #Requesting web page from the web
                flipkart_page=Uclient.read() #reading the page
                Uclient.close() #Closing the connection
                flipkart_html=bs(flipkart_page,"html.parser")
                bigboxes=flipkart_html.findAll('div',{'class':'_1AtVbE col-12-12'})#searching for appropriate class
                del bigboxes[0:3]
                box=bigboxes[0]
                productlink='https://www.flipkart.com'+box.div.div.div.a['href'] #extracting actual product link
                prodres=requests.get(productlink)
                prod_html=bs(prodres.text,"html.parser")
                comment_box=prod_html.findAll('div',{'class':'_16PBlm'})#getting the class containing the reviews

                table=db[searchstring]#creating collection with the same name as the searchstring

                reviews=[]

                for comment in comment_box:
                    try:
                        name=comment.div.div.findAll('p',{'class':'_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name='No name'

                    try:
                        rating=comment.div.div.div.div.text
                    except:
                        rating='No rating'

                    try:
                        commentHead = comment.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'

                    try:
                        comtag=comment.div.div.findAll('div',{'class':''})
                        custcomment=comtag[0].div.text
                    except:
                        custcomment='No customer comment'

                    mydict={'Product':searchstring,'Name':name,'Rating':rating,'CommentHead':commentHead,
                            'Comment':custcomment}
                    x=table.insert_one(mydict)#Insert one element
                    reviews.append(mydict)
                return render_template('results.html',reviews=reviews)
        except:
            return 'something is wrong'
    else:
        return(render_template('index.html'))

if __name__ == '__main__':
    app.run(port=8000,debug=True)