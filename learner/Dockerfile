FROM python:3.10-slim-buster
# Install python packages
COPY requirements.txt /tmp

RUN apt update

RUN apt install -y libpq-dev python-dev gcc

RUN pip install --upgrade pip


WORKDIR /usr/src/app
# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Command to run the app
CMD ["python", "./main.py"]