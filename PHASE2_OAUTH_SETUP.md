# Phase 2: Apple Sign-In & Facebook Login Setup Guide

## Overview
Phase 1 is COMPLETE with Google OAuth fully functional. Apple and Facebook buttons are present but sealed until you provide credentials.

---

## 🍎 APPLE SIGN-IN SETUP

### Prerequisites
- **Apple Developer Program** membership ($99/year)
- **Xcode** (for generating keys)

### Step 1: Create App ID
1. Go to [Apple Developer Portal](https://developer.apple.com)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Click **Identifiers** → **+** button
4. Select **App IDs** → Continue
5. Configure:
   - Description: `Conqueror's Court`
   - Bundle ID: `com.conquerorcourt.webapp`
   - Check **Sign in with Apple** capability
6. Click **Continue** → **Register**

### Step 2: Create Service ID (Client ID)
1. In **Identifiers**, click **+** button again
2. Select **Services IDs** → Continue
3. Configure:
   - Description: `Conqueror's Court Web Auth`
   - Identifier: `com.conquerorcourt.webapp.signin` (This is your **APPLE_SERVICE_ID**)
4. Check **Sign in with Apple**
5. Click **Configure** next to Sign in with Apple
6. Settings:
   - Primary App ID: Select your App ID from Step 1
   - Domains: `your-domain.com` (or localhost for testing)
   - Return URLs: `https://your-domain.com/auth/callback`
7. Click **Save** → **Continue** → **Register**

### Step 3: Create Signing Key
1. Navigate to **Keys** → click **+** button
2. Configure:
   - Key Name: `Conqueror's Court Sign In Key`
   - Check **Sign in with Apple**
3. Click **Configure** next to Sign in with Apple
4. Select your Primary App ID
5. Click **Save** → **Continue** → **Register**
6. **DOWNLOAD** the `.p8` key file immediately (you can only download once!)
7. Note the **Key ID** (10 characters) - This is your **APPLE_KEY_ID**

### Step 4: Get Team ID
1. Go to [Apple Developer Membership](https://developer.apple.com/account#membership)
2. Your **Team ID** is displayed at the top - This is your **APPLE_TEAM_ID**

### Step 5: Add Credentials to Backend
```bash
# Edit /app/backend/.env
APPLE_TEAM_ID=YOUR_10_CHAR_TEAM_ID
APPLE_SERVICE_ID=com.conquerorcourt.webapp.signin
APPLE_KEY_ID=YOUR_10_CHAR_KEY_ID
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQg...
(paste full content of .p8 file here, keep on multiple lines)
-----END PRIVATE KEY-----
```

### Step 6: Restart Backend
```bash
sudo supervisorctl restart backend
```

**Apple Sign-In is now ACTIVE!** The button will automatically unlock.

---

## 📘 FACEBOOK LOGIN SETUP

### Prerequisites
- **Facebook Developer Account** (free)

### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com)
2. Click **My Apps** → **Create App**
3. Select **Consumer** use case → **Next**
4. Configure:
   - App Name: `Conqueror's Court`
   - Contact Email: Your email
5. Click **Create App**

### Step 2: Configure Facebook Login
1. In your app dashboard, click **Add Product**
2. Find **Facebook Login** → click **Set Up**
3. Select **Web** platform
4. Enter your Site URL: `https://your-domain.com`
5. Click **Save** → **Continue**

### Step 3: Configure OAuth Settings
1. Go to **Facebook Login** → **Settings**
2. Add to **Valid OAuth Redirect URIs**:
   ```
   https://your-domain.com/auth/callback
   http://localhost:3000/auth/callback  (for local testing)
   ```
3. Click **Save Changes**

### Step 4: Get App Credentials
1. Go to **Settings** → **Basic**
2. Copy **App ID** - This is your **FACEBOOK_APP_ID**
3. Copy **App Secret** (click Show) - This is your **FACEBOOK_APP_SECRET**

### Step 5: Add Credentials to Backend
```bash
# Edit /app/backend/.env
FACEBOOK_APP_ID=YOUR_APP_ID_HERE
FACEBOOK_APP_SECRET=YOUR_APP_SECRET_HERE
```

### Step 6: Restart Backend
```bash
sudo supervisorctl restart backend
```

**Facebook Login is now ACTIVE!** The button will automatically unlock.

---

## 🔍 VERIFY OAUTH STATUS

Check which providers are active:
```bash
curl https://your-domain.com/api/auth/oauth/status
```

Response:
```json
{
  "google": true,    // Always true (Emergent-managed)
  "apple": true,     // true when credentials added
  "facebook": true   // true when credentials added
}
```

---

## 🧪 TESTING

### Test Google OAuth (Already Working)
1. Go to `/login` or `/register`
2. Click **Continue with Google**
3. Authenticate with Google
4. You'll be redirected to dashboard

### Test Apple/Facebook (After credentials added)
1. Add credentials following steps above
2. Restart backend
3. Visit `/login` or `/register`
4. Buttons will automatically unlock
5. Click to test authentication flow

---

## 🛡️ SECURITY NOTES

1. **HTTPS Required**: OAuth only works with HTTPS in production
2. **Domain Configuration**: Update redirect URIs when deploying
3. **Environment Variables**: Never commit `.env` files to git
4. **Key Rotation**: Regularly rotate API keys and secrets

---

## 🎯 UNIFIED USER MODEL

All three OAuth providers use the same database structure:

```javascript
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "oauth_provider": "google|apple|facebook",  // Which provider
  "oauth_id": "provider_user_id",             // Provider's user ID
  "picture_url": "https://...",               // Profile picture
  "subscription_status": "active|inactive",
  "dietary_preferences": [],
  "cooking_methods": [],
  "created_at": "2024-..."
}
```

**Account Linking**: If a user signs in with Google using `user@example.com`, then later signs in with Facebook using the same email, the accounts are automatically linked.

---

## 📋 QUICK CHECKLIST

### Apple
- [ ] Apple Developer Program membership ($99/year)
- [ ] App ID created
- [ ] Service ID created (APPLE_SERVICE_ID)
- [ ] Signing key created and downloaded (.p8 file)
- [ ] Team ID obtained (APPLE_TEAM_ID)
- [ ] Key ID noted (APPLE_KEY_ID)
- [ ] Private key content added to .env
- [ ] Backend restarted

### Facebook
- [ ] Facebook Developer account created
- [ ] App created
- [ ] Facebook Login product added
- [ ] OAuth redirect URIs configured
- [ ] App ID obtained (FACEBOOK_APP_ID)
- [ ] App Secret obtained (FACEBOOK_APP_SECRET)
- [ ] Credentials added to .env
- [ ] Backend restarted

---

## 🆘 TROUBLESHOOTING

**"The Gate is sealed" not unlocking after adding credentials:**
```bash
# Verify .env file has credentials
cat /app/backend/.env | grep -E "APPLE|FACEBOOK"

# Restart backend
sudo supervisorctl restart backend

# Check status
curl http://localhost:8001/api/auth/oauth/status
```

**Apple Sign-In errors:**
- Verify `.p8` file content is correct (including BEGIN/END lines)
- Check Team ID is exactly 10 characters
- Ensure Service ID matches exactly

**Facebook Login errors:**
- Verify redirect URI matches exactly (including protocol)
- Check App is not in Development Mode if testing from non-localhost
- Ensure App Secret is kept secure

---

## 🎉 READY FOR PHASE 2

Once you provide the credentials, simply:
1. Update `/app/backend/.env` with Apple and/or Facebook credentials
2. Run `sudo supervisorctl restart backend`
3. The sealed buttons will automatically unlock
4. Users can sign in with all three providers!

**Current Status:**
- ✅ Google OAuth: ACTIVE (Emergent-managed)
- 🔒 Apple Sign-In: SEALED (awaiting credentials)
- 🔒 Facebook Login: SEALED (awaiting credentials)
