# Deployment Guide

## Building for Production

### 1. Create Production Build

```bash
npm run build
```

This will:
- Compile TypeScript to JavaScript
- Bundle and minify all assets
- Optimize images and fonts
- Generate source maps
- Output to `dist/` directory

### 2. Preview Production Build Locally

```bash
npm run preview
```

This serves the production build locally for testing.

## Deployment Options

### Option 1: Static Hosting (Vercel, Netlify, GitHub Pages)

#### Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

#### Netlify
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod
```

#### GitHub Pages
```bash
# Add to package.json
"homepage": "https://yourusername.github.io/mainframe-ui"

# Deploy
npm run build
npx gh-pages -d dist
```

### Option 2: Docker Container

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Build and run:
```bash
docker build -t mainframe-ui .
docker run -p 8080:80 mainframe-ui
```

### Option 3: AWS S3 + CloudFront

```bash
# Build
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Environment Variables

Create `.env.production`:
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
```

Access in code:
```typescript
const API_URL = import.meta.env.VITE_API_BASE_URL;
```

## Performance Optimization

### 1. Enable Compression
Most hosting platforms enable gzip/brotli automatically. For custom servers:

**Nginx:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### 2. Caching Strategy
Configure cache headers:

**Nginx:**
```nginx
location /assets {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location / {
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

### 3. CDN Configuration
- Enable CDN for static assets
- Configure proper cache policies
- Use edge locations near your users

## Security Considerations

### 1. HTTPS Only
Always serve over HTTPS in production.

### 2. Security Headers
Add these headers to your server config:

```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;";
```

### 3. API Security
- Use environment variables for API endpoints
- Implement proper CORS policies
- Use authentication tokens
- Enable rate limiting

## Health Checks

Create a simple health check endpoint:

**Static hosting:** Add `health.html` to public folder
**Docker:** Add to nginx config:
```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

## Monitoring

### 1. Analytics
Add analytics to `index.html`:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
```

### 2. Error Tracking
Integrate Sentry or similar:
```bash
npm install @sentry/react
```

### 3. Performance Monitoring
Use Lighthouse CI for continuous performance monitoring.

## Rollback Strategy

### Git-based Deployment
```bash
# Tag current release
git tag -a v1.0.0 -m "Release 1.0.0"

# Rollback to previous tag
git checkout v0.9.9
npm run build
# Deploy
```

### Docker-based Deployment
```bash
# Tag images
docker tag mainframe-ui:latest mainframe-ui:v1.0.0

# Rollback
docker run mainframe-ui:v0.9.9
```

## CI/CD Pipeline Example

**GitHub Actions (.github/workflows/deploy.yml):**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Build
        run: npm run build
        
      - name: Deploy to Vercel
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

## Post-Deployment Checklist

- [ ] Verify all pages load correctly
- [ ] Test navigation between routes
- [ ] Confirm API endpoints are connecting
- [ ] Check console for errors
- [ ] Test on mobile devices
- [ ] Verify SSL certificate
- [ ] Test with different browsers
- [ ] Check performance metrics
- [ ] Verify security headers
- [ ] Test error pages (404, etc.)

## Troubleshooting

### Routes not working (404 on refresh)
Configure server to serve `index.html` for all routes.

### Assets not loading
Check base path in `vite.config.ts`:
```typescript
export default defineConfig({
  base: '/your-subdirectory/',
})
```

### CORS errors
Configure backend CORS or use proxy in production.

## Support

For deployment issues:
1. Check build logs for errors
2. Verify environment variables
3. Test production build locally first
4. Check browser console for errors
5. Review server/CDN logs

---

Happy deploying! 🚀
