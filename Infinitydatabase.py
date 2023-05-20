from bs4 import BeautifulSoup
import requests

class Infinitydatabase:

    def __init__(self, adminurl):
        self.adminurl =adminurl
        self.host =adminurl.split('login')[0]
        self.db =self.adminurl.split('db=')[1]
        self.display_response =['select ', 'show ', 'desc']
        self.session =requests.Session()
        self.headers ={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        }
        self.session.headers =self.headers
        response =self.session.get(self.adminurl, verify=False).text
        self.commonparams =response.split('PMA_commonParams.setAll(')[1].split(');')[0]
        self.server =self.commonparams.split('server:"')[1].split('"')[0]
        self.token =self.commonparams.split('token:"')[1].split('"')[0]
        self.user =self.commonparams.split('user:"')[1].split('"')[0]
        self.data ={
            'ajax_request':True,
            'ajax_page_request':True,
            'session_max_rows':10000,
            'pftext':'F',
            'sql_query':'',
            'server':self.server,
            'db':self.db,
            'token':self.token
        }

    def query(self, query):
        self.data['sql_query'] =query.strip(' \n\t')
        result =self.session.post(self.host+'sql.php', data=self.data, verify=False).json()
        if [True for s in self.display_response if self.data['sql_query'].lower().startswith(s)] and result['success']: return self.display_query_response(result.get('message'))
        elif result['success']: return True
        else: return False
    
    def display_query_response(self, result):
        table ={'column':[], 'row':[]}
        html =BeautifulSoup(result, 'html.parser')
        for tag in html.find_all():
            if tag.has_attr('data-column'): table['column'].append(tag.text.strip(' \n'))
        for r in html.find_all('tr'):
            row =[]
            for tag in r.find_all():
                if tag.has_attr('data-decimals'): row.append(tag.text.strip(' \n'))
            if row: table['row'].append(row)
        return table
