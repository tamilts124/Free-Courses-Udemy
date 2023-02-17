from time import sleep
from threading import Thread
from bs4 import BeautifulSoup
import datetime as dt
import requests, json, os

class Infinitydatabase:

    def __init__(self, adminurl):
        self.adminurl =adminurl
        self.host =adminurl.split('login')[0]
        self.db =self.adminurl.split('db=')[1]
        self.display_response =['select', 'show', 'desc']
        self.session =requests.Session()
        self.headers ={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        }
        self.session.headers =self.headers
        response =self.session.get(self.adminurl).text
        self.commonparams =response.split('PMA_commonParams.setAll(')[1].split(');')[0]
        self.server =self.commonparams.split('server:"')[1].split('"')[0]
        self.token =self.commonparams.split('token:"')[1].split('"')[0]
        self.user =self.commonparams.split('user:"')[1].split('"')[0]
        self.data ={
            'ajax_request':True,
            'ajax_page_request':True,
            'pftext':'F',
            'sql_query':'',
            'server':self.server,
            'db':self.db,
            'token':self.token
        }

    def query(self, query):
        self.data['sql_query'] =query.strip(' \n\t')
        response =self.session.post(self.host+'sql.php', data =self.data)
        result =response.json()
        if [True for s in self.display_response if self.data['sql_query'].lower().startswith(s)] and result['success']: return self.display_query_response(response)
        elif result['success']: return 1
        else: return 0
    
    def display_query_response(self, response):
        result =response.text
        table ={'column':[], 'row':[]}

        for column in result.split('data-column=\\"')[1:]:
            column =column.split('\\"')[0]
            table['column'].append(column)
        
        datas =result.split('<tr ')[1:]
        if not datas: return table
        if 'tr>' in datas[-1]: datas[-1] =datas[-1].split('tr>')[0]
        for data in datas:
            row =[]
            for rowdata in data.split('<td data-decimals=')[1:]:
                row.append(rowdata.split('>')[1].split('<')[0])
            if row: table['row'].append(row)
        return table

