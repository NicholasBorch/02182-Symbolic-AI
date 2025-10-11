FROM ghcr.io/mavis-dtu/02182-base:latest

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Install student defined dependencies.
# Separated to improve the caching of the build steps.
COPY requirements.students.txt /tmp/
RUN pip3 install -r /tmp/requirements.students.txt
