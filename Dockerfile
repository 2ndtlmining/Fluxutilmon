# Use the Python slim image as the base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY . .

# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Set the appropriate permissions for the project files
RUN chmod -R 755 /app

# Expose any necessary ports
EXPOSE 8049

# Set the command to run when the container starts
CMD ["python3", "app.py"]