class Realdiscount:

    def __init__(self, accesstoken, sessionid, fromday=0, today=1):
        self.accesstoken =accesstoken
        self.sessionid =sessionid
        self.fromday =fromday
        self.today =today
        self.useragent ='Mozilla/5.0 (X11; Windows x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'
        self.requests_limit =os.environ['REQUESTS_LIMIT']
        self.enrolls_limit =os.environ['ENROLLS_LIMIT']
        self.isthour =5
        self.istminute =30

    def request_resource(self, url, method='get', headers={}, cookies={}, data={}, allow_redirectects=True):
        while True:
            try:
                if method.lower()=='get': return requests.get(url, headers=headers, cookies=cookies, data=data, allow_redirects=allow_redirectects)
                elif method.lower()=='post': return requests.post(url, headers=headers, cookies=cookies, data=data, allow_redirects=allow_redirectects)
            except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.SSLError): continue

    def get_courseid(self, data):
        datas =data.split('https://img-c.udemycdn.com/course/')
        for data in datas:
            if '.jpg' in data:
                datas =data.split('/')
                for data in datas:
                    if '.jpg' in data:
                        datas =data.split('\\')
                        for data in datas:
                            if '.jpg' in data:
                                datas =data.split('_')
                                return int(datas[0])

    def get_coupon_status(self, course_id, coupon):
        json_data =self.request_resource(
            f'https://www.udemy.com/api-2.0/course-landing-components/{course_id}/me/?components=purchase,redeem_coupon,discount_expiration&discountCode={coupon}',
            headers={'User-Agent': self.useragent}
        ).json()
        if not json_data.get('redeem_coupon'):return
        status =json_data['redeem_coupon']['discount_attempts'][0]['status']
        if status=='applied':return {
            'uses_remaining':json_data['purchase']['data']['pricing_result']['campaign']['uses_remaining'],
            'real_price':json_data['purchase']['data']['pricing_result']['list_price']['amount'],
            'end_time':json_data['discount_expiration']['data']['discount_deadline_text']
        }


    def collect_offer(self, offer, coupon_datas, wrong_datas, thread):
        result_page =self.request_resource(f'https://www.real.discount{offer[0]}').text
        coupon_links =BeautifulSoup(result_page, 'html.parser').findAll('a')
        for coupon_link in coupon_links:
            if coupon_link['href'].startswith('https://www.udemy.com/course/'):
                coupon_datas.append([offer[1], coupon_link['href']])
                break
        else: wrong_datas.append(offer[1])
        thread[0] -=1

    def check_offer(self, coupon_data, avail_offers, wast_offers, final_offers, thread):
        course_title =coupon_data[0]
        course_name =coupon_data[1].split('/')[-2]
        coupon_code =coupon_data[1].split('=')[-1]
        course_id =self.get_courseid(self.request_resource(coupon_data[1]).text)
        result_json =self.get_coupon_status(course_id, coupon_code)
        coupon_data =[]
        if result_json and result_json.get('uses_remaining'):
            result_page =self.request_resource(f'https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/', headers={'User-Agent': self.useragent}, cookies={'access_token': self.accesstoken})
            if result_page.status_code==403 and not result_page.text.lower()=='resource not found':
                update ='Available'
                final_offers.append({
                        "discountInfo":{"code":coupon_code},
                        "price":{"amount":0,"currency":"INR"},
                        "buyable":{"id":course_id,"type":"course"}
                })
                for data in [course_name, course_id, coupon_code, update, int(result_json.get('real_price')), result_json.get('end_time'), result_json['uses_remaining']]: coupon_data.append(data)
                avail_offers.append(coupon_data)
            else:
                update ='Enrolled'
                for data in [course_name, course_id, coupon_code, update, int(result_json.get('real_price', 0)), result_json.get('end_time', ''), result_json.get('uses_remaining')]: coupon_data.append(data)
                wast_offers.append(coupon_data)
        else:
            update ='Expired'
            for data in [course_name, course_id, coupon_code, update, int(result_json['real_price'] if result_json['real_price'] else 0), '', 0]: coupon_data.append(data)
            wast_offers.append(coupon_data)
        thread[0] -=1
        print(course_title+f' [{update}]')
        coupon_data.append(course_title)

    def enroll_course(self, courses):
        try:
            common_data ={
                "checkout_environment":"Marketplace",
                "checkout_event":"Submit",
                "shopping_info":{"items":courses,"is_cart":True},
                "payment_info":{"method_id":"0","payment_vendor":"Free","payment_method":"free-method"}
            }
            result_page =self.request_resource('https://www.udemy.com/payment/checkout-submit/', data=json.dumps(common_data), headers={'User-Agent': self.useragent, 'Content-Type': 'application/json;charset=utf-8'}, cookies={'access_token': self.accesstoken, 'dj_session_id': self.sessionid}, method='POST')
            result_json =result_page.json()
            if result_json.get('status')=='succeeded':update ='Succeeded'
            else:update ='Failed'
            if not result_json.get('status')=='succeeded':print(result_json)
        except json.JSONDecodeError:
            if result_page.status_code==504:update ='Succeeded'
            else:print(result_page.text);update ='Error'
        return update

    def make_cache(self, db, db_table, coupon_datas):
        query =f'insert into {db_table} values'
        date =dt.datetime.now()
        delta =dt.timedelta(hours=self.isthour, minutes=self.istminute)
        date =(date+delta).date()
        for data in coupon_datas:
            query+=f''' (null, "{data[0]}", {data[1]}, "{data[2]}", "{data[3]}", {data[4]}, "{date.year}-{date.month}-{date.day}", {'"'+data[5]+'"' if data[6] else "null"}, {data[6] if data[6] else "null"}),'''
        query =query[:-1]
        return db.query(query)

    def get_cache(self, db, db_table):
        date =dt.datetime.now()
        delta =dt.timedelta(hours=self.isthour, minutes=self.istminute)
        date =(date+delta).date()
        query =f'select CourseName, CouponCode from {db_table} where DateOfCheck="{date}"'
        coupon_datas =db.query(query)['row']
        if coupon_datas:
            old_datas =[]
            for data in coupon_datas:
                old_datas.append('https://www.udemy.com/course/'+data[0]+'/?couponCode='+data[1])
            return old_datas
        return []

    def realdiscount(self, db, db_table):
        old_coupons =self.get_cache(db, db_table)
        print('\n> Collecting Offers Pages...\n')
        anger_tags =BeautifulSoup(self.request_resource('https://www.real.discount/articles/').text, 'html.parser').findAll('a')
        article_links, offer_links =[], []
        for anger_tag in anger_tags:
            if anger_tag['href'].startswith('https://app.real.discount/article/'): article_links.append(anger_tag['href'])
        articles =article_links[self.fromday:self.today]
        for id, article in enumerate(articles, start=1):
            print(f'\t{id}/{len(articles)}\t', end='\r')
            div_tags =BeautifulSoup(self.request_resource(article).text, 'html.parser').findAll('div', {'class':'ml-3'})
            for div_tag in div_tags:
                sub_div_tags =div_tag.findAll('div')
                if sub_div_tags[1].find('span', {'class':'text-muted text-sm ml-2'}).string.split(' ')[-1]=='0$' and sub_div_tags[0].a['href'].startswith('/offer/'):
                    offer_links.append((sub_div_tags[0].a['href'], sub_div_tags[0].a.string))
        
        if not len(offer_links) == len(list(set(offer_links))):
            offer_links =list(set(offer_links))
        coupon_datas, wrong_datas =[], []

        print('\n\n> Collecting Course Offers...\n')
        thread =[0]
        for offer in range(len(offer_links)):
            Thread(target=self.collect_offer, args=[offer_links[offer], coupon_datas, wrong_datas, thread]).start()
            thread[0] +=1
            while (thread[0]>=self.requests_limit and offer<len(offer_links)-1)  or offer==len(offer_links)-1:
                sleep(0.5)
                print(f'\t{len(coupon_datas)+len(wrong_datas)}/{len(offer_links)}\t', end='\r')
                if len(coupon_datas)+len(wrong_datas)==len(offer_links): break

        if not coupon_datas:
            print('> Free Course Offers Not Found..\n')
            return 1
        
        avail_offers, wast_offers, old_offers, final_offers =[], [], [], []
        print('\n\n> Checking Offers For Enrolling...\n')
        thread =[0]
        for coupon_data in range(len(coupon_datas)):
            if coupon_datas[coupon_data][1] in old_coupons: print(coupon_datas[coupon_data][0]+f' [Old Coupon]'); old_offers.append(coupon_datas[coupon_data][1])
            else:
                Thread(target=self.check_offer, args=[coupon_datas[coupon_data], avail_offers, wast_offers, final_offers, thread]).start()
                thread[0] +=1
            while (thread[0]>=self.requests_limit and coupon_data<len(coupon_datas)-1)  or coupon_data==len(coupon_datas)-1:
                sleep(0.5)
                print(f"\t{len(avail_offers)+len(wast_offers)+len(old_offers)}/{len(coupon_datas)}", end='\r')
                if len(avail_offers)+len(wast_offers)+len(old_offers)==len(coupon_datas): break

        if not avail_offers:
            print('\n\n> Courses Not Valid For Enrolling..\n')
            if wast_offers:
                if self.make_cache(db, db_table, wast_offers): print('> Success, Enrolled and Expired Datas Updated...\n')
                else: print('> Fail, Enrolled and Expired Datas Update...\n')
            else: print('> No Datas For Update...\n')
            return 1

        print('\n\n> Valid Courses..\n')
        for id, data in enumerate(avail_offers, start =1): print(f'{id}. {data[-1]}')
        print('\n> Enrolling Courses..\n')
        bundle_size =self.enrolls_limit
        total_bundle =len(final_offers)//bundle_size
        remaining =len(final_offers)%bundle_size
        total_status =[]
        for bundle in range(1, total_bundle+1): total_status.append(self.enroll_course(final_offers[bundle_size*bundle-bundle_size:bundle_size*bundle]))
        else:
            if total_bundle and remaining:total_status.append(self.enroll_course(final_offers[bundle_size*total_bundle:]))
            elif not total_bundle and remaining:total_status.append(self.enroll_course(final_offers))
        print(f"> Total Courses: {len(final_offers)}, Status: {total_status}\n")
        for status in total_status:
            if status != 'Succeeded':
                if self.make_cache(db, db_table, wast_offers): print('> Success, Enrolled and Expired Datas Updated...\n')
                else: print('> Fail, Enrolled and Expired Datas Update...\n')
                return 0
        else:
            if self.make_cache(db, db_table, wast_offers+avail_offers): print('> Success, Datas Updated...\n')
            else: print('> Fail, Datas Update...\n')
        return 1


def main():
    infinity_db =Infinitydatabase(os.environ['DB_ADMIN_URL'])
    rdiscount =Realdiscount(os.environ['ACCESS_TOKEN'], os.environ['SESSION_ID'], os.environ['FROM_DAY'], os.environ['TO_DAY'])
    while True:
        if rdiscount.realdiscount(infinity_db, os.environ['DB_TABLE_NAME']): break

if __name__ == '__main__':
    main()