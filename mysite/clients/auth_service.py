import httpx
from fastapi import HTTPException
from mysite.config import settings

async def verify_access_token(token: str):
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            response = await client.get(
                f'{settings.auth_service_url}/auth/verify/',
                headers={'Authorization': f'Bearer {token}'}
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail='Auth service жеткиликтүү эмес')

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail='Access token туура эмес же мөөнөтү бүттү')
    elif response.status_code != 200:
        raise HTTPException(status_code=503, detail='Авторизацияны текшерүүдө ката кетти')

    try:
        user_db = response.json()
        return {
            'id': int(user_db['id']),
            'username': user_db['username'],
            'status': user_db['status']
        }
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail='Auth service туура эмес маалымат кайтарды')