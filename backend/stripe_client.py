import os
import httpx
import stripe

async def get_stripe_credentials():
    """Fetch Stripe credentials from Replit connector API"""
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        return None, None
    
    is_production = os.environ.get('REPLIT_DEPLOYMENT') == '1'
    target_environment = 'production' if is_production else 'development'
    
    url = f"https://{hostname}/api/v2/connection"
    params = {
        'include_secrets': 'true',
        'connector_names': 'stripe',
        'environment': target_environment
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            }
        )
        
        data = response.json()
        items = data.get('items', [])
        
        if items and items[0].get('settings'):
            settings = items[0]['settings']
            return settings.get('publishable'), settings.get('secret')
    
    return None, None

async def get_stripe_client():
    """Get configured Stripe client"""
    _, secret_key = await get_stripe_credentials()
    if secret_key:
        stripe.api_key = secret_key
    return stripe

async def init_stripe():
    """Initialize Stripe with credentials from Replit connector or env var"""
    import logging
    publishable, secret = await get_stripe_credentials()
    if secret:
        stripe.api_key = secret
        logging.info("Stripe initialized via Replit connector")
        return True
    # Fallback to environment variable
    env_key = os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_API_KEY')
    if env_key:
        stripe.api_key = env_key
        logging.info("Stripe initialized via environment variable")
        return True
    logging.warning("Stripe not configured - payment features will be disabled")
    return False
