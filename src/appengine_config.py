'''
Created on Sep 27, 2013

@author: vbrown
'''

from gaesessions import SessionMiddleware

def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key="ifjwpsla9fv83jrfeeddnffkje983j38")
    return app