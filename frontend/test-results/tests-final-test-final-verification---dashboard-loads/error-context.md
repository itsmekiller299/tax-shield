# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/final-test.test.ts >> final verification - dashboard loads
- Location: tests/final-test.test.ts:3:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.readiness-score')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.readiness-score') with timeout 5000ms
  - waiting for locator('.readiness-score')

```

```yaml
- complementary:
  - link "Tax Shield":
    - /url: /dashboard
    - img
    - text: Tax Shield
  - navigation "Main navigation":
    - link "Dashboard":
      - /url: /dashboard
    - link "Transactions":
      - /url: /transactions
    - link "Documents":
      - /url: /documents
    - link "Obligations":
      - /url: /obligations
    - link "Deadlines":
      - /url: /deadlines
    - link "Scenarios":
      - /url: /scenarios
    - link "Reports":
      - /url: /reports
    - link "Settings":
      - /url: /settings
  - paragraph: Tax Shield v1.0.0
- banner:
  - heading "Dashboard" [level=1]
  - button "Notifications":
    - img
    - text: "3"
  - button "User":
    - img
    - text: User
    - img
- main
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | 
  3  | test('final verification - dashboard loads', async ({ page }) => {
  4  |   await page.goto('http://localhost:3000/dashboard')
  5  |   await expect(page).toHaveURL('http://localhost:3000/dashboard')
  6  |   await expect(page.locator('h1')).toContainText('Dashboard')
> 7  |   await expect(page.locator('.readiness-score')).toBeVisible()
     |                                                  ^ Error: expect(locator).toBeVisible() failed
  8  | })
  9  | 
  10 | test('final verification - API endpoints', async ({ request }) => {
  11 |   const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlcjhAZXhhbXBsZS5jb20iLCJleHAiOjE3ODkxNTczODl9.-EXIInysFKP7fYKTegtEObgRANBvOE9YVgK_4upqK_w'
  12 |   const dashboard = await request.get('http://localhost:8000/api/dashboard', {
  13 |     headers: { Authorization: `Bearer ${token}` }
  14 |   })
  15 |   expect(dashboard.status()).toBe(200)
  16 |   const dr = await dashboard.json()
  17 |   expect(dr).toHaveProperty('readiness_score')
  18 |   
  19 |   const score = await request.get('http://localhost:8000/api/readiness-score', {
  20 |     headers: { Authorization: `Bearer ${token}` }
  21 |   })
  22 |   expect(score.status()).toBe(200)
  23 |   const sr = await score.json()
  24 |   expect(sr).toHaveProperty('score')
  25 | })
  26 | 
```