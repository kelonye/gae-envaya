import webapp2 as webapp
import views

urls = views.urls

app = webapp.WSGIApplication(urls, debug=True)
