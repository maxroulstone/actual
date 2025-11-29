FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY src ./src
COPY data ./data

# Build the project
RUN npm run build

# Expose port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
