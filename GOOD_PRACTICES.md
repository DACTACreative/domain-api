# Domain API Project - Good Practices Guide

## Project Structure
- All code is hosted on GitHub: https://github.com/DACTACreative/domain-api
- Test page is hosted on GitHub Pages: https://dactacreative.github.io/domain-api/test.html
- API server is hosted on Render: https://domain-api-dacta.onrender.com

## Development Guidelines

### 1. GitHub-First Approach
- Always work directly on GitHub
- Never rely on local development
- Use GitHub's web interface for quick edits
- For larger changes, use GitHub Codespaces

### 2. Deployment
- Frontend (Test Page):
  - Automatically deployed to GitHub Pages
  - URL: https://dactacreative.github.io/domain-api/test.html
  - Updates when changes are pushed to main branch

- Backend (API Server):
  - Hosted on Render.com
  - URL: https://domain-api-dacta.onrender.com
  - Auto-deploys from GitHub main branch

### 3. API Endpoints
Always use the deployed URLs:
```javascript
// API Base URL
const API_BASE = 'https://domain-api-dacta.onrender.com';

// Test Connection
fetch(`${API_BASE}/test-domain`);

// Search Listings
fetch(`${API_BASE}/search-listings/${suburb}`);
```

### 4. Testing Changes
1. Make changes in GitHub
2. Commit to main branch
3. GitHub Pages will auto-update (usually within 1-2 minutes)
4. Test at https://dactacreative.github.io/domain-api/test.html

### 5. Environment Variables
- Store all sensitive data (API keys, secrets) in Render.com environment variables
- Never commit sensitive data to GitHub
- Use placeholder values in example code

### 6. Documentation
- Keep README.md updated with latest changes
- Document all API endpoints
- Include example requests and responses
- Add troubleshooting guides

### 7. Version Control
- Use meaningful commit messages
- Group related changes in single commits
- Push changes frequently to keep everything in sync

### 8. Error Handling
- Always include proper error messages
- Log errors on the server
- Show user-friendly error messages in UI

## Quick Reference

### Important URLs
- GitHub Repository: https://github.com/DACTACreative/domain-api
- Test Page: https://dactacreative.github.io/domain-api/test.html
- API Server: https://domain-api-dacta.onrender.com

### Common Tasks
1. Update Test Page:
   - Edit test.html in GitHub
   - Commit changes
   - Test at GitHub Pages URL

2. Update API:
   - Edit main.py in GitHub
   - Commit changes
   - Render will auto-deploy

3. View Logs:
   - Check Render.com dashboard for API logs
   - Use browser console for test page logs

### Remember
- Always use deployed URLs
- Never rely on localhost
- Keep everything in GitHub
- Test changes on live URLs
