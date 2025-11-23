# Development Dockerfile for Next.js frontend with hot reload

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source files
COPY . .

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Run development server
CMD ["npm", "run", "dev"]
