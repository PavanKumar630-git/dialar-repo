from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import re
import uuid
from fastapi import Response, Cookie
from fastapi import Body
import urllib.parse
from pydantic import BaseModel

app = FastAPI()

VICIDIAL_URL = "https://dialer.insurancepolicy4u.com/agc/vicidial.php?relogin=YES&session_epoch=1580115277&session_id=8600061&session_name=1580115274_610112861720&VD_login=20ddd01&VD_campaign=AIRBUdddLK&phone_login=2001&phone_pass=ss20ddd01&VD_pass=ss2001&LOGINvarONE=&LOGINvarTWO=&LOGINvarTHREE=&LOGINvarFOUR=&LOGINvarFIVE="
# VICIDIAL_URL = "https://dialer.insurancepolicy4u.com/agc/vicidial.php?relogin=YES&session_epoch=1580115277&session_id=8600061&session_name=1580115274_610112861720&VD_login=2001&VD_campaign=AIRBULK&phone_login=2001&phone_pass=ss2001&VD_pass=ss2001&LOGINvarONE=&LOGINvarTWO=&LOGINvarTHREE=&LOGINvarFOUR=&LOGINvarFIVE="
def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

@app.post("/api/login")
async def vicidial_login():
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            r = await client.get(VICIDIAL_URL)
            html = r.text.lower()
    except Exception:
        return {"success": False}

    failure_signatures = [
        "sorry, your phone login and password are not active in this system",
        "login incorrect",
        "user logins disabled",
        "your session has expired",
        "-- user login error --",
        "user login error",
        "invalid",
    ]

    page_indicators = [
        "logincampaign_query",
        "vicidial_form",
        "vicidial.php",
    ]

    # 1) explicit failure
    for sig in failure_signatures:
        if sig in html:
            return {"success": False,"message":"Login Fail"}

    # 2) looks like login page (means login failed)
    # for sig in page_indicators:
    #     if sig in html:
    #         return {"success": False,"message":"Login Fail"}

    # 3) otherwise treat as successful login
    return {"success": True,"message":"Login Success"}


_sessions = {}

@app.post("/api/login-session")
async def vicidial_login_session(response: Response):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            r = await client.get(VICIDIAL_URL)
            html = r.text.lower()
    except Exception:
        return {"success": False,"message":"Login Fail"}

    failure_signatures = [
        "sorry, your phone login and password are not active in this system",
        "login incorrect",
        "user logins disabled",
        "your session has expired",
        "-- user login error --",
        "user login error",
        "invalid",
    ]

    page_indicators = [
        "logincampaign_query",
        "vicidial_form",
        "vicidial.php",
    ]

    for sig in failure_signatures:
        if sig in html:
            return {"success": False,"message":"Login Fail"}

    # for sig in page_indicators:
    #     if sig in html:
    #         return {"success": False,"message":"Login Fail"}

    token = str(uuid.uuid4())
    cookies_dict = {k: v for k, v in r.cookies.items()}
    headers_dict = dict(r.headers)

    _sessions[token] = {
        "url": VICIDIAL_URL,
        "cookies": cookies_dict,
        "headers": headers_dict,
    }

    response.set_cookie("session_token", token, httponly=True)
    return {
        "success": True,
        "token": token,
        "cookies": cookies_dict,
        "headers": headers_dict
    }


class VicidialLoginPayload(BaseModel):
    VD_login: str
    VD_campaign: str
    phone_login: str
    phone_pass: str
    VD_pass: str
    session_epoch: str = ""
    session_id: str = ""
    session_name: str = ""
    LOGINvarONE: str = ""
    LOGINvarTWO: str = ""
    LOGINvarTHREE: str = ""
    LOGINvarFOUR: str = ""
    LOGINvarFIVE: str = ""


@app.post("/api/custom-login")
async def custom_login(
    payload: VicidialLoginPayload = Body(
        ...,
        example={
            "VD_login": "2001",
            "VD_campaign": "AIRBULK",
            "phone_login": "2001",
            "phone_pass": "ss2001",
            "VD_pass": "ss2001",
            "session_epoch": "1580115277",
            "session_id": "8600061",
            "session_name": "1580115274_610112861720",
            "LOGINvarONE": "",
            "LOGINvarTWO": "",
            "LOGINvarTHREE": "",
            "LOGINvarFOUR": "",
            "LOGINvarFIVE": ""
        }
    )
):
    params = {
        "relogin": "YES",
        "session_epoch": payload.session_epoch,
        "session_id": payload.session_id,
        "session_name": payload.session_name,
        "VD_login": payload.VD_login,
        "VD_campaign": payload.VD_campaign,
        "phone_login": payload.phone_login,
        "phone_pass": payload.phone_pass,
        "VD_pass": payload.VD_pass,
        "LOGINvarONE": payload.LOGINvarONE,
        "LOGINvarTWO": payload.LOGINvarTWO,
        "LOGINvarTHREE": payload.LOGINvarTHREE,
        "LOGINvarFOUR": payload.LOGINvarFOUR,
        "LOGINvarFIVE": payload.LOGINvarFIVE,
    }

    base = "https://dialer.insurancepolicy4u.com/agc/vicidial.php"
    qs = urllib.parse.urlencode(params)
    url = f"{base}?{qs}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            r = await client.get(url)
            html = (r.text or "").lower()
    except:
        return {"success": False, "message": "Login Fail"}

    failure_signatures = [
        "sorry, your phone login and password are not active in this system",
        "login incorrect",
        "user logins disabled",
        "your session has expired",
        "-- user login error --",
        "user login error",
        "invalid",
    ]

    for sig in failure_signatures:
        if sig in html:
            return {"success": False, "message": "Login Fail"}

    return {"success": True, "message": "Login Success"}
