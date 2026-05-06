FROM node:20-alpine

WORKDIR /app

# Install dependencies first for layer caching
COPY package.json package-lock.json* ./
RUN npm install

# Copy application files
COPY . .

# Expose Vite port
EXPOSE 5173

# Run the dev server bound to all network interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
