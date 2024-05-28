## Principle

The principle of request forwarding is to add an intermediate stage between
the user side and the server side. Django is used to implement this
intermediate stage. In this stage, requests from the user side are forwarded
to the server side, and then the response from the server side is displayed on
the user side page.

## Implementation

### User side

Add a new route in App.js:

    
    
    import WCI from "./screen/WCI"
    ...
    <Route path="/wci1" element={<WCI />} />
    

Simply write the user side interface, get page from the backend and display it
in the <iframe> tag.

    
    
    import { useEffect, useState } from "react"
    import { HttpGet } from "../utils/http"
    
    const WCI = () => {
      const [page, setPage] = useState("")
      useEffect(() => {
        fetchData()
      }, [])
    
      const fetchData = async () => {
        await HttpGet("/wciapi/")
          .then((response) => response.text())
          .then((result) => {
            setPage(result)
          })
      }
      
      return <iframe title="WCI1" style={{ width: "100%", height: "900px" }} srcDoc={page}></iframe>
    }
    export default WCI
    

### Server side

Add a path in urls.py:

    
    
    urlpatterns = [
        ...
        re_path(r'^wciapi/', views.WCI1.as_view()),
    ]
    

Add a class in views.py named WCI1:

    
    
    class WCI1(PyiAuthAPIView):
        SESSIONS = {}       # TODO: need to remove the timeout sessions
    
        def get(self, request, *args, **kwargs):
            return self.__processRequest(request)
    
        def post(self, request, *args, **kwargs):
            return self.__processRequest(request)
    
        def __processRequest(self, request):
            wciBaseUrl = 'http://localhost:8080'
            wci2RequestFlag = '__PYI_VER__=2'
            additionalPrms = '__HAS_OpenMainWindow=true&' + wci2RequestFlag
    
            try:
                requestUrl = request.get_full_path() # /wci/index.jsp?__REQUEST_ID=XE6cpuzd8mxbnhf
                requestUrl = requestUrl.replace('wciapi', 'wci')
                requestUrlWithPrms = requestUrl.lower()
                qIndex = requestUrlWithPrms.find('?')
                requestUrl += ('&' if qIndex != -1 else '?') + additionalPrms
                headers = {}
                for key, value in request.headers.items():
                    if key in ['Host', 'Origin', 'Referer']:
                        continue    # Host=localhost:8000, Origin=http://localhost:3000, Referer=http://localhost:3000/
                    if key == 'Content-Length' and value == '':
                        continue
                    headers[key] = value
                token = self.__getToken(request)
                s = WCI1.SESSIONS.get(token, None)
                if s is None:
                    s = requests.Session()
                    WCI1.SESSIONS[token] = s
                
                r = None
                if request.method == 'GET':
                    r = s.get(wciBaseUrl + requestUrl, headers=headers)
                else:
                    r = s.post(wciBaseUrl + requestUrl, headers=headers, data=request.data)
                if len(r.history) > 0 and r.history[-1].status_code == 302:
                    url = r.url[len(wciBaseUrl + '/wci1'):]
                    url = '/wciapi/' + url 
                    url += '&token=' + token    # TODO: need to add tooken to request head or cookie
                    return redirect(url)
                else:
                    hr = HttpResponse(content=r.text)
                    return hr
            except Exception as e:
                traceback.print_exc()
                return HttpResponse(content='System error: ' + str(e))
    
        def __getToken(self, request) -> str:
            tokenRc = IkyUsrToken.objects.filter(usr=request.user).first()
            return '' if tokenRc is None else tokenRc.token
    

Function __processRequest is the core content.

First, configure the request URL and request header for the request to the
server based on the request from the user side.

Then, based on the request method, choose between `requests.Session().get(url,
headers=...)` or `requests.Session().post(url, headers=...,
data=request.data)`. If the method is POST, an additional `request.data` needs
to be passed, which includes interactions such as click events.

Ultimately, if a redirect occurs, simply redirect directly to the new address
after processing.

