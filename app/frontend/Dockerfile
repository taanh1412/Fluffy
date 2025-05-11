FROM nginx:alpine

# Copy frontend files explicitly
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY main.js /usr/share/nginx/html/

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]