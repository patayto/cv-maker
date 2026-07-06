# LinkedIn Bot Detection Issue

**Date:** 2026-02-16
**Status:** RESOLVED 2026-07-05 - Replaced browser scraping with LinkedIn's public, unauthenticated `jobs-guest` API (`backend/linkedin_guest.py`). No cookies, no Playwright, no bot detection. HTML paste mode remains as a fallback for edge cases. See ai-job-search's linkedin-search skill for the original pattern.

## Problem

LinkedIn job parsing fails with `ERR_TOO_MANY_REDIRECTS` for both HTTP and browser-based (Playwright) approaches.

## Attempted Solutions

### 1. HTTP-Only Mode (requests library)
**Result:** Failed - Redirect loop (30+ redirects)
```
Error fetching URL: Exceeded 30 redirects.
```

### 2. Browser Mode with Single Cookie (Playwright)
**Result:** Failed - Browser timeout, stuck on `about:blank`
```
Browser error fetching https://www.linkedin.com/jobs/view/4336041065/:
Page.goto: net::ERR_TOO_MANY_REDIRECTS
```

### 3. Browser Mode with Multiple Cookies + Stealth
**Implementation:**
- Added `playwright-stealth` package for automation hiding
- Set 5 LinkedIn cookies: `li_at`, `JSESSIONID`, `liap`, `bcookie`, `bscookie`
- Applied stealth mode to hide `navigator.webdriver` and other automation signals

**Result:** Partially worked once, then LinkedIn logged out the session
**Outcome:** LinkedIn's anti-bot system still detected and blocked the automation

## Root Cause

LinkedIn actively employs sophisticated bot detection:
1. **Multiple detection vectors:**
   - Browser fingerprinting (Canvas, WebGL, fonts)
   - CDP (Chrome DevTools Protocol) detection
   - Request timing patterns
   - Missing browser features (extensions, permissions)
   - Session behavior analysis

2. **Cookie-based session management:**
   - Even with valid cookies, LinkedIn can invalidate sessions server-side
   - Requires multiple cookies for full authentication
   - Cookies expire/rotate frequently

3. **Active countermeasures:**
   - Redirect loops to block automated browsers
   - Session invalidation when automation detected
   - Rate limiting and IP-based blocking

## Workaround Implemented

**Manual HTML Paste Mode:**
- User visits job page in regular browser
- User inspects page source and copies HTML
- User pastes HTML into application
- Parser processes HTML directly without fetching

This bypasses all bot detection since no automated requests are made.

## Future Solutions to Consider

1. **LinkedIn Official API:**
   - Requires LinkedIn partnership/API access
   - Limited endpoints, may not have job posting details
   - Likely expensive

2. **Real Browser Profile:**
   - Use actual Chrome user profile with logged-in session
   - Playwright can launch with existing profile: `user_data_dir`
   - More human-like but requires user's Chrome profile path

3. **Human Timing Patterns:**
   - Add random delays between actions (2-5 seconds)
   - Mouse movements and scrolling simulation
   - Make requests look more human-like

4. **Rotating Proxies:**
   - Use residential proxies to avoid IP blocking
   - Rotate user agents and browser fingerprints
   - Expensive and requires proxy service subscription

5. **Paid Scraping Services:**
   - ScrapingBee, ScraperAPI, Bright Data
   - Handle bot detection and proxies
   - Monthly cost for API access

6. **Accept Limitations:**
   - Manual entry for LinkedIn jobs
   - Focus automation on sites with less aggressive bot detection
   - Use HTML paste mode as workaround

## Technical Details

### Packages Installed
```bash
uv add playwright-stealth  # v2.0.2
```

### Code Changes Made
- `browser_fetcher.py`: Added stealth mode and multi-cookie support
- `.env`: Added fields for 5 LinkedIn cookies

### Cookies Required for LinkedIn
From DevTools → Application → Cookies → linkedin.com:
- `li_at` - Main authentication token
- `JSESSIONID` - Session ID (format: `ajax:1234567890123456789`)
- `liap` - Authentication flag (value: `true`)
- `bcookie` - Browser cookie (format: `"v=2&uuid"`)
- `bscookie` - Browser session cookie (format: `"v=1&timestamp+uuid"`)

## Recommendation

For a personal job tracker, the **HTML paste mode** is the most practical solution:
- No ongoing arms race with LinkedIn's bot detection
- Works reliably every time
- No API costs or proxy services needed
- User maintains full control

For production scraping at scale, consider paid scraping services or LinkedIn's official API.

## Related Files
- `backend/browser_fetcher.py` - Browser automation with stealth
- `backend/job_parser.py` - Job parsing logic
- `backend/.env` - Cookie configuration
- `.claude/plans/cozy-orbiting-crescent.md` - Original fetch_mode plan